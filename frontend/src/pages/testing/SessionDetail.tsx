import { useState, useRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Spin, Tabs, Button, Modal, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { fetchSession, calculateSession, fetchResults, submitObservations, deleteSession } from '@/api/sessions';
import type { CalculateResponse } from '@/api/sessions';
import { generateReport } from '@/api/reports';
import PageHeader from '@/components/common/PageHeader';
import StatusTag from '@/components/common/StatusTag';
import MeasurementErrorChart from '@/components/charts/MeasurementErrorChart';
import type { ErrorChartPoint } from '@/components/charts/MeasurementErrorChart';
import { buildAllObservations } from '@/utils/demoData';
import { getRequiredTests } from '@/utils/mpe';
import WeighingPerformanceForm from '@/components/forms/WeighingPerformanceForm';
import EccentricityForm from '@/components/forms/EccentricityForm';
import RepeatabilityForm from '@/components/forms/RepeatabilityForm';
import DiscriminationForm from '@/components/forms/DiscriminationForm';
import SensitivityForm from '@/components/forms/SensitivityForm';
import TareForm from '@/components/forms/TareForm';
import TemperatureForm from '@/components/forms/TemperatureForm';
import TiltForm from '@/components/forms/TiltForm';
import PowerSupplyForm from '@/components/forms/PowerSupplyForm';
import DurabilityForm from '@/components/forms/DurabilityForm';
import SpanStabilityForm from '@/components/forms/SpanStabilityForm';
import ZeroTrackingForm from '@/components/forms/ZeroTrackingForm';
import TimeDependenceForm from '@/components/forms/TimeDependenceForm';

const EVAL_TYPE_LABELS: Record<string, string> = {
  type_evaluation: 'Type Evaluation',
  initial_verification: 'Initial Verification',
  subsequent_verification: 'Subsequent Verification',
};

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div style={{ display: 'inline-flex', marginRight: 32, marginBottom: 8 }}>
      <span style={{ color: '#999999', fontSize: 12, marginRight: 8 }}>{label}</span>
      <span style={{ fontSize: 14, color: '#1a1a1a', fontVariantNumeric: 'tabular-nums' }}>{value ?? '—'}</span>
    </div>
  );
}

