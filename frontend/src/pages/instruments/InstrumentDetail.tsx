import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Spin, Button, Modal, message } from 'antd';
import { fetchInstrument, deleteInstrument } from '@/api/instruments';
import PageHeader from '@/components/common/PageHeader';
import StatusTag from '@/components/common/StatusTag';

function Field({ label, value }: { label: string; value: string | number | null | undefined }) {
  return (
    <div style={{ display: 'flex', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
      <div style={{ width: 240, color: '#666666', fontSize: 14, flexShrink: 0 }}>{label}</div>
      <div style={{ fontSize: 14, color: '#1a1a1a', fontVariantNumeric: 'tabular-nums' }}>
        {value ?? '—'}
      </div>
    </div>
  );
}

export default function InstrumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();

  const { data: instrument, isLoading } = useQuery({
    queryKey: ['instrument', id],
    queryFn: () => fetchInstrument(Number(id)),
    enabled: !!id,
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteInstrument(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instruments'] });
      messageApi.success('Instrument deleted');
      navigate('/instruments');
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      messageApi.error(detail || 'Failed to delete instrument');
    },
  });

  const handleDelete = () => {
    Modal.confirm({
      title: 'Delete instrument?',
      content: `This will delete "${instrument?.manufacturer} ${instrument?.model_name}". This action cannot be undone.`,
      okText: 'Delete',
      okType: 'danger',
      onOk: () => deleteMutation.mutateAsync(),
    });
  };

  if (isLoading) return <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>;
  if (!instrument) return null;

  return (
    <div>
      {contextHolder}
      <PageHeader
        title={`${instrument.manufacturer} ${instrument.model_name}`}
        extra={
          <div style={{ display: 'flex', gap: 8 }}>
            <Button type="primary" onClick={() => navigate('/sessions/new', { state: { instrumentId: instrument.id } })}>
              New test session
            </Button>
            <Button danger onClick={handleDelete} loading={deleteMutation.isPending}>
              Delete
            </Button>
          </div>
        }
      />

      <div style={{ maxWidth: 640 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, marginTop: 0 }}>Identification</h2>
        <Field label="Manufacturer" value={instrument.manufacturer} />
        <Field label="Model" value={instrument.model_name} />
        <Field label="Serial number" value={instrument.serial_number} />
        <Field label="Status" value={undefined} />
        <div style={{ display: 'flex', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
          <div style={{ width: 240, color: '#666666', fontSize: 14, flexShrink: 0 }}>Status</div>
          <StatusTag status={instrument.status} />
        </div>

        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, marginTop: 32 }}>Metrological characteristics</h2>
        <Field label="Accuracy class" value={instrument.accuracy_class} />
        <Field label="Max capacity (Max)" value={`${instrument.max_capacity} ${instrument.unit}`} />
        <Field label="Min capacity (Min)" value={`${instrument.min_capacity} ${instrument.unit}`} />
        <Field label="Verification scale interval (e)" value={`${instrument.verification_scale_interval_e} ${instrument.unit}`} />
        <Field label="Actual scale interval (d)" value={`${instrument.actual_scale_interval_d} ${instrument.unit}`} />
        <Field label="Number of scale intervals (n)" value={instrument.num_scale_intervals_n} />
        <Field label="Unit" value={instrument.unit} />

        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, marginTop: 32 }}>Additional</h2>
        <Field label="Tare device type" value={instrument.tare_device_type || 'None'} />
        <Field label="Max additive tare (T+)" value={instrument.max_additive_tare ? `${instrument.max_additive_tare} ${instrument.unit}` : 'N/A'} />
        <Field label="Max safe load (Lim)" value={instrument.max_safe_load ? `${instrument.max_safe_load} ${instrument.unit}` : 'N/A'} />
        <Field label="Multi-interval" value={instrument.is_multi_interval ? 'Yes' : 'No'} />
        {instrument.is_multi_interval && instrument.multi_interval_config && (
          <>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, marginTop: 32 }}>Multi-interval ranges</h2>
            {instrument.multi_interval_config.map((r, i) => (
              <Field key={i} label={`Range ${i + 1}`} value={`Max = ${r.max} ${instrument.unit}, e = ${r.e} ${instrument.unit}`} />
            ))}
          </>
        )}
      </div>
    </div>
  );
}
