# Information Extraction App

A Databricks-native web application for extracting structured information from unstructured documents using AI/ML processing.

![Databricks Apps](https://img.shields.io/badge/Databricks-Apps-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![React](https://img.shields.io/badge/React-18+-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue)

## Overview

Upload documents (PDFs, Word files, images), define extraction schemas, and automatically extract structured data using Databricks AI/ML workflows.

**Key Features:**
- 📝 **Schema Management** - Define reusable extraction templates with custom fields
- 📤 **Document Upload** - Drag-and-drop upload with batch support
- 🤖 **AI Processing** - Databricks job integration for intelligent extraction
- 📊 **Results Viewing** - Structured data display with export capabilities
- 📈 **Job Tracking** - Real-time status monitoring and activity logs

## Quick Start

### 1. Setup

Run the interactive setup wizard to configure everything:

```bash
./setup.sh
```

The wizard automates:
- ✅ Databricks authentication
- ✅ Database configuration and migrations
- ✅ Unity Catalog volume setup
- ✅ Databricks job deployment
- ✅ App deployment to Databricks Apps

### 2. Development

Start the development server with hot reloading:

```bash
nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Stop servers:**
```bash
kill $(cat /tmp/databricks-app-watch.pid)
```

### 3. Deploy

Deploy to Databricks Apps:

```bash
./deploy.sh
```

Monitor deployment:
```bash
uv run python dba_logz.py <app-url> --duration 60
```

## Configuration

### Files

**config/base.yaml** - All configuration (single source of truth)
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

**.env.local** - Local secrets (not in git)
```bash
DATABRICKS_CONFIG_PROFILE=your-profile-name
DB_PASSWORD=your_db_password
```

**app.yaml** - Databricks App deployment (resource references only)
```yaml
command:
  - uvicorn
  - server.app:app
env:
  - name: DB_PASSWORD
    valueFrom: lakebase_db_password
  - name: UPLOAD_BASE_PATH
    valueFrom: documents_upload_volume
  - name: DATABRICKS_JOB_ID
    valueFrom: information_extraction_job
```

## User Workflow

### 1. Create Schema

Define what fields to extract:
1. Navigate to **Schemas** page
2. Click **Create Schema**
3. Add fields (name, type, required/optional)
4. Save for reuse

### 2. Upload Documents

Upload files for processing:
1. Go to **Upload** page
2. Select a schema
3. Name your job
4. Drag & drop documents
5. Job created with status "not_submitted"

### 3. Submit for Processing

Trigger Databricks job:
1. View job in **Dashboard**
2. Click **Submit to Databricks**
3. Monitor status updates
4. Check **Activity Logs** for details

### 4. View Results

See extracted data:
1. Navigate to **Results** page
2. View structured data in tables
3. Download results as needed
4. Review confidence scores

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

### Core Tables

**extraction_schemas** - User-defined extraction schemas
- Fields: id, name, description, fields (JSON), is_active, created_at

**extraction_jobs** - Processing jobs
- Fields: id, name, schema_id, status, upload_directory, databricks_run_id, timestamps, error_message

**documents** - Uploaded files
- Fields: id, job_id, filename, file_path, file_size, upload_time

**extraction_results** - Extracted data
- Fields: id, job_id, document_id, schema_id, extracted_data (JSON), confidence_scores, created_at

**upload_logs** - Processing activity logs
- Fields: id, analysis_id, upload_directory, event_type, message, details (JSON), created_at

## API Endpoints

### Schemas
- `GET /api/schemas` - List all schemas
- `POST /api/schemas` - Create schema
- `GET /api/schemas/{id}` - Get schema details
- `PUT /api/schemas/{id}` - Update schema
- `DELETE /api/schemas/{id}` - Delete schema

### Jobs
- `GET /api/jobs` - List all jobs
- `POST /api/jobs` - Create job
- `GET /api/jobs/{id}` - Get job details
- `PUT /api/jobs/{id}` - Update job
- `POST /api/jobs/{id}/submit` - Submit to Databricks
- `DELETE /api/jobs/{id}` - Delete job

### Documents & Results
- `POST /api/jobs/{id}/upload` - Upload documents
- `GET /api/jobs/{id}/documents` - List documents
- `GET /api/jobs/{id}/results` - Get extraction results
- `GET /api/results/{id}` - Get result details

### Monitoring
- `GET /api/logs` - Processing activity logs
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Databricks-hosted database
- **Databricks SDK** - Job triggering and monitoring
- **uv** - Fast Python package management

### Frontend
- **React 18** - Modern React with TypeScript
- **Vite** - Fast build tool
- **shadcn/ui** - Beautiful, accessible components
- **Tailwind CSS** - Utility-first styling
- **React Query** - API state management
- **Bun** - Fast package manager

## Development Scripts

| Command | Description |
|---------|-------------|
| `./setup.sh` | Interactive setup wizard |
| `./watch.sh` | Development server with hot reload |
| `./fix.sh` | Format code (ruff + prettier) |
| `./deploy.sh` | Deploy to Databricks Apps |
| `./app_status.sh` | Check deployed app status |
| `dba_logz.py` | Stream deployment logs |
| `dba_client.py` | Test deployed endpoints |

## Troubleshooting

### Database Connection
```bash
# Test database connection
uv run python -c "from server.database import test_db_connection; print(test_db_connection())"

# Check config
cat config/base.yaml

# Verify password
grep DB_PASSWORD .env.local
```

### File Upload Issues
```bash
# Check volume path
databricks workspace ls /Volumes/catalog/schema/

# Verify permissions
databricks workspace put-file test.txt /Volumes/catalog/schema/volume/test.txt
```

### Job Submission
```bash
# Test job exists
databricks jobs get <job_id>

# Check authentication
databricks current-user me

# View recent runs
databricks jobs runs list --job-id <job_id>
```

### Deployment Issues
```bash
# Monitor deployment logs
uv run python dba_logz.py <app-url> --duration 60

# Test deployed app
uv run python dba_client.py <app-url> /health

# Check app status
./app_status.sh --verbose
```

### Development Server
```bash
# View logs
tail -f /tmp/databricks-app-watch.log

# Restart servers
kill $(cat /tmp/databricks-app-watch.pid)
nohup ./watch.sh > /tmp/databricks-app-watch.log 2>&1 &

# Check running processes
ps aux | grep databricks-app
```

## Databricks Integration

### Prerequisites
- Databricks workspace with Jobs API access
- PostgreSQL database (Serverless SQL)
- Unity Catalog volume for file storage
- Databricks job configured for document processing

### Job Notebook Requirements

The processing notebook should:
1. Read documents from Unity Catalog volume (`upload_directory` parameter)
2. Load schema from `extraction_schemas` table (`schema_id` parameter)
3. Process documents and extract structured data
4. Write results to `extraction_results` table
5. Update job status in `extraction_jobs` table
6. Log activity to `upload_logs` table

### App Resources

When creating the Databricks App, configure these resources:
- **lakebase_db_password** - Database password secret
- **documents_upload_volume** - Unity Catalog volume path
- **information_extraction_job** - Databricks job ID

## Documentation

- **[Complete Documentation](docs/README.md)** - Full app documentation
- **[Databricks APIs](docs/databricks_apis/)** - API reference guides
- **[FastAPI Docs](https://fastapi.tiangolo.com/)** - Backend framework
- **[React Docs](https://react.dev/)** - Frontend framework
- **[Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/)** - Platform documentation

## Development

### Code Formatting
```bash
./fix.sh  # Formats Python and TypeScript code
```

### Adding Features

**New API Endpoint:**
1. Add route in `server/routers/`
2. TypeScript client auto-generates on save
3. Use in React with `import { apiClient } from '@/fastapi_client'`

**New UI Component:**
1. Create in `client/src/components/`
2. Use shadcn/ui: `npx shadcn@latest add <component>`
3. Import in pages

**Database Changes:**
1. Update schema in `server/database.py`
2. Run migrations: Edit `create_tables()` function
3. Restart app to apply changes

## License

See [LICENSE.md](LICENSE.md) for details.

---

**Questions?** Check the [full documentation](docs/README.md) or open an issue.
