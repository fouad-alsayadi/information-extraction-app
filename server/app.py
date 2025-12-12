"""FastAPI application for Information Extraction App."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from server.database import create_tables, init_db_pool, test_db_connection
from server.routers import router
from server.routers.dashboard import router as dashboard_router
from server.routers.jobs import router as jobs_router
from server.routers.logs import router as logs_router
from server.routers.schemas import router as schemas_router


# Load environment variables from .env.local if it exists
def load_env_file(filepath: str) -> None:
  """Load environment variables from a file."""
  if Path(filepath).exists():
    with open(filepath) as f:
      for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
          key, _, value = line.partition('=')
          if key and value:
            os.environ[key] = value


# Load .env files
load_env_file('.env')
load_env_file('.env.local')

# Configure logging to show full tracebacks
import logging

logging.basicConfig(
  level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Also configure uvicorn logger to show exceptions
uvicorn_logger = logging.getLogger('uvicorn.error')
uvicorn_logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
  """Manage application lifespan."""
  # Startup: Initialize database
  try:
    init_db_pool()
    create_tables()
    if not test_db_connection():
      print('Warning: Database connection test failed')
    else:
      print('Database connection successful')
  except Exception as e:
    print(f'Database initialization failed: {e}')

  yield

  # Shutdown: Clean up resources
  # Add any cleanup code here if needed


app = FastAPI(
  title='Information Extraction App API',
  description='Document information extraction using Databricks AI/ML capabilities',
  version='0.1.0',
  lifespan=lifespan,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
  ],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)


# Global exception handler for HTTPException to log 500-level errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
  """Log HTTPException errors (especially 500-level) with context."""
  import traceback

  exception_logger = logging.getLogger(__name__)

  # Log 500-level errors with full details
  if exc.status_code >= 500:
    exception_logger.error('=' * 80)
    exception_logger.error(f'HTTP {exc.status_code} ERROR: {request.method} {request.url.path}')
    exception_logger.error(f'Detail: {exc.detail}')
    exception_logger.error('Traceback:')
    exception_logger.error(traceback.format_exc())
    exception_logger.error('=' * 80)

  # Return the default HTTPException response
  return JSONResponse(
    status_code=exc.status_code, content={'detail': exc.detail, 'path': str(request.url.path)}
  )


# Global exception handler to log all unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
  """Catch all unhandled exceptions and log with full traceback."""
  import traceback

  exception_logger = logging.getLogger(__name__)

  # Log the full exception details
  exception_logger.error('=' * 80)
  exception_logger.error(f'UNHANDLED EXCEPTION: {request.method} {request.url.path}')
  exception_logger.error(f'Exception Type: {type(exc).__name__}')
  exception_logger.error(f'Exception Message: {str(exc)}')
  exception_logger.error('Full Traceback:')
  exception_logger.error(traceback.format_exc())
  exception_logger.error('=' * 80)

  # Return a proper error response
  return JSONResponse(
    status_code=500,
    content={
      'detail': 'Internal Server Error',
      'error': str(exc),
      'type': type(exc).__name__,
      'path': str(request.url.path),
    },
  )


# Middleware to catch and log all exceptions with proper traceback context
@app.middleware('http')
async def exception_logging_middleware(request: Request, call_next):
  """Catch all exceptions and log them with full tracebacks before re-raising."""
  import traceback

  exception_logger = logging.getLogger(__name__)

  try:
    return await call_next(request)
  except Exception as exc:
    # Log the exception with full traceback context
    exc_type = type(exc).__name__
    exc_detail = str(exc)

    # Determine status code
    if isinstance(exc, HTTPException):
      status_code = exc.status_code
      if status_code >= 500:
        exception_logger.error(f'HTTP {status_code} on {request.method} {request.url}')
        exception_logger.error(f'Detail: {exc.detail}')
        exception_logger.error(f'Full traceback:\n{traceback.format_exc()}')
    else:
      exception_logger.error(f'Unhandled {exc_type} on {request.method} {request.url}')
      exception_logger.error(f'Exception: {exc_detail}')
      exception_logger.error(f'Full traceback:\n{traceback.format_exc()}')

    # Re-raise to let FastAPI's exception handlers format the response
    raise


app.include_router(router, prefix='/api', tags=['api'])
app.include_router(dashboard_router, prefix='/api', tags=['dashboard'])
app.include_router(logs_router, prefix='/api', tags=['logs'])
app.include_router(schemas_router, prefix='/api', tags=['schemas'])
app.include_router(jobs_router, prefix='/api', tags=['jobs'])


@app.get('/health')
async def health():
  """Health check endpoint."""
  try:
    db_status = 'connected' if test_db_connection() else 'disconnected'
  except Exception:
    db_status = 'error'

  return {'status': 'healthy', 'database': db_status, 'service': 'information-extraction-app'}


# ============================================================================
# SERVE STATIC FILES FROM CLIENT BUILD DIRECTORY (MUST BE LAST!)
# ============================================================================

# Add explicit SPA fallback route for deep links
@app.get('/{full_path:path}')
async def spa_fallback(full_path: str):
  """Serve index.html for all non-API routes to support SPA routing."""
  # Skip if this is an API route
  if full_path.startswith('api/') or full_path.startswith('health') or full_path.startswith('docs'):
    # This shouldn't happen as these routes are already defined above
    return JSONResponse(status_code=404, content={'detail': 'Not Found'})

  # Check if it's a static file request (has file extension)
  if '.' in full_path.split('/')[-1]:
    # Try to serve the static file
    static_file_path = f'client/build/{full_path}'
    if os.path.exists(static_file_path):
      return FileResponse(static_file_path)
    else:
      return JSONResponse(status_code=404, content={'detail': 'File not found'})

  # For all other routes (SPA deep links), serve index.html
  index_path = 'client/build/index.html'
  if os.path.exists(index_path):
    return FileResponse(index_path)
  else:
    return JSONResponse(status_code=404, content={'detail': 'React app not built'})

# Mount static files for serving assets (CSS, JS, images, etc.)
# This will handle requests like /assets/index-abc123.js
if os.path.exists('client/build/assets'):
  app.mount('/assets', StaticFiles(directory='client/build/assets'), name='assets')
if os.path.exists('client/build/logo'):
  app.mount('/logo', StaticFiles(directory='client/build/logo'), name='logo')
# Mount any other static directories as needed
