/**
 * Schema Details page showing schema information and associated jobs
 * Based on folio-parse-stream design patterns with corporate styling
 */

import { useState, useEffect } from 'react';
import {
  ArrowLeft,
  FileText,
  Calendar,
  Settings,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Loader2,
  Plus,
  Copy
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SchemasService, ExtractionSchema, ExtractionJobSummary } from '../fastapi_client';
import { Page } from '../App';

interface SchemaDetailsPageProps {
  schemaId: number;
  onPageChange: (page: Page, jobId?: number) => void;
}

interface SchemaJobData {
  schema: ExtractionSchema;
  jobs: ExtractionJobSummary[];
}

export function SchemaDetailsPage({ schemaId, onPageChange }: SchemaDetailsPageProps) {
  const [schemaData, setSchemaData] = useState<SchemaJobData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSchemaDetails();
  }, [schemaId]);

  const loadSchemaDetails = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load schema details and jobs in parallel
      const [schemaResponse, jobsResponse] = await Promise.all([
        SchemasService.getSchemaApiSchemasSchemaIdGet(schemaId),
        SchemasService.getJobsBySchemaApiSchemasSchemaIdJobsGet(schemaId)
      ]);

      setSchemaData({
        schema: schemaResponse,
        jobs: jobsResponse
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load schema details');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-success" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-destructive" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-info animate-spin" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-warning" />;
      case 'not_submitted':
        return <AlertCircle className="h-5 w-5 text-muted-foreground" />;
      case 'uploaded':
        return <AlertCircle className="h-5 w-5 text-blue-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-warning" />;
    }
  };

  const getStatusVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'failed':
        return 'destructive';
      case 'processing':
      case 'pending':
      case 'uploaded':
        return 'secondary';
      case 'not_submitted':
        return 'outline';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2 text-muted-foreground">Loading schema details...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <Card className="border-destructive/20 bg-destructive/10">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 text-destructive">
                <XCircle className="h-5 w-5" />
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!schemaData) {
    return null;
  }

  const { schema, jobs } = schemaData;

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="ghost"
            onClick={() => onPageChange('schemas')}
            className="text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Schemas
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-corporate">{schema.name}</h1>
            <p className="mt-2 text-muted-foreground">
              {schema.description || 'No description provided'}
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => {
              // Navigate to schemas page with duplicate intent
              onPageChange({ type: 'schemas', duplicateSchemaId: schemaId });
            }}
            className="gap-2"
          >
            <Copy className="h-4 w-4" />
            Duplicate Schema
          </Button>
        </div>

        {/* Schema Information Section */}
        <div className="grid gap-6 lg:grid-cols-4 mb-8">
          <Card className="bg-card border-border shadow-soft">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge
                variant={schema.is_active ? "default" : "secondary"}
                className={schema.is_active ? "bg-success text-success-foreground" : ""}
              >
                {schema.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-soft">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground">Created</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-foreground">
                <Calendar className="h-4 w-4" />
                {new Date(schema.created_at).toLocaleDateString()}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-soft">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Fields</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-foreground">{schema.fields.length}</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-soft">
            <CardHeader className="pb-4">
              <CardTitle className="text-sm font-medium text-muted-foreground">Jobs Created</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-foreground">{jobs.length}</p>
            </CardContent>
          </Card>
        </div>

        {/* Schema Fields Table */}
        <Card className="bg-card border-border shadow-soft mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Schema Fields
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 font-medium text-foreground">Field Name</th>
                    <th className="text-left py-3 px-4 font-medium text-foreground">Type</th>
                    <th className="text-left py-3 px-4 font-medium text-foreground">Required</th>
                    <th className="text-left py-3 px-4 font-medium text-foreground">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {schema.fields.map((field, index) => (
                    <tr key={index} className="border-b border-border/50 hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <span className="font-medium text-foreground">{field.name}</span>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className="text-xs">
                          {field.type}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        {field.required ? (
                          <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700 border-blue-200">
                            Yes
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground text-sm">No</span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-muted-foreground text-sm">
                          {field.description || 'No description'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Jobs Grid */}
        <Card className="bg-card border-border shadow-soft">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Play className="h-5 w-5" />
                Jobs Using This Schema
              </CardTitle>
              <div className="flex items-center gap-3">
                <Button
                  variant="default"
                  size="sm"
                  className="gap-1.5"
                  onClick={() => {
                    // Navigate to upload page with pre-selected schema
                    onPageChange?.({ type: 'upload', selectedSchemaId: schemaId });
                  }}
                >
                  <Plus className="h-4 w-4" />
                  Create New Job
                </Button>
                <Badge variant="outline">
                  {jobs.length} job{jobs.length !== 1 ? 's' : ''}
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {jobs.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No jobs found</h3>
                <p className="text-muted-foreground">
                  No extraction jobs have been created with this schema yet.
                </p>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {jobs.map((job) => (
                  <Card
                    key={job.id}
                    className="cursor-pointer transition-all duration-200 hover:shadow-medium hover:border-accent/50 border-border bg-background"
                    onClick={() => onPageChange('job-details', job.id)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2 min-w-0 flex-1">
                          {getStatusIcon(job.status)}
                          <h3 className="font-medium text-foreground truncate">
                            {job.name}
                          </h3>
                        </div>
                        <Badge variant={getStatusVariant(job.status)} className="whitespace-nowrap">
                          {job.status}
                        </Badge>
                      </div>

                      <div className="space-y-2 text-sm text-muted-foreground">
                        <div className="flex justify-between">
                          <span>Documents:</span>
                          <span className="text-foreground font-medium">{job.documents_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Created:</span>
                          <span className="text-foreground font-medium">
                            {new Date(job.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        {job.completed_at && (
                          <div className="flex justify-between">
                            <span>Completed:</span>
                            <span className="text-foreground font-medium">
                              {new Date(job.completed_at).toLocaleDateString()}
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="mt-3 pt-3 border-t border-border">
                        <div className="text-xs text-accent font-medium bg-accent/10 px-2 py-1 rounded text-center">
                          Click to view details →
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}