import apiClient from './client';

export interface LoginPayload {
  username: string;
  password: string;
}

export interface TokenResponse {
  access: string;
  refresh: string;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  laboratory: number | null;
  laboratory_name: string | null;
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>('/auth/login/', payload);
  return res.data;
}

export async function refreshToken(refresh: string): Promise<{ access: string }> {
  const res = await apiClient.post<{ access: string }>('/auth/refresh/', { refresh });
  return res.data;
}

export async function getMe(): Promise<UserProfile> {
  const res = await apiClient.get<UserProfile>('/auth/users/me/');
  return res.data;
}
