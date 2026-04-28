import apiClient from "./client";

export interface StartResearchResponse {
  job_id: string;
  status: string;
}

export interface JobStatus {
  job_id: string;
  topic: string;
  status: string;
  progress: {
    current_step: string;
    steps_done: number;
    total_steps: number;
    current_node: string;
  } | null;
  confidence: "high" | "medium" | "low" | null;
  confidence_score: number | null;
  report_path: string | null;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export const researchApi = {
  start: (topic: string) =>
    apiClient.post<StartResearchResponse>("/api/v1/research", { topic }),

  getStatus: (jobId: string) =>
    apiClient.get<JobStatus>(`/api/v1/research/${jobId}/status`),

  getHistory: () =>
    apiClient.get<JobStatus[]>("/api/v1/research/history"),

  download: (jobId: string) =>
    apiClient.get(`/api/v1/research/${jobId}/download`, { responseType: "blob" }),

  cancel: (jobId: string) =>
    apiClient.delete(`/api/v1/research/${jobId}`),
};
