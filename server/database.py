"""Database connection and operations for Information Extraction App."""

import json
import logging
import traceback
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool

from server.models import (
  DBDocument,
  DBExtractionJob,
  DBExtractionResult,
  DBExtractionSchema,
  Document,
  ExtractionJob,
  ExtractionSchema,
  ExtractionSchemaSummary,
  SchemaField,
)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

# Global connection pool
_connection_pool: Optional[SimpleConnectionPool] = None


def get_db_config() -> Dict[str, str]:
  """Get database configuration from centralized config system (config/base.yaml)."""
  from server.config import get_config

  config = get_config()

  # Check if database config exists
  if config.database is None:
    raise ValueError(
      'Database configuration not found in config/base.yaml. '
      'Please run the setup wizard: ./setup.sh'
    )

  return {
    'host': config.database.host,
    'port': str(config.database.port),
    'database': config.database.name,
    'user': config.database.user,
    'password': config.database.password,
  }


def init_db_pool() -> None:
  """Initialize the database connection pool."""
  global _connection_pool
  if _connection_pool is None:
    config = get_db_config()
    _connection_pool = SimpleConnectionPool(minconn=1, maxconn=10, **config)


def get_db_connection():
  """Get a database connection from the pool."""
  if _connection_pool is None:
    init_db_pool()
  return _connection_pool.getconn()


def return_db_connection(conn):
  """Return a database connection to the pool."""
  if _connection_pool:
    _connection_pool.putconn(conn)


def close_db_pool() -> None:
  """Close all database connections."""
  global _connection_pool
  if _connection_pool:
    _connection_pool.closeall()
    _connection_pool = None


# ============================================================================
# DATABASE SCHEMA CREATION
# ============================================================================


