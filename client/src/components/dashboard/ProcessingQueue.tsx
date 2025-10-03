import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Eye } from "lucide-react";
import { useJobPolling } from "@/hooks/useJobPolling";

interface JobSummary {
  id: number;
  name: string;
  schema_name: string;
  status: string;
  documents_count: number;
  created_at: string;
  completed_at?: string;
}

interface JobRun {
  id: string;
  name: string;
  schema: string;
  status: string;
  progress: number;
  documentsTotal: number;
  documentsProcessed: number;
  estimatedTime: string;
  job_id: number;
}

function getStatusBadge(status: string) {
  const statusLower = status?.toLowerCase() || '';

  if (statusLower.includes('running') || statusLower.includes('processing')) {
    return "bg-blue-100 text-blue-800 border-blue-200";
  } else if (statusLower.includes('success') || statusLower.includes('completed')) {
    return "bg-green-100 text-green-800 border-green-200";
  } else if (statusLower.includes('failed') || statusLower.includes('error')) {
    return "bg-red-100 text-red-800 border-red-200";
  } else if (statusLower.includes('pending') || statusLower.includes('queued')) {
    return "bg-yellow-100 text-yellow-800 border-yellow-200";
  } else if (statusLower.includes('not_submitted')) {
    return "bg-slate-100 text-slate-600 border-slate-200";
  } else if (statusLower.includes('uploaded')) {
    return "bg-blue-50 text-blue-600 border-blue-200";
  } else {
    return "bg-gray-100 text-gray-600 border-gray-200";
  }
}

// Transform job summary to ProcessingQueue format
const transformJobSummary = (job: JobSummary): JobRun => {
  const statusLower = job.status?.toLowerCase() || '';
  const isCompleted = statusLower === 'completed' || statusLower === 'failed';
  const isProcessing = statusLower === 'processing';

  // Calculate progress based on status
  let progress = 0;
  if (isCompleted) {
    progress = 100;
  } else if (isProcessing) {
    // Estimate progress for processing jobs (could be enhanced with real-time data)
    progress = 50;
  } else if (statusLower === 'pending') {
    progress = 10;
  } else if (statusLower === 'not_submitted') {
    progress = 0;
  } else if (statusLower === 'uploaded') {
    progress = 5;
  }

  let estimatedTime = "";
  if (statusLower === 'completed') {
    estimatedTime = "Completed";
  } else if (statusLower === 'failed') {
    estimatedTime = "Failed";
  } else if (isProcessing) {
    estimatedTime = "Processing...";
  } else if (statusLower === 'pending') {
    estimatedTime = "Queued";
  } else if (statusLower === 'not_submitted') {
    estimatedTime = "Awaiting Upload";
  } else if (statusLower === 'uploaded') {
    estimatedTime = "Ready to Process";
  } else {
    estimatedTime = "Unknown";
  }

  return {
    id: `job_${job.id}`,
    name: job.name,
    schema: job.schema_name || "Unknown Schema",
    status: job.status,
    progress: progress,
    documentsTotal: job.documents_count,
    documentsProcessed: isCompleted ? job.documents_count : Math.floor((progress / 100) * job.documents_count),
    estimatedTime: estimatedTime,
    job_id: job.id
  };
};

interface ProcessingQueueProps {
  onPageChange?: (page: 'schemas' | 'upload' | 'results' | 'dashboard' | 'job-details', jobId?: number) => void;
}

export function ProcessingQueue({ onPageChange }: ProcessingQueueProps = {}) {
  const { jobs: allJobs, loading: isLoading } = useJobPolling({ pollingInterval: 10000 });

  // Filter to show recent jobs and active jobs
  const jobs = allJobs
    .filter((job: JobSummary) => {
      const jobDate = new Date(job.created_at);
      const daysSinceCreation = (Date.now() - jobDate.getTime()) / (1000 * 60 * 60 * 24);
      return daysSinceCreation <= 7; // Show jobs from last 7 days
    })
    .slice(0, 4) // Show only top 4
    .map(transformJobSummary);

  const handleViewAll = () => {
    onPageChange?.('results');
  };

  const handleViewJob = (job: JobRun) => {
    onPageChange?.('job-details', job.job_id);
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-border shadow-soft flex flex-col">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
          <div>
            <CardTitle className="text-lg font-semibold text-foreground">Processing Queue</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Recent document processing jobs
            </p>
          </div>
          <Skeleton className="h-8 w-16" />
        </CardHeader>
        <CardContent className="h-96 overflow-y-auto space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-24" />
                </div>
                <div className="flex items-center gap-2">
                  <Skeleton className="h-6 w-16" />
                  <div className="flex gap-1">
                    <Skeleton className="h-8 w-8" />
                  </div>
                </div>
              </div>
              <div className="space-y-2">
                <Skeleton className="h-2 w-full" />
                <div className="flex justify-between">
                  <Skeleton className="h-3 w-24" />
                  <Skeleton className="h-3 w-20" />
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  if (jobs.length === 0) {
    return (
      <Card className="bg-card border-border shadow-soft flex flex-col">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
          <div>
            <CardTitle className="text-lg font-semibold text-foreground">Processing Queue</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Recent document processing jobs
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={handleViewAll} className="text-accent border-accent/30 hover:bg-accent/10">
            View All
          </Button>
        </CardHeader>
        <CardContent className="h-96 p-6 text-center flex items-center justify-center">
          <div>
            <p className="text-muted-foreground">No recent processing jobs</p>
            <p className="text-xs text-muted-foreground mt-1">Jobs will appear here when documents are being processed</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border shadow-soft flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
        <div>
          <CardTitle className="text-lg font-semibold text-foreground">Processing Queue</CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Recent document processing jobs
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleViewAll} className="text-accent border-accent/30 hover:bg-accent/10">
          View All
        </Button>
      </CardHeader>
      <CardContent className="h-96 overflow-y-auto space-y-2">
        {jobs.map((job) => (
          <div key={job.id} className="border border-border rounded-lg p-4 hover:shadow-soft transition-all duration-200">
            <div className="flex items-center justify-between mb-3">
              <div className="space-y-1">
                <h4 className="font-medium text-foreground">{job.name}</h4>
                <p className="text-sm text-muted-foreground">{job.schema}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge className={getStatusBadge(job.status)}>
                  {job.status || 'Unknown'}
                </Badge>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    onClick={() => handleViewJob(job)}
                    title="View Results"
                  >
                    <Eye className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Progress value={job.progress} className="h-2" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>{job.documentsProcessed} / {job.documentsTotal} documents</span>
                <span>
                  {job.estimatedTime}
                </span>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}