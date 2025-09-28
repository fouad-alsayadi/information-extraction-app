# Information Extraction App - Technical Design Document

## High-Level Architecture

### System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Client  │◄──►│  FastAPI Server │◄──►│   SQLite DB     │
│                 │    │                 │    │                 │
│ - File Upload   │    │ - REST API      │    │ - Simple Schema │
│ - Schema Editor │    │ - File Storage  │    │ - 4 Core Tables │
│ - Results View  │    │ - Job Triggers  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Databricks Jobs │
                       │                 │
                       │ - Doc Processing│
                       │ - AI Extraction │
                       │ - Result Callback│
                       └─────────────────┘
```

### Design Principles
1. **Simplicity First**: Start with minimal complexity, add features incrementally
2. **Clear Separation**: Frontend UI, Backend API, Database, External Processing
3. **Standard Patterns**: Use established FastAPI and React conventions
4. **Progressive Enhancement**: Build MVP first, then add advanced features
5. **Maintainable Code**: Clear naming, minimal abstractions, good documentation

## Technology Stack

### Frontend Stack
- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Type safety and better development experience
- **Vite**: Fast development server and production builds
- **shadcn/ui**: Pre-built accessible components with Tailwind CSS
- **React Query**: Server state management and API caching
- **React Hook Form**: Form handling with validation

### Backend Stack
- **FastAPI**: Modern Python web framework with automatic OpenAPI docs
- **Pydantic**: Data validation and serialization
- **PostgreSQL**: Databricks-hosted PostgreSQL database (using existing configuration)
- **Databricks SDK**: Official SDK for job triggering and monitoring
- **Uvicorn**: ASGI server for FastAPI

### Development Tools
- **uv**: Fast Python package management
- **bun**: Fast Node.js package management and runtime
- **ESLint + Prettier**: Code formatting and linting
- **TypeScript client generation**: Auto-generated from OpenAPI spec

## Data Architecture

### Database Schema (Simplified)
```sql
-- Core entity for tracking extraction jobs
CREATE TABLE extraction_jobs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    error_message TEXT,
    databricks_run_id INTEGER
);

-- User-defined schemas for extraction
CREATE TABLE extraction_schemas (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    schema_definition TEXT NOT NULL, -- JSON string with field definitions
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Documents uploaded for processing
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES extraction_jobs (id)
);

-- Extracted results from processing
CREATE TABLE extraction_results (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    schema_id INTEGER NOT NULL,
    extracted_data TEXT NOT NULL, -- JSON string with extracted field values
    confidence_scores TEXT, -- JSON string with AI confidence scores
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES extraction_jobs (id),
    FOREIGN KEY (document_id) REFERENCES documents (id),
    FOREIGN KEY (schema_id) REFERENCES extraction_schemas (id)
);
```

### Data Models (Pydantic)
```python
# Core models for API
class ExtractionSchema(BaseModel):
    id: int
    name: str
    description: str
    fields: List[SchemaField]

class SchemaField(BaseModel):
    name: str
    type: Literal['text', 'number', 'date', 'currency', 'percentage']
    required: bool = False
    description: str = ""

class ExtractionJob(BaseModel):
    id: int
    name: str
    status: Literal['pending', 'processing', 'completed', 'failed']
    documents: List[Document]
    schema_id: int
    created_at: datetime

class ExtractionResult(BaseModel):
    job_id: int
    document_id: int
    extracted_data: Dict[str, Any]
    confidence_scores: Dict[str, float]
```

## API Design

### RESTful Endpoints
```
POST   /api/schemas              # Create extraction schema
GET    /api/schemas              # List all schemas
GET    /api/schemas/{id}         # Get specific schema
PUT    /api/schemas/{id}         # Update schema
DELETE /api/schemas/{id}         # Delete schema

POST   /api/jobs                 # Create new extraction job
GET    /api/jobs                 # List all jobs
GET    /api/jobs/{id}            # Get job details with results
DELETE /api/jobs/{id}            # Delete job

POST   /api/jobs/{id}/upload     # Upload documents to job
GET    /api/jobs/{id}/status     # Get job processing status
POST   /api/jobs/{id}/process    # Trigger processing (auto after upload)

GET    /api/results/{job_id}     # Get extraction results
GET    /api/results/{job_id}/export # Export results as CSV/JSON

GET    /api/health               # Health check
```

### Request/Response Examples
```typescript
// Create Schema
POST /api/schemas
{
  "name": "Invoice Extraction",
  "description": "Extract key fields from invoices",
  "fields": [
    {"name": "invoice_number", "type": "text", "required": true},
    {"name": "total_amount", "type": "currency", "required": true},
    {"name": "invoice_date", "type": "date", "required": true}
  ]
}

// Upload Files
POST /api/jobs/123/upload
Content-Type: multipart/form-data
- files: [invoice1.pdf, invoice2.pdf]
- schema_id: 456

// Get Results
GET /api/results/123
{
  "job_id": 123,
  "status": "completed",
  "results": [
    {
      "document": "invoice1.pdf",
      "extracted_data": {
        "invoice_number": "INV-2024-001",
        "total_amount": 1250.00,
        "invoice_date": "2024-01-15"
      },
      "confidence_scores": {
        "invoice_number": 0.95,
        "total_amount": 0.89,
        "invoice_date": 0.92
      }
    }
  ]
}
```

## Integration Points

### Databricks Integration
```python
# Simplified Databricks service
class DatabricksService:
    @staticmethod
    async def trigger_extraction_job(job_id: int, schema_id: int, file_paths: List[str]):
        """Trigger Databricks notebook for document processing"""
        job_params = {
            "job_id": str(job_id),
            "schema_id": str(schema_id),
            "file_paths": json.dumps(file_paths)
        }

        run_id = databricks_client.jobs.run_now(
            job_id=settings.DATABRICKS_JOB_ID,
            notebook_params=job_params
        )

        # Update job with run_id for tracking
        update_job_status(job_id, "processing", run_id)
        return run_id

    @staticmethod
    def get_job_status(run_id: int):
        """Check status of Databricks job run"""
        return databricks_client.jobs.get_run(run_id)