def create_tables() -> None:
  """Create database tables if they don't exist."""
  logger = logging.getLogger(__name__)
  logger.info('🔧 Starting database initialization...')

  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      # Create schema if it doesn't exist
      logger.info('Creating information_extraction schema...')
      cursor.execute('CREATE SCHEMA IF NOT EXISTS information_extraction')

      # Create extraction_schemas table (updated to match notebook expectations)
      logger.info('Creating extraction_schemas table...')
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS information_extraction.extraction_schemas (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    fields TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

      # Migrate existing schema_definition column to fields column
      cursor.execute("""
                DO $$
                BEGIN
                    -- Check if schema_definition column exists and fields doesn't
                    IF EXISTS (SELECT 1 FROM information_schema.columns
                              WHERE table_schema = 'information_extraction'
                              AND table_name = 'extraction_schemas'
                              AND column_name = 'schema_definition')
                       AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                                      WHERE table_schema = 'information_extraction'
                                      AND table_name = 'extraction_schemas'
                                      AND column_name = 'fields') THEN
                        -- Add fields column
                        ALTER TABLE information_extraction.extraction_schemas ADD COLUMN fields TEXT;

                        -- Copy data from schema_definition to fields
                        UPDATE information_extraction.extraction_schemas SET fields = schema_definition;

                        -- Make fields NOT NULL
                        ALTER TABLE information_extraction.extraction_schemas ALTER COLUMN fields SET NOT NULL;

                        -- Drop old column
                        ALTER TABLE information_extraction.extraction_schemas DROP COLUMN schema_definition;
                    END IF;
                END $$;
            """)

      # Create extraction_jobs table (updated with upload_directory)
      logger.info('Creating extraction_jobs table...')
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS information_extraction.extraction_jobs (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    schema_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'not_submitted',
                    upload_directory TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    databricks_run_id BIGINT,
                    FOREIGN KEY (schema_id) REFERENCES information_extraction.extraction_schemas (id)
                )
            """)

      # === TABLE CREATION FIRST ===

      # Create documents table
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS information_extraction.documents (
                    id SERIAL PRIMARY KEY,
                    job_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES information_extraction.extraction_jobs (id)
                )
            """)

      # Create extraction_results table
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS information_extraction.extraction_results (
                    id SERIAL PRIMARY KEY,
                    job_id INTEGER NOT NULL,
                    document_id INTEGER NOT NULL,
                    schema_id INTEGER NOT NULL,
                    extracted_data TEXT NOT NULL,
                    confidence_scores TEXT,
                    file_content_checksum TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES information_extraction.extraction_jobs (id),
                    FOREIGN KEY (document_id) REFERENCES information_extraction.documents (id),
                    FOREIGN KEY (schema_id) REFERENCES information_extraction.extraction_schemas (id)
                )
            """)

      # Create upload_logs table (required by notebook)
      cursor.execute("""
                CREATE TABLE IF NOT EXISTS information_extraction.upload_logs (
                    id SERIAL PRIMARY KEY,
                    analysis_id INTEGER NOT NULL,
                    upload_directory TEXT NOT NULL,
                    event_type TEXT DEFAULT 'upload',
                    message TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES information_extraction.extraction_jobs (id)
                )
            """)

      # Create indexes for better performance
      cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_jobs_status ON information_extraction.extraction_jobs (status)'
      )
      cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_jobs_schema_id ON information_extraction.extraction_jobs (schema_id)'
      )
      cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_documents_job_id ON information_extraction.documents (job_id)'
      )
      cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_results_job_id ON information_extraction.extraction_results (job_id)'
      )
      cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_upload_logs_analysis_id ON information_extraction.upload_logs (analysis_id)'
      )

      # === DATABASE MIGRATIONS (Run after all tables are created) ===
      logger.info('🔄 Running database migrations after table creation...')

      # Add upload_directory column to extraction_jobs if it doesn't exist
      logger.info('🔄 Adding upload_directory column to extraction_jobs...')
      cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                  WHERE table_schema = 'information_extraction'
                                  AND table_name = 'extraction_jobs'
                                  AND column_name = 'upload_directory') THEN
                        ALTER TABLE information_extraction.extraction_jobs ADD COLUMN upload_directory TEXT;
                    END IF;
                END $$;
            """)

      # Add user tracking columns for auditing
      logger.info('🔄 Adding user tracking columns for audit trail...')
      cursor.execute("""
                DO $$
                BEGIN
                    -- Add created_by to extraction_schemas
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                  WHERE table_schema = 'information_extraction'
                                  AND table_name = 'extraction_schemas'
                                  AND column_name = 'created_by') THEN
                        ALTER TABLE information_extraction.extraction_schemas ADD COLUMN created_by VARCHAR(255);
                    END IF;

                    -- Add created_by to extraction_jobs
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                  WHERE table_schema = 'information_extraction'
                                  AND table_name = 'extraction_jobs'
                                  AND column_name = 'created_by') THEN
                        ALTER TABLE information_extraction.extraction_jobs ADD COLUMN created_by VARCHAR(255);
                    END IF;

                    -- Add user_id to upload_logs
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                  WHERE table_schema = 'information_extraction'
                                  AND table_name = 'upload_logs'
                                  AND column_name = 'user_id') THEN
                        ALTER TABLE information_extraction.upload_logs ADD COLUMN user_id VARCHAR(255);
                    END IF;

                    -- Add user_email for better user identification
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                  WHERE table_schema = 'information_extraction'
                                  AND table_name = 'upload_logs'
                                  AND column_name = 'user_email') THEN
                        ALTER TABLE information_extraction.upload_logs ADD COLUMN user_email VARCHAR(255);
                    END IF;
                END $$;
            """)

      # Migrate databricks_run_id column from INTEGER to BIGINT to support 64-bit run IDs
      logger.info('🔄 Migrating databricks_run_id column from INTEGER to BIGINT...')
      cursor.execute("""
                DO $$
                BEGIN
                    -- Check if the column exists and is INTEGER type
                    IF EXISTS (SELECT 1 FROM information_schema.columns
                              WHERE table_schema = 'information_extraction'
                              AND table_name = 'extraction_jobs'
                              AND column_name = 'databricks_run_id'
                              AND data_type = 'integer') THEN
                        -- Alter the column type to BIGINT
                        ALTER TABLE information_extraction.extraction_jobs
                        ALTER COLUMN databricks_run_id TYPE BIGINT;
                    END IF;
                END $$;
            """)

      # Add file_content_checksum column to extraction_results table if it doesn't exist
      logger.info('🔄 Adding file_content_checksum column to extraction_results...')
      cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                  WHERE table_schema = 'information_extraction'
                                  AND table_name = 'extraction_results'
                                  AND column_name = 'file_content_checksum') THEN
                        ALTER TABLE information_extraction.extraction_results ADD COLUMN file_content_checksum TEXT;
                    END IF;
                END $$;
            """)

      # Add unique constraint for upsert operations (job_id, document_id, schema_id)
      logger.info('🔄 Adding unique constraint for extraction_results upsert operations...')
      cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints
                                  WHERE table_schema = 'information_extraction'
                                  AND table_name = 'extraction_results'
                                  AND constraint_name = 'unique_job_document_schema') THEN
                        ALTER TABLE information_extraction.extraction_results
                        ADD CONSTRAINT unique_job_document_schema
                        UNIQUE (job_id, document_id, schema_id);
                    END IF;
                END $$;
            """)

      conn.commit()
      logger.info('✅ Database initialization completed successfully!')
      logger.info('✅ BIGINT migration for databricks_run_id completed!')
  except Exception as e:
    logger.error(f'❌ Database initialization failed: {str(e)}')
    logger.error(f'❌ Full traceback: {traceback.format_exc()}')
    conn.rollback()
    raise
  finally:
    return_db_connection(conn)


