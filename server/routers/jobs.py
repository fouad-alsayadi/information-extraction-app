"""API routes for extraction job management."""

import logging
import os
import traceback
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

logger = logging.getLogger(__name__)
from databricks.sdk import WorkspaceClient

from server.database import (
  create_document,
  create_extraction_job,
  create_upload_log,
  get_all_extraction_jobs,
  get_documents_by_job,
  get_extraction_job,
  get_extraction_schema,
  get_results_by_job,
  update_extraction_job,
)
from server.dependencies.auth import get_current_user_context, get_user_for_logging
from server.models import (
  DBDocument,
  DBExtractionJob,
  ExtractionJobCreate,
  FileUploadResponse,
  JobResultsResponse,
  JobStatusResponse,
)
from server.services.databricks_service import DatabricksService

router = APIRouter()

# File upload configuration for UC Volumes
UPLOAD_BASE_PATH = os.getenv(
  'UPLOAD_BASE_PATH', '/Volumes/fouad_demos/portfolio_analysis/information_extraction_uploads/'
)
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_workspace_client() -> WorkspaceClient:
  """Get Databricks workspace client."""
  return WorkspaceClient()


def upload_to_uc_volumes(file_content: bytes, file_path: str) -> None:
  """Upload file content to UC Volumes using Databricks workspace API."""
  client = get_workspace_client()

  # Upload to UC Volumes using workspace files API
  client.files.upload(file_path=str(file_path), contents=file_content, overwrite=True)


@router.get('/jobs', response_model=List[dict])
async def get_jobs():
  """Get all extraction jobs with summary information."""
  try:
    return get_all_extraction_jobs()
  except Exception as e:
    logger.error(f'Error fetching jobs: {str(e)}')
    logger.error(f'Full traceback: {traceback.format_exc()}')
    raise HTTPException(status_code=500, detail=f'Failed to fetch jobs: {str(e)}')


@router.post('/jobs', response_model=dict)
async def create_job(
  job: ExtractionJobCreate,
  user_context: Dict[str, Optional[str]] = Depends(get_current_user_context),
):
  """Create a new extraction job."""
  try:
    # Verify schema exists
    schema = get_extraction_schema(job.schema_id)
    if not schema:
      raise HTTPException(status_code=404, detail='Schema not found')

    db_job = DBExtractionJob(
      name=job.name,
      schema_id=job.schema_id,
    )

    user_id = get_user_for_logging(user_context)
    job_id = create_extraction_job(db_job, created_by=user_id)

    return {
      'success': True,
      'message': 'Job created successfully',
      'job_id': job_id,
    }
  except HTTPException:
    raise
  except Exception as e:
    logger.error(f'Error creating job: {str(e)}')
    logger.error(f'Full traceback: {traceback.format_exc()}')
    raise HTTPException(status_code=500, detail=f'Failed to create job: {str(e)}')


@router.get('/jobs/{job_id}', response_model=dict)
async def get_job(job_id: int):
  """Get job details with documents and results."""
  try:
    job = get_extraction_job(job_id)
    if not job:
      raise HTTPException(status_code=404, detail='Job not found')

    documents = get_documents_by_job(job_id)
    results = get_results_by_job(job_id)

    return {
      'job': job.dict(),
      'documents': [doc.dict() for doc in documents],
      'results': results,
    }
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to fetch job details: {str(e)}')


