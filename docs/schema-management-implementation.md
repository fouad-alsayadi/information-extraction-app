# Schema Management Improvements - Implementation Guide

## Overview
Enhance the existing schema management system with advanced features for better usability, validation, and management capabilities.

## Current Architecture Analysis

### Existing Components
- `SchemasPage.tsx` - Main schema listing and management interface
- Schema creation form with basic field definitions
- Backend API endpoints for schema CRUD operations

### Current Limitations
1. No real-time validation of schema structure
2. Manual field definition without templates
3. No version control or change tracking
4. Limited field types and validation options
5. No testing capabilities before deployment

## Feature Specifications

### 1. Schema Validation System

#### Backend Implementation
```python
# New endpoint: /api/schemas/validate
class SchemaValidationRequest(BaseModel):
    schema_definition: Dict[str, Any]
    validation_rules: Optional[Dict[str, Any]] = None

class SchemaValidationResponse(BaseModel):
    is_valid: bool
    errors: List[Dict[str, str]]
    warnings: List[Dict[str, str]]
    suggestions: List[Dict[str, str]]
```

#### Frontend Components
```typescript
// SchemaValidator.tsx
interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  suggestions: string[];
}

// Real-time validation hook
const useSchemaValidation = (schema: SchemaDefinition) => {
  // Debounced validation logic
  // Return validation state and results
}
```

### 2. Schema Templates System

#### Template Categories
1. **Financial Documents**
   - Invoice template
   - Receipt template
   - Bank statement template
   - Financial report template

2. **Legal Documents**
   - Contract template
   - Agreement template
   - Legal notice template

3. **Business Documents**
   - Report template
   - Proposal template
   - Memo template

#### Implementation Structure
```typescript
interface SchemaTemplate {
  id: string;
  name: string;
  category: string;
  description: string;
  fields: FieldDefinition[];
  metadata: TemplateMetadata;
}

// TemplateSelector.tsx
const TemplateSelector: React.FC<{
  onTemplateSelect: (template: SchemaTemplate) => void;
}> = ({ onTemplateSelect }) => {
  // Template browsing and selection UI
}
```

### 3. Schema Versioning

#### Database Schema
```sql
-- New tables for versioning
CREATE TABLE schema_versions (
    id SERIAL PRIMARY KEY,
    schema_id INTEGER REFERENCES schemas(id),
    version_number INTEGER NOT NULL,
    changes_summary TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    schema_definition JSONB,
    is_active BOOLEAN DEFAULT FALSE
);

CREATE TABLE schema_change_log (
    id SERIAL PRIMARY KEY,
    schema_id INTEGER REFERENCES schemas(id),
    version_from INTEGER,
    version_to INTEGER,
    change_type VARCHAR(50),
    change_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Version Management API
```python
@router.get("/schemas/{schema_id}/versions")
async def get_schema_versions(schema_id: int):
    """Get all versions of a schema"""

@router.post("/schemas/{schema_id}/versions")
async def create_schema_version(schema_id: int, version_data: SchemaVersionCreate):
    """Create new schema version"""

@router.post("/schemas/{schema_id}/versions/{version_id}/activate")
async def activate_schema_version(schema_id: int, version_id: int):
    """Activate a specific schema version"""
```

### 4. Schema Testing Framework

#### Test Document Upload
```typescript
interface SchemaTest {
  id: string;
  schemaId: string;
  testDocument: File;
  expectedResults: Record<string, any>;
  actualResults?: Record<string, any>;
  accuracy?: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

// SchemaTestRunner.tsx
const SchemaTestRunner: React.FC<{
  schema: SchemaDefinition;
  onTestComplete: (results: SchemaTest) => void;
}> = ({ schema, onTestComplete }) => {
  // Test execution UI and results display
}
```

#### Backend Testing Service
```python
class SchemaTestService:
    async def test_schema_against_document(
        self,
        schema_definition: Dict[str, Any],
        document_file: UploadFile
    ) -> SchemaTestResult:
        """Test schema extraction against sample document"""

