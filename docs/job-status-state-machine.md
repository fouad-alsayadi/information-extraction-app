# Job Status State Machine

This document describes the complete state machine for extraction job status transitions in the Information Extraction App.

## State Machine Diagram

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                                                         │
                    │           JOB STATUS STATE MACHINE                      │
                    │                                                         │
                    └─────────────────────────────────────────────────────────┘

                                    ┌─────────────┐
                                    │   CREATE    │
                                    │     JOB     │
                                    └──────┬──────┘
                                           │
                                           ▼
                                   ┌───────────────┐
                                   │ NOT_SUBMITTED │
                                   │   (default)   │
                                   └───────┬───────┘
                                           │
                                           │ UPLOAD FILES
                                           │ (success)
                                           ▼
                                   ┌───────────────┐
                                   │   UPLOADED    │
                                   │               │
                                   └───┬───────┬───┘
                                       │       │
                              TRIGGER  │       │ TRIGGER
                              SUCCESS  │       │ FAILURE
                                       │       |________
                                       ▼                │
                               ┌───────────────┐        │
                               │  PROCESSING   │        │
                               │               │        │
                               └───┬───────┬───┘        │
                                   │       │ DATABRICKS │
                          DATABRICKS       │  FAILURE   |
                          SUCCESS          │____        │
                                   │            │       │
                                   ▼            ▼       ▼
                           ┌───────────────┐ ┌───────────────┐
                           │   COMPLETED   │ │    FAILED     │
                           │   (final)     │ │   (final)     │
                           └───────────────┘ └───────────────┘
```

### Upload Failure Handling
**IMPORTANT**: Upload failures do NOT change job status.
- Upload failure from `not_submitted` → HTTP error returned, job remains `not_submitted`
- Upload failure from `uploaded` → HTTP error returned, job remains `uploaded`
- Upload failure from `failed` → HTTP error returned, job remains `failed`
- Job status only changes to 'failed' during Databricks processing failures

**Example**: If a user tries to upload invalid files to a job in `not_submitted` state, the upload will fail with HTTP 422/400, but the job status stays `not_submitted` - allowing the user to retry with correct files.

## Status Definitions

### Core States

| Status | Description | Type | Actions Allowed |
|--------|-------------|------|-----------------|
| `not_submitted` | Job created, waiting for file upload | Initial | Upload files |
| `uploaded` | Files uploaded successfully | Transition | Trigger processing |
| `processing` | Databricks job running | Active | Monitor progress |
| `completed` | Job finished successfully | Final | View results, export |
| `failed` | Job encountered an error | Final | Retry, debug |

## State Transitions

### 1. Job Creation
```
[USER ACTION] → not_submitted
```
- **Trigger**: User creates a new extraction job
- **Initial State**: `not_submitted`
- **Code**: `server/database.py:137` - `DEFAULT 'not_submitted'`

### 2. File Upload
```
not_submitted → uploaded
```
- **Trigger**: Successful file upload via `/api/jobs/{job_id}/upload`
- **Validation**: Job must be in uploadable state
- **Code**: `server/routers/jobs.py:201` - `{'status': 'uploaded'}`

### 3. Processing Trigger
```
uploaded → processing
```
- **Trigger**: Databricks job triggered successfully
- **Databricks Run ID**: Assigned during this transition
- **Code**: `server/routers/jobs.py:223` - `{'status': 'processing'}`

### 4. Successful Completion
```
processing → completed
```
- **Trigger**: Databricks job terminates with `result_state: SUCCESS`
- **Progress**: 100%
- **Code**: `server/routers/jobs.py:278` - `{'status': 'completed'}`

### 5. Failure (from any state)
```
[any_state] → failed
```
- **Triggers**:
  - File upload failure
  - Databricks trigger failure: `server/routers/jobs.py:229`
  - Processing failure: `server/routers/jobs.py:286`
  - System errors

## Upload Validation Rules

### Allowed States for Upload
Jobs can accept file uploads when in these states:
- ✅ `not_submitted` - Initial state
- ✅ `uploaded` - Re-upload allowed
- ✅ `failed` - Retry after failure

### Blocked States for Upload
Jobs cannot accept file uploads when in these states:
- ❌ `processing` - Job is actively running
- ❌ `completed` - Job is finished

**Implementation**: `server/routers/jobs.py:138`
```python
if job.status not in ['not_submitted', 'uploaded', 'failed']:
    raise HTTPException(status_code=400, detail=f'Cannot upload files to job with status: {job.status}')
```

## Progress Tracking

### Databricks Job Monitoring
When job is in `processing` state, the system monitors Databricks job progress:

| Databricks Stage | Progress % | Description |
|------------------|------------|-------------|
| `PENDING` | 0% | Job queued in Databricks |
| `RUNNING` | 50% | Job actively executing |
| `TERMINATED` + `SUCCESS` | 100% | Job completed successfully |
| `TERMINATED` + `FAILURE` | 0% | Job failed |

**Implementation**: `server/routers/jobs.py:264-286`

## Error Handling

### Failure Scenarios

1. **Upload Failures**
   - File validation errors
   - Storage upload errors
   - Network issues

2. **Processing Trigger Failures**
   - Databricks API errors
   - Authentication issues
   - Resource limitations

3. **Execution Failures**
   - Processing errors in Databricks
   - Data validation failures
   - Timeout issues

### Error Recovery
- Jobs in `failed` state can be retried by uploading new files
- Error messages are stored in `error_message` field
- Detailed logs available in activity logs

## Database Schema

### Job Status Fields
```sql
-- Primary status field
status VARCHAR NOT NULL DEFAULT 'pending'

-- Additional tracking fields
created_at TIMESTAMP
updated_at TIMESTAMP
completed_at TIMESTAMP
error_message TEXT
databricks_run_id BIGINT
```

## API Integration

### Status Endpoints

#### Get Job Status
```http
GET /api/jobs/{job_id}/status
```
Returns current status with progress information.

#### Get All Jobs
```http
GET /api/jobs
```
Returns all jobs with computed status (handles legacy states).

### Frontend Integration

#### Polling Strategy
- **Results Page**: 30-second intervals
- **Processing Queue**: 45-second intervals
- **Dashboard**: On-demand refresh

#### Status Icons
- `not_submitted`: Alert icon (muted color)
- `uploaded`: Alert icon (blue color)
- `processing`: Spinning clock (info color)
- `completed`: Check circle (success color)
- `failed`: X circle (destructive color)

## Implementation Notes

### Code Locations
- **Model Definition**: `server/models.py:259`
- **Status Transitions**: `server/routers/jobs.py`
- **Upload Validation**: `server/routers/jobs.py:138`
- **Databricks Monitoring**: `server/routers/jobs.py:264-286`
- **Frontend Polling**: `client/src/hooks/useJobPolling.ts`

### Performance Considerations
- Status polling optimized to reduce server load
- Databricks API calls minimized through intelligent caching
- Database queries use computed status for efficiency

## Testing Scenarios

### Happy Path
1. Create job → `not_submitted`
2. Upload files → `uploaded`
3. Trigger processing → `processing`
4. Wait for completion → `completed`

### Error Scenarios
1. Upload invalid files → HTTP error, job status unchanged
2. Databricks trigger fails → `failed`
3. Processing errors → `failed`

### Recovery Testing
1. Retry failed jobs
2. Re-upload to uploaded jobs
3. Monitor long-running jobs

---

*Last Updated: October 4, 2025*
*Version: 1.0*