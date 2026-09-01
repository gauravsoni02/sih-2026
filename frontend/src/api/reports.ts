import apiClient from './client';
import type { Report } from '@/types/report';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function fetchReports(params?: Record<string, string>): Promise<PaginatedResponse<Report>> {
  const res = await apiClient.get<PaginatedResponse<Report>>('/reports/', { params });
  return res.data;
}

export async function fetchReport(id: number): Promise<Report> {
  const res = await apiClient.get<Report>(`/reports/${id}/`);
  return res.data;
}

export async function generateReport(sessionId: number): Promise<Report> {
  const res = await apiClient.post<Report>(`/reports/generate/${sessionId}/`);
  return res.data;
}

export async function approveReport(id: number): Promise<Report> {
  const res = await apiClient.post<Report>(`/reports/${id}/approve/`);
  return res.data;
}

export async function reviewReport(id: number): Promise<Report> {
  const res = await apiClient.post<Report>(`/reports/${id}/review/`);
  return res.data;
}

export async function downloadReport(id: number, format: 'pdf' | 'docx'): Promise<void> {
  const res = await apiClient.get(`/reports/${id}/download/${format}/`, {
    responseType: 'blob',
  });
  const blob = new Blob([res.data]);
  const contentDisposition = res.headers['content-disposition'] as string | undefined;
  let filename = `report.${format}`;
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
    if (match) filename = match[1];
  }
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export function getReportDownloadUrl(id: number, format: 'pdf' | 'docx'): string {
  return `/api/reports/${id}/download/${format}/`;
}

export interface ReportPreviewData {
  report: {
    report_number: string;
    version: number;
    status: string;
    overall_verdict: string;
    created_at: string;
    generated_by: string;
    approved_by: string | null;
    approved_at: string | null;
    checked_by: string | null;
    checked_at: string | null;
  };
  session: {
    id: number;
    session_date: string;
    temperature_start: string | null;
    temperature_end: string | null;
    humidity: string | null;
    barometric_pressure: string | null;
    evaluation_type: string;
    verification_type: string;
    engineer: string;
  };
  instrument: {
    manufacturer: string;
    model_name: string;
    serial_number: string;
    accuracy_class: string;
    max_capacity: string;
    min_capacity: string;
    verification_scale_interval_e: string;
    actual_scale_interval_d: string;
    num_scale_intervals_n: number;
    unit: string;
  };
  laboratory: {
    name: string;
    address: string;
    accreditation_number: string;
    lab_code: string;
  };
  results: Array<{
    test_type: string;
    test_point_load: string | null;
    computed_error: string | null;
    mpe_applicable: string | null;
    expanded_uncertainty?: string | null;
    compliance_status: string;
    position: string;
    trial_number: number;
    remarks: string;
  }>;
  org_settings: {
    jurisdiction: string;
    doc_control_number: string;
    doc_issue_number: string;
    doc_rev_number: string;
    doc_issue_date: string;
    default_remarks: string[];
    logo_data_uri: string;
  };
}

export async function fetchReportPreview(id: number): Promise<ReportPreviewData> {
  const res = await apiClient.get<ReportPreviewData>(`/reports/${id}/preview/`);
  return res.data;
}

export interface SearchResult {
  id: number;
  report_number: string;
  overall_verdict: string;
  status: string;
  version: number;
  created_at: string;
  session_date: string;
  instrument_name: string;
  serial_number: string;
  accuracy_class: string;
  laboratory_name: string;
}

export interface SearchResponse {
  count: number;
  results: SearchResult[];
}

export async function searchReports(params: Record<string, string>): Promise<SearchResponse> {
  const res = await apiClient.get<SearchResponse>('/reports/search/', { params });
  return res.data;
}
