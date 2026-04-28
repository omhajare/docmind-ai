import apiClient from "./client";

export interface Session {
  id: string;
  title: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface SourceInfo {
  document_sources: Array<{
    filename: string;
    page_number: number | null;
    chunk_preview: string;
    cosine_score: number;
  }>;
  web_sources: Array<{
    url: string;
    title: string;
    snippet: string;
  }>;
}

export interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceInfo | null;
  tools_used: string[] | null;
  confidence: "high" | "medium" | "low" | null;
  created_at: string | null;
}

export const chatApi = {
  createSession: (title?: string) =>
    apiClient.post<Session>("/api/v1/chat/sessions", { title }),

  listSessions: () =>
    apiClient.get<Session[]>("/api/v1/chat/sessions"),

  renameSession: (sessionId: string, title: string) =>
    apiClient.patch<Session>(`/api/v1/chat/sessions/${sessionId}`, { title }),

  deleteSession: (sessionId: string) =>
    apiClient.delete(`/api/v1/chat/sessions/${sessionId}`),

  sendMessage: (sessionId: string, query: string) =>
    apiClient.post<Message>(`/api/v1/chat/${sessionId}/messages`, { query }),

  getMessages: (sessionId: string, limit = 10, offset = 0) =>
    apiClient.get<Message[]>(`/api/v1/chat/${sessionId}/messages`, {
      params: { limit, offset },
    }),

  deleteMessage: (messageId: string) =>
    apiClient.delete(`/api/v1/chat/messages/${messageId}`),
};
