import apiClient from "./client";

export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

export const authApi = {
  register: (data: { email: string; password: string; full_name: string }) =>
    apiClient.post<User>("/api/v1/auth/register", data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<LoginResponse>("/api/v1/auth/login", data),

  refresh: () =>
    apiClient.post<RefreshResponse>("/api/v1/auth/refresh"),

  logout: () =>
    apiClient.post("/api/v1/auth/logout"),

  forgotPassword: (email: string) =>
    apiClient.post("/api/v1/auth/forgot-password", { email }),

  resetPassword: (data: { token: string; new_password: string }) =>
    apiClient.post("/api/v1/auth/reset-password", data),
};
