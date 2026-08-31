export type ReportStatus = 'draft' | 'approved';

export interface Report {
  id: number;
  report_number: string;
  session: number;
  generated_by: number;
  generated_by_name?: string;
  approved_by: number | null;
  approved_by_name?: string;
  overall_verdict: string;
  pdf_path: string;
  docx_path: string;
  version: number;
  status: ReportStatus;
  created_at: string;
  updated_at: string;
}