def test_db_connection() -> bool:
  """Test database connection."""
  try:
    conn = get_db_connection()
    with conn.cursor() as cursor:
      cursor.execute('SELECT 1')
      result = cursor.fetchone()
    return_db_connection(conn)
    return result[0] == 1
  except Exception:
    return False


# ============================================================================
# EXTRACTION SCHEMA OPERATIONS
# ============================================================================


def create_extraction_schema(schema: DBExtractionSchema, created_by: str = 'System') -> int:
  """Create a new extraction schema and return its ID."""
  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      cursor.execute(
        """
                INSERT INTO information_extraction.extraction_schemas (name, description, fields, is_active, created_by)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """,
        (schema.name, schema.description, schema.fields, schema.is_active, created_by),
      )
      schema_id = cursor.fetchone()[0]
      conn.commit()
      return schema_id
  finally:
    return_db_connection(conn)


def get_extraction_schema(schema_id: int) -> Optional[ExtractionSchema]:
  """Get extraction schema by ID."""
  conn = get_db_connection()
  try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
      cursor.execute(
        """
                SELECT id, name, description, fields, is_active, created_at
                FROM information_extraction.extraction_schemas
                WHERE id = %s
            """,
        (schema_id,),
      )
      row = cursor.fetchone()
      if row:
        fields = json.loads(row['fields'])
        return ExtractionSchema(
          id=row['id'],
          name=row['name'],
          description=row['description'],
          fields=[SchemaField(**field) for field in fields],
          is_active=row['is_active'],
          created_at=row['created_at'],
        )
      return None
  finally:
    return_db_connection(conn)


def get_all_extraction_schemas() -> List[ExtractionSchemaSummary]:
  """Get all extraction schemas with summary information."""
  conn = get_db_connection()
  try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
      cursor.execute("""
                SELECT
                    id,
                    name,
                    description,
                    fields,
                    is_active,
                    created_at
                FROM information_extraction.extraction_schemas
                ORDER BY created_at DESC
            """)
      rows = cursor.fetchall()
      schemas = []
      for row in rows:
        fields = json.loads(row['fields'])
        schemas.append(
          ExtractionSchemaSummary(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            fields_count=len(fields),
            is_active=row['is_active'],
            created_at=row['created_at'],
          )
        )
      return schemas
  finally:
    return_db_connection(conn)


def update_extraction_schema(schema_id: int, updates: Dict[str, Any]) -> bool:
  """Update extraction schema."""
  if not updates:
    return False

  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      set_clauses = []
      values = []

      for key, value in updates.items():
        if key in ['name', 'description', 'fields', 'is_active']:
          set_clauses.append(f'{key} = %s')
          values.append(value)

      if not set_clauses:
        return False

      values.append(schema_id)

      cursor.execute(
        f"""
                UPDATE information_extraction.extraction_schemas
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """,
        values,
      )

      affected_rows = cursor.rowcount
      conn.commit()
      return affected_rows > 0
  finally:
    return_db_connection(conn)


def delete_extraction_schema(schema_id: int) -> bool:
  """Delete extraction schema."""
  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      cursor.execute(
        'DELETE FROM information_extraction.extraction_schemas WHERE id = %s', (schema_id,)
      )
      affected_rows = cursor.rowcount
      conn.commit()
      return affected_rows > 0
  finally:
    return_db_connection(conn)


# ============================================================================
# EXTRACTION JOB OPERATIONS
# ============================================================================


def create_extraction_job(job: DBExtractionJob, created_by: str = 'System') -> int:
  """Create a new extraction job and return its ID."""
  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      cursor.execute(
        """
                INSERT INTO information_extraction.extraction_jobs (name, schema_id, status, created_by)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """,
        (job.name, job.schema_id, job.status, created_by),
      )
      job_id = cursor.fetchone()[0]
      conn.commit()
      return job_id
  finally:
    return_db_connection(conn)


