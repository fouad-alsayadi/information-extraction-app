/**
 * Schemas page for managing extraction schemas
 * Based on folio-parse-stream design patterns with corporate styling
 */

import { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, FileText, Calendar, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiClient, ExtractionSchemaSummary, SchemaField } from '../lib/api';

export function SchemasPage() {
  const [schemas, setSchemas] = useState<ExtractionSchemaSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Load schemas on mount
  useEffect(() => {
    loadSchemas();
  }, []);

  const loadSchemas = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSchemas();
      setSchemas(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load schemas');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSchema = async (schemaData: {
    name: string;
    description: string;
    fields: SchemaField[];
  }) => {
    try {
      await apiClient.createSchema(schemaData);
      setShowCreateModal(false);
      loadSchemas(); // Reload the list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create schema');
    }
  };

  const handleDeleteSchema = async (id: number, name: string) => {
    if (window.confirm(`Are you sure you want to delete the schema "${name}"?`)) {
      try {
        await apiClient.deleteSchema(id);
        loadSchemas(); // Reload the list
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete schema');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-subtle">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2 text-muted-foreground">Loading schemas...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-subtle">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-corporate">Schema Management</h1>
            <p className="mt-2 text-muted-foreground">
              Create and manage extraction templates for your documents
            </p>
          </div>
          <Button
            onClick={() => setShowCreateModal(true)}
            className="bg-gradient-accent text-accent-foreground hover:opacity-90"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create New Schema
          </Button>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-destructive/20 bg-destructive/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 text-destructive">
                <Trash2 className="h-5 w-5" />
                <span className="text-sm">{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Empty State or Schema Grid */}
        {schemas.length === 0 ? (
          <Card className="bg-card border-border shadow-soft">
            <CardContent className="p-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">No schemas found</h3>
              <p className="text-muted-foreground mb-6">
                Create your first schema to start extracting data from documents
              </p>
              <Button
                onClick={() => setShowCreateModal(true)}
                className="bg-primary text-primary-foreground hover:bg-primary-hover"
              >
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Schema
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {schemas.map((schema) => (
              <Card
                key={schema.id}
                className="bg-card border-border shadow-soft hover:shadow-medium transition-shadow"
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <FileText className="h-6 w-6 text-primary" />
                      <h3 className="ml-3 text-lg font-medium text-foreground truncate">
                        {schema.name}
                      </h3>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {/* TODO: Edit schema */}}
                        className="text-muted-foreground hover:text-foreground"
                        title="Edit schema"
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteSchema(schema.id, schema.name)}
                        className="text-muted-foreground hover:text-destructive"
                        title="Delete schema"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
                    {schema.description || 'No description provided'}
                  </p>

                  <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
                    <span>{schema.fields_count} fields</span>
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-1" />
                      {new Date(schema.created_at).toLocaleDateString()}
                    </div>
                  </div>

                  <div className="mt-4 flex items-center justify-between">
                    <Badge
                      variant={schema.is_active ? "default" : "secondary"}
                      className={schema.is_active ? "bg-success text-success-foreground" : ""}
                    >
                      {schema.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create Schema Modal */}
        {showCreateModal && (
          <CreateSchemaModal
            onClose={() => setShowCreateModal(false)}
            onCreate={handleCreateSchema}
          />
        )}
      </div>
    </div>
  );
}

// Create Schema Modal Component
interface CreateSchemaModalProps {
  onClose: () => void;
  onCreate: (data: { name: string; description: string; fields: SchemaField[] }) => void;
}

function CreateSchemaModal({ onClose, onCreate }: CreateSchemaModalProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [fields, setFields] = useState<SchemaField[]>([
    { name: '', type: 'text', required: false, description: '' },
  ]);

  const addField = () => {
    setFields([...fields, { name: '', type: 'text', required: false, description: '' }]);
  };

  const removeField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
  };

  const updateField = (index: number, updates: Partial<SchemaField>) => {
    setFields(fields.map((field, i) => (i === index ? { ...field, ...updates } : field)));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate
    if (!name.trim()) {
      alert('Schema name is required');
      return;
    }

    const validFields = fields.filter(field => field.name.trim());
    if (validFields.length === 0) {
      alert('At least one field is required');
      return;
    }

    onCreate({
      name: name.trim(),
      description: description.trim(),
      fields: validFields,
    });
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Schema</h3>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Schema Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Invoice Extraction"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe what this schema extracts..."
              />
            </div>

            {/* Fields */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  Fields *
                </label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={addField}
                  className="text-sm text-primary hover:text-primary-hover"
                >
                  + Add Field
                </Button>
              </div>

              <div className="space-y-3">
                {fields.map((field, index) => (
                  <div key={index} className="border border-gray-200 rounded-md p-3">
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                      <div>
                        <input
                          type="text"
                          placeholder="Field name"
                          value={field.name}
                          onChange={(e) => updateField(index, { name: e.target.value })}
                          className="w-full border border-gray-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div className="flex space-x-2">
                        <select
                          value={field.type}
                          onChange={(e) => updateField(index, { type: e.target.value as any })}
                          className="flex-1 border border-gray-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="text">Text</option>
                          <option value="number">Number</option>
                          <option value="date">Date</option>
                          <option value="currency">Currency</option>
                          <option value="percentage">Percentage</option>
                        </select>
                        <label className="flex items-center text-sm">
                          <input
                            type="checkbox"
                            checked={field.required}
                            onChange={(e) => updateField(index, { required: e.target.checked })}
                            className="mr-1"
                          />
                          Required
                        </label>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeField(index)}
                          className="text-destructive hover:text-destructive/80"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    <div className="mt-2">
                      <input
                        type="text"
                        placeholder="Field description (optional)"
                        value={field.description}
                        onChange={(e) => updateField(index, { description: e.target.value })}
                        className="w-full border border-gray-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="bg-gradient-primary text-primary-foreground hover:opacity-90"
              >
                Create Schema
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}