# Information Extraction App

A Databricks-native web application for extracting structured information from unstructured documents using AI/ML processing.

## Overview

This application allows users to:
1. **Define extraction schemas** - Specify what fields to extract from documents
2. **Upload documents** - Upload PDF, Word, and image files for processing
3. **Trigger Databricks jobs** - Automatically process documents using Databricks workflows
4. **View results** - See extracted data, track job status, and monitor processing logs

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Client  │◄──►│  FastAPI Server │◄──►│  PostgreSQL DB  │
│                 │    │                 │    │  (Databricks)   │
│ - Upload UI     │    │ - REST API      │    │                 │
│ - Schema Editor │    │ - File Storage  │    │ - Jobs          │
│ - Results View  │    │ - Job Triggers  │    │ - Schemas       │
│ - Job Status    │    │                 │    │ - Documents     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Databricks Jobs │
                       │                 │
                       │ - Parse docs    │
                       │ - AI extraction │
                       │ - Store results │
                       └─────────────────┘
```

## Database Schema

The app uses a PostgreSQL database hosted on Databricks with the following tables:

### Core Tables

**extraction_schemas** - User-defined extraction schemas
- `id` - Primary key
- `name` - Schema name
- `description` - Optional description
- `fields` - JSON definition of fields to extract
- `is_active` - Whether schema is active
- `created_at` - Creation timestamp

**extraction_jobs** - Processing jobs
- `id` - Primary key
- `name` - Job name
- `schema_id` - Foreign key to extraction_schemas
- `status` - Job status (not_submitted, submitted, running, completed, failed)
- `upload_directory` - Path to uploaded files (Unity Catalog volume)
- `databricks_run_id` - Databricks job run ID
- `created_at`, `updated_at`, `completed_at` - Timestamps
- `error_message` - Error details if failed

**documents** - Uploaded files
- `id` - Primary key
- `job_id` - Foreign key to extraction_jobs
- `filename` - Original filename
- `file_path` - Full path in storage
- `file_size` - File size in bytes
- `upload_time` - Upload timestamp

**extraction_results** - Extracted data
- `id` - Primary key
- `job_id`, `document_id`, `schema_id` - Foreign keys
- `extracted_data` - JSON with extracted field values
- `confidence_scores` - Optional AI confidence scores
- `created_at` - Creation timestamp

**upload_logs** - Processing activity logs
- `id` - Primary key
- `analysis_id` - Job ID reference
- `upload_directory` - Upload location
- `event_type` - Log event type
- `message` - Log message
- `details` - Additional JSON details
- `created_at` - Log timestamp

## Configuration System

The app uses a centralized configuration system:

### Files
- **config/base.yaml** - All configuration (database, Databricks job, upload settings)
- **config/local.yaml** - Local development overrides (optional, not in git)
- **.env.local** - Local secrets (DB_PASSWORD for development)
- **app.yaml** - Databricks App deployment config (resource references only)

### Configuration Loading
1. Load `config/base.yaml` (required)
2. Overlay `config/local.yaml` if exists (local dev only)
3. Get `DB_PASSWORD` from environment or `.env.local`
4. Get `UPLOAD_BASE_PATH` and `DATABRICKS_JOB_ID` from environment with fallback to base.yaml

### Example base.yaml
```yaml
database:
  host: instance-xxx.database.cloud.databricks.com
  port: 5432
  name: information_extractor
  user: app_user
  schema: information_extraction

databricks:
  job_id: 424554646032710
  output_table: catalog.schema.table_name

upload:
  base_path: /Volumes/catalog/schema/volume_name
  max_size_mb: 50
  allowed_extensions: [.pdf, .docx, .doc, .png, .jpg, .jpeg, .txt]
```

## Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and builds
- **shadcn/ui** components with Tailwind CSS
- **React Query** for API state management
- **Bun** for package management

### Backend
- **FastAPI** with automatic OpenAPI docs
- **PostgreSQL** (Databricks-hosted)
- **Databricks SDK** for job triggering and monitoring
- **uv** for Python package management

## Development Workflow

### Setup
```bash
# Run interactive setup wizard
./setup.sh

# Or manually configure
# 1. Edit config/base.yaml with your database and Databricks settings
# 2. Create .env.local with DB_PASSWORD=your_password
# 3. Set DATABRICKS_CONFIG_PROFILE in .env.local
```

### Development Server
```bash
# Start both frontend and backend with hot reloading
nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &

# Check logs
tail -f /tmp/databricks-app-watch.log

# Stop servers
kill $(cat /tmp/databricks-app-watch.pid)
```

### Deployment
```bash
# Deploy to Databricks Apps
./deploy.sh

# Monitor deployment logs
uv run python dba_logz.py <app-url> --duration 60

