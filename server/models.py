"""Pydantic models for Information Extraction App."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# SCHEMA FIELD MODELS
# ============================================================================

class SchemaField(BaseModel):
    """Individual field definition in an extraction schema."""
    name: str = Field(..., min_length=1, max_length=100)
    type: Literal['text', 'number', 'date', 'currency', 'percentage']
    required: bool = False
    description: str = Field(default='', max_length=500)


# ============================================================================
# EXTRACTION SCHEMA MODELS
# ============================================================================

class ExtractionSchemaCreate(BaseModel):
    """Request to create a new extraction schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default='', max_length=1000)
    fields: List[SchemaField] = Field(..., min_items=1, max_items=50)


class ExtractionSchemaUpdate(BaseModel):
    """Update an existing extraction schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    fields: Optional[List[SchemaField]] = Field(None, min_items=1, max_items=50)
    is_active: Optional[bool] = None


class ExtractionSchema(BaseModel):
    """Full extraction schema record."""
    id: int
    name: str
    description: str
    fields: List[SchemaField]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionSchemaSummary(BaseModel):
    """Summary view of extraction schema for listings."""
    id: int
    name: str
    description: str
    fields_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# EXTRACTION JOB MODELS
# ============================================================================

class ExtractionJobCreate(BaseModel):
    """Request to create a new extraction job."""
    name: str = Field(..., min_length=1, max_length=255)
    schema_id: int = Field(..., gt=0)


class ExtractionJobUpdate(BaseModel):
    """Update an existing extraction job."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[Literal['pending', 'processing', 'completed', 'failed']] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    databricks_run_id: Optional[int] = None


class ExtractionJob(BaseModel):
    """Full extraction job record."""
    id: int
    name: str
    schema_id: int
    status: str
    upload_directory: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    databricks_run_id: Optional[int] = None

    class Config:
        from_attributes = True


class ExtractionJobSummary(BaseModel):
    """Summary view of extraction job for listings."""
    id: int
    name: str
    schema_name: str
    status: str
    documents_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# DOCUMENT MODELS
# ============================================================================

class Document(BaseModel):
    """Document record."""
    id: int
    job_id: int
    filename: str
    file_path: str
    file_size: int
    upload_time: datetime

    class Config:
        from_attributes = True


class DocumentSummary(BaseModel):
    """Summary view of document for listings."""
    id: int
    filename: str
    file_size: int
    upload_time: datetime

    class Config:
        from_attributes = True


# ============================================================================
# EXTRACTION RESULT MODELS
# ============================================================================

class ExtractionResult(BaseModel):
    """Extraction result record."""
    id: int
    job_id: int
    document_id: int
    schema_id: int
    extracted_data: Dict[str, Any]
    confidence_scores: Optional[Dict[str, float]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionResultSummary(BaseModel):
    """Summary view of extraction results."""
    document_filename: str
    extracted_data: Dict[str, Any]
    confidence_scores: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True


# ============================================================================
# API RESPONSE MODELS
# ============================================================================

class FileUploadResponse(BaseModel):
    """Response for file upload operations."""
    success: bool
    message: str
    job_id: int
    uploaded_files: List[str]
    file_count: int


class JobStatusResponse(BaseModel):
    """Response for job status checks."""
    job_id: int
    status: str
    progress_percent: Optional[int] = None
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    databricks_run_id: Optional[int] = None


class JobResultsResponse(BaseModel):
    """Response for job results."""
    job_id: int
    job_name: str
    schema_name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: List[ExtractionResultSummary]


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    service: str = 'information-extraction-app'


# ============================================================================
# DATABASE TABLE MODELS (for raw database interactions)
# ============================================================================

class DBExtractionSchema(BaseModel):
    """Database model for extraction_schemas table."""
    id: Optional[int] = None
    name: str
    description: str
    fields: str  # JSON string
    is_active: bool = True
    created_at: Optional[datetime] = None


class DBExtractionJob(BaseModel):
    """Database model for extraction_jobs table."""
    id: Optional[int] = None
    name: str
    schema_id: int
    status: str = 'pending'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    databricks_run_id: Optional[int] = None


class DBDocument(BaseModel):
    """Database model for documents table."""
    id: Optional[int] = None
    job_id: int
    filename: str
    file_path: str
    file_size: int
    upload_time: Optional[datetime] = None


class DBExtractionResult(BaseModel):
    """Database model for extraction_results table."""
    id: Optional[int] = None
    job_id: int
    document_id: int
    schema_id: int
    extracted_data: str  # JSON string
    confidence_scores: Optional[str] = None  # JSON string
    created_at: Optional[datetime] = None