import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Button, Card, Spin, Tag } from 'antd';
import {
  SafetyCertificateOutlined,
  CloseCircleOutlined,
  CheckCircleOutlined,
  DisconnectOutlined,
} from '@ant-design/icons';
import axios, { isAxiosError } from 'axios';

interface VerifyResponse {
  valid: boolean;
  report_number: string;
  status: string;
  overall_verdict: string;
  version: number;
  issued_at: string;
  approved: boolean;
  approved_at: string | null;
  session_date: string;
  instrument: {
    manufacturer: string;
    model_name: string;
    serial_number: string;
    accuracy_class: string;
  };
  laboratory: {
    name: string;
    accreditation_number: string;
  };
}

// Public page — intentionally does not use the authenticated apiClient
// (its interceptors redirect to /login on 401).
const API_BASE = import.meta.env.VITE_API_URL || '/api';

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
      <div style={{ width: 180, color: '#888', fontSize: 13 }}>{label}</div>
      <div style={{ fontWeight: 500, fontSize: 13 }}>{value}</div>
    </div>
  );
}

export default function VerifyCertificate() {
  const { code } = useParams<{ code: string }>();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<VerifyResponse | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [unreachable, setUnreachable] = useState(false);

  const verify = useCallback(() => {
    if (!code) return;
    setLoading(true);
    setNotFound(false);
    setUnreachable(false);
    axios
      .get<VerifyResponse>(`${API_BASE}/reports/verify/${code}/`, { timeout: 60000 })
      .then((res) => setData(res.data))
      .catch((err: unknown) => {
        // Only a definitive 404 means the certificate does not exist.
        // Anything else (network error, timeout, 5xx) is a service problem
        // and must never be presented as a forgery.
        if (isAxiosError(err) && err.response?.status === 404) {
          setNotFound(true);
        } else {
          setUnreachable(true);
        }
      })
      .finally(() => setLoading(false));
  }, [code]);

  useEffect(() => {
    verify();
  }, [verify]);

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#f5f5f5',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 60,
        paddingLeft: 16,
        paddingRight: 16,
      }}
    >
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <SafetyCertificateOutlined style={{ fontSize: 40, color: '#1a3c6e' }} />
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: '8px 0 2px' }}>
          Certificate Verification
        </h1>
        <div style={{ color: '#888', fontSize: 13 }}>
          76 Labs — NAWI Test Report Generator — OIML R 76-1:2006
        </div>
      </div>

      <Card style={{ width: '100%', maxWidth: 560 }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
          </div>
        )}

        {!loading && unreachable && (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <DisconnectOutlined style={{ fontSize: 48, color: '#d97706' }} />
            <h2 style={{ fontSize: 18, marginTop: 12 }}>Verification service unavailable</h2>
            <p style={{ color: '#888', fontSize: 13 }}>
              Could not reach the verification service — the server may be
              waking up. Please try again in a minute.
            </p>
            <Button type="primary" onClick={verify}>Try again</Button>
          </div>
        )}

        {!loading && notFound && (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <CloseCircleOutlined style={{ fontSize: 48, color: '#cf1322' }} />
            <h2 style={{ fontSize: 18, marginTop: 12 }}>Certificate not found</h2>
            <p style={{ color: '#888', fontSize: 13 }}>
              No certificate exists for this verification code. The document
              presented to you may be forged or has been withdrawn.
            </p>
          </div>
        )}

        {!loading && data && (
          <div>
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <CheckCircleOutlined style={{ fontSize: 48, color: '#389e0d' }} />
              <h2 style={{ fontSize: 18, marginTop: 12, marginBottom: 4 }}>
                Genuine certificate
              </h2>
              <div>
                {data.approved ? (
                  <Tag color="green">APPROVED</Tag>
                ) : (
                  <Tag color="orange">DRAFT — pending approval</Tag>
                )}
                {data.overall_verdict === 'pass' ? (
                  <Tag color="green">CONFORMS</Tag>
                ) : (
                  <Tag color="red">DOES NOT CONFORM</Tag>
                )}
              </div>
            </div>

            <Row label="Certificate number" value={data.report_number} />
            <Row label="Version" value={String(data.version)} />
            <Row label="Test date" value={data.session_date} />
            <Row label="Issued" value={new Date(data.issued_at).toLocaleDateString()} />
            {data.approved_at && (
              <Row
                label="Approved"
                value={new Date(data.approved_at).toLocaleDateString()}
              />
            )}
            <Row
              label="Instrument"
              value={`${data.instrument.manufacturer} ${data.instrument.model_name}`}
            />
            <Row label="Serial number" value={data.instrument.serial_number} />
            <Row label="Accuracy class" value={data.instrument.accuracy_class} />
            <Row label="Laboratory" value={data.laboratory.name} />
            <Row
              label="Accreditation no."
              value={data.laboratory.accreditation_number}
            />

            <p style={{ color: '#aaa', fontSize: 11, marginTop: 16, marginBottom: 0 }}>
              This page confirms that the certificate above was issued by the
              laboratory named on it. Compare the details shown here against
              the printed document.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