export default function SessionDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const sessionId = Number(id);
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();
  const [r76Warnings, setR76Warnings] = useState<string[]>([]);
  const [demoModalOpen, setDemoModalOpen] = useState(false);
  const demoPassRef = useRef<boolean>(true);

  const { data: session, isLoading } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => fetchSession(sessionId),
    enabled: !!id,
  });

  const { data: results } = useQuery({
    queryKey: ['results', sessionId],
    queryFn: () => fetchResults(sessionId),
    enabled: !!id,
  });

  const handleCalcResponse = (data: CalculateResponse) => {
    queryClient.invalidateQueries({ queryKey: ['session', sessionId] });
    queryClient.invalidateQueries({ queryKey: ['results', sessionId] });
    setR76Warnings(data.r76_2_warnings ?? []);
    if (data.r76_2_warnings?.length) {
      messageApi.warning(`Calculation complete — ${data.r76_2_warnings.length} R 76-2 warning(s)`);
    } else {
      messageApi.success('Calculation complete');
    }
  };

  const calcMutation = useMutation({
    mutationFn: () => calculateSession(sessionId),
    onSuccess: handleCalcResponse,
    onError: () => messageApi.error('Calculation failed'),
  });

  const demoMutation = useMutation({
    mutationFn: async () => {
      const obs = buildAllObservations(session?.instrument_detail, demoPassRef.current);
      await submitObservations(sessionId, obs as Parameters<typeof submitObservations>[1], true);
      return calculateSession(sessionId);
    },
    onSuccess: (data) => {
      setDemoModalOpen(false);
      handleCalcResponse(data);
    },
    onError: () => messageApi.error('Failed to load demo data'),
  });

  const handleLoadDemo = (shouldPass: boolean) => {
    demoPassRef.current = shouldPass;
    demoMutation.mutate();
  };

  const reportMutation = useMutation({
    mutationFn: () => generateReport(sessionId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      messageApi.success('Report generated');
      navigate(`/reports/${data.id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      messageApi.error(detail || 'Report generation failed');
    },
  });

  const sessionDeleteMutation = useMutation({
    mutationFn: () => deleteSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      messageApi.success('Session deleted');
      navigate('/sessions');
    },
    onError: () => messageApi.error('Failed to delete session'),
  });

  const handleDeleteSession = () => {
    Modal.confirm({
      title: 'Delete test session?',
      content: 'This will delete this test session and all its data. This action cannot be undone.',
      okText: 'Delete',
      okType: 'danger',
      onOk: () => sessionDeleteMutation.mutateAsync(),
    });
  };

  const errorChartData = useMemo<ErrorChartPoint[]>(() => {
    if (!results) return [];
    return results
      .filter(
        (r) =>
          r.test_type === 'weighing_performance' &&
          r.computed_error &&
          r.mpe_applicable,
      )
      .map((r) => ({
        nominalLoad: parseFloat(r.remarks?.match(/load=([^ ]+)/)?.[1] || '0'),
        error: parseFloat(r.computed_error),
        upperMpe: parseFloat(r.mpe_applicable),
        lowerMpe: -parseFloat(r.mpe_applicable),
      }))
      .sort((a, b) => a.nominalLoad - b.nominalLoad);
  }, [results]);

  const testSummary = useMemo(() => {
    if (!results || results.length === 0) return null;
    const passed = results.filter((r) => r.compliance_status === 'pass').length;
    const failed = results.filter((r) => r.compliance_status === 'fail').length;
    const na = results.filter((r) => r.compliance_status === 'not_applicable').length;
    return { passed, failed, na, total: results.length };
  }, [results]);

  if (isLoading) return <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>;
  if (!session) return null;

  const inst = session.instrument_detail;
  const accuracyClass = inst?.accuracy_class || '';
  const isClassI = accuracyClass === 'I';
  const maxCapacity = parseFloat(inst?.max_capacity || '0');
  const showTilt = !isClassI;
  const showDurability = maxCapacity <= 100;
  const evalType = session.evaluation_type || 'initial_verification';
  const requiredTests = getRequiredTests(evalType);

  const allTabs = [
    {
      key: 'weighing_performance',
      label: 'Weighing Performance',
      children: <WeighingPerformanceForm sessionId={sessionId} results={results} instrumentDetail={inst} />,
    },
    {
      key: 'eccentricity',
      label: 'Eccentricity',
      children: <EccentricityForm sessionId={sessionId} results={results} instrumentDetail={inst} />,
    },
    {
      key: 'repeatability',
      label: 'Repeatability',
      children: <RepeatabilityForm sessionId={sessionId} results={results} instrumentDetail={inst} />,
    },
    {
      key: 'discrimination',
      label: 'Discrimination',
      children: <DiscriminationForm sessionId={sessionId} results={results} instrumentDetail={inst} />,
    },
    {
      key: 'sensitivity',
      label: 'Sensitivity',
      children: <SensitivityForm sessionId={sessionId} results={results} />,
    },
    {
      key: 'tare',
      label: 'Tare',
      children: <TareForm sessionId={sessionId} results={results} />,
    },
    {
      key: 'creep',
      label: 'Creep / Time Dep.',
      children: <TimeDependenceForm sessionId={sessionId} results={results} />,
    },
    {
      key: 'temperature',
      label: 'Temperature',
      children: <TemperatureForm sessionId={sessionId} results={results} />,
    },
    ...(showTilt ? [{
      key: 'tilt',
      label: 'Tilt',
      children: <TiltForm sessionId={sessionId} results={results} />,
    }] : []),
    {
      key: 'power_supply',
      label: 'Power Supply',
      children: <PowerSupplyForm sessionId={sessionId} results={results} />,
    },
    ...(showDurability ? [{
      key: 'durability',
      label: 'Durability',
      children: <DurabilityForm sessionId={sessionId} results={results} />,
    }] : []),
    {
      key: 'span_stability',
      label: 'Span Stability',
      children: <SpanStabilityForm sessionId={sessionId} results={results} />,
    },
    {
      key: 'zero_tracking',
      label: 'Zero Tracking',
      children: <ZeroTrackingForm sessionId={sessionId} results={results} />,
    },
  ];

  const tabItems = allTabs.map((tab) => ({
    ...tab,
    label: requiredTests.includes(tab.key)
      ? tab.label
      : <span style={{ color: '#999999' }}>{tab.label}</span>,
  }));

  return (
    <div>
      {contextHolder}

      <Modal
        title="Load test data"
        open={demoModalOpen}
        onCancel={() => setDemoModalOpen(false)}
        footer={null}
        width={400}
      >
        <p style={{ color: '#666666', fontSize: 13, marginBottom: 20 }}>
          Choose the type of demo data to fill all test forms and calculate results.
        </p>
        <div style={{ display: 'flex', gap: 12 }}>
          <Button
            block
            size="large"
            icon={<CheckCircleOutlined />}
            loading={demoMutation.isPending && demoPassRef.current}
            disabled={demoMutation.isPending && !demoPassRef.current}
            onClick={() => handleLoadDemo(true)}
            style={{ height: 64, borderColor: '#389e0d', color: '#389e0d' }}
          >
            Passing data
          </Button>
          <Button
            block
            size="large"
            icon={<CloseCircleOutlined />}
            loading={demoMutation.isPending && !demoPassRef.current}
            disabled={demoMutation.isPending && demoPassRef.current}
            onClick={() => handleLoadDemo(false)}
            style={{ height: 64, borderColor: '#cf1322', color: '#cf1322' }}
          >
            Failing data
          </Button>
        </div>
      </Modal>

      <PageHeader
        title={`Test Session — ${session.session_date}`}
        extra={
          <div style={{ display: 'flex', gap: 8 }}>
            <Button onClick={() => setDemoModalOpen(true)}>
              Load test data
            </Button>
            <Button
              type="primary"
              loading={calcMutation.isPending}
              onClick={() => calcMutation.mutate()}
            >
              Calculate
            </Button>
            {session.status === 'completed' && session.overall_verdict === 'pass' && (
              <Button
                loading={reportMutation.isPending}
                onClick={() => reportMutation.mutate()}
              >
                Generate Report
              </Button>
            )}
            <Button
              danger
              loading={sessionDeleteMutation.isPending}
              onClick={handleDeleteSession}
            >
              Delete
            </Button>
          </div>
        }
      />

      {session.overall_verdict && (
        <div style={{ marginBottom: 24 }}>
          <span style={{
            fontSize: 16,
            fontWeight: 600,
            color: session.overall_verdict === 'pass' ? '#389e0d' : '#cf1322',
          }}>
            {session.overall_verdict === 'pass' ? 'CONFORMS' : 'DOES NOT CONFORM'}
          </span>
        </div>
      )}

      {r76Warnings.length > 0 && (
        <div style={{
          marginBottom: 24,
          padding: '8px 12px',
          border: '1px solid #faad14',
          borderRadius: 4,
          fontSize: 13,
          color: '#1a1a1a',
          background: '#fffbe6',
        }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>R 76-2 warnings</div>
          {r76Warnings.map((w, i) => (
            <div key={i}>— {w}</div>
          ))}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: testSummary ? '1fr 240px' : '1fr', gap: 24, marginBottom: 24 }}>
        <div>
          <div style={{ padding: '12px 0', borderBottom: '1px solid #e8e8e8' }}>
            {inst && (
              <div style={{ display: 'flex', flexWrap: 'wrap' }}>
                <Field label="Instrument" value={`${inst.manufacturer} ${inst.model_name}`} />
                <Field label="Serial" value={inst.serial_number} />
                <Field label="Class" value={inst.accuracy_class} />
                <Field label="Max" value={`${inst.max_capacity} ${inst.unit}`} />
                <Field label="e" value={`${inst.verification_scale_interval_e} ${inst.unit}`} />
                <Field label="d" value={`${inst.actual_scale_interval_d} ${inst.unit}`} />
              </div>
            )}
            <div style={{ display: 'flex', flexWrap: 'wrap', marginTop: 4 }}>
              <span style={{ marginRight: 32 }}>
                <span style={{ color: '#999999', fontSize: 12, marginRight: 8 }}>Status</span>
                <StatusTag status={session.status} />
              </span>
              <Field label="Evaluation" value={EVAL_TYPE_LABELS[evalType] ?? evalType} />
              <Field label="Verification" value={session.verification_type} />
              <Field label="Temp" value={session.temperature_start ? `${session.temperature_start}°C` : null} />
              <Field label="Humidity" value={session.humidity ? `${session.humidity}%` : null} />
            </div>
          </div>

          {errorChartData.length >= 2 && (
            <div style={{ marginTop: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: '#1a1a1a', marginBottom: 8 }}>
                Measurement error profile
              </h3>
              <MeasurementErrorChart
                data={errorChartData}
                unit={inst?.unit ?? 'g'}
                height={220}
              />
            </div>
          )}
        </div>

        {testSummary && (
          <div style={{ padding: '16px', borderLeft: '1px solid #e8e8e8' }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: '#1a1a1a', marginBottom: 16 }}>Test summary</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, color: '#389e0d' }}>Passed</span>
                <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{testSummary.passed}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, color: '#cf1322' }}>Failed</span>
                <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{testSummary.failed}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, color: '#999999' }}>N/A</span>
                <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{testSummary.na}</span>
              </div>
              <div style={{ borderTop: '1px solid #e8e8e8', paddingTop: 12, display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13, color: '#666666' }}>Total</span>
                <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{testSummary.total}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <Tabs items={tabItems} size="small" />
    </div>
  );
}
