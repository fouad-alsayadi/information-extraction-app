/**
 * API client for Information Extraction App
 */

const API_BASE_URL = process.env.NODE_ENV === 'development'
  ? 'http://localhost:8000/api'
  : '/api';

// Types
export interface SchemaField {
  name: string;
  type: 'text' | 'number' | 'date' | 'currency' | 'percentage';
  required: boolean;
  description: string;
}

export interface ExtractionSchema {
  id: number;
  name: string;
  description: string;
  fields: SchemaField[];
  is_active: boolean;
  created_at: string;
}

export interface ExtractionSchemaSummary {
  id: number;
  name: string;
  description: string;
  fields_count: number;
  is_active: boolean;
  created_at: string;
}

export interface ExtractionJob {
  id: number;
  name: string;
  schema_id: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  error_message?: string;
  databricks_run_id?: number;
}

export interface JobSummary {
  id: number;
  name: string;
  schema_name: string;
  status: string;
  documents_count: number;
  created_at: string;
  completed_at?: string;
}

export interface ExtractedResult {
  document_filename: string;
  extracted_data: Record<string, any>;
  confidence_scores?: Record<string, number>;
}

export interface JobResults {
  job_id: number;
  job_name: string;
  schema_name: string;
  status: string;
  created_at: string;
  completed_at?: string;
  results: ExtractedResult[];
}

// API Client Class
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, defaultOptions);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  // Schema API
  async getSchemas(): Promise<ExtractionSchemaSummary[]> {
    return this.request('/schemas');
  }

  async getSchema(id: number): Promise<ExtractionSchema> {
    return this.request(`/schemas/${id}`);
  }

  async createSchema(schema: {
    name: string;
    description: string;
    fields: SchemaField[];
  }): Promise<{ success: boolean; message: string; schema_id: number }> {
    return this.request('/schemas', {
      method: 'POST',
      body: JSON.stringify(schema),
    });
  }

  async updateSchema(
    id: number,
    updates: Partial<{
      name: string;
      description: string;
      fields: SchemaField[];
      is_active: boolean;
    }>
  ): Promise<{ success: boolean; message: string }> {
    return this.request(`/schemas/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteSchema(id: number): Promise<{ success: boolean; message: string }> {
    return this.request(`/schemas/${id}`, {
      method: 'DELETE',
    });
  }

  // Jobs API
  async getJobs(): Promise<JobSummary[]> {
    return this.request('/jobs');
  }

  async getJob(id: number): Promise<{
    job: ExtractionJob;
    documents: any[];
    results: any[];
  }> {
    return this.request(`/jobs/${id}`);
  }

  async createJob(job: {
    name: string;
    schema_id: number;
  }): Promise<{ success: boolean; message: string; job_id: number }> {
    return this.request('/jobs', {
      method: 'POST',
      body: JSON.stringify(job),
    });
  }

  async uploadFiles(
    jobId: number,
    files: File[]
  ): Promise<{
    success: boolean;
    message: string;
    job_id: number;
    uploaded_files: string[];
    file_count: number;
  }> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await fetch(`${this.baseUrl}/jobs/${jobId}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload Error: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  async getJobDetails(id: number): Promise<{
    job: {
      id: number;
      name: string;
      status: string;
      created_at: string;
      updated_at: string;
      schema_id: number;
      databricks_run_id?: number;
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
  }> {
    return this.request(`/jobs/${id}`);
  }

  async getJobStatus(id: number): Promise<{
    job_id: number;
    status: string;
    progress_percent?: number;
    current_stage?: string;
    error_message?: string;
    databricks_run_id?: number;
  }> {
    return this.request(`/jobs/${id}/status`);
  }

  async getJobResults(id: number): Promise<JobResults> {
    return this.request(`/jobs/${id}/results`);
  }

  // Health check
  async healthCheck(): Promise<{
    status: string;
    database: string;
    service: string;
  }> {
    return this.request('/health', { method: 'GET' });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;