import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Spin, Button, message } from 'antd';
import { PrinterOutlined } from '@ant-design/icons';
import { fetchReport, approveReport, downloadReport, fetchReportPreview } from '@/api/reports';
import type { ReportPreviewData } from '@/api/reports';
import { useAuthStore } from '@/store/authStore';
import PageHeader from '@/components/common/PageHeader';


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

/* ---------- NABL-style certificate preview ---------- */

function ReportPreview({ data }: { data: ReportPreviewData }) {
  const { report, session, instrument, laboratory, results } = data;

  const testTypes = [...new Set(results.map((r) => r.test_type))];

  /* --- shared table styles --- */
  const borderColor = '#999';
  const tableBorder = `1px solid ${borderColor}`;

  const dataTableStyle: React.CSSProperties = {
    width: '100%',
    borderCollapse: 'collapse',
    margin: '4px 0 12px 0',
    fontSize: 9,
    fontFamily: '"Times New Roman", Times, serif',
  };
  const thStyle: React.CSSProperties = {
    background: '#E8E8E8',
    border: tableBorder,
    padding: '4px 6px',
    textAlign: 'left',
    fontWeight: 700,
    fontSize: 9,
  };
  const tdStyle: React.CSSProperties = {
    border: tableBorder,
    padding: '3px 6px',
    fontSize: 9,
    verticalAlign: 'top',
  };
  const numTdStyle: React.CSSProperties = {
    ...tdStyle,
    textAlign: 'right',
    fontFamily: '"Courier New", Courier, monospace',
    fontVariantNumeric: 'tabular-nums',
  };
  const kvLabelStyle: React.CSSProperties = {
    ...tdStyle,
    background: '#F0F0F0',
    fontWeight: 600,
    width: '26%',
    color: '#333',
    fontSize: 9.5,
  };
  const kvValueStyle: React.CSSProperties = {
    ...tdStyle,
    width: '24%',
    fontFamily: '"Courier New", Courier, monospace',
    fontSize: 9.5,
  };

  const passStyle: React.CSSProperties = { color: '#006400', fontWeight: 700 };
  const failStyle: React.CSSProperties = { color: '#8B0000', fontWeight: 700 };
  const naStyle: React.CSSProperties = { color: '#888', fontStyle: 'italic' };

  /* --- build compliance summary from results --- */
  const complianceSummary = testTypes.map((tt) => {
    const typeResults = results.filter((r) => r.test_type === tt);
    const hasFail = typeResults.some((r) => r.compliance_status === 'fail');
    const allNA = typeResults.every(
      (r) => r.compliance_status !== 'pass' && r.compliance_status !== 'fail',
    );
    let status: 'pass' | 'fail' | 'na' = 'pass';
    if (hasFail) status = 'fail';
    else if (allNA) status = 'na';
    return { test_type: tt, status };
  });

  return (
    <div
      id="report-preview"
      style={{
        maxWidth: 800,
        margin: '24px auto',
        padding: '40px 44px 28px',
        background: '#ffffff',
        border: '1px solid #ccc',
        fontFamily: '"Times New Roman", Times, serif',
        color: '#1a1a1a',
        lineHeight: 1.35,
        fontSize: 10,
      }}
    >
      {/* ========== PAGE 1: GOVERNMENT HEADER ========== */}
      <div style={{ textAlign: 'center', marginBottom: 8 }}>
        <div
          style={{
            fontSize: 14,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: 1,
          }}
        >
          Government of India
        </div>
        <div
          style={{
            fontSize: 11,
            fontWeight: 700,
            textTransform: 'uppercase',
            marginTop: 2,
          }}
        >
          Ministry of Consumer Affairs, Food &amp; Public Distribution
        </div>
        <div
          style={{
            fontSize: 10,
            fontWeight: 700,
            textTransform: 'uppercase',
            marginTop: 1,
          }}
        >
          Department of Consumer Affairs
        </div>
        <div
          style={{
            fontSize: 15,
            fontWeight: 700,
            textTransform: 'uppercase',
            marginTop: 12,
            letterSpacing: 0.5,
          }}
        >
          Legal Metrology Laboratory
        </div>
        <div style={{ fontSize: 10, color: '#333', marginTop: 3 }}>
          {laboratory.name}
          {laboratory.address ? `, ${laboratory.address}` : ''}
        </div>
        <hr
          style={{
            border: 'none',
            borderTop: '2.5px solid #1a1a1a',
            margin: '8px 0',
          }}
        />
        <div
          style={{
            fontSize: 12,
            fontWeight: 700,
            textTransform: 'uppercase',
            marginTop: 4,
            letterSpacing: 0.5,
          }}
        >
          Test Report for Non-Automatic Weighing Instrument
        </div>
        <div style={{ fontSize: 10, color: '#333', marginTop: 4 }}>
          As per OIML R 76-1:2006 &middot;{' '}
          {session.evaluation_type
            ? session.evaluation_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
            : 'Type Evaluation'}
        </div>
      </div>

      {/* Certificate info row */}
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: 10,
          margin: '10px 0 8px 0',
        }}
      >
        <tbody>
          <tr>
            <td style={{ padding: '2px 4px', fontWeight: 600, color: '#333', whiteSpace: 'nowrap' }}>
              Certificate No:
            </td>
            <td style={{ padding: '2px 4px', fontWeight: 700 }}>{report.report_number}</td>
            <td
              style={{
                padding: '2px 4px',
                fontWeight: 600,
                color: '#333',
                textAlign: 'right',
                whiteSpace: 'nowrap',
              }}
            >
              ULR No:
            </td>
            <td style={{ padding: '2px 4px', fontWeight: 700, textAlign: 'right' }}>
              {laboratory.accreditation_number}
            </td>
          </tr>
          <tr>
            <td style={{ padding: '2px 4px', fontWeight: 600, color: '#333', whiteSpace: 'nowrap' }}>
              Certificate Issue Date:
            </td>
            <td style={{ padding: '2px 4px', fontWeight: 700 }}>{session.session_date}</td>
            <td
              style={{
                padding: '2px 4px',
                fontWeight: 600,
                color: '#333',
                textAlign: 'right',
                whiteSpace: 'nowrap',
              }}
            >
              Verification Type:
            </td>
            <td style={{ padding: '2px 4px', fontWeight: 700, textAlign: 'right' }}>
              {session.verification_type || '—'}
            </td>
          </tr>
          <tr>
            <td style={{ padding: '2px 4px', fontWeight: 600, color: '#333', whiteSpace: 'nowrap' }}>
              Report Version:
            </td>
            <td style={{ padding: '2px 4px', fontWeight: 700 }}>{report.version}</td>
            <td />
            <td />
          </tr>
        </tbody>
      </table>

      {/* ========== INSTRUMENT DETAILS ========== */}
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          textTransform: 'uppercase',
          background: '#E8E8E8',
          border: tableBorder,
          padding: '4px 8px',
          margin: '14px 0 6px 0',
          letterSpacing: 0.3,
        }}
      >
        1. Instrument Under Test
      </div>

      <table style={{ ...dataTableStyle, fontSize: 10 }}>
        <tbody>
          <tr>
            <td style={kvLabelStyle}>Instrument Detail</td>
            <td style={{ ...kvValueStyle, width: undefined }} colSpan={3}>
              Non-Automatic Weighing Instrument
            </td>
          </tr>
          <tr>
            <td style={kvLabelStyle}>Make / Manufacturer</td>
            <td style={kvValueStyle}>{instrument.manufacturer}</td>
            <td style={kvLabelStyle}>Model</td>
            <td style={kvValueStyle}>{instrument.model_name}</td>
          </tr>
          <tr>
            <td style={kvLabelStyle}>Serial Number</td>
            <td style={kvValueStyle}>{instrument.serial_number}</td>
            <td style={kvLabelStyle}>Accuracy Class</td>
            <td style={kvValueStyle}>{instrument.accuracy_class}</td>
          </tr>
          <tr>
            <td style={kvLabelStyle}>Max Capacity (Max)</td>
            <td style={kvValueStyle}>
              {instrument.max_capacity} {instrument.unit}
            </td>
            <td style={kvLabelStyle}>Min Capacity (Min)</td>
            <td style={kvValueStyle}>
              {instrument.min_capacity} {instrument.unit}
            </td>
          </tr>
          <tr>
            <td style={kvLabelStyle}>Verification Scale Interval (e)</td>
            <td style={kvValueStyle}>
              {instrument.verification_scale_interval_e} {instrument.unit}
            </td>
            <td style={kvLabelStyle}>Actual Scale Interval (d)</td>
            <td style={kvValueStyle}>
              {instrument.actual_scale_interval_d} {instrument.unit}
            </td>
          </tr>
          <tr>
            <td style={kvLabelStyle}>Number of Scale Intervals (n)</td>
            <td style={kvValueStyle}>{instrument.num_scale_intervals_n}</td>
            <td style={kvLabelStyle}>Tare Device</td>
            <td style={kvValueStyle}>{'—'}</td>
          </tr>
        </tbody>
      </table>

      {/* ========== ENVIRONMENTAL CONDITIONS ========== */}
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          textTransform: 'uppercase',
          background: '#E8E8E8',
          border: tableBorder,
          padding: '4px 8px',
          margin: '14px 0 6px 0',
          letterSpacing: 0.3,
        }}
      >
        2. Environmental Conditions During Test
      </div>

      <table style={{ ...dataTableStyle, fontSize: 10 }}>
        <tbody>
          <tr>
            <td style={kvLabelStyle}>Average Temperature</td>
            <td style={kvValueStyle}>
              {session.temperature_start
                ? `${session.temperature_start}${session.temperature_end ? ' – ' + session.temperature_end : ''} °C`
                : '—'}
            </td>
            <td style={kvLabelStyle}>Average Relative Humidity</td>
            <td style={kvValueStyle}>
              {session.humidity ? `${session.humidity} %` : '—'}
            </td>
          </tr>
          <tr>
            <td style={kvLabelStyle}>Average Barometric Pressure</td>
            <td style={kvValueStyle}>
              {session.barometric_pressure
                ? `${session.barometric_pressure} hPa`
                : '—'}
            </td>
            <td style={kvLabelStyle} />
            <td style={kvValueStyle} />
          </tr>
        </tbody>
      </table>

      {/* ========== IMPORTANT REMARKS ========== */}
      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          textTransform: 'uppercase',
          background: '#E8E8E8',
          border: tableBorder,
          padding: '4px 8px',
          margin: '14px 0 6px 0',
          letterSpacing: 0.3,
        }}
      >
        3. Important Remarks
      </div>

      <div
        style={{
          border: tableBorder,
          padding: '8px 12px',
          margin: '4px 0 12px 0',
          fontSize: 9,
          lineHeight: 1.5,
        }}
      >
        <ol style={{ margin: 0, paddingLeft: 18 }}>
          <li style={{ marginBottom: 3 }}>
            This certificate is issued on the basis of test results obtained during examination and
            testing of the instrument described above, as per the procedures laid down in OIML R
            76-1:2006.
          </li>
          <li style={{ marginBottom: 3 }}>
            The test results reported herein relate only to the specific instrument tested under the
            stated environmental conditions and the test loads used during the examination.
          </li>
          <li style={{ marginBottom: 3 }}>
            The standard weights/masses used for testing are traceable to the National Standards
            maintained at the National Physical Laboratory (NPL), New Delhi, India.
          </li>
          <li style={{ marginBottom: 3 }}>
            The reported measurement uncertainty, where applicable, has been estimated in accordance
            with the guidelines given in the document EA-4/02 &ldquo;Expression of the Uncertainty
            of Measurement in Calibration&rdquo;.
          </li>
          <li style={{ marginBottom: 3 }}>
            This certificate shall not be reproduced, except in full, without the prior written
            approval of the issuing laboratory.
          </li>
          <li style={{ marginBottom: 3 }}>
            The calibration/test results are valid at the time of testing. The issuing laboratory is
            not responsible for any subsequent changes in the performance of the instrument.
          </li>
          <li style={{ marginBottom: 3 }}>
            This test report is generated electronically by the NAWI Test Report Generator and is
            valid without signature if issued through the approved digital workflow.
          </li>
        </ol>
      </div>

      {/* ========== PAGE 2+: TEST RESULTS ========== */}
      <div style={{ pageBreakBefore: 'always' }} />

      {/* Repeat header on results pages */}
      <div style={{ textAlign: 'center', marginBottom: 8, marginTop: 24 }}>
        <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase' }}>
          Legal Metrology Laboratory &mdash; {laboratory.name}
        </div>
        <div style={{ fontSize: 9, color: '#333' }}>
          Certificate No: {report.report_number} &middot; Date: {session.session_date}
        </div>
      </div>

      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          textTransform: 'uppercase',
          background: '#E8E8E8',
          border: tableBorder,
          padding: '4px 8px',
          margin: '14px 0 6px 0',
          letterSpacing: 0.3,
        }}
      >
        4. Test Results
      </div>

      {testTypes.map((testType, sectionIdx) => {
        const typeResults = results.filter((r) => r.test_type === testType);
        const hasLoad = typeResults.some((r) => r.test_point_load != null);
        const hasPosition = typeResults.some((r) => r.position);
        const hasTrial = typeResults.some((r) => r.trial_number != null);
        const hasUncertainty = typeResults.some((r) => r.expanded_uncertainty != null);

        return (
          <div key={testType} style={{ marginBottom: 16, pageBreakInside: 'avoid' }}>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                margin: '10px 0 4px 0',
                paddingBottom: 2,
                borderBottom: `0.5px solid ${borderColor}`,
              }}
            >
              4.{sectionIdx + 1} {TEST_TYPE_LABELS[testType] || testType}
            </div>

            {typeResults.length > 0 ? (
              <table style={dataTableStyle}>
                <thead>
                  <tr>
                    <th style={{ ...thStyle, width: 36, textAlign: 'center' }}>Sr No.</th>
                    {hasLoad && (
                      <th style={{ ...thStyle, textAlign: 'right' }}>
                        Test Point ({instrument.unit})
                      </th>
                    )}
                    {hasPosition && <th style={thStyle}>Position</th>}
                    {hasTrial && (
                      <th style={{ ...thStyle, textAlign: 'center' }}>Trial</th>
                    )}
                    <th style={{ ...thStyle, textAlign: 'right' }}>
                      Error ({instrument.unit})
                    </th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>
                      MPE (&plusmn;{instrument.unit})
                    </th>
                    {hasUncertainty && (
                      <th style={{ ...thStyle, textAlign: 'right' }}>
                        U (&plusmn;{instrument.unit}) k=2
                      </th>
                    )}
                    <th style={{ ...thStyle, textAlign: 'center', width: 64 }}>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {typeResults.map((r, i) => {
                    const rowBg = i % 2 === 1 ? '#FAFAFA' : '#ffffff';
                    const statusStyle =
                      r.compliance_status === 'pass'
                        ? passStyle
                        : r.compliance_status === 'fail'
                          ? failStyle
                          : naStyle;
                    const statusLabel =
                      r.compliance_status === 'pass'
                        ? 'Pass'
                        : r.compliance_status === 'fail'
                          ? 'Fail'
                          : 'N/A';

                    return (
                      <tr key={i} style={{ background: rowBg }}>
                        <td style={{ ...tdStyle, textAlign: 'center' }}>{i + 1}</td>
                        {hasLoad && (
                          <td style={numTdStyle}>{r.test_point_load ?? '—'}</td>
                        )}
                        {hasPosition && (
                          <td style={tdStyle}>{r.position || '—'}</td>
                        )}
                        {hasTrial && (
                          <td style={{ ...tdStyle, textAlign: 'center' }}>
                            {r.trial_number ?? '—'}
                          </td>
                        )}
                        <td style={numTdStyle}>{r.computed_error ?? '—'}</td>
                        <td style={numTdStyle}>
                          {r.mpe_applicable != null ? `±${r.mpe_applicable}` : '—'}
                        </td>
                        {hasUncertainty && (
                          <td style={numTdStyle}>
                            {r.expanded_uncertainty != null ? `±${r.expanded_uncertainty}` : '—'}
                          </td>
                        )}
                        <td style={{ ...tdStyle, textAlign: 'center', ...statusStyle }}>
                          {statusLabel}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <p style={{ ...naStyle, padding: '6px 0', fontSize: 9 }}>
                Not Applicable &mdash; Test was not performed for this instrument.
              </p>
            )}
          </div>
        );
      })}

      {/* ========== LAST PAGE: OVERALL TEST SUMMARY ========== */}
      <div style={{ pageBreakBefore: 'always' }} />

      {/* Repeat header on summary page */}
      <div style={{ textAlign: 'center', marginBottom: 8, marginTop: 24 }}>
        <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase' }}>
          Legal Metrology Laboratory &mdash; {laboratory.name}
        </div>
        <div style={{ fontSize: 9, color: '#333' }}>
          Certificate No: {report.report_number} &middot; Date: {session.session_date}
        </div>
      </div>

      <div
        style={{
          fontSize: 11,
          fontWeight: 700,
          textTransform: 'uppercase',
          background: '#E8E8E8',
          border: tableBorder,
          padding: '4px 8px',
          margin: '14px 0 6px 0',
          letterSpacing: 0.3,
        }}
      >
        5. Overall Test Summary
      </div>

      <table style={dataTableStyle}>
        <thead>
          <tr>
            <th style={{ ...thStyle, width: 48, textAlign: 'center' }}>Sr No.</th>
            <th style={thStyle}>Test Performed</th>
            <th style={{ ...thStyle, width: 100, textAlign: 'center' }}>Result</th>
          </tr>
        </thead>
        <tbody>
          {complianceSummary.map((item, i) => {
            const statusStyle =
              item.status === 'pass' ? passStyle : item.status === 'fail' ? failStyle : naStyle;
            const statusLabel =
              item.status === 'pass'
                ? 'Pass'
                : item.status === 'fail'
                  ? 'Fail'
                  : 'Not Applicable';

            return (
              <tr key={item.test_type} style={{ background: i % 2 === 1 ? '#FAFAFA' : '#fff' }}>
                <td style={{ ...tdStyle, textAlign: 'center' }}>{i + 1}</td>
                <td style={tdStyle}>{TEST_TYPE_LABELS[item.test_type] || item.test_type}</td>
                <td style={{ ...tdStyle, textAlign: 'center', ...statusStyle }}>{statusLabel}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Overall verdict box */}
      <div
        style={{
          textAlign: 'center',
          padding: '10px 16px',
          margin: '14px 0',
          border: `2.5px solid ${report.overall_verdict === 'pass' ? '#006400' : '#8B0000'}`,
          fontSize: 14,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: 0.5,
          color: report.overall_verdict === 'pass' ? '#006400' : '#8B0000',
          background: report.overall_verdict === 'pass' ? '#f0fff0' : '#fff5f5',
        }}
      >
        {report.overall_verdict === 'pass'
          ? 'CONFORMS TO OIML R 76-1:2006'
          : 'DOES NOT CONFORM TO OIML R 76-1:2006'}
      </div>

      {/* Conclusion narrative */}
      <div
        style={{
          fontSize: 10,
          lineHeight: 1.5,
          margin: '8px 0',
          textAlign: 'justify',
        }}
      >
        Based on the test results obtained in accordance with OIML Recommendation R 76-1:2006
        (Non-automatic weighing instruments &mdash; Part 1: Metrological and technical requirements
        &mdash; Tests), the above-described instrument bearing Serial Number{' '}
        <strong>{instrument.serial_number}</strong>, manufactured by{' '}
        <strong>{instrument.manufacturer}</strong>, Model <strong>{instrument.model_name}</strong>,
        with maximum capacity{' '}
        <strong>
          {instrument.max_capacity} {instrument.unit}
        </strong>{' '}
        and accuracy class <strong>{instrument.accuracy_class}</strong>,{' '}
        <strong
          style={report.overall_verdict === 'pass' ? passStyle : failStyle}
        >
          {report.overall_verdict === 'pass' ? 'CONFORMS' : 'DOES NOT CONFORM'}
        </strong>{' '}
        to the requirements specified for its declared accuracy class as per the said recommendation.
      </div>

      {/* ========== SIGNATORIES ========== */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 48,
          gap: 16,
        }}
      >
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ borderTop: '1px solid #1a1a1a', marginTop: 48, paddingTop: 6 }}>
            <div style={{ fontWeight: 700, fontSize: 10 }}>Tested By</div>
            <div style={{ fontSize: 9, marginTop: 2 }}>{session.engineer}</div>
            <div style={{ fontSize: 8, color: '#666', marginTop: 1 }}>Testing Officer</div>
            <div style={{ fontSize: 8, color: '#666', marginTop: 2 }}>
              Date: {session.session_date}
            </div>
          </div>
        </div>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ borderTop: '1px solid #1a1a1a', marginTop: 48, paddingTop: 6 }}>
            <div style={{ fontWeight: 700, fontSize: 10 }}>Checked By</div>
            <div style={{ fontSize: 9, marginTop: 2 }}>________________</div>
            <div style={{ fontSize: 8, color: '#666', marginTop: 1 }}>Senior Technical Officer</div>
            <div style={{ fontSize: 8, color: '#666', marginTop: 2 }}>Date: ________________</div>
          </div>
        </div>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ borderTop: '1px solid #1a1a1a', marginTop: 48, paddingTop: 6 }}>
            <div style={{ fontWeight: 700, fontSize: 10 }}>Approved By</div>
            <div style={{ fontSize: 9, marginTop: 2 }}>
              {report.approved_by || '________________'}
            </div>
            <div style={{ fontSize: 8, color: '#666', marginTop: 1 }}>Laboratory In-Charge</div>
            <div style={{ fontSize: 8, color: '#666', marginTop: 2 }}>
              Date:{' '}
              {report.status === 'approved' ? report.created_at.slice(0, 10) : '________________'}
            </div>
          </div>
        </div>
      </div>

      {/* Document control footer */}
      <div
        style={{
          marginTop: 24,
          borderTop: '1.5px solid #1a1a1a',
          paddingTop: 6,
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 8,
          color: '#666',
        }}
      >
        <span>Doc No: LM-FMT-NAWI-01</span>
        <span>Issue No: 01</span>
        <span>Issue Date: 01-01-2024</span>
        <span>Amendment No: 00</span>
        <span>NAWI Test Report Generator</span>
      </div>
    </div>
  );
}

export default function ReportDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const [messageApi, contextHolder] = message.useMessage();
  const [downloading, setDownloading] = useState<'pdf' | 'docx' | null>(null);
  const { data: report, isLoading } = useQuery({
    queryKey: ['report', id],
    queryFn: () => fetchReport(Number(id)),
    enabled: !!id,
  });

  const { data: preview, isLoading: previewLoading } = useQuery({
    queryKey: ['report-preview', id],
    queryFn: () => fetchReportPreview(Number(id)),
    enabled: !!id,
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
            width: 210mm;
            border: none !important;
            margin: 0 !important;
            padding: 18mm 15mm !important;
            box-shadow: none !important;
            font-size: 10pt !important;
          }
          @page {
            size: A4;
            margin: 0;
          }
        }
      `}</style>
      <PageHeader
        title={report.report_number}
        extra={
          <div style={{ display: 'flex', gap: 8 }}>
            {preview && (
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

      {preview && <ReportPreview data={preview} />}
      {previewLoading && (
        <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>
      )}
    </div>
  );
}
