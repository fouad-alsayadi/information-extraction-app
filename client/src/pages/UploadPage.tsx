/**
 * Upload page for creating jobs and uploading documents
 */

import { useState, useEffect, useCallback } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { apiClient, ExtractionSchemaSummary } from '../lib/api';

export function UploadPage() {
  const [schemas, setSchemas] = useState<ExtractionSchemaSummary[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<number | null>(null);
  const [jobName, setJobName] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [jobId, setJobId] = useState<number | null>(null);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);

  // Load schemas on mount
  useEffect(() => {
    loadSchemas();
  }, []);

  const loadSchemas = async () => {
    try {
      const data = await apiClient.getSchemas();
      setSchemas(data.filter(schema => schema.is_active));
    } catch (err) {
      setError('Failed to load schemas');
    }
  };

  const handleFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    setFiles(selectedFiles);
    setError(null);
  }, []);

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFiles = Array.from(event.dataTransfer.files);
    setFiles(droppedFiles);
    setError(null);
  }, []);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  }, []);

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const validateForm = () => {
    if (!jobName.trim()) {
      setError('Job name is required');
      return false;
    }
    if (!selectedSchema) {
      setError('Please select an extraction schema');
      return false;
    }
    if (files.length === 0) {
      setError('Please select at least one file to upload');
      return false;
    }

    // Validate file types and sizes
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.txt'];
    const maxFileSize = 50 * 1024 * 1024; // 50MB

    for (const file of files) {
      const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
      if (!allowedExtensions.includes(extension)) {
        setError(`File type ${extension} is not supported. Allowed: ${allowedExtensions.join(', ')}`);
        return false;
      }
      if (file.size > maxFileSize) {
        setError(`File ${file.name} is too large. Maximum size: 50MB`);
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      setUploadProgress('Creating job...');

      // Create job
      const jobResponse = await apiClient.createJob({
        name: jobName.trim(),
        schema_id: selectedSchema!,
      });

      const newJobId = jobResponse.job_id;
      setJobId(newJobId);
      setUploadProgress('Uploading files...');

      // Upload files
      const uploadResponse = await apiClient.uploadFiles(newJobId, files);

      setUploadProgress('Processing documents...');
      setSuccess(
        `Successfully created job and uploaded ${uploadResponse.file_count} files. Processing has started.`
      );

      // Reset form
      setJobName('');
      setSelectedSchema(null);
      setFiles([]);
      setUploadProgress(null);

      // You could add polling here to check job status
      setTimeout(() => {
        setUploadProgress('Processing in progress...');
      }, 1000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job and upload files');
      setUploadProgress(null);
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Upload Documents</h1>
        <p className="mt-2 text-gray-600">
          Create a new extraction job and upload your documents for processing
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex">
            <CheckCircle className="h-5 w-5 text-green-400" />
            <div className="ml-3">
              <p className="text-sm text-green-800">{success}</p>
              {jobId && (
                <p className="text-sm text-green-600 mt-1">
                  Job ID: {jobId} - You can view progress in the Results page
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Upload Progress */}
      {uploadProgress && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex items-center">
            <Clock className="h-5 w-5 text-blue-400 animate-spin" />
            <div className="ml-3">
              <p className="text-sm text-blue-800">{uploadProgress}</p>
            </div>
          </div>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6 bg-white shadow rounded-lg p-6">
        {/* Job Name */}
        <div>
          <label htmlFor="jobName" className="block text-sm font-medium text-gray-700">
            Job Name *
          </label>
          <input
            type="text"
            id="jobName"
            value={jobName}
            onChange={(e) => setJobName(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Invoice Processing - March 2024"
            required
            disabled={loading}
          />
          <p className="mt-1 text-sm text-gray-500">
            Give your extraction job a descriptive name
          </p>
        </div>

        {/* Schema Selection */}
        <div>
          <label htmlFor="schema" className="block text-sm font-medium text-gray-700">
            Extraction Schema *
          </label>
          <select
            id="schema"
            value={selectedSchema || ''}
            onChange={(e) => setSelectedSchema(e.target.value ? parseInt(e.target.value) : null)}
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            required
            disabled={loading}
          >
            <option value="">Select a schema...</option>
            {schemas.map((schema) => (
              <option key={schema.id} value={schema.id}>
                {schema.name} ({schema.fields_count} fields)
              </option>
            ))}
          </select>
          <p className="mt-1 text-sm text-gray-500">
            Choose the schema that defines what information to extract
          </p>
          {schemas.length === 0 && (
            <p className="mt-1 text-sm text-orange-600">
              No active schemas found. Please create a schema first.
            </p>
          )}
        </div>

        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Documents *
          </label>

          {/* Drop Zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors"
          >
            <div className="space-y-1 text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <div className="flex text-sm text-gray-600">
                <label
                  htmlFor="file-upload"
                  className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                >
                  <span>Upload files</span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    multiple
                    accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.txt"
                    onChange={handleFileChange}
                    disabled={loading}
                  />
                </label>
                <p className="pl-1">or drag and drop</p>
              </div>
              <p className="text-xs text-gray-500">
                PDF, DOCX, DOC, PNG, JPG, TXT up to 50MB each
              </p>
            </div>
          </div>

          {/* Selected Files */}
          {files.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Selected Files ({files.length})
              </h4>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                  >
                    <div className="flex items-center space-x-3">
                      <FileText className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file.name}</p>
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="text-gray-400 hover:text-red-600"
                      disabled={loading}
                    >
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading || schemas.length === 0}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </>
            ) : (
              <>
                <Upload className="h-5 w-5 mr-2" />
                Create Job & Upload Files
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}