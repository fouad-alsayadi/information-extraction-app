"""API routes for extraction schema management."""

import json
import logging
import traceback
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

from server.database import (
  create_extraction_schema,
  delete_extraction_schema,
  get_all_extraction_schemas,
  get_extraction_schema,
  get_extraction_jobs_by_schema,
  update_extraction_schema,
)
from server.dependencies.auth import get_current_user_context, get_user_for_logging
from server.models import (
  DBExtractionSchema,
  ExtractionJobSummary,
  ExtractionSchema,
  ExtractionSchemaCreate,
  ExtractionSchemaSummary,
  ExtractionSchemaUpdate,
)

router = APIRouter()


@router.get('/schemas', response_model=List[ExtractionSchemaSummary])
async def get_schemas():
  """Get all extraction schemas with summary information."""
  try:
    return get_all_extraction_schemas()
  except Exception as e:
    logger.error(f'Error fetching schemas: {str(e)}')
    logger.error(f'Full traceback: {traceback.format_exc()}')
    raise HTTPException(status_code=500, detail=f'Failed to fetch schemas: {str(e)}')


@router.post('/schemas', response_model=dict)
async def create_schema(
  schema: ExtractionSchemaCreate,
  user_context: Dict[str, Optional[str]] = Depends(get_current_user_context),
):
  """Create a new extraction schema."""
  try:
    # Convert fields to JSON string for database storage
    fields_json = json.dumps([field.dict() for field in schema.fields])

    db_schema = DBExtractionSchema(
      name=schema.name,
      description=schema.description,
      fields=fields_json,
    )

    user_id = get_user_for_logging(user_context)
    schema_id = create_extraction_schema(db_schema, created_by=user_id)

    return {
      'success': True,
      'message': 'Schema created successfully',
      'schema_id': schema_id,
    }
  except Exception as e:
    logger.error(f'Error creating schema: {str(e)}')
    logger.error(f'Full traceback: {traceback.format_exc()}')
    raise HTTPException(status_code=500, detail=f'Failed to create schema: {str(e)}')


@router.get('/schemas/{schema_id}', response_model=ExtractionSchema)
async def get_schema(schema_id: int):
  """Get detailed schema by ID."""
  try:
    schema = get_extraction_schema(schema_id)
    if not schema:
      raise HTTPException(status_code=404, detail='Schema not found')
    return schema
  except HTTPException:
    raise
  except Exception as e:
    logger.error(f'Error fetching schema {schema_id}: {str(e)}')
    logger.error(f'Full traceback: {traceback.format_exc()}')
    raise HTTPException(status_code=500, detail=f'Failed to fetch schema: {str(e)}')


@router.put('/schemas/{schema_id}', response_model=dict)
async def update_schema(schema_id: int, schema_update: ExtractionSchemaUpdate):
  """Update an existing schema."""
  try:
    # Check if schema exists
    existing_schema = get_extraction_schema(schema_id)
    if not existing_schema:
      raise HTTPException(status_code=404, detail='Schema not found')

    # Prepare updates
    updates = {}
    if schema_update.name is not None:
      updates['name'] = schema_update.name
    if schema_update.description is not None:
      updates['description'] = schema_update.description
    if schema_update.fields is not None:
      updates['fields'] = json.dumps([field.model_dump() for field in schema_update.fields])
    if schema_update.is_active is not None:
      updates['is_active'] = schema_update.is_active

    if not updates:
      raise HTTPException(status_code=400, detail='No valid updates provided')

    success = update_extraction_schema(schema_id, updates)
    if not success:
      raise HTTPException(status_code=500, detail='Failed to update schema')

    return {
      'success': True,
      'message': 'Schema updated successfully',
    }
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to update schema: {str(e)}')


@router.delete('/schemas/{schema_id}', response_model=dict)
async def delete_schema(schema_id: int):
  """Delete a schema."""
  try:
    # Check if schema exists
    existing_schema = get_extraction_schema(schema_id)
    if not existing_schema:
      raise HTTPException(status_code=404, detail='Schema not found')

    success = delete_extraction_schema(schema_id)
    if not success:
      raise HTTPException(status_code=500, detail='Failed to delete schema')

    return {
      'success': True,
      'message': 'Schema deleted successfully',
    }
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Failed to delete schema: {str(e)}')


@router.get('/schemas/{schema_id}/jobs', response_model=List[ExtractionJobSummary])
async def get_jobs_by_schema(schema_id: int):
  """Get all jobs that use a specific schema."""
  try:
    # Check if schema exists
    existing_schema = get_extraction_schema(schema_id)
    if not existing_schema:
      raise HTTPException(status_code=404, detail='Schema not found')

    jobs = get_extraction_jobs_by_schema(schema_id)
    return jobs
  except HTTPException:
    raise
  except Exception as e:
    logger.error(f'Error fetching jobs for schema {schema_id}: {str(e)}')
    logger.error(f'Full traceback: {traceback.format_exc()}')
    raise HTTPException(status_code=500, detail=f'Failed to fetch jobs for schema: {str(e)}')
