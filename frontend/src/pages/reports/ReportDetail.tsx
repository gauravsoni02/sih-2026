import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Spin, Button, message } from 'antd';
import { PrinterOutlined } from '@ant-design/icons';
import { fetchReport, approveReport, downloadReport, fetchReportPreview } from '@/api/reports';
import type { ReportPreviewData } from '@/api/reports';
import { useAuthStore } from '@/store/authStore';
import PageHeader from '@/components/common/PageHeader';
import StatusTag from '@/components/common/StatusTag';

const TEST_TYPE_LABELS: Record<string, string> = {
  weighing_performance: 'Weighing Performance',
  eccentricity: 'Eccentricity',
  repeatability: 'Repeatability',
  discrimination: 'Discrimination',
  sensitivity: 'Sensitivity',
  tare: 'Tare Device',
  creep: 'Creep / Time Dependence',
  temperature: 'Temperature',
  tilt: 'Tilt',
  power_supply: 'Power Supply',
  durability: 'Durability',
  span_stability: 'Span Stability',
  zero_tracking: 'Zero Tracking',
};

function ReportPreview({ data }: { data: ReportPreviewData }) {
  const { report, session, instrument, laboratory, results } = data;

  const testTypes = [...new Set(results.map((r) => r.test_type))];

  const cellStyle: React.CSSProperties = {
    padding: '6px 10px',
    border: '1px solid #d9d9d9',
    fontSize: 12,
    fontVariantNumeric: 'tabular-nums',
  };
  const headerCellStyle: React.CSSProperties = {
    ...cellStyle,
    fontWeight: 600,
    background: '#fafafa',
    textAlign: 'left',
  };

  return (
    <div
      id="report-preview"
      style={{
        maxWidth: 800,
        margin: '24px auto',
        padding: '48px 48px 32px',
        background: '#ffffff',
        border: '1px solid #e8e8e8',
        fontFamily: 'Georgia, "Times New Roman", serif',
        color: '#1a1a1a',
        lineHeight: 1.6,
      }}
    >
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <div style={{ fontSize: 14, fontWeight: 600, letterSpacing: 1, color: '#333' }}>
          Government of India
        </div>
        <div style={{ fontSize: 12, color: '#666666', marginTop: 2 }}>
          Department of Consumer Affairs
        </div>
        <div style={{
          fontSize: 16,
          fontWeight: 700,
          marginTop: 16,
          paddingBottom: 12,
          borderBottom: '2px solid #1a1a1a',
        }}>
          Legal Metrology Laboratory
        </div>
        <div style={{ fontSize: 13, marginTop: 8, color: '#666666' }}>
          NAWI Examination and Test Report &middot; OIML R 76 Compliance
        </div>
      </div>

      {/* Report info bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        padding: '8px 0',
        borderTop: '1px solid #e8e8e8',
        borderBottom: '1px solid #e8e8e8',
        fontSize: 12,
        color: '#666666',
        marginBottom: 24,
      }}>
        <span><strong>Report No:</strong> {report.report_number}</span>
        <span><strong>Version:</strong> {report.version}</span>
        <span><strong>Date:</strong> {report.created_at.slice(0, 10)}</span>
        <span><strong>Status:</strong> {report.status === 'approved' ? 'Approved' : 'Draft'}</span>
      </div>

      {/* Two-column: Instrument | Test Info */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, marginBottom: 24 }}>
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 700, borderBottom: '1px solid #e8e8e8', paddingBottom: 4, marginBottom: 8 }}>
            Instrument Identification
          </h3>
          <table style={{ fontSize: 12, width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {[
                ['Manufacturer', instrument.manufacturer],
                ['Model', instrument.model_name],
                ['Serial No.', instrument.serial_number],
                ['Accuracy Class', instrument.accuracy_class],
                ['Max Capacity', `${instrument.max_capacity} ${instrument.unit}`],
                ['Min Capacity', `${instrument.min_capacity} ${instrument.unit}`],
                ['e (verification)', `${instrument.verification_scale_interval_e} ${instrument.unit}`],
                ['d (actual)', `${instrument.actual_scale_interval_d} ${instrument.unit}`],
                ['n (intervals)', String(instrument.num_scale_intervals_n)],
              ].map(([label, value]) => (
                <tr key={label}>
                  <td style={{ padding: '3px 0', color: '#666666', width: '50%' }}>{label}</td>
                  <td style={{ padding: '3px 0', fontWeight: 500 }}>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div>
          <h3 style={{ fontSize: 13, fontWeight: 700, borderBottom: '1px solid #e8e8e8', paddingBottom: 4, marginBottom: 8 }}>
            Test Information
          </h3>
          <table style={{ fontSize: 12, width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {[
                ['Laboratory', laboratory.name],
                ['Accreditation', laboratory.accreditation_number],
                ['Test Date', session.session_date],
                ['Evaluation Type', session.evaluation_type.replace(/_/g, ' ')],
                ['Verification', session.verification_type],
                ['Testing Officer', session.engineer],
                ['Temperature', session.temperature_start ? `${session.temperature_start}°C – ${session.temperature_end ?? '—'}°C` : '—'],
                ['Humidity', session.humidity ? `${session.humidity}%` : '—'],
                ['Pressure', session.barometric_pressure ? `${session.barometric_pressure} hPa` : '—'],
              ].map(([label, value]) => (
                <tr key={label}>
                  <td style={{ padding: '3px 0', color: '#666666', width: '50%' }}>{label}</td>
                  <td style={{ padding: '3px 0', fontWeight: 500 }}>{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Results tables */}
      <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, borderBottom: '2px solid #1a1a1a', paddingBottom: 4 }}>
        Measurement Results
      </h3>

      {testTypes.map((testType) => {
        const typeResults = results.filter((r) => r.test_type === testType);
        const hasLoad = typeResults.some((r) => r.test_point_load);

        return (
          <div key={testType} style={{ marginBottom: 20 }}>
            <h4 style={{ fontSize: 12, fontWeight: 700, marginBottom: 6, color: '#333' }}>
              {TEST_TYPE_LABELS[testType] || testType}
            </h4>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={headerCellStyle}>#</th>
                  {hasLoad && <th style={{ ...headerCellStyle, textAlign: 'right' }}>Load ({instrument.unit})</th>}
                  {typeResults.some((r) => r.position) && <th style={headerCellStyle}>Position</th>}
                  <th style={{ ...headerCellStyle, textAlign: 'right' }}>Error ({instrument.unit})</th>
                  <th style={{ ...headerCellStyle, textAlign: 'right' }}>MPE ({instrument.unit})</th>
                  <th style={headerCellStyle}>Result</th>
                </tr>
              </thead>
              <tbody>
                {typeResults.map((r, i) => (
                  <tr key={i} style={{ background: i % 2 === 1 ? '#fafafa' : '#ffffff' }}>
                    <td style={cellStyle}>{i + 1}</td>
                    {hasLoad && <td style={{ ...cellStyle, textAlign: 'right' }}>{r.test_point_load ?? '—'}</td>}
                    {typeResults.some((rr) => rr.position) && <td style={cellStyle}>{r.position || '—'}</td>}
                    <td style={{ ...cellStyle, textAlign: 'right' }}>{r.computed_error ?? '—'}</td>
                    <td style={{ ...cellStyle, textAlign: 'right' }}>{r.mpe_applicable ? `±${r.mpe_applicable}` : '—'}</td>
                    <td style={{
                      ...cellStyle,
                      color: r.compliance_status === 'pass' ? '#389e0d' : r.compliance_status === 'fail' ? '#cf1322' : '#999999',
                      fontWeight: 600,
                    }}>
                      {r.compliance_status === 'pass' ? 'Pass' : r.compliance_status === 'fail' ? 'Fail' : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}

      {/* Conclusion */}
      <div style={{
        marginTop: 32,
        padding: '16px',
        border: '2px solid ' + (report.overall_verdict === 'pass' ? '#389e0d' : '#cf1322'),
        borderRadius: 4,
      }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>Conclusion</h3>
        <p style={{ fontSize: 13, margin: 0 }}>
          Based on the test results obtained in accordance with OIML Recommendation R 76-1:2006,
          the above instrument{' '}
          <strong style={{ color: report.overall_verdict === 'pass' ? '#389e0d' : '#cf1322' }}>
            {report.overall_verdict === 'pass' ? 'CONFORMS' : 'DOES NOT CONFORM'}
          </strong>{' '}
          to the requirements for accuracy class {instrument.accuracy_class} non-automatic weighing instruments.
        </p>
      </div>

      {/* Authorization */}
      <div style={{ marginTop: 48, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 48 }}>
        <div>
          <div style={{ borderTop: '1px solid #1a1a1a', paddingTop: 8, fontSize: 12 }}>
            <div style={{ fontWeight: 600 }}>Tested by</div>
            <div>{session.engineer}</div>
            <div style={{ color: '#999999', marginTop: 4 }}>Date: {session.session_date}</div>
          </div>
        </div>
        <div>
          <div style={{ borderTop: '1px solid #1a1a1a', paddingTop: 8, fontSize: 12 }}>
            <div style={{ fontWeight: 600 }}>Approved by</div>
            <div>{report.approved_by || '—'}</div>
            <div style={{ color: '#999999', marginTop: 4 }}>Date: {report.status === 'approved' ? report.created_at.slice(0, 10) : '—'}</div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{
        marginTop: 48,
        paddingTop: 12,
        borderTop: '1px solid #e8e8e8',
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: 10,
        color: '#999999',
      }}>
        <span>Document ID: {report.report_number} v{report.version}</span>
        <span>Generated by NAWI Test Report System</span>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div style={{ display: 'flex', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
      <div style={{ width: 200, color: '#666666', fontSize: 14, flexShrink: 0 }}>{label}</div>
      <div style={{ fontSize: 14, color: '#1a1a1a' }}>{value ?? '—'}</div>
    </div>
  );
}

export default function ReportDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const [messageApi, contextHolder] = message.useMessage();
  const [downloading, setDownloading] = useState<'pdf' | 'docx' | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  const { data: report, isLoading } = useQuery({
    queryKey: ['report', id],
    queryFn: () => fetchReport(Number(id)),
    enabled: !!id,
  });

  const { data: preview } = useQuery({
    queryKey: ['report-preview', id],
    queryFn: () => fetchReportPreview(Number(id)),
    enabled: !!id && showPreview,
  });

  const approveMutation = useMutation({
    mutationFn: () => approveReport(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', id] });
      queryClient.invalidateQueries({ queryKey: ['report-preview', id] });
      messageApi.success('Report approved');
    },
    onError: () => messageApi.error('Approval failed'),
  });

  const handleDownload = async (format: 'pdf' | 'docx') => {
    setDownloading(format);
    try {
      await downloadReport(Number(id), format);
    } catch {
      messageApi.error(`Failed to download ${format.toUpperCase()}`);
    } finally {
      setDownloading(null);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) return <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>;
  if (!report) return null;

  const canApprove = (user?.role === 'admin' || user?.role === 'lab_manager') && report.status === 'draft';

  return (
    <div>
      {contextHolder}
      <style>{`
        @media print {
          body * { visibility: hidden; }
          #report-preview, #report-preview * { visibility: visible; }
          #report-preview {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            border: none !important;
            margin: 0 !important;
            padding: 24px !important;
            box-shadow: none !important;
          }
        }
      `}</style>
      <PageHeader
        title={report.report_number}
        extra={
          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              onClick={() => setShowPreview(!showPreview)}
            >
              {showPreview ? 'Hide Preview' : 'Preview Report'}
            </Button>
            {showPreview && preview && (
              <Button icon={<PrinterOutlined />} onClick={handlePrint}>
                Print
              </Button>
            )}
            {report.pdf_path && (
              <Button
                loading={downloading === 'pdf'}
                onClick={() => handleDownload('pdf')}
              >
                Download PDF
              </Button>
            )}
            {report.docx_path && (
              <Button
                loading={downloading === 'docx'}
                onClick={() => handleDownload('docx')}
              >
                Download DOCX
              </Button>
            )}
            {canApprove && (
              <Button type="primary" onClick={() => approveMutation.mutate()} loading={approveMutation.isPending}>
                Approve
              </Button>
            )}
          </div>
        }
      />

      {!showPreview && (
        <div style={{ maxWidth: 560 }}>
          <Field label="Report number" value={report.report_number} />
          <Field label="Version" value={report.version} />
          <div style={{ display: 'flex', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
            <div style={{ width: 200, color: '#666666', fontSize: 14, flexShrink: 0 }}>Status</div>
            <StatusTag status={report.status} />
          </div>
          <div style={{ display: 'flex', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
            <div style={{ width: 200, color: '#666666', fontSize: 14, flexShrink: 0 }}>Verdict</div>
            <StatusTag status={report.overall_verdict} />
          </div>
          <Field label="Generated by" value={report.generated_by_name} />
          <Field label="Approved by" value={report.approved_by_name || '—'} />
          <Field label="Created" value={report.created_at?.slice(0, 10)} />
        </div>
      )}

      {showPreview && preview && <ReportPreview data={preview} />}
      {showPreview && !preview && (
        <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>
      )}
    </div>
  );
}
