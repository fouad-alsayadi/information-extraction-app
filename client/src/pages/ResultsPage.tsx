/**
 * Results page for viewing extraction job results
 */

import { useState, useEffect } from 'react';
import { Download, Eye, Clock, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { apiClient, JobSummary, JobResults, ExtractedResult } from '../lib/api';

export function ResultsPage() {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingResults, setLoadingResults] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load jobs on mount
  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getJobs();
      setJobs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

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
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Extraction Results</h1>
          <p className="mt-2 text-gray-600">
            View and export results from your document extraction jobs
          </p>
        </div>
        <button
          onClick={loadJobs}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <XCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Jobs List */}
        <div className="lg:col-span-1">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Extraction Jobs</h2>

          {jobs.length === 0 ? (
            <div className="text-center py-8">
              <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No jobs yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Create your first extraction job in the Upload page
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  onClick={() => loadJobResults(job.id)}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors hover:bg-gray-50 ${
                    selectedJob?.job_id === job.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(job.status)}
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {job.name}
                      </h3>
                    </div>
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(job.status)}`}
                    >
                      {job.status}
                    </span>
                  </div>

                  <div className="mt-2 text-sm text-gray-500">
                    <p>Schema: {job.schema_name}</p>
                    <p>Documents: {job.documents_count}</p>
                    <p>Created: {new Date(job.created_at).toLocaleDateString()}</p>
                    {job.completed_at && (
                      <p>Completed: {new Date(job.completed_at).toLocaleDateString()}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Results Display */}
        <div className="lg:col-span-2">
          {selectedJob ? (
            <div>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-medium text-gray-900">{selectedJob.job_name}</h2>
                  <p className="text-sm text-gray-500">Schema: {selectedJob.schema_name}</p>
                </div>

                {selectedJob.results.length > 0 && (
                  <div className="flex space-x-2">
                    <button
                      onClick={() => exportResults(selectedJob.results, 'csv')}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Export CSV
                    </button>
                    <button
                      onClick={() => exportResults(selectedJob.results, 'json')}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Export JSON
                    </button>
                  </div>
                )}
              </div>

              {loadingResults ? (
                <div className="flex justify-center items-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : selectedJob.results.length === 0 ? (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <Eye className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No results yet</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {selectedJob.status === 'processing'
                      ? 'Results will appear here when processing is complete'
                      : 'No extraction results found for this job'}
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {selectedJob.results.map((result, index) => (
                    <div key={index} className="bg-white border border-gray-200 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-medium text-gray-900">
                          {result.document_filename}
                        </h3>
                      </div>

                      {/* Extracted Data Table */}
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Field
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Value
                              </th>
                              {result.confidence_scores && (
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                  Confidence
                                </th>
                              )}
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {Object.entries(result.extracted_data).map(([field, value]) => (
                              <tr key={field}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                  {field}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </td>
                                {result.confidence_scores && (
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {result.confidence_scores[field] ? (
                                      <span
                                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                          result.confidence_scores[field] >= 0.8
                                            ? 'bg-green-100 text-green-800'
                                            : result.confidence_scores[field] >= 0.6
                                            ? 'bg-yellow-100 text-yellow-800'
                                            : 'bg-red-100 text-red-800'
                                        }`}
                                      >
                                        {Math.round(result.confidence_scores[field] * 100)}%
                                      </span>
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
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <Eye className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Select a job</h3>
              <p className="mt-1 text-sm text-gray-500">
                Choose a job from the list to view its extraction results
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}