# Test deployed endpoints
uv run python dba_client.py <app-url> /health
```

## API Endpoints

### Schemas
- `GET /api/schemas` - List all schemas
- `POST /api/schemas` - Create new schema
- `GET /api/schemas/{id}` - Get schema details
- `PUT /api/schemas/{id}` - Update schema
- `DELETE /api/schemas/{id}` - Delete schema

### Jobs
- `GET /api/jobs` - List all jobs
- `POST /api/jobs` - Create new job
- `GET /api/jobs/{id}` - Get job details
- `PUT /api/jobs/{id}` - Update job status
- `POST /api/jobs/{id}/submit` - Submit job to Databricks
- `DELETE /api/jobs/{id}` - Delete job

### Documents
- `POST /api/jobs/{id}/upload` - Upload documents to job
- `GET /api/jobs/{id}/documents` - List job documents

### Results
- `GET /api/jobs/{id}/results` - Get extraction results for job
- `GET /api/results/{id}` - Get specific result details

### Monitoring
- `GET /api/logs` - Get processing activity logs
- `GET /health` - Health check endpoint
- `GET /docs` - OpenAPI documentation

## User Workflow

### 1. Create Schema
Navigate to Schemas page and define:
- Schema name and description
- Fields to extract (name, type, required/optional)
- Save for reuse across multiple jobs

### 2. Create Job & Upload
1. Go to Upload page
2. Select a schema
3. Name your job
4. Upload documents (PDF, DOCX, images)
5. Job is created with status "not_submitted"

### 3. Submit for Processing
1. View job in Dashboard
2. Click "Submit to Databricks"
3. Triggers Databricks workflow job
4. Status updates: not_submitted → submitted → running → completed/failed

### 4. View Results
1. Navigate to Results page or job details
2. See extracted data in table format
3. Download results as needed
4. Check activity logs for processing details

## Key Features

### Schema Management
- Define reusable extraction templates
- Support for text, number, date, boolean field types
- Mark fields as required or optional
- Edit and version schemas

### Document Processing
- Drag-and-drop file upload
- Batch upload support
- File validation (type, size limits)
- Automatic Unity Catalog volume storage

### Job Orchestration
- Databricks Jobs API integration
- Real-time status tracking
- Error handling and retry logic
- Processing activity logs

### Results Viewing
- Structured data display
- Per-document extraction results
- Confidence scores (if available)
- Export capabilities

## Databricks Integration

### Prerequisites
1. Databricks workspace with Jobs API access
2. PostgreSQL database (Serverless SQL)
3. Unity Catalog volume for file storage
4. Databricks job configured for document processing

### Job Notebook Requirements
The Databricks processing job should:
1. Read documents from Unity Catalog volume (provided in `upload_directory`)
2. Load schema definition from `extraction_schemas` table (provided in `schema_id`)
3. Process documents and extract structured data
4. Write results to `extraction_results` table
5. Update job status in `extraction_jobs` table
6. Log activity to `upload_logs` table

### Resource References (app.yaml)
```yaml
env:
  - name: DB_PASSWORD
    valueFrom: lakebase_db_password
  - name: UPLOAD_BASE_PATH
    valueFrom: documents_upload_volume
  - name: DATABRICKS_JOB_ID
    valueFrom: information_extraction_job
```

## Troubleshooting

### Database Connection Issues
- Check `config/base.yaml` has correct database settings
- Verify `DB_PASSWORD` in `.env.local` or environment
- Test connection: `uv run python -c "from server.database import test_db_connection; print(test_db_connection())"`

### File Upload Issues
- Check `UPLOAD_BASE_PATH` points to valid Unity Catalog volume
- Verify volume permissions for app service principal
- Check file size limits in `config/base.yaml`

### Job Submission Issues
- Verify `DATABRICKS_JOB_ID` in config
- Check Databricks authentication (DATABRICKS_HOST, DATABRICKS_TOKEN)
- View job runs in Databricks UI: Workflows → Job → Runs

### Deployment Issues
- Monitor logs: `uv run python dba_logz.py <app-url>`
- Check app resources are configured (secrets, volumes, job)
- Verify `app.yaml` has correct resource references

## Development Scripts

- `./setup.sh` - Interactive setup wizard
- `./watch.sh` - Development server with hot reload
- `./fix.sh` - Format code (ruff, prettier)
- `./deploy.sh` - Deploy to Databricks Apps
- `dba_logz.py` - Stream deployment logs
- `dba_client.py` - Test deployed endpoints
- `app_status.sh` - Check app status and URL

## Documentation

- `docs/README.md` - This file
- `docs/databricks_apis/` - Databricks API reference docs
- `server/` - Backend API code
- `client/src/` - Frontend React code
- `config/` - Configuration files