def get_extraction_job(job_id: int) -> Optional[ExtractionJob]:
  """Get extraction job by ID."""
  conn = get_db_connection()
  try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
      cursor.execute(
        """
                SELECT id, name, schema_id, status, created_at, updated_at,
                       completed_at, error_message, databricks_run_id
                FROM information_extraction.extraction_jobs
                WHERE id = %s
            """,
        (job_id,),
      )
      row = cursor.fetchone()
      if row:
        return ExtractionJob(**dict(row))
      return None
  finally:
    return_db_connection(conn)


def get_extraction_job_with_schema(job_id: int) -> Optional[Dict[str, Any]]:
  """Get extraction job by ID with schema name included."""
  conn = get_db_connection()
  try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
      cursor.execute(
        """
                SELECT j.id, j.name, j.schema_id, j.status, j.created_at, j.updated_at,
                       j.completed_at, j.error_message, j.databricks_run_id,
                       s.name as schema_name
                FROM information_extraction.extraction_jobs j
                LEFT JOIN information_extraction.extraction_schemas s ON j.schema_id = s.id
                WHERE j.id = %s
            """,
        (job_id,),
      )
      row = cursor.fetchone()
      if row:
        return dict(row)
      return None
  finally:
    return_db_connection(conn)


def get_all_extraction_jobs() -> List[Dict[str, Any]]:
  """Get all extraction jobs with schema names and proper status logic."""
  conn = get_db_connection()
  try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
      cursor.execute("""
                SELECT
                    j.id,
                    j.name,
                    j.status,
                    j.databricks_run_id,
                    j.created_at,
                    j.completed_at,
                    s.name as schema_name,
                    COALESCE(doc_count.count, 0) as documents_count,
                    -- Calculate proper status based on databricks_run_id
                    CASE
                        WHEN j.databricks_run_id IS NULL AND j.status NOT IN ('failed', 'uploaded')
                        THEN 'not_submitted'
                        ELSE j.status
                    END as computed_status
                FROM information_extraction.extraction_jobs j
                LEFT JOIN information_extraction.extraction_schemas s ON j.schema_id = s.id
                LEFT JOIN (
                    SELECT job_id, COUNT(*) as count
                    FROM information_extraction.documents
                    GROUP BY job_id
                ) doc_count ON j.id = doc_count.job_id
                ORDER BY j.created_at DESC
            """)

      # Convert to list and update status to computed_status
      jobs = []
      for row in cursor.fetchall():
        job_dict = dict(row)
        job_dict['status'] = job_dict['computed_status']  # Use computed status
        del job_dict['computed_status']  # Remove computed field
        jobs.append(job_dict)

      return jobs
  finally:
    return_db_connection(conn)


def get_extraction_jobs_by_schema(schema_id: int) -> List[Dict[str, Any]]:
  """Get all extraction jobs for a specific schema ID."""
  conn = get_db_connection()
  try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
      cursor.execute(
        """
                SELECT
                    j.id,
                    j.name,
                    j.status,
                    j.databricks_run_id,
                    j.created_at,
                    j.completed_at,
                    s.name as schema_name,
                    COALESCE(doc_count.count, 0) as documents_count,
                    -- Calculate proper status based on databricks_run_id
                    CASE
                        WHEN j.databricks_run_id IS NULL AND j.status NOT IN ('failed', 'uploaded')
                        THEN 'not_submitted'
                        ELSE j.status
                    END as computed_status
                FROM information_extraction.extraction_jobs j
                LEFT JOIN information_extraction.extraction_schemas s ON j.schema_id = s.id
                LEFT JOIN (
                    SELECT job_id, COUNT(*) as count
                    FROM information_extraction.documents
                    GROUP BY job_id
                ) doc_count ON j.id = doc_count.job_id
                WHERE j.schema_id = %s
                ORDER BY j.created_at DESC
            """,
        (schema_id,),
      )

      # Convert to list and update status to computed_status
      jobs = []
      for row in cursor.fetchall():
        job_dict = dict(row)
        job_dict['status'] = job_dict['computed_status']  # Use computed status
        del job_dict['computed_status']  # Remove computed field
        jobs.append(job_dict)

      return jobs
  finally:
    return_db_connection(conn)