@router.post('/jobs/{job_id}/upload', response_model=FileUploadResponse)
async def upload_files(
  job_id: int,
  files: List[UploadFile] = File(...),
  user_context: Dict[str, Optional[str]] = Depends(get_current_user_context),
):
  """Upload documents to a job and trigger processing."""
  try:
    # Check if job exists
    job = get_extraction_job(job_id)
    if not job:
      raise HTTPException(status_code=404, detail='Job not found')

    if job.status not in ['not_submitted', 'pending', 'uploaded', 'failed']:
      raise HTTPException(
        status_code=400,
        detail=f'Cannot upload files to job with status: {job.status}',
      )

    # Validate files
    if not files:
      raise HTTPException(status_code=400, detail='No files provided')

    uploaded_files = []
    total_size = 0

    # Prepare UC Volumes path for this job
    job_upload_path = f'{UPLOAD_BASE_PATH.rstrip("/")}/job_{job_id}'

    for file in files:
      # Validate file extension
      file_ext = Path(file.filename).suffix.lower()
      if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
          status_code=400,
          detail=(
            f'File type {file_ext} not supported. '
            f'Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
          ),
        )

      # Read and validate file size
      content = await file.read()
      if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
          status_code=400,
          detail=(
            f'File {file.filename} is too large. '
            f'Maximum size: {MAX_FILE_SIZE // 1024 // 1024}MB'
          ),
        )

      # Upload to UC Volumes
      uc_file_path = f'{job_upload_path}/{file.filename}'
      try:
        upload_to_uc_volumes(content, uc_file_path)
      except Exception as e:
        raise HTTPException(
          status_code=500,
          detail=f'Failed to upload {file.filename} to UC Volumes: {str(e)}',
        )

      # Create document record
      document = DBDocument(
        job_id=job_id,
        filename=file.filename,
        file_path=uc_file_path,
        file_size=len(content),
      )
      create_document(document)

      uploaded_files.append(file.filename)
      total_size += len(content)

    # Update job status and upload directory
    update_extraction_job(
      job_id, {'status': 'uploaded', 'upload_directory': job_upload_path}
    )

    # Create upload log entry (required by notebook)
    user_id = get_user_for_logging(user_context)
    user_email = user_context.get('email', '')
    create_upload_log(
      job_id,
      job_upload_path,
      'upload',
      'Files uploaded to UC Volumes',
      '',  # details
      user_id,
      user_email,
    )

    # Trigger Databricks processing
    try:
      run_id = await DatabricksService.trigger_extraction_job(job_id, job.schema_id)

      # Update job with Databricks run ID and processing status
      update_extraction_job(
        job_id, {'status': 'processing', 'databricks_run_id': run_id}
      )

    except Exception as e:
      # Update job status to indicate processing trigger failed
      update_extraction_job(
        job_id, {'status': 'failed', 'error_message': f'Failed to trigger processing: {str(e)}'}
      )
      raise HTTPException(
        status_code=500,
        detail=f'Files uploaded but failed to trigger processing: {str(e)}',
      )

    return FileUploadResponse(
      success=True,
      message=f'Successfully uploaded {len(uploaded_files)} files and triggered processing',
      job_id=job_id,
      uploaded_files=uploaded_files,
      file_count=len(uploaded_files),
    )

  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to upload files: {str(e)}')


@router.get('/jobs/{job_id}/status', response_model=JobStatusResponse)
async def get_job_status(job_id: int):
  """Get job processing status."""
  try:
    job = get_extraction_job(job_id)
    if not job:
      raise HTTPException(status_code=404, detail='Job not found')

    # If job has Databricks run ID, get detailed status from Databricks
    current_stage = None
    progress_percent = None

    if job.databricks_run_id:
      try:
        databricks_status = await DatabricksService.get_job_status(job.databricks_run_id)
        current_stage = databricks_status.get('state', {}).get('life_cycle_state', 'unknown')

        # Map Databricks states to progress percentages
        if current_stage == 'PENDING':
          progress_percent = 10
        elif current_stage == 'RUNNING':
          progress_percent = 50
        elif current_stage == 'TERMINATED':
          result_state = databricks_status.get('state', {}).get('result_state')
          if result_state == 'SUCCESS':
            progress_percent = 100
            # Update local job status if not already completed
            if job.status != 'completed':
              update_extraction_job(job_id, {'status': 'completed'})
          else:
            progress_percent = 0
            # Update local job status if not already failed
            if job.status != 'failed':
              error_msg = databricks_status.get('state', {}).get(
                'state_message', 'Processing failed'
              )
              update_extraction_job(job_id, {'status': 'failed', 'error_message': error_msg})

      except Exception as e:
        current_stage = f'Status check failed: {str(e)}'

    return JobStatusResponse(
      job_id=job_id,
      status=job.status,
      progress_percent=progress_percent,
      current_stage=current_stage,
      error_message=job.error_message,
      databricks_run_id=job.databricks_run_id,
    )

  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to get job status: {str(e)}')


@router.get('/jobs/{job_id}/results', response_model=JobResultsResponse)
async def get_job_results(job_id: int):
  """Get extraction results for a job."""
  try:
    job = get_extraction_job(job_id)
    if not job:
      raise HTTPException(status_code=404, detail='Job not found')

    schema = get_extraction_schema(job.schema_id)
    schema_name = schema.name if schema else 'Unknown Schema'

    results = get_results_by_job(job_id)

    return JobResultsResponse(
      job_id=job_id,
      job_name=job.name,
      schema_name=schema_name,
      status=job.status,
      created_at=job.created_at,
      completed_at=job.completed_at,
      results=[
        {
          'document_filename': result['document_filename'],
          'extracted_data': result['extracted_data'],
          'confidence_scores': result['confidence_scores'],
        }
        for result in results
      ],
    )

  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to get job results: {str(e)}')
