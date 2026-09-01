import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Form, Select, DatePicker, Input, InputNumber, Button } from 'antd';
import dayjs from 'dayjs';
import { fetchInstruments } from '@/api/instruments';
import { fetchLaboratories } from '@/api/laboratory';
import { createSession } from '@/api/sessions';
import { useAuthStore } from '@/store/authStore';
import PageHeader from '@/components/common/PageHeader';
import { DEMO_SESSION } from '@/utils/demoData';
import { getEvaluationTypes, getVerificationTypeForEvaluation } from '@/utils/mpe';
import { loadPrefs } from '@/utils/prefs';

export default function SessionCreate() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const [form] = Form.useForm();
  const [error, setError] = useState('');

  const preselectedInstrument = (location.state as { instrumentId?: number } | null)?.instrumentId;

  const { data: instrumentsData } = useQuery({
    queryKey: ['instruments', 'all'],
    queryFn: () => fetchInstruments({ page_size: '1000' }),
  });

  const { data: laboratories } = useQuery({
    queryKey: ['laboratories'],
    queryFn: fetchLaboratories,
  });

  const mutation = useMutation({
    mutationFn: createSession,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      navigate(`/sessions/${data.id}`);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      if (msg) {
        const first = Object.entries(msg).map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`).join('; ');
        setError(first);
      } else {
        setError('Failed to create session');
      }
    },
  });

  const onFinish = (values: Record<string, unknown>) => {
    setError('');
    const evalType = (values.evaluation_type as string) || 'initial_verification';
    const verType = getVerificationTypeForEvaluation(evalType);
    mutation.mutate({
      instrument: values.instrument as number,
      laboratory: values.laboratory as number,
      engineer: user?.id,
      session_date: (values.session_date as dayjs.Dayjs).format('YYYY-MM-DD'),
      temperature_start: values.temperature_start ? String(values.temperature_start) : null,
      temperature_end: values.temperature_end ? String(values.temperature_end) : null,
      humidity: values.humidity ? String(values.humidity) : null,
      barometric_pressure: values.barometric_pressure ? String(values.barometric_pressure) : null,
      evaluation_type: evalType,
      verification_type: verType,
      customer_name: (values.customer_name as string) || '',
      customer_address: (values.customer_address as string) || '',
      customer_contact: (values.customer_contact as string) || '',
      request_date: values.request_date
        ? (values.request_date as dayjs.Dayjs).format('YYYY-MM-DD')
        : null,
    } as Partial<import('@/types/session').TestSession>);
  };

  const instrumentOptions = (instrumentsData?.results ?? []).map((inst) => ({
    value: inst.id,
    label: `${inst.manufacturer} ${inst.model_name} — ${inst.serial_number} (Class ${inst.accuracy_class})`,
  }));

  const labOptions = (laboratories ?? []).map((lab) => ({
    value: lab.id,
    label: `${lab.name} — ${lab.lab_code}`,
  }));

  const evalTypeOptions = getEvaluationTypes().map((et) => ({
    value: et.value,
    label: et.label,
  }));

  return (
    <div>
      <PageHeader
        title="New test session"
        extra={
          <Button onClick={() => {
            const first = instrumentOptions[0]?.value;
            form.setFieldsValue({
              ...DEMO_SESSION,
              ...(first ? { instrument: first } : {}),
              laboratory: labOptions[0]?.value,
            });
          }}>
            Load demo data
          </Button>
        }
      />
      <div style={{ maxWidth: 560 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          requiredMark="optional"
          initialValues={{
            instrument: preselectedInstrument,
            session_date: dayjs(),
            request_date: dayjs(),
            evaluation_type: loadPrefs().defaultEvaluationType,
          }}
        >
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, marginTop: 0 }}>Instrument</h2>
          <Form.Item label="Select instrument" name="instrument" rules={[{ required: true, message: 'Required' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={instrumentOptions}
              placeholder="Search by manufacturer, model, or serial..."
            />
          </Form.Item>
          <Form.Item label="Laboratory" name="laboratory" rules={[{ required: true, message: 'Required' }]}>
            <Select
              showSearch
              optionFilterProp="label"
              options={labOptions}
              placeholder="Select laboratory"
            />
          </Form.Item>
          <Form.Item label="Evaluation type (R 76-2)" name="evaluation_type" rules={[{ required: true, message: 'Required' }]}>
            <Select options={evalTypeOptions} />
          </Form.Item>
          <Form.Item label="Session date" name="session_date" rules={[{ required: true, message: 'Required' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <div style={{ borderTop: '1px solid #e8e8e8', marginTop: 24, marginBottom: 24 }} />
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, marginTop: 0 }}>Customer details</h2>

          <Form.Item label="Customer name" name="customer_name">
            <Input placeholder="e.g. M/s Precision Traders Pvt. Ltd." />
          </Form.Item>
          <Form.Item label="Customer address" name="customer_address">
            <Input.TextArea rows={2} placeholder="Registered address of the customer" />
          </Form.Item>
          <Form.Item label="Contact person" name="customer_contact">
            <Input placeholder="Name of the customer contact" />
          </Form.Item>
          <Form.Item label="Request date" name="request_date">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <div style={{ borderTop: '1px solid #e8e8e8', marginTop: 24, marginBottom: 24 }} />
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, marginTop: 0 }}>Environmental conditions</h2>

          <Form.Item label="Temperature start (°C)" name="temperature_start">
            <InputNumber style={{ width: '100%' }} step={0.1} />
          </Form.Item>
          <Form.Item label="Temperature end (°C)" name="temperature_end">
            <InputNumber style={{ width: '100%' }} step={0.1} />
          </Form.Item>
          <Form.Item label="Relative humidity (%)" name="humidity">
            <InputNumber style={{ width: '100%' }} min={0} max={100} step={0.1} />
          </Form.Item>
          <Form.Item label="Barometric pressure (hPa)" name="barometric_pressure">
            <InputNumber style={{ width: '100%' }} step={0.1} />
          </Form.Item>

          {error && <div style={{ color: '#cf1322', fontSize: 12, marginBottom: 16 }}>{error}</div>}

          <Form.Item style={{ marginTop: 24, textAlign: 'right' }}>
            <Button type="primary" htmlType="submit" loading={mutation.isPending}>
              Create session
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  );
}