```

### File Storage
```python
# Simple file handling (no complex abstractions)
def save_uploaded_file(file: UploadFile, job_id: int) -> str:
    """Save uploaded file to job directory"""
    job_dir = Path(f"uploads/job_{job_id}")
    job_dir.mkdir(parents=True, exist_ok=True)

    file_path = job_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return str(file_path)
```

## Implementation Plan

### Phase 1: MVP Core Features (Week 1-2)

#### Backend Implementation
1. **Set up FastAPI app** with basic structure
   - `server/app.py` - Main FastAPI application
   - `server/models.py` - Pydantic models
   - `server/database.py` - SQLite connection and basic CRUD
   - `server/routers/` - API endpoint routers

2. **Core API endpoints**
   - Schema CRUD operations
   - Job creation and file upload
   - Basic Databricks job triggering
   - Simple result retrieval

3. **Database setup**
   - SQLite database with 4 core tables
   - Basic migrations and setup script
   - Simple connection pooling

#### Frontend Implementation
1. **Replace WelcomePage** with main application interface
2. **Schema management page**
   - Create/edit extraction schemas
   - Field definition form with validation
   - Schema list with basic actions

3. **Document upload page**
   - File upload component with drag-and-drop
   - Schema selection dropdown
   - Upload progress indication

4. **Results page**
   - Display extracted data in table format
   - Basic export functionality
   - Job status monitoring

#### Integration
1. **Auto-generated TypeScript client** from FastAPI OpenAPI spec
2. **Basic error handling** and loading states
3. **Simple navigation** between pages

### Phase 2: Enhanced Features (Week 3-4)

#### Backend Enhancements
1. **Advanced schema types** (date, currency, percentage)
2. **Batch file processing** support
3. **Job status polling** and webhooks
4. **Results export** (CSV, JSON formats)
5. **Error handling improvements**

#### Frontend Enhancements
1. **Improved UI/UX** with better components
2. **Real-time progress tracking**
3. **Schema templates** for common document types
4. **Results visualization** improvements
5. **File preview capabilities**

#### Integration Improvements
1. **Databricks webhook integration** for status updates
2. **Background job processing** with status polling
3. **File cleanup** and storage management
4. **Performance optimizations**

### Phase 3: Production Features (Week 5-6)

#### Advanced Features
1. **Confidence scoring** display
2. **Document preview** alongside results
3. **Audit trail** and processing logs
4. **Schema versioning** and migration
5. **User management** and permissions

#### Production Readiness
1. **Comprehensive error handling**
2. **Logging and monitoring**
3. **Performance optimization**
4. **Security hardening**
5. **Documentation and testing**

## Development Workflow

### File Organization
```
information-extraction-app/
├── server/
│   ├── app.py                 # FastAPI main application
│   ├── models.py              # Pydantic models
│   ├── database.py            # Database connection and CRUD
│   └── routers/
│       ├── schemas.py         # Schema management endpoints
│       ├── jobs.py            # Job management endpoints
│       ├── upload.py          # File upload endpoints
│       └── results.py         # Results retrieval endpoints
├── client/
│   ├── src/
│   │   ├── App.tsx            # Main React application
│   │   ├── pages/
│   │   │   ├── SchemasPage.tsx    # Schema management
│   │   │   ├── UploadPage.tsx     # Document upload
│   │   │   └── ResultsPage.tsx    # Results viewing
│   │   └── components/
│   │       ├── SchemaEditor.tsx   # Schema definition form
│   │       ├── FileUpload.tsx     # File upload component
│   │       └── ResultsTable.tsx   # Results display
└── docs/
    ├── product.md             # Product requirements
    └── design.md              # Technical design
```

### Development Commands
```bash
# Start development servers
./watch.sh

# Add new Python dependencies
uv add package-name

# Add new frontend dependencies
cd client && bun add package-name

# Format code
./fix.sh

# Deploy to Databricks
./deploy.sh
```

### Key Development Principles
1. **Start simple**: Implement basic functionality first, add complexity incrementally
2. **Use existing patterns**: Follow FastAPI and React best practices
3. **Validate early**: Test each feature as it's implemented
4. **Keep it modular**: Clear separation between frontend, backend, and integration
5. **Document decisions**: Update design docs as implementation evolves

---

## Comparison with Current App

### Simplified Approach
- **4 tables** instead of 6+ complex interconnected tables
- **Direct API calls** instead of multiple service abstraction layers
- **Standard FastAPI patterns** instead of custom error handling frameworks
- **Simple PostgreSQL schema** instead of complex multi-table relationships
- **Clear data models** instead of mixed portfolio/document concepts
- **Minimal dependencies** instead of heavy ORM and middleware stack

### Benefits
- **Faster development**: Less complexity means quicker implementation
- **Easier maintenance**: Standard patterns are more maintainable
- **Better performance**: Fewer abstractions and database operations
- **Clearer code**: Explicit, readable code without over-engineering
- **Easier testing**: Simple components are easier to test and debug