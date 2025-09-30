/**
 * Upload page for creating jobs and uploading documents
 * Based on folio-parse-stream design patterns with corporate styling
 */

import { useState, useEffect, useCallback } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Clock, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-corporate">Upload Documents</h1>
          <p className="mt-2 text-muted-foreground">
            Create a new extraction job and upload your documents for processing
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="mb-6 border-destructive/20 bg-destructive/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 text-destructive">
                <AlertCircle className="h-5 w-5" />
                <span className="text-sm">{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Success Message */}
        {success && (
          <Card className="mb-6 border-success/20 bg-success/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 text-success">
                <CheckCircle className="h-5 w-5" />
                <div>
                  <p className="text-sm">{success}</p>
                  {jobId && (
                    <p className="text-sm text-success/80 mt-1">
                      Job ID: {jobId} - You can view progress in the Results page
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Upload Progress */}
        {uploadProgress && (
          <Card className="mb-6 border-info/20 bg-info/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3 text-info">
                <Clock className="h-5 w-5 animate-spin" />
                <span className="text-sm">{uploadProgress}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Form */}
        <Card className="bg-card border-border shadow-soft">
          <CardContent className="p-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Job Name */}
              <div>
                <label htmlFor="jobName" className="block text-sm font-medium text-foreground">
                  Job Name *
                </label>
                <input
                  type="text"
                  id="jobName"
                  value={jobName}
                  onChange={(e) => setJobName(e.target.value)}
                  className="mt-1 block w-full border border-input bg-background rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring"
                  placeholder="e.g., Invoice Processing - March 2024"
                  required
                  disabled={loading}
                />
                <p className="mt-1 text-sm text-muted-foreground">
                  Give your extraction job a descriptive name
                </p>
              </div>

              {/* Schema Selection */}
              <div>
                <label htmlFor="schema" className="block text-sm font-medium text-foreground">
                  Extraction Schema *
                </label>
                <select
                  id="schema"
                  value={selectedSchema || ''}
                  onChange={(e) => setSelectedSchema(e.target.value ? parseInt(e.target.value) : null)}
                  className="mt-1 block w-full border border-input bg-background rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring"
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
                <p className="mt-1 text-sm text-muted-foreground">
                  Choose the schema that defines what information to extract
                </p>
                {schemas.length === 0 && (
                  <p className="mt-1 text-sm text-warning">
                    No active schemas found. Please create a schema first.
                  </p>
                )}
              </div>

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Documents *
                </label>

                {/* Drop Zone */}
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed border-border rounded-md hover:border-accent transition-colors bg-background"
                >
                  <div className="space-y-1 text-center">
                    <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
                    <div className="flex text-sm text-muted-foreground">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-background rounded-md font-medium text-primary hover:text-primary-hover focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-ring"
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
                    <p className="text-xs text-muted-foreground">
                      PDF, DOCX, DOC, PNG, JPG, TXT up to 50MB each
                    </p>
                  </div>
                </div>

                {/* Selected Files */}
                {files.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-foreground mb-2">
                      Selected Files ({files.length})
                    </h4>
                    <div className="space-y-2">
                      {files.map((file, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 bg-muted/50 rounded-md border border-border"
                        >
                          <div className="flex items-center space-x-3">
                            <FileText className="h-5 w-5 text-primary" />
                            <div>
                              <p className="text-sm font-medium text-foreground">{file.name}</p>
                              <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                            </div>
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(index)}
                            className="text-muted-foreground hover:text-destructive"
                            disabled={loading}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Submit Button */}
              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={loading || schemas.length === 0}
                  className="bg-gradient-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Clock className="animate-spin h-5 w-5 mr-2" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="h-5 w-5 mr-2" />
                      Create Job & Upload Files
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}