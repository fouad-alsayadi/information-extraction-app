"""Database connection and operations for Information Extraction App."""

import json
import os
from datetime import datetime
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
    ExtractionResult,
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
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'information_extraction'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
    }


def init_db_pool() -> None:
    """Initialize the database connection pool."""
    global _connection_pool
    if _connection_pool is None:
        config = get_db_config()
        _connection_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **config
        )


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
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Create schema if it doesn't exist
            cursor.execute("CREATE SCHEMA IF NOT EXISTS information_extraction")

            # Create extraction_schemas table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS information_extraction.extraction_schemas (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    schema_definition TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create extraction_jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS information_extraction.extraction_jobs (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    schema_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    databricks_run_id INTEGER,
                    FOREIGN KEY (schema_id) REFERENCES information_extraction.extraction_schemas (id)
                )
            """)

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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES information_extraction.extraction_jobs (id),
                    FOREIGN KEY (document_id) REFERENCES information_extraction.documents (id),
                    FOREIGN KEY (schema_id) REFERENCES information_extraction.extraction_schemas (id)
                )
            """)

            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON information_extraction.extraction_jobs (status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_schema_id ON information_extraction.extraction_jobs (schema_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_job_id ON information_extraction.documents (job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_job_id ON information_extraction.extraction_results (job_id)")

            conn.commit()
    finally:
        return_db_connection(conn)


def test_db_connection() -> bool:
    """Test database connection."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        return_db_connection(conn)
        return result[0] == 1
    except Exception:
        return False


# ============================================================================
# EXTRACTION SCHEMA OPERATIONS
# ============================================================================

def create_extraction_schema(schema: DBExtractionSchema) -> int:
    """Create a new extraction schema and return its ID."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO information_extraction.extraction_schemas (name, description, schema_definition, is_active)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (schema.name, schema.description, schema.schema_definition, schema.is_active))
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
            cursor.execute("""
                SELECT id, name, description, schema_definition, is_active, created_at
                FROM information_extraction.extraction_schemas
                WHERE id = %s
            """, (schema_id,))
            row = cursor.fetchone()
            if row:
                fields = json.loads(row['schema_definition'])
                return ExtractionSchema(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    fields=[SchemaField(**field) for field in fields],
                    is_active=row['is_active'],
                    created_at=row['created_at']
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
                    schema_definition,
                    is_active,
                    created_at
                FROM information_extraction.extraction_schemas
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            schemas = []
            for row in rows:
                fields = json.loads(row['schema_definition'])
                schemas.append(ExtractionSchemaSummary(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    fields_count=len(fields),
                    is_active=row['is_active'],
                    created_at=row['created_at']
                ))
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
                if key in ['name', 'description', 'schema_definition', 'is_active']:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)

            if not set_clauses:
                return False

            values.append(schema_id)

            cursor.execute(f"""
                UPDATE information_extraction.extraction_schemas
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """, values)

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
            cursor.execute("DELETE FROM information_extraction.extraction_schemas WHERE id = %s", (schema_id,))
            affected_rows = cursor.rowcount
            conn.commit()
            return affected_rows > 0
    finally:
        return_db_connection(conn)


# ============================================================================
# EXTRACTION JOB OPERATIONS
# ============================================================================

def create_extraction_job(job: DBExtractionJob) -> int:
    """Create a new extraction job and return its ID."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO information_extraction.extraction_jobs (name, schema_id, status)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (job.name, job.schema_id, job.status))
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
            cursor.execute("""
                SELECT id, name, schema_id, status, created_at, updated_at,
                       completed_at, error_message, databricks_run_id
                FROM information_extraction.extraction_jobs
                WHERE id = %s
            """, (job_id,))
            row = cursor.fetchone()
            if row:
                return ExtractionJob(**dict(row))
            return None
    finally:
        return_db_connection(conn)


def get_all_extraction_jobs() -> List[Dict[str, Any]]:
    """Get all extraction jobs with schema names."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT
                    j.id,
                    j.name,
                    j.status,
                    j.created_at,
                    j.completed_at,
                    s.name as schema_name,
                    COALESCE(doc_count.count, 0) as documents_count
                FROM information_extraction.extraction_jobs j
                LEFT JOIN information_extraction.extraction_schemas s ON j.schema_id = s.id
                LEFT JOIN (
                    SELECT job_id, COUNT(*) as count
                    FROM information_extraction.documents
                    GROUP BY job_id
                ) doc_count ON j.id = doc_count.job_id
                ORDER BY j.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
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
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")

            for key, value in updates.items():
                if key in ['name', 'status', 'error_message', 'completed_at', 'databricks_run_id']:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)

            values.append(job_id)

            cursor.execute(f"""
                UPDATE information_extraction.extraction_jobs
                SET {', '.join(set_clauses)}
                WHERE id = %s
            """, values)

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
            cursor.execute("""
                INSERT INTO information_extraction.documents (job_id, filename, file_path, file_size)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (document.job_id, document.filename, document.file_path, document.file_size))
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
            cursor.execute("""
                SELECT id, job_id, filename, file_path, file_size, upload_time
                FROM information_extraction.documents
                WHERE job_id = %s
                ORDER BY upload_time DESC
            """, (job_id,))
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
            cursor.execute("""
                INSERT INTO information_extraction.extraction_results
                (job_id, document_id, schema_id, extracted_data, confidence_scores)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                result.job_id,
                result.document_id,
                result.schema_id,
                result.extracted_data,
                result.confidence_scores
            ))
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
            cursor.execute("""
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
            """, (job_id,))
            results = []
            for row in cursor.fetchall():
                result_dict = dict(row)
                result_dict['extracted_data'] = json.loads(result_dict['extracted_data'])
                if result_dict['confidence_scores']:
                    result_dict['confidence_scores'] = json.loads(result_dict['confidence_scores'])
                results.append(result_dict)
            return results
    finally:
        return_db_connection(conn)