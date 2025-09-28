# Information Extraction App - Product Requirements Document (PRD)

## Executive Summary

**Problem Statement:**
Organizations need to extract structured information from unstructured documents (PDFs, Word docs, images, etc.) at scale. Manual data extraction is time-consuming, error-prone, and doesn't scale with document volume.

**Solution:**
A streamlined web application that allows users to upload documents, define extraction schemas, and automatically process documents using Databricks AI/ML capabilities to extract structured data.

**Core Value Proposition:**
- **Simple**: Intuitive UI for document upload and schema definition
- **Automated**: Leverages Databricks for scalable document processing
- **Flexible**: Supports custom extraction schemas for different document types
- **Fast**: Real-time progress tracking and results viewing

## Target Users

### Primary Users
- **Business Analysts**: Need to extract data from financial reports, contracts, invoices
- **Operations Teams**: Process forms, applications, compliance documents
- **Data Engineers**: Automate data extraction pipelines for downstream analysis

### User Personas

**Sarah - Business Analyst**
- Processes 50-100 financial documents weekly
- Needs to extract specific metrics (revenue, expenses, dates)
- Wants simple interface, doesn't need technical complexity
- Values accuracy and time savings

**Mike - Operations Manager**
- Handles customer forms and applications
- Needs consistent data extraction across document types
- Requires audit trail and progress tracking
- Values reliability and ease of use

## Core Features

### 1. Document Upload
**What:** Simple drag-and-drop interface for document upload
- Support PDF, DOCX, images (PNG, JPG)
- Batch upload capability (multiple files at once)
- File validation and size limits
- Upload progress indicators

### 2. Schema Management
**What:** Define what information to extract from documents
- Create custom extraction schemas with field definitions
- Field types: text, number, date, currency, percentage
- Required/optional field specification
- Schema templates for common document types
- Schema versioning and reuse

### 3. Processing Engine Integration
**What:** Trigger Databricks jobs to process documents
- Automatic job triggering after upload
- Pass schema definition to processing notebook
- Handle job parameters and configuration
- Error handling and retry logic

### 4. Progress Tracking
**What:** Real-time visibility into processing status
- Job status monitoring (queued, running, completed, failed)
- Progress indicators and estimated completion times
- Processing logs and error messages
- Email notifications for completion

### 5. Results Viewing
**What:** View and download extracted data
- Structured data display in table format
- Export to CSV, JSON formats
- Confidence scores for extracted fields
- Side-by-side document and results view

## User Stories

### Document Upload Flow
```
As a business analyst,
I want to upload multiple PDF documents at once,
So that I can process my weekly financial reports efficiently.

Acceptance Criteria:
- Can drag and drop up to 10 files simultaneously
- See upload progress for each file
- Get immediate feedback on file validation errors
- Files are stored securely and associated with my session
```

### Schema Definition Flow
```
As an operations manager,
I want to create a reusable schema for customer applications,
So that I can consistently extract the same data fields across all forms.

Acceptance Criteria:
- Can define custom field names and types
- Can mark fields as required or optional
- Can save schema for future use
- Can preview schema before applying to documents
```

### Processing Flow
```
As a data engineer,
I want to automatically trigger document processing after upload,
So that extraction happens without manual intervention.

Acceptance Criteria:
- Processing starts automatically after upload and schema selection
- Can monitor job progress in real-time
- Get notifications when processing completes
- Can view detailed logs if processing fails
```

### Results Flow
```
As a business analyst,
I want to view extracted data in a structured format,
So that I can validate accuracy and export for further analysis.

Acceptance Criteria:
- See extracted data in table format
- Can export results to CSV
- Can view original document alongside extracted data
- Can see confidence scores for AI-extracted fields
```

## Success Metrics

### User Experience Metrics
- **Upload Success Rate**: >99% of valid files upload successfully
- **Processing Speed**: Average processing time <5 minutes per document
- **User Task Completion**: >90% of users complete full upload-to-results flow
- **Return Usage**: >80% of users create multiple extraction jobs

### Technical Metrics
- **System Uptime**: >99.5% availability
- **API Response Time**: <2 seconds for all endpoints
- **Processing Throughput**: Handle 1000+ documents per hour
- **Error Rate**: <1% of processing jobs fail

