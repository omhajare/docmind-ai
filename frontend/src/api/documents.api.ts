import apiClient from "./client";

export interface Document {
  id: string;
  filename: string;
  storage_path: string;
  chunk_count: number;
  file_size_kb: number | null;
  uploaded_at: string | null;
}

export interface SuggestedQuestion {
  id: string;
  question: string;
}

export interface UploadResponse {
  document: Document;
  suggested_questions: SuggestedQuestion[];
}

export interface DocumentListResponse {
  documents: Document[];
  document_count: number;
  document_limit: number;
}

export interface DeleteResponse {
  success: boolean;
  message: string;
  warnings?: string[];
}

export const documentsApi = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.post<UploadResponse>("/api/v1/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  list: () => apiClient.get<DocumentListResponse>("/api/v1/documents"),

  delete: (documentId: string) =>
    apiClient.delete<DeleteResponse>(`/api/v1/documents/${documentId}`),

  getSuggestedQuestions: (documentId: string) =>
    apiClient.get<SuggestedQuestion[]>(
      `/api/v1/documents/${documentId}/suggested-questions`
    ),
};
