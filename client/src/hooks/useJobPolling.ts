import { useState, useEffect, useRef, useCallback } from 'react';
import { JobsService } from '@/fastapi_client';

interface JobSummary {
  id: number;
  name: string;
  schema_name: string;
  status: string;
  documents_count: number;
  created_at: string;
  completed_at?: string;
}

interface UseJobPollingOptions {
  pollingInterval?: number;
  enabled?: boolean;
}

export function useJobPolling(options: UseJobPollingOptions = {}) {
  const { pollingInterval = 15000, enabled = true } = options;
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchJobs = useCallback(async () => {
    if (!enabled) return;

    try {
      if (loading) setLoading(true);
      const response = await JobsService.getJobsApiJobsGet();
      const jobData = response as JobSummary[];

      // Check status of processing/pending jobs to trigger updates
      const processingJobs = jobData.filter(job =>
        job.status.toLowerCase() === 'processing' || job.status.toLowerCase() === 'pending'
      );

      // Call status endpoint for each processing job to trigger status updates
      if (processingJobs.length > 0) {
        console.log(`useJobPolling: Checking status for ${processingJobs.length} processing jobs`);
        await Promise.all(
          processingJobs.map(async (job) => {
            try {
              await JobsService.getJobStatusApiJobsJobIdStatusGet(job.id);
            } catch (err) {
              console.warn(`Failed to check status for job ${job.id}:`, err);
            }
          })
        );

        // Refetch jobs after status checks to get updated data
        const updatedResponse = await JobsService.getJobsApiJobsGet();
        const updatedJobData = updatedResponse as JobSummary[];
        setJobs(updatedJobData);

        // Check again for processing jobs after status updates
        const stillProcessingJobs = updatedJobData.some(job =>
          job.status.toLowerCase() === 'processing' || job.status.toLowerCase() === 'pending'
        );

        // Start/stop polling based on processing jobs
        if (stillProcessingJobs && !intervalRef.current) {
          console.log(`useJobPolling: Starting polling (${pollingInterval}ms) - found processing jobs`);
          intervalRef.current = setInterval(fetchJobs, pollingInterval);
        } else if (!stillProcessingJobs && intervalRef.current) {
          console.log('useJobPolling: Stopping polling - no processing jobs');
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } else {
        setJobs(jobData);
        // Stop polling if no processing jobs
        if (intervalRef.current) {
          console.log('useJobPolling: Stopping polling - no processing jobs');
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }

      setError(null);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      if (loading) setLoading(false);
    }
  }, [enabled, pollingInterval, loading]);

  useEffect(() => {
    fetchJobs();

    // Cleanup interval on unmount or when disabled
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [fetchJobs]);

  // Manual refresh function
  const refresh = useCallback(() => {
    fetchJobs();
  }, [fetchJobs]);

  return {
    jobs,
    loading,
    error,
    refresh,
    isPolling: !!intervalRef.current
  };
}