### Business Metrics
- **User Adoption**: 50+ active users within first month
- **Processing Volume**: 10,000+ documents processed per month
- **User Satisfaction**: >4.5/5 average rating
- **Time Savings**: Users report >70% time reduction vs manual extraction

## Implementation Priority

### Phase 1: Core Functionality (MVP)
**Goal**: Basic upload, schema, and processing workflow
1. **Document Upload**: Single file upload with validation
2. **Simple Schema**: Basic field definition (text, number only)
3. **Databricks Integration**: Trigger processing job
4. **Basic Results**: Display extracted data in simple table

**Timeline**: 2 weeks
**Success Criteria**: Users can upload a document, define basic schema, and view results

### Phase 2: Enhanced User Experience
**Goal**: Improved usability and functionality
1. **Batch Upload**: Multiple file support
2. **Rich Schema Types**: Date, currency, percentage fields
3. **Progress Tracking**: Real-time job status monitoring
4. **Export Functionality**: CSV download of results

**Timeline**: 2 weeks
**Success Criteria**: Users can efficiently process multiple documents with rich data types

### Phase 3: Advanced Features
**Goal**: Production-ready application
1. **Schema Templates**: Pre-built schemas for common document types
2. **Advanced Results View**: Document preview alongside extracted data
3. **Confidence Scoring**: AI confidence indicators for extracted fields
4. **Audit Trail**: Complete processing history and logs

**Timeline**: 2 weeks
**Success Criteria**: Application ready for production deployment

## Technical Requirements

### Frontend Requirements
- **Framework**: React with TypeScript
- **UI Components**: shadcn/ui for consistent design
- **File Upload**: Drag-and-drop with progress indicators
- **Data Display**: Tables with sorting, filtering, export
- **Responsive Design**: Works on desktop and tablet

### Backend Requirements
- **Framework**: FastAPI (Python)
- **Database**: Simple SQLite or PostgreSQL (much simpler schema than current app)
- **File Storage**: Local filesystem or cloud storage integration
- **Job Integration**: Databricks Jobs API
- **API Design**: RESTful endpoints with OpenAPI documentation

### Integration Requirements
- **Databricks**: Jobs API for triggering document processing
- **Processing Notebook**: Standardized interface for schema and file inputs
- **Authentication**: Databricks workspace authentication
- **Monitoring**: Basic logging and error tracking

## Non-Functional Requirements

### Performance
- Support 100 concurrent users
- Handle files up to 50MB each
- Process batches of up to 10 files
- Response times under 2 seconds for UI operations

### Security
- File upload validation and sanitization
- Secure file storage with access controls
- Databricks authentication integration
- Input validation on all user data

### Reliability
- Graceful error handling for processing failures
- Retry logic for transient errors
- Data backup and recovery procedures
- Monitoring and alerting for system health

### Usability
- Intuitive UI requiring minimal training
- Clear error messages and guidance
- Responsive design for different screen sizes
- Accessibility compliance (WCAG 2.1)

---

## Appendix: Current App Analysis

### Issues with Existing folio-parse-stream App
1. **Overly Complex Database Schema**: Multiple interconnected tables (portfolio_analyses, portfolio_data, analysis_results, upload_logs, extraction_schemas, schema_executions) when simpler models would suffice
2. **Mixed Concerns**: Portfolio analysis concepts mixed with document extraction functionality
3. **Over-Engineering**: Complex service layers, excessive abstraction, redundant validation
4. **Poor Separation of Concerns**: Database logic mixed with business logic in services
5. **Inconsistent Error Handling**: Multiple exception types and complex error propagation
6. **Heavy Dependencies**: Complex SQLAlchemy patterns, unnecessary middleware

### Simplified Approach for New App
1. **Simple Data Model**: 3-4 core tables maximum (documents, schemas, jobs, results)
2. **Clear Single Purpose**: Focus only on document information extraction
3. **Minimal Services**: Direct database operations, simple job triggering
4. **Standard Patterns**: Use FastAPI best practices, avoid custom abstractions
5. **Progressive Enhancement**: Start simple, add complexity only when needed
6. **Modern Stack**: Leverage template's existing FastAPI + React setup