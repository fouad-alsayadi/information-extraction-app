"""FastAPI application for Information Extraction App."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


# Global exception handler to log full tracebacks
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
  """Log full traceback for all unhandled exceptions."""
  import traceback

  logger = logging.getLogger(__name__)
  logger.error(f'Unhandled exception on {request.method} {request.url}')
  logger.error(f'Exception: {str(exc)}')
  logger.error(f'Full traceback:\n{traceback.format_exc()}')

  # Return generic 500 error to client
  return JSONResponse(status_code=500, content={'detail': 'Internal server error'})


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
# This static file mount MUST be the last route registered!
# It catches all unmatched requests and serves the React app.
# Any routes added after this will be unreachable!
if os.path.exists('client/build'):
  app.mount('/', StaticFiles(directory='client/build', html=True), name='static')
