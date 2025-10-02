/**
 * Job Details Page - Comprehensive view of a single job
 * Shows job metadata, files, schema info, and results in one place
 */

import { useEffect, useState } from 'react';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api';
import { Page } from '../App';

interface JobDetailsData {
  job: {
    id: number;
    name: string;
    status: string;
    created_at: string;
    updated_at: string;
    schema_id: number;
  };
  documents: Array<{
    id: number;
    filename: string;
    file_size: number;
    upload_time: string;
  }>;
  results: Array<{
    id: number;
    document_filename: string;
    extracted_data: Record<string, any>;
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
      const response = await apiClient.getJobDetails(id);
      setJobData(response);
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
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header with Back Button and Job Name */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="mr-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-corporate">
                {jobData.job.name}
              </h1>
              <p className="text-muted-foreground mt-1">
                Job Details • ID: {jobData.job.id}
              </p>
            </div>
          </div>

          {/* Placeholder for future action buttons */}
          <div className="flex gap-2">
            <Button variant="outline" disabled>
              Actions Coming Soon
            </Button>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Job Overview - Placeholder */}
          <Card className="lg:col-span-1 bg-card border-border shadow-soft">
            <CardHeader>
              <CardTitle className="text-lg text-foreground">Job Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div>
                  <span className="text-sm font-medium text-muted-foreground">Status:</span>
                  <p className="text-foreground">{jobData.job.status}</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-muted-foreground">Created:</span>
                  <p className="text-foreground">
                    {new Date(jobData.job.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <span className="text-sm font-medium text-muted-foreground">Files:</span>
                  <p className="text-foreground">{jobData.documents.length} documents</p>
                </div>
                <div>
                  <span className="text-sm font-medium text-muted-foreground">Results:</span>
                  <p className="text-foreground">{jobData.results.length} processed</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Files and Results - Placeholder */}
          <div className="lg:col-span-2 space-y-6">
            {/* Files Placeholder */}
            <Card className="bg-card border-border shadow-soft">
              <CardHeader>
                <CardTitle className="text-lg text-foreground">Uploaded Files</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  File list will be implemented in the next step
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Found {jobData.documents.length} files
                </p>
              </CardContent>
            </Card>

            {/* Results Placeholder */}
            <Card className="bg-card border-border shadow-soft">
              <CardHeader>
                <CardTitle className="text-lg text-foreground">Extraction Results</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">
                  Results display will be implemented in upcoming steps
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Found {jobData.results.length} results
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}