/**
 * Results page for viewing extraction job results
 * Based on folio-parse-stream design patterns with corporate styling
 */

import { Clock, CheckCircle, XCircle, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useJobPolling } from '@/hooks/useJobPolling';
import { Page } from '../App';

interface ResultsPageProps {
  onPageChange?: (page: Page, jobId?: number) => void;
}

export function ResultsPage({ onPageChange }: ResultsPageProps = {}) {
  const { jobs, loading, error, refresh } = useJobPolling({ pollingInterval: 30000 });

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

        {/* Jobs Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {jobs.length === 0 ? (
            <div className="col-span-full">
              <Card className="bg-card border-border shadow-soft">
                <CardContent className="text-center py-12">
                  <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-2 text-sm font-medium text-foreground">No jobs yet</h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Create your first extraction job in the Upload page
                  </p>
                </CardContent>
              </Card>
            </div>
          ) : (
            jobs.map((job) => (
              <Card
                key={job.id}
                onClick={() => onPageChange?.('job-details', job.id)}
                className="cursor-pointer transition-all duration-200 hover:shadow-medium hover:border-accent/50 border-border bg-background"
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="flex items-center space-x-2 min-w-0 flex-1">
                      {getStatusIcon(job.status)}
                      <h3 className="text-lg font-semibold text-foreground truncate">
                        {job.name}
                      </h3>
                    </div>
                    <Badge variant={getStatusVariant(job.status)} className="whitespace-nowrap">
                      {job.status}
                    </Badge>
                  </div>

                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p>Schema: <span className="text-foreground font-medium">{job.schema_name}</span></p>
                    <p>Documents: <span className="text-foreground font-medium">{job.documents_count}</span></p>
                    <p>Created: <span className="text-foreground font-medium">{new Date(job.created_at).toLocaleDateString()}</span></p>
                    {job.completed_at && (
                      <p>Completed: <span className="text-foreground font-medium">{new Date(job.completed_at).toLocaleDateString()}</span></p>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t border-border">
                    <div className="text-xs text-accent font-medium bg-accent/10 px-3 py-2 rounded text-center">
                      Click to view details, files & results →
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}