"""API routes for dashboard statistics and data."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from server.database import get_db_connection, return_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/dashboard/stats')
async def get_dashboard_stats() -> Dict[str, Any]:
  """Get dashboard statistics."""
  try:
    conn = get_db_connection()

    with conn.cursor() as cursor:
      # Get job statistics
      cursor.execute("""
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_jobs,
                    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs
                FROM information_extraction.extraction_jobs
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
      job_stats = cursor.fetchone()

      # Get schema statistics
      cursor.execute("""
                SELECT
                    COUNT(*) as total_schemas,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active_schemas
                FROM information_extraction.extraction_schemas
            """)
      schema_stats = cursor.fetchone()

      # Get document statistics
      cursor.execute("""
                SELECT
                    COUNT(*) as total_documents,
                    COALESCE(SUM(file_size), 0) as total_file_size
                FROM information_extraction.documents d
                JOIN information_extraction.extraction_jobs j ON d.job_id = j.id
                WHERE j.created_at >= NOW() - INTERVAL '30 days'
            """)
      doc_stats = cursor.fetchone()

      # Get extraction results count
      cursor.execute("""
                SELECT COUNT(*) as total_results
                FROM information_extraction.extraction_results r
                JOIN information_extraction.extraction_jobs j ON r.job_id = j.id
                WHERE j.created_at >= NOW() - INTERVAL '30 days'
            """)
      result_stats = cursor.fetchone()

      # Calculate success rate
      total_jobs = job_stats[0] if job_stats[0] > 0 else 1
      completed_jobs = job_stats[3]
      success_rate = round((completed_jobs / total_jobs) * 100, 1)

      return {
        'total_jobs': job_stats[0],
        'pending_jobs': job_stats[1],
        'processing_jobs': job_stats[2],
        'completed_jobs': job_stats[3],
        'failed_jobs': job_stats[4],
        'total_schemas': schema_stats[0],
        'active_schemas': schema_stats[1],
        'total_documents': doc_stats[0],
        'total_file_size': doc_stats[1],
        'total_results': result_stats[0],
        'success_rate': success_rate,
        'last_updated': 'now',
      }

  except Exception as e:
    logger.error(f'Error fetching dashboard stats: {str(e)}')
    raise HTTPException(status_code=500, detail=f'Failed to fetch dashboard stats: {str(e)}')
  finally:
    if 'conn' in locals():
      return_db_connection(conn)


@router.get('/dashboard/recent-activity')
async def get_recent_activity() -> Dict[str, Any]:
  """Get recent activity for dashboard."""
  try:
    conn = get_db_connection()

    with conn.cursor() as cursor:
      # Get recent jobs with their details
      cursor.execute("""
                SELECT
                    j.id,
                    j.name,
                    j.status,
                    j.created_at,
                    j.completed_at,
                    s.name as schema_name,
                    COUNT(d.id) as document_count,
                    COUNT(r.id) as result_count
                FROM information_extraction.extraction_jobs j
                LEFT JOIN information_extraction.extraction_schemas s ON j.schema_id = s.id
                LEFT JOIN information_extraction.documents d ON j.id = d.job_id
                LEFT JOIN information_extraction.extraction_results r ON j.id = r.job_id
                GROUP BY j.id, j.name, j.status, j.created_at, j.completed_at, s.name
                ORDER BY j.created_at DESC
                LIMIT 10
            """)

      activities = []
      for row in cursor.fetchall():
        job_id, name, status, created_at, completed_at, schema_name, doc_count, result_count = row

        # Determine activity type and message
        if status == 'completed':
          activity_type = 'success'
          message = f'Completed extraction of {result_count} results from {doc_count} documents'
        elif status == 'processing':
          activity_type = 'process'
          message = f'Processing {doc_count} documents'
        elif status == 'failed':
          activity_type = 'error'
          message = f'Failed to process {doc_count} documents'
        else:
          activity_type = 'upload'
          message = f'Uploaded {doc_count} documents for processing'

        activities.append(
          {
            'id': str(job_id),
            'user': 'System',  # Could be enhanced to track actual users
            'action': message,
            'schema': schema_name or 'Unknown Schema',
            'timestamp': created_at.isoformat() if created_at else None,
            'type': activity_type,
            'job_id': job_id,
          }
        )

      return {'activities': activities}

  except Exception as e:
    logger.error(f'Error fetching recent activity: {str(e)}')
    raise HTTPException(status_code=500, detail=f'Failed to fetch recent activity: {str(e)}')
  finally:
    if 'conn' in locals():
      return_db_connection(conn)
