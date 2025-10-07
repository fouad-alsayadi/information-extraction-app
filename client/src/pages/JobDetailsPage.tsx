/**
 * Job Details Page - Comprehensive view of a single job
 * Shows job metadata, files, schema info, and results in one place
 */

import { useEffect, useState } from 'react';
import { ArrowLeft, Loader2, Download, FileText, CheckCircle, XCircle, Clock, AlertCircle, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { JobsService, LogsService } from '../fastapi_client';
import { Page } from '../App';

interface JobDetailsData {
  job: {
    id: number;
    name: string;
    status: string;
    created_at: string;
    updated_at: string;
    schema_id: number;
    schema_name?: string;
    databricks_run_id?: number;
    databricks_job_id?: number;
    schema_field_count?: number;
    run_page_url?: string;
  };
  documents: Array<{
    id: number;
    filename: string;
    file_size: number;
    upload_time: string;
  }>;
  results: Array<{
    document_filename: string;
    extracted_data: Record<string, any>;
    confidence_scores?: Record<string, number> | null;
  }>;
}

interface JobDetailsPageProps {
  jobId: number;
  onPageChange?: (page: Page) => void;
}

export function JobDetailsPage({ jobId, onPageChange }: JobDetailsPageProps) {
  const [jobData, setJobData] = useState<JobDetailsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadJobDetails(jobId);
  }, [jobId]);

  const loadJobDetails = async (id: number) => {
    try {
      setLoading(true);

      // Load job details and results in parallel
      const [jobDetailsResponse, jobResultsResponse] = await Promise.all([
        JobsService.getJobApiJobsJobIdGet(id),
        JobsService.getJobResultsApiJobsJobIdResultsGet(id).catch(() => ({ results: [] })) // Fallback to empty results if fails
      ]);

      // Combine the data
      const combinedData: JobDetailsData = {
        job: jobDetailsResponse.job,
        documents: jobDetailsResponse.documents,
        results: jobResultsResponse.results || []
      };

      setJobData(combinedData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load job details');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    onPageChange?.('results');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-600" />;
      case 'not_submitted':
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
      case 'uploaded':
        return <AlertCircle className="h-5 w-5 text-blue-600" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
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

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const exportResults = async (results: JobDetailsData['results'], format: 'json' | 'excel') => {
    const extension = format === 'excel' ? 'xlsx' : format;
    const filename = `extraction-results-${jobData?.job.name}-${Date.now()}.${extension}`;

    if (format === 'json') {
      const dataStr = JSON.stringify(results, null, 2);
      const blob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      // Log the export event
      try {
        await LogsService.logExportEventApiLogsExportPost(
          jobId,
          filename,
          results.length
        );
      } catch (error) {
        console.error('Failed to log export event:', error);
      }
    } else if (format === 'excel') {
      if (results.length === 0) return;

      // Import xlsx library dynamically
      import('xlsx').then(async (XLSX) => {
        const firstResult = results[0];
        const headers = ['document_filename', ...Object.keys(firstResult.extracted_data)];

        // Prepare data for Excel
        const worksheetData = [
          headers, // Header row
          ...results.map(result => [
            result.document_filename,
            ...headers.slice(1).map(header => {
              const value = result.extracted_data[header];
              return value || '';
            })
          ])
        ];

        // Create workbook and worksheet
        const workbook = XLSX.utils.book_new();
        const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);

        // Auto-size columns
        const colWidths = headers.map((header, colIndex) => {
          const maxLength = Math.max(
            header.length,
            ...worksheetData.slice(1).map(row => String(row[colIndex] || '').length)
          );
          return { wch: Math.min(maxLength + 2, 50) }; // Max width 50, min header length + 2
        });
        worksheet['!cols'] = colWidths;

        // Add worksheet to workbook
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Extraction Results');

        // Generate Excel file and download
        const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
        const blob = new Blob([excelBuffer], {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        });

        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        // Log the export event
        try {
          await LogsService.logExportEventApiLogsExportPost(
            jobId,
            filename,
            results.length
          );
        } catch (error) {
          console.error('Failed to log export event:', error);
        }
      }).catch(error => {
        console.error('Failed to load Excel export library:', error);
      });
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2 text-muted-foreground">Loading job details...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center mb-6">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="mr-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <h1 className="text-2xl font-bold text-foreground">Job Details</h1>
          </div>

          <Card className="border-destructive/20 bg-destructive/10">
            <CardContent className="p-6">
              <div className="text-center">
                <p className="text-destructive font-medium">Error loading job details</p>
                <p className="text-sm text-muted-foreground mt-1">{error}</p>
                <Button
                  onClick={() => loadJobDetails(jobId)}
                  className="mt-4"
                  variant="outline"
                >
                  Try Again
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!jobData) {
    return (
      <div className="p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center mb-6">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="mr-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <h1 className="text-2xl font-bold text-foreground">Job Details</h1>
          </div>

          <Card>
            <CardContent className="p-6 text-center">
              <p className="text-muted-foreground">Job not found</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 pl-8">
      <div className="max-w-7xl">
        {/* Header with Back Button and Job Name */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="mr-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Results
            </Button>
            <div>
              <div className="flex items-center gap-3">
                {getStatusIcon(jobData.job.status)}
                <h1 className="text-3xl font-bold text-corporate">
                  {jobData.job.name}
                </h1>
                <Badge variant={getStatusVariant(jobData.job.status)}>
                  {jobData.job.status}
                </Badge>
                {jobData.job.status === 'processing' && jobData.job.databricks_run_id && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    onClick={() => {
                      // Use the dynamic run_page_url from Databricks SDK if available
                      if (jobData.job.run_page_url) {
                        window.open(jobData.job.run_page_url, '_blank');
                      } else {
                        // Fallback: Try to construct URL manually if run_page_url not available
                        let databricksHost;
                        if (window.location.hostname.includes('databricks')) {
                          // Running in Databricks workspace - extract host from current URL
                          const parts = window.location.hostname.split('.');
                          if (parts.length > 2) {
                            databricksHost = `https://${parts[0]}.cloud.databricks.com`;
                          } else {
                            databricksHost = window.location.origin;
                          }
                        } else {
                          // Local development fallback
                          databricksHost = import.meta.env.VITE_DATABRICKS_HOST;
                        }

                        if (databricksHost && jobData.job.databricks_job_id && jobData.job.databricks_run_id) {
                          const url = `${databricksHost}/jobs/${jobData.job.databricks_job_id}/runs/${jobData.job.databricks_run_id}`;
                          window.open(url, '_blank');
                        } else {
                          alert('Unable to open Databricks job page. Job URL not available.');
                        }
                      }
                    }}
                  >
                    <ExternalLink className="h-4 w-4" />
                    View in Databricks
                  </Button>
                )}
              </div>
              <p className="text-muted-foreground mt-1">
                Job ID: {jobData.job.id} • Schema: {jobData.job.schema_name || 'Unknown'}
              </p>
            </div>
          </div>

          {/* Export Actions */}
          {jobData.results.length > 0 && (
            <div className="flex gap-2">
              <Button
                onClick={() => exportResults(jobData.results, 'excel')}
                variant="outline"
                size="sm"
              >
                <Download className="h-4 w-4 mr-2" />
                Export Excel
              </Button>
              <Button
                onClick={() => exportResults(jobData.results, 'json')}
                variant="outline"
                size="sm"
              >
                <Download className="h-4 w-4 mr-2" />
                Export JSON
              </Button>
            </div>
          )}
        </div>

        {/* Job Overview and Files - Side by Side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Job Overview */}
          <Card className="bg-card border-border shadow-soft">
            <CardHeader>
              <CardTitle className="text-lg text-foreground">Job Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-x-8 gap-y-3">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Created:</span>
                  <span className="text-sm text-foreground font-medium">
                    {new Date(jobData.job.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Last Updated:</span>
                  <span className="text-sm text-foreground font-medium">
                    {new Date(jobData.job.updated_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Files Uploaded:</span>
                  <span className="text-sm text-foreground font-medium">{jobData.documents.length} documents</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Results Generated:</span>
                  <span className="text-sm text-foreground font-medium">{jobData.results.length} processed</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Schema ID:</span>
                  <span className="text-sm text-foreground font-medium">{jobData.job.schema_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-muted-foreground">Schema Fields:</span>
                  <span className="text-sm text-foreground font-medium">
                    {jobData.job.schema_field_count !== undefined ? jobData.job.schema_field_count : 'N/A'} fields
                  </span>
                </div>
                {jobData.job.databricks_run_id && (
                  <div className="col-span-2 pt-3 border-t border-border">
                    <div className="flex justify-between items-start">
                      <span className="text-sm font-medium text-muted-foreground">Databricks Run ID:</span>
                      <span className="text-foreground font-medium text-xs font-mono break-all text-right max-w-[60%]">
                        {jobData.job.databricks_run_id}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Uploaded Files */}
          <Card className="bg-card border-border shadow-soft">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg text-foreground">
                <FileText className="h-5 w-5" />
                Uploaded Files ({jobData.documents.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {jobData.documents.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">No files uploaded yet</p>
              ) : (
                <div className="max-h-80 overflow-y-auto">
                  <table className="min-w-full divide-y divide-border">
                    <thead className="bg-muted/50 sticky top-0">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          File Name
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Size
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                          Uploaded
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-background divide-y divide-border">
                      {jobData.documents.map((doc) => (
                        <tr key={doc.id} className="hover:bg-muted/30">
                          <td className="px-4 py-3 text-sm">
                            <div className="flex items-center gap-2">
                              <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                              <span className="font-medium text-foreground truncate">{doc.filename}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm text-muted-foreground">
                            {formatFileSize(doc.file_size)}
                          </td>
                          <td className="px-4 py-3 text-sm text-muted-foreground">
                            {new Date(doc.upload_time).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Extraction Results - Two Column Layout */}
        <Card className="bg-card border-border shadow-soft">
          <CardHeader>
            <CardTitle className="text-lg text-foreground">
              Extraction Results ({jobData.results.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {jobData.results.length === 0 ? (
              <div className="text-center py-12 bg-muted/30 rounded-lg">
                <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-2 text-sm font-medium text-foreground">No results yet</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {jobData.job.status === 'processing'
                    ? 'Results will appear here when processing is complete'
                    : 'No extraction results found for this job'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {jobData.results.map((result, index) => (
                  <Card key={index} className="bg-background border-border">
                    <CardHeader>
                      <CardTitle className="text-base text-foreground flex items-center gap-2">
                        <FileText className="h-4 w-4" />
                        {result.document_filename}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-border">
                          <thead className="bg-muted/50">
                            <tr>
                              <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase">
                                Field
                              </th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase">
                                Value
                              </th>
                              {result.confidence_scores && (
                                <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase">
                                  Confidence
                                </th>
                              )}
                            </tr>
                          </thead>
                          <tbody className="bg-background divide-y divide-border">
                            {Object.entries(result.extracted_data).map(([field, value]) => (
                              <tr key={field}>
                                <td className="px-4 py-3 text-sm font-medium text-foreground">
                                  {field}
                                </td>
                                <td className="px-4 py-3 text-sm text-muted-foreground break-words">
                                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </td>
                                {result.confidence_scores && (
                                  <td className="px-4 py-3 text-sm text-muted-foreground">
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
      </div>
    </div>
  );
}