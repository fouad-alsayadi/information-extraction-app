# Job Details Page - Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for creating a comprehensive Job Details page that addresses the current gap in our application. Currently, we only have a ResultsPage with limited job information. This new page will provide a complete view of job information including metadata, files, schema details, and results.

## Current State Analysis

### Existing Components
- **ResultsPage**: Shows job list on left, results on right (limited view)
- **ProcessingQueue**: Shows job cards with basic status
- **UploadPage**: Create new jobs and upload files

### Missing Functionality
- **Comprehensive Job View**: Single page showing all job information
- **File Management**: View, add, remove uploaded files
- **Job Management**: Edit, delete, duplicate jobs
- **State-Aware Actions**: Context-appropriate actions based on job state

## Implementation Philosophy

- **One feature at a time** with complete testing before moving forward
- **User validation** required after each step before proceeding
- **Code review** and push after each completed feature
- **No moving forward** until current step is approved and tested

## Step-by-Step Implementation Roadmap

### Step 1: Basic Job Details Page Structure
**Goal**: Create the foundation page with routing and basic layout

**Files to Create/Modify**:
- `client/src/pages/JobDetailsPage.tsx` (new)
- `client/src/App.tsx` (add routing)
- `client/src/components/dashboard/ProcessingQueue.tsx` (add navigation)

**Implementation Tasks**:
1. Create new `JobDetailsPage.tsx` component
2. Add routing for `/jobs/:jobId`
3. Basic page layout with header and placeholder cards
4. Navigation integration from ProcessingQueue

**Testing Criteria**:
- ✅ Route `/jobs/16` loads the page
- ✅ Breadcrumb navigation works
- ✅ Can navigate to job details from ProcessingQueue
- ✅ Page layout is responsive

**API Requirements**: Use existing `/api/jobs/{job_id}` endpoint

---

### Step 2: Job Overview Information Display
**Goal**: Show basic job information (status, dates, schema summary)

**Files to Create/Modify**:
- `client/src/components/job-details/JobOverviewCard.tsx` (new)
- `client/src/pages/JobDetailsPage.tsx` (integrate component)

**Implementation Tasks**:
1. Fetch job details from existing `/api/jobs/{job_id}` endpoint
2. Create JobOverviewCard component
3. Display job metadata (name, status, dates)
4. Show simple schema info (name, ID, field count)

**Testing Criteria**:
- ✅ Job information displays correctly
- ✅ Status badges match other pages
- ✅ Schema info shows: "Invoice Information (#1) - 9 fields"
- ✅ Loading and error states work

**Data Structure**:
```typescript
interface JobDetails {
  job: {
    id: number;
    name: string;
    status: string;
    created_at: string;
    updated_at: string;
    schema_id: number;
  };
  schema: {
    id: number;
    name: string;
    fields: SchemaField[];
  };
}
```

---

### Step 3: File List Display
**Goal**: Show uploaded files with metadata

**Files to Create/Modify**:
- `client/src/components/job-details/FileListCard.tsx` (new)
- `client/src/pages/JobDetailsPage.tsx` (integrate component)

**Implementation Tasks**:
1. Create FileListCard component
2. Display files from existing job API response
3. Show file metadata (name, size, upload date)
4. Format file sizes and dates properly

**Testing Criteria**:
- ✅ All uploaded files are listed
- ✅ File sizes are human-readable (252 KB)
- ✅ Upload dates are formatted correctly
- ✅ Empty state when no files

**Data Structure**:
```typescript
interface DocumentInfo {
  id: number;
  filename: string;
  file_size: number;
  upload_time: string;
}
```

---

### Step 4: Results Summary Display
**Goal**: Show extraction results in compact format

**Files to Create/Modify**:
- `client/src/components/job-details/ResultsPreviewCard.tsx` (new)
- `client/src/pages/JobDetailsPage.tsx` (integrate component)

