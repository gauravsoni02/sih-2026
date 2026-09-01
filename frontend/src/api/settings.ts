import apiClient from './client';

export interface OrgSettings {
  jurisdiction: string;
  report_prefix: string;
  doc_control_number: string;
  doc_issue_number: string;
  doc_rev_number: string;
  default_remarks: string[];
  logo_data_uri: string;
  updated_at?: string;
}

export async function fetchOrgSettings(): Promise<OrgSettings> {
  const res = await apiClient.get<OrgSettings>('/settings/org/');
  return res.data;
}

export async function updateOrgSettings(data: Partial<OrgSettings>): Promise<OrgSettings> {
  const res = await apiClient.put<OrgSettings>('/settings/org/', data);
  return res.data;
}
