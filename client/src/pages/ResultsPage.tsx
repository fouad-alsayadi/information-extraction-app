/**
 * Results page for viewing extraction job results
 * Based on folio-parse-stream design patterns with corporate styling
 */

import { useState } from 'react';
import { Download, Eye, Clock, CheckCircle, XCircle, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiClient, JobResults, ExtractedResult } from '../lib/api';
import { useJobPolling } from '@/hooks/useJobPolling';

export function ResultsPage() {
  const { jobs, loading, error, refresh } = useJobPolling({ pollingInterval: 15000 });
  const [selectedJob, setSelectedJob] = useState<JobResults | null>(null);
  const [loadingResults, setLoadingResults] = useState(false);


  const loadJobResults = async (jobId: number) => {
    try {
      setLoadingResults(true);
      const results = await apiClient.getJobResults(jobId);
      setSelectedJob(results);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load job results');
    } finally {
      setLoadingResults(false);
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
        return 'secondary';
      case 'pending':
        return 'secondary';
      case 'not_submitted':
        return 'outline';
      case 'uploaded':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  const exportResults = (results: ExtractedResult[], format: 'json' | 'csv') => {
    if (format === 'json') {
      const dataStr = JSON.stringify(results, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `extraction-results-${Date.now()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } else if (format === 'csv') {
      // Convert to CSV format
      if (results.length === 0) return;

      const firstResult = results[0];
      const headers = ['document_filename', ...Object.keys(firstResult.extracted_data)];

      const csvContent = [
        headers.join(','),
        ...results.map(result => {
          const row = [
            `"${result.document_filename}"`,
            ...headers.slice(1).map(header => {
              const value = result.extracted_data[header];
              return typeof value === 'string' ? `"${value}"` : String(value || '');
            })
          ];
          return row.join(',');
        })
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `extraction-results-${Date.now()}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2 text-muted-foreground">Loading results...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-corporate">Extraction Results</h1>
            <p className="mt-2 text-muted-foreground">
              View and export results from your document extraction jobs
            </p>
          </div>
          <Button
            onClick={refresh}
            variant="outline"
            className="border-border hover:bg-accent/10"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-destructive/20 bg-destructive/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 text-destructive">
                <XCircle className="h-5 w-5" />
                <span className="text-sm">{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Jobs List */}
          <Card className="lg:col-span-1 bg-card border-border shadow-soft">
            <CardHeader>
              <CardTitle className="text-lg text-foreground">Extraction Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              {jobs.length === 0 ? (
                <div className="text-center py-8">
                  <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-2 text-sm font-medium text-foreground">No jobs yet</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Create your first extraction job in the Upload page
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {jobs.map((job) => (
                    <Card
                      key={job.id}
                      onClick={() => loadJobResults(job.id)}
                      className={`cursor-pointer transition-colors hover:shadow-medium ${
                        selectedJob?.job_id === job.id ? 'border-primary bg-accent/10' : 'border-border bg-background'
                      }`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(job.status)}
                            <h3 className="text-sm font-medium text-foreground truncate">
                              {job.name}
                            </h3>
                          </div>
                          <Badge variant={getStatusVariant(job.status)}>
                            {job.status}
                          </Badge>
                        </div>

                        <div className="mt-2 text-sm text-muted-foreground">
                          <p>Schema: {job.schema_name}</p>
                          <p>Documents: {job.documents_count}</p>
                          <p>Created: {new Date(job.created_at).toLocaleDateString()}</p>
                          {job.completed_at && (
                            <p>Completed: {new Date(job.completed_at).toLocaleDateString()}</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Results Display */}
          <div className="lg:col-span-2">
            {selectedJob ? (
              <Card className="bg-card border-border shadow-soft">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg text-foreground">{selectedJob.job_name}</CardTitle>
                      <p className="text-sm text-muted-foreground">Schema: {selectedJob.schema_name}</p>
                    </div>

                    {selectedJob.results.length > 0 && (
                      <div className="flex space-x-2">
                        <Button
                          onClick={() => exportResults(selectedJob.results, 'csv')}
                          variant="outline"
                          size="sm"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Export CSV
                        </Button>
                        <Button
                          onClick={() => exportResults(selectedJob.results, 'json')}
                          variant="outline"
                          size="sm"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Export JSON
                        </Button>
                      </div>
                    )}
                  </div>
                </CardHeader>

                <CardContent>
                  {loadingResults ? (
                    <div className="flex justify-center items-center h-32">
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      <span className="ml-2 text-muted-foreground">Loading results...</span>
                    </div>
                  ) : selectedJob.results.length === 0 ? (
                    <div className="text-center py-12 bg-muted/30 rounded-lg">
                      <Eye className="mx-auto h-12 w-12 text-muted-foreground" />
                      <h3 className="mt-2 text-sm font-medium text-foreground">No results yet</h3>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {selectedJob.status === 'processing'
                          ? 'Results will appear here when processing is complete'
                          : 'No extraction results found for this job'}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {selectedJob.results.map((result, index) => (
                        <Card key={index} className="bg-background border-border">
                          <CardHeader>
                            <CardTitle className="text-lg text-foreground">
                              {result.document_filename}
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            {/* Extracted Data Table */}
                            <div className="overflow-x-auto">
                              <table className="min-w-full divide-y divide-border">
                                <thead className="bg-muted/50">
                                  <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                      Field
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                      Value
                                    </th>
                                    {result.confidence_scores && (
                                      <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                        Confidence
                                      </th>
                                    )}
                                  </tr>
                                </thead>
                                <tbody className="bg-background divide-y divide-border">
                                  {Object.entries(result.extracted_data).map(([field, value]) => (
                                    <tr key={field}>
                                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-foreground">
                                        {field}
                                      </td>
                                      <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                      </td>
                                      {result.confidence_scores && (
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">
                                          {result.confidence_scores[field] ? (
                                            <Badge
                                              variant={
                                                result.confidence_scores[field] >= 0.8
                                                  ? 'default'
                                                  : result.confidence_scores[field] >= 0.6
                                                  ? 'secondary'
                                                  : 'destructive'
                                              }
                                            >
                                              {Math.round(result.confidence_scores[field] * 100)}%
                                            </Badge>
                                          ) : (
                                            '-'
                                          )}
                                        </td>
                                      )}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-card border-border shadow-soft">
                <CardContent className="text-center py-12">
                  <Eye className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-2 text-sm font-medium text-foreground">Select a job</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Choose a job from the list to view its extraction results
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}