**Implementation Tasks**:
1. Create ResultsPreviewCard component
2. Display results from existing job API response
3. Show key extracted fields per document
4. Add "View Full" interaction for detailed view

**Testing Criteria**:
- ✅ Results show for each processed document
- ✅ Key fields are displayed (Invoice #, Date, etc.)
- ✅ Results match what's in current ResultsPage
- ✅ Handles documents with/without results

---

### Step 5: State-Aware Action Buttons
**Goal**: Add job actions based on current state

**Files to Create/Modify**:
- `client/src/components/job-details/JobHeader.tsx` (new)
- `client/src/pages/JobDetailsPage.tsx` (integrate component)

**Implementation Tasks**:
1. Add action buttons to job header
2. Implement state logic for button visibility
3. Add basic job operations (View Results, Export)
4. Connect existing functionality (link to ResultsPage)

**State-Action Mapping**:
```typescript
const getJobActions = (status: string) => {
  switch (status) {
    case 'not_submitted': return ['Upload Files', 'Edit Job', 'Delete Job']
    case 'uploaded': return ['Add Files', 'Remove Files', 'Edit Job']
    case 'processing': return ['View Status', 'View Logs']
    case 'completed': return ['Export Results', 'Duplicate Job', 'Archive Job']
    case 'failed': return ['Retry Job', 'Edit Job', 'View Error', 'Delete Job']
  }
}
```

**Testing Criteria**:
- ✅ Completed jobs show "Export Results" button
- ✅ Processing jobs show "View Status" button
- ✅ Not_submitted jobs show "Upload Files" button
- ✅ Actions work correctly for each state

---

## Future Steps (Steps 6-10)

### Step 6: Enhanced API Endpoint (if needed)
- Evaluate existing API sufficiency
- Create optimized endpoint if needed
- Include schema info with field count

### Step 7: File Management Actions
- Add file upload/remove functionality
- Implement file validation
- Add confirmation dialogs

### Step 8: Job Management Operations
- Add job editing functionality
- Add job deletion with confirmation
- Add job duplication

### Step 9: Enhanced Results Export
- Add individual document export
- Add bulk export options
- Improve export file naming

### Step 10: Error Handling and Edge Cases
- Add comprehensive error handling
- Handle missing/deleted jobs
- Add retry mechanisms

## Component Architecture

### Main Component Structure
```
JobDetailsPage/
├── JobHeader (Step 5)
├── JobOverviewCard (Step 2)
├── FileListCard (Step 3)
└── ResultsPreviewCard (Step 4)
```

### Shared Types
```typescript
// client/src/types/job-details.ts
interface JobDetailsResponse {
  job: JobMetadata;
  documents: DocumentInfo[];
  results: ExtractionResult[];
  schema: SchemaInfo;
}
```

## Review Process

After each step:
1. **Code Review**: Present changes and explain implementation
2. **User Testing**: User tests functionality in browser
3. **Feedback Integration**: Address any issues or improvements
4. **Code Push**: Commit and push changes after approval
5. **Documentation Update**: Update progress in this document

## Success Criteria

Final job details page should:
- ✅ Show complete job information in one place
- ✅ Provide state-aware actions for all job states
- ✅ Support file management operations
- ✅ Enable job management (edit, delete, duplicate)
- ✅ Display results with export options
- ✅ Handle all error scenarios gracefully
- ✅ Be fully responsive and accessible
- ✅ Integrate seamlessly with existing app navigation

## Progress Tracking

- [ ] **Step 1**: Basic page structure *(In Progress)*
- [ ] **Step 2**: Job overview display
- [ ] **Step 3**: File list display
- [ ] **Step 4**: Results summary display
- [ ] **Step 5**: State-aware actions
- [ ] **Step 6**: Enhanced API (if needed)
- [ ] **Step 7**: File management
- [ ] **Step 8**: Job management
- [ ] **Step 9**: Enhanced export
- [ ] **Step 10**: Error handling

---

*This document will be updated after each step completion with lessons learned and any adjustments to the plan.*