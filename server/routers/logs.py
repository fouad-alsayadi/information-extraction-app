"""API routes for system logs and activity tracking."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from server.database import get_db_connection, return_db_connection
from server.dependencies.auth import get_current_user_context, get_user_for_logging

logger = logging.getLogger(__name__)

router = APIRouter()



@router.get('/logs')
async def get_logs(
  limit: int = Query(default=200, ge=1, le=1000),
  offset: int = Query(default=0, ge=0),
  activity_type: Optional[str] = Query(default=None),
  user: Optional[str] = Query(default=None),
  search: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
  """Get user activity logs for business auditing."""
  try:
    conn = get_db_connection()

    with conn.cursor() as cursor:
      # Build the WHERE clause based on filters
      where_conditions = []
      params = []

      if activity_type and activity_type != 'all':
        where_conditions.append('activity_type = %s')
        params.append(activity_type)

      if user and user != 'all':
        where_conditions.append('user_name ILIKE %s')
        params.append(f'%{user}%')

      if search:
        where_conditions.append('(message ILIKE %s OR details ILIKE %s)')
        params.extend([f'%{search}%', f'%{search}%'])

      where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''

      # Get total count
      count_query = f"""
                SELECT COUNT(*)
                FROM (
                    -- File uploads and exports
                    SELECT
                        id,
                        created_at as timestamp,
                        CASE
                            WHEN event_type = 'export' THEN 'Export'
                            WHEN event_type = 'upload' THEN 'Upload'
                            ELSE 'System'
                        END as activity_type,
                        message,
                        details
                    FROM information_extraction.upload_logs

                    UNION ALL

                    -- Job activities (creation and completion)
                    SELECT
                        j.id,
                        j.created_at as timestamp,
                        'Job Creation' as activity_type,
                        CONCAT(COALESCE(j.created_by, 'System'), ' created job "', j.name, '"') as message,
                        CONCAT('Schema: ', s.name) as details
                    FROM information_extraction.extraction_jobs j
                    LEFT JOIN information_extraction.extraction_schemas s ON j.schema_id = s.id

                    UNION ALL

                    -- Job completions/failures
                    SELECT
                        j.id + 10000,
                        COALESCE(j.completed_at, j.updated_at) as timestamp,
                        CASE
                            WHEN j.status = 'completed' THEN 'Job Completion'
                            WHEN j.status = 'failed' THEN 'Job Failure'
                            ELSE 'Job Update'
                        END as activity_type,
                        CONCAT('Job "', j.name, '" ', j.status, ' (triggered by ', COALESCE(j.created_by, 'System'), ')') as message,
                        CONCAT(COALESCE(doc_count.count, 0), ' documents processed') as details
                    FROM information_extraction.extraction_jobs j
                    LEFT JOIN (
                        SELECT job_id, COUNT(*) as count
                        FROM information_extraction.documents
                        GROUP BY job_id
                    ) doc_count ON j.id = doc_count.job_id
                    WHERE j.status IN ('completed', 'failed')

                    UNION ALL

                    -- Schema creation
                    SELECT
                        s.id + 20000,
                        s.created_at as timestamp,
                        'Schema Creation' as activity_type,
                        CONCAT(COALESCE(s.created_by, 'System'), ' created schema "', s.name, '"') as message,
                        s.description as details
                    FROM information_extraction.extraction_schemas s
                ) activities
                {where_clause}
            """

      cursor.execute(count_query, params)
      total_count = cursor.fetchone()[0]

      # Get paginated results
      data_query = f"""
                SELECT
                    id,
                    timestamp,
                    activity_type,
                    message,
                    details,
                    user_name
                FROM (
                    -- File uploads and exports
                    SELECT
                        CONCAT('upload_', id) as id,
                        created_at as timestamp,
                        CASE
                            WHEN event_type = 'export' THEN 'Export'
                            WHEN event_type = 'upload' THEN 'Upload'
                            ELSE 'System'
                        END as activity_type,
                        CASE
                            WHEN event_type = 'export' THEN CONCAT(COALESCE(user_email, user_id, 'System'), ' exported results to ', SUBSTRING(upload_directory FROM '[^/]*$'))
                            WHEN event_type = 'upload' THEN CONCAT(COALESCE(user_email, user_id, 'System'), ' uploaded files for processing')
                            ELSE message
                        END as message,
                        details,
                        COALESCE(user_email, user_id, 'System') as user_name
                    FROM information_extraction.upload_logs

                    UNION ALL

                    -- Job creation
                    SELECT
                        CONCAT('job_create_', j.id) as id,
                        j.created_at as timestamp,
                        'Job Creation' as activity_type,
                        CONCAT(COALESCE(j.created_by, 'System'), ' created job "', j.name, '"') as message,
                        CONCAT('Schema: ', s.name) as details,
                        COALESCE(j.created_by, 'System') as user_name
                    FROM information_extraction.extraction_jobs j
                    LEFT JOIN information_extraction.extraction_schemas s ON j.schema_id = s.id

                    UNION ALL

                    -- Job completions/failures
                    SELECT
                        CONCAT('job_status_', j.id) as id,
                        COALESCE(j.completed_at, j.updated_at) as timestamp,
                        CASE
                            WHEN j.status = 'completed' THEN 'Job Completion'
                            WHEN j.status = 'failed' THEN 'Job Failure'
                            ELSE 'Job Update'
                        END as activity_type,
                        CONCAT('Job "', j.name, '" ', j.status, ' (triggered by ', COALESCE(j.created_by, 'System'), ')') as message,
                        CONCAT(COALESCE(doc_count.count, 0), ' documents processed') as details,
                        COALESCE(j.created_by, 'System') as user_name
                    FROM information_extraction.extraction_jobs j
                    LEFT JOIN (
                        SELECT job_id, COUNT(*) as count
                        FROM information_extraction.documents
                        GROUP BY job_id
                    ) doc_count ON j.id = doc_count.job_id
                    WHERE j.status IN ('completed', 'failed')

                    UNION ALL

                    -- Schema creation
                    SELECT
                        CONCAT('schema_', s.id) as id,
                        s.created_at as timestamp,
                        'Schema Creation' as activity_type,
                        CONCAT(COALESCE(s.created_by, 'System'), ' created schema "', s.name, '"') as message,
                        s.description as details,
                        COALESCE(s.created_by, 'System') as user_name
                    FROM information_extraction.extraction_schemas s
                ) activities
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """

      params.extend([limit, offset])
      cursor.execute(data_query, params)

      activities = []
      for row in cursor.fetchall():
        activity_id, timestamp, activity_type, message, details, user_name = row
        activities.append(
          {
            'id': str(activity_id),
            'timestamp': timestamp.isoformat() if timestamp else None,
            'activity_type': activity_type,
            'message': message or '',
            'details': details or '',
            'user': user_name or 'System',
          }
        )

      return {'logs': activities, 'total': total_count, 'limit': limit, 'offset': offset}

  except Exception as e:
    logger.error(f'Error fetching logs: {str(e)}')
    raise HTTPException(status_code=500, detail=f'Failed to fetch logs: {str(e)}')
  finally:
    if 'conn' in locals():
      return_db_connection(conn)


@router.post('/logs/export')
async def log_export_event(
  analysis_id: int,
  filename: str,
  results_count: int,
  user_context: Dict[str, Optional[str]] = Depends(get_current_user_context),
) -> Dict[str, Any]:
  """Log an export event."""
  try:
    conn = get_db_connection()

    with conn.cursor() as cursor:
      user_id = get_user_for_logging(user_context)
      user_email = user_context.get('email', '')

      # Log the export event
      cursor.execute(
        """
                INSERT INTO information_extraction.upload_logs
                (analysis_id, upload_directory, event_type, message, details, user_id, user_email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
        (
          analysis_id,
          f'/exports/{filename}',
          'export',
          f'Results exported to {filename}',
          f'Exported {results_count} results',
          user_id,
          user_email,
        ),
      )

      log_id = cursor.fetchone()[0]
      conn.commit()

      return {'success': True, 'message': 'Export event logged successfully', 'log_id': log_id}

  except Exception as e:
    logger.error(f'Error logging export event: {str(e)}')
    raise HTTPException(status_code=500, detail=f'Failed to log export event: {str(e)}')
  finally:
    if 'conn' in locals():
      return_db_connection(conn)
