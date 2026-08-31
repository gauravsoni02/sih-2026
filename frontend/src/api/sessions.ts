import apiClient from './client';
import type { TestSession, TestObservation, TestResult } from '@/types/session';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CalculateResponse {
  results: TestResult[];
  r76_2_warnings: string[];
}

export interface TestPlan {
  evaluation_type: string;
  verification_type: string;
  required_tests: string[];
  weighing_test_points: string[];
  repeatability: {
    loads: string[];
    min_repetitions: number;
  };
  discrimination_loads: string[];
}

export async function fetchSessions(params?: Record<string, string>): Promise<PaginatedResponse<TestSession>> {
  const res = await apiClient.get<PaginatedResponse<TestSession>>('/sessions/', { params });
  return res.data;
}

export async function fetchSession(id: number): Promise<TestSession> {
  const res = await apiClient.get<TestSession>(`/sessions/${id}/`);
  return res.data;
}

export async function createSession(data: Partial<TestSession>): Promise<TestSession> {
  const res = await apiClient.post<TestSession>('/sessions/', data);
  return res.data;
}

export async function submitObservations(sessionId: number, observations: Omit<TestObservation, 'session'>[], replace = false): Promise<TestObservation[]> {
  const url = replace
    ? `/sessions/${sessionId}/observations/?replace=true`
    : `/sessions/${sessionId}/observations/`;
  const res = await apiClient.post<TestObservation[]>(url, observations);
  return res.data;
}

export async function calculateSession(sessionId: number): Promise<CalculateResponse> {
  const res = await apiClient.post<CalculateResponse>(`/sessions/${sessionId}/calculate/`);
  return res.data;
}

export async function fetchResults(sessionId: number): Promise<TestResult[]> {
  const res = await apiClient.get<TestResult[]>(`/sessions/${sessionId}/results/`);
  return res.data;
}

export async function fetchTestPlan(sessionId: number): Promise<TestPlan> {
  const res = await apiClient.get<TestPlan>(`/sessions/${sessionId}/test-plan/`);
  return res.data;
}

export async function deleteSession(sessionId: number): Promise<void> {
  await apiClient.delete(`/sessions/${sessionId}/`);
}