    async def calculate_accuracy(
        self,
        expected_results: Dict[str, Any],
        actual_results: Dict[str, Any]
    ) -> float:
        """Calculate extraction accuracy percentage"""
```

### 5. Advanced Field Types

#### New Field Type Definitions
```typescript
type FieldType =
  | 'text'
  | 'number'
  | 'date'
  | 'boolean'
  | 'email'
  | 'phone'
  | 'currency'
  | 'percentage'
  | 'array'
  | 'object'
  | 'calculated'
  | 'reference';

interface AdvancedFieldDefinition extends BaseFieldDefinition {
  type: FieldType;
  validation?: FieldValidation;
  calculation?: CalculationFormula;
  reference?: ReferenceDefinition;
  arrayItemType?: FieldType;
  objectSchema?: AdvancedFieldDefinition[];
}
```

#### Field Builder Component
```typescript
// AdvancedFieldBuilder.tsx
const AdvancedFieldBuilder: React.FC<{
  field: AdvancedFieldDefinition;
  onChange: (field: AdvancedFieldDefinition) => void;
}> = ({ field, onChange }) => {
  // Advanced field configuration UI
  // Drag-and-drop field reordering
  // Visual field type selector
  // Validation rule builder
}
```

### 6. AI-Powered Field Mapping

#### MLflow Integration
```python
class FieldMappingSuggestionService:
    def __init__(self):
        self.mlflow_client = mlflow.tracking.MlflowClient()

    async def suggest_field_mappings(
        self,
        document_content: str,
        document_type: str
    ) -> List[FieldSuggestion]:
        """Use ML model to suggest field mappings"""

    async def learn_from_user_corrections(
        self,
        document_id: str,
        suggested_mappings: List[FieldMapping],
        user_corrections: List[FieldMapping]
    ):
        """Improve suggestions based on user feedback"""
```

## Implementation Timeline

### Week 1: Foundation & Validation
- **Day 1-2**: Schema validation system
  - Backend validation endpoints
  - Frontend real-time validation
  - Error handling and user feedback

- **Day 3-4**: Schema templates
  - Template data structure
  - Template selection UI
  - Pre-built template library

- **Day 5**: Testing and integration

### Week 2: Versioning & Testing
- **Day 1-2**: Schema versioning
  - Database schema updates
  - Version management API
  - Version comparison UI

- **Day 3-4**: Schema testing framework
  - Test execution service
  - Test results visualization
  - Accuracy calculation

- **Day 5**: Advanced field types foundation

### Week 3: Advanced Features
- **Day 1-2**: Advanced field types
  - New field type implementations
  - Advanced field builder UI
  - Validation rule system

- **Day 3-4**: AI-powered suggestions
  - MLflow integration
  - Suggestion algorithm
  - Learning from feedback

- **Day 5**: Final testing and optimization

## Technical Requirements

### Backend Dependencies
```python
# Additional dependencies needed
pydantic-extra-types  # For advanced field validation
jsonschema           # For schema validation
mlflow               # For AI suggestions
redis                # For caching suggestions
```

### Frontend Dependencies
```json
{
  "react-dnd": "^16.0.1",
  "react-dnd-html5-backend": "^16.0.1",
  "@monaco-editor/react": "^4.6.0",
  "react-hook-form": "^7.47.0",
  "yup": "^1.3.3"
}
```

### Database Migrations
1. Create schema versioning tables
2. Add indexes for performance
3. Update existing schema table structure
4. Create audit trail tables

## Testing Strategy

### Unit Tests
- Schema validation logic
- Template system functionality
- Version management operations
- Field type validation

### Integration Tests
- End-to-end schema creation flow
- Template application workflow
- Version activation process
- AI suggestion pipeline

### User Acceptance Tests
- Schema builder usability
- Template selection experience
- Version management workflow
- Testing framework effectiveness

## Success Metrics

### User Experience
- 50% reduction in schema creation time
- 90% user satisfaction with template system
- 80% accuracy in AI-powered suggestions

### System Performance
- Real-time validation response < 100ms
- Template loading < 500ms
- Version switching < 200ms

### Business Impact
- Increased schema adoption rate
- Reduced schema-related errors
- Improved extraction accuracy

## Risk Mitigation

### Technical Risks
1. **Performance Impact**: Large schemas may slow validation
   - **Mitigation**: Implement debounced validation and caching

2. **Data Migration**: Existing schemas need version migration
   - **Mitigation**: Automated migration scripts with rollback capability

3. **AI Model Accuracy**: ML suggestions may be inaccurate initially
   - **Mitigation**: Start with rule-based suggestions, improve with user feedback

### User Adoption Risks
1. **Complexity**: Advanced features may overwhelm users
   - **Mitigation**: Progressive disclosure, guided tutorials

2. **Migration Burden**: Users may resist updating existing schemas
   - **Mitigation**: Backward compatibility, optional migration

## Next Steps

1. **Review and approval** of this implementation plan
2. **Environment setup** for development
3. **Database migration planning** and testing
4. **Begin implementation** with schema validation system
5. **User feedback collection** throughout development

---

**Document Version**: 1.0
**Created**: 2025-01-27
**Estimated Completion**: 3 weeks
**Dependencies**: MLflow setup, Redis configuration