def update_extraction_job(job_id: int, updates: Dict[str, Any]) -> bool:
  """Update extraction job."""
  if not updates:
    return False

  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      set_clauses = []
      values = []

      # Always update updated_at when making changes
      set_clauses.append('updated_at = CURRENT_TIMESTAMP')

      # Exclude only protected/system fields that shouldn't be directly updated
      protected_fields = {'id', 'created_at', 'updated_at'}

      for key, value in updates.items():
        if key not in protected_fields:
          set_clauses.append(f'{key} = %s')
          values.append(value)

      values.append(job_id)

      cursor.execute(
        f"""
                UPDATE information_extraction.extraction_jobs
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """,
        values,
      )

      affected_rows = cursor.rowcount
      conn.commit()
      return affected_rows > 0
  finally:
    return_db_connection(conn)


# ============================================================================
# DOCUMENT OPERATIONS
# ============================================================================


def create_document(document: DBDocument) -> int:
  """Create a new document record and return its ID."""
  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      cursor.execute(
        """
                INSERT INTO information_extraction.documents (job_id, filename, file_path, file_size)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """,
        (document.job_id, document.filename, document.file_path, document.file_size),
      )
      document_id = cursor.fetchone()[0]
      conn.commit()
      return document_id
  finally:
    return_db_connection(conn)


def get_documents_by_job(job_id: int) -> List[Document]:
  """Get all documents for a job."""
  conn = get_db_connection()
  try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
      cursor.execute(
        """
                SELECT id, job_id, filename, file_path, file_size, upload_time
                FROM information_extraction.documents
                WHERE job_id = %s
                ORDER BY upload_time DESC
            """,
        (job_id,),
      )
      return [Document(**dict(row)) for row in cursor.fetchall()]
  finally:
    return_db_connection(conn)


# ============================================================================
# EXTRACTION RESULT OPERATIONS
# ============================================================================


def create_extraction_result(result: DBExtractionResult) -> int:
  """Create a new extraction result and return its ID."""
  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      cursor.execute(
        """
                INSERT INTO information_extraction.extraction_results
                (job_id, document_id, schema_id, extracted_data, confidence_scores)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """,
        (
          result.job_id,
          result.document_id,
          result.schema_id,
          result.extracted_data,
          result.confidence_scores,
        ),
      )
      result_id = cursor.fetchone()[0]
      conn.commit()
      return result_id
  finally:
    return_db_connection(conn)


def get_results_by_job(job_id: int) -> List[Dict[str, Any]]:
  """Get all extraction results for a job."""
  conn = get_db_connection()
  try:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
      cursor.execute(
        """
                SELECT
                    r.id,
                    r.job_id,
                    r.document_id,
                    r.schema_id,
                    r.extracted_data,
                    r.confidence_scores,
                    r.created_at,
                    d.filename as document_filename
                FROM information_extraction.extraction_results r
                LEFT JOIN information_extraction.documents d ON r.document_id = d.id
                WHERE r.job_id = %s
                ORDER BY r.created_at DESC
            """,
        (job_id,),
      )
      results = []
      for row in cursor.fetchall():
        result_dict = dict(row)
        # Handle NULL or empty extracted_data
        if result_dict['extracted_data']:
          try:
            result_dict['extracted_data'] = json.loads(result_dict['extracted_data'])
          except (json.JSONDecodeError, ValueError):
            result_dict['extracted_data'] = {}
        else:
          result_dict['extracted_data'] = {}

        # Handle NULL or empty confidence_scores
        if result_dict['confidence_scores']:
          try:
            result_dict['confidence_scores'] = json.loads(result_dict['confidence_scores'])
          except (json.JSONDecodeError, ValueError):
            result_dict['confidence_scores'] = {}
        else:
          result_dict['confidence_scores'] = {}

        results.append(result_dict)
      return results
  finally:
    return_db_connection(conn)


# ============================================================================
# UPLOAD LOG OPERATIONS (required by notebook)
# ============================================================================


def create_upload_log(
  analysis_id: int,
  upload_directory: str,
  event_type: str = 'upload',
  message: str = '',
  details: str = '',
  user_id: str = 'System',
  user_email: str = '',
) -> int:
  """Create a new upload log entry and return its ID."""
  conn = get_db_connection()
  try:
    with conn.cursor() as cursor:
      cursor.execute(
        """
                INSERT INTO information_extraction.upload_logs (analysis_id, upload_directory, event_type, message, details, user_id, user_email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """,
        (analysis_id, upload_directory, event_type, message, details, user_id, user_email),
      )
      log_id = cursor.fetchone()[0]
      conn.commit()
      return log_id
  finally:
    return_db_connection(conn)
