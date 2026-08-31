import apiClient from './client';

export interface DashboardStats {
  total_instruments: number;
  sessions_this_month: number;
  reports_generated: number;
  pass_rate: number;
  prev_instruments: number;
  prev_sessions: number;
  prev_reports: number;
  prev_pass_rate: number;
}

export interface MonthlyTest {
  month: string;
  count: number;
  passed: number;
  failed: number;
  pending: number;
}

export interface PassFailSummary {
  passed: number;
  failed: number;
  pending: number;
  total: number;
}

export interface ErrorProfilePoint {
  nominalLoad: number;
  error: number;
  upperMpe: number | null;
  lowerMpe: number | null;
  status: string;
}

export interface ErrorProfileData {
  points: ErrorProfilePoint[];
  instrument: {
    name: string;
    serial_number: string;
    accuracy_class: string;
    max_capacity: string;
    unit: string;
  } | null;
  session_id: number | null;
  session_date: string | null;
}

export interface RecentSession {
  id: number;
  session_date: string;
  instrument_name: string;
  serial_number: string;
  accuracy_class: string;
  engineer: string;
  status: string;
  overall_verdict: string | null;
}

export interface DemoSample {
  id: number;
  session_date: string;
  instrument_name: string;
  serial_number: string;
  accuracy_class: string;
  status: string;
  overall_verdict: string | null;
  engineer?: string;
}

export interface DemoSamplesResponse {
  samples: DemoSample[];
  count: number;
  message?: string;
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const res = await apiClient.get<DashboardStats>('/dashboard/stats/');
  return res.data;
}

export async function fetchMonthlyTests(): Promise<MonthlyTest[]> {
  const res = await apiClient.get<MonthlyTest[]>('/dashboard/monthly-tests/');
  return res.data;
}

export async function fetchRecentSessions(): Promise<RecentSession[]> {
  const res = await apiClient.get<RecentSession[]>('/dashboard/recent-sessions/');
  return res.data;
}

export async function fetchDemoSamples(): Promise<DemoSamplesResponse> {
  const res = await apiClient.get<DemoSamplesResponse>('/dashboard/demo-samples/');
  return res.data;
}

export async function loadDemoSamples(): Promise<DemoSamplesResponse> {
  const res = await apiClient.post<DemoSamplesResponse>('/dashboard/demo-samples/load/');
  return res.data;
}

export async function clearDemoSamples(): Promise<{ message: string }> {
  const res = await apiClient.post<{ message: string }>('/dashboard/demo-samples/clear/');
  return res.data;
}

export interface AuditLogEntry {
  id: number;
  timestamp: string;
  action: string;
  model: string;
  object_id: string | null;
  object_label: string;
  user: string | null;
  changes: Record<string, unknown>;
}

export async function fetchAuditLog(limit = 20): Promise<AuditLogEntry[]> {
  const res = await apiClient.get<AuditLogEntry[]>('/dashboard/audit-log/', { params: { limit } });
  return res.data;
}

export async function fetchPassFailSummary(): Promise<PassFailSummary> {
  const res = await apiClient.get<PassFailSummary>('/dashboard/pass-fail-summary/');
  return res.data;
}

export async function fetchErrorProfile(sessionId?: number): Promise<ErrorProfileData> {
  const params = sessionId ? { session_id: sessionId } : {};
  const res = await apiClient.get<ErrorProfileData>('/dashboard/error-profile/', { params });
  return res.data;
}
