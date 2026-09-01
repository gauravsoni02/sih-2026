import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Form, Input, InputNumber, Select, Switch, Button, Modal } from 'antd';
import { createInstrument } from '@/api/instruments';
import PageHeader from '@/components/common/PageHeader';
import { DEMO_INSTRUMENTS } from '@/utils/demoData';
import { loadPrefs } from '@/utils/prefs';
import type { InstrumentCreatePayload } from '@/types/instrument';

export default function InstrumentCreate() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [error, setError] = useState('');
  const [demoModalOpen, setDemoModalOpen] = useState(false);
  const isMultiInterval = Form.useWatch('is_multi_interval', form);

  const mutation = useMutation({
    mutationFn: createInstrument,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['instruments'] });
      navigate(`/instruments/${data.id}`);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      if (msg) {
        const first = Object.entries(msg).map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`).join('; ');
        setError(first);
      } else {
        setError('Failed to create instrument');
      }
    },
  });

  const onFinish = (values: InstrumentCreatePayload) => {
    setError('');
    const payload = { ...values };
    if (!payload.is_multi_interval) {
      delete payload.multi_interval_config;
    }
    mutation.mutate(payload);
  };

  return (
    <div>
      <Modal
        title="Select demo instrument"
        open={demoModalOpen}
        onCancel={() => setDemoModalOpen(false)}
        footer={null}
        width={480}
      >
        <p style={{ color: '#666666', fontSize: 13, marginBottom: 16 }}>
          Choose an instrument preset to fill the form.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {DEMO_INSTRUMENTS.map((item, i) => (
            <Button
              key={i}
              block
              style={{ textAlign: 'left', height: 'auto', padding: '10px 16px', whiteSpace: 'normal' }}
              onClick={() => {
                form.setFieldsValue({
                  ...item.value,
                  serial_number: `DEMO-${item.value.manufacturer.slice(0, 2).toUpperCase()}-${Date.now().toString(36).slice(-4).toUpperCase()}`,
                });
                setDemoModalOpen(false);
              }}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </Modal>

      <PageHeader
        title="Register instrument"
        extra={
          <Button onClick={() => setDemoModalOpen(true)}>
            Load demo data
          </Button>
        }
      />
      <div style={{ maxWidth: 560 }}>
        <Form form={form} layout="vertical" onFinish={onFinish} requiredMark="optional" initialValues={{ unit: loadPrefs().defaultUnit, accuracy_class: loadPrefs().defaultAccuracyClass, is_multi_interval: false }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, marginTop: 0 }}>Identification</h2>

          <Form.Item label="Manufacturer" name="manufacturer" rules={[{ required: true, message: 'Required' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Model name" name="model_name" rules={[{ required: true, message: 'Required' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="Serial number" name="serial_number" rules={[{ required: true, message: 'Required' }]}>
            <Input />
          </Form.Item>

          <div style={{ borderTop: '1px solid #e8e8e8', marginTop: 24, marginBottom: 24 }} />
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, marginTop: 0 }}>Metrological characteristics</h2>

          <Form.Item label="Accuracy class" name="accuracy_class" rules={[{ required: true, message: 'Required' }]}>
            <Select options={[
              { value: 'I', label: 'Class I — Special' },
              { value: 'II', label: 'Class II — High' },
              { value: 'III', label: 'Class III — Medium' },
              { value: 'IIII', label: 'Class IIII — Ordinary' },
            ]} />
          </Form.Item>
          <Form.Item label="Unit" name="unit" rules={[{ required: true, message: 'Required' }]}>
            <Select options={[
              { value: 'mg', label: 'mg' },
              { value: 'g', label: 'g' },
              { value: 'kg', label: 'kg' },
              { value: 't', label: 't (tonne)' },
              { value: 'ct', label: 'ct (carat)' },
            ]} />
          </Form.Item>
          <Form.Item label="Max capacity (Max)" name="max_capacity" rules={[{ required: true, message: 'Required' }]}>
            <InputNumber style={{ width: '100%' }} min={0} stringMode />
          </Form.Item>
          <Form.Item label="Min capacity (Min)" name="min_capacity" rules={[{ required: true, message: 'Required' }]}>
            <InputNumber style={{ width: '100%' }} min={0} stringMode />
          </Form.Item>
          <Form.Item label="Verification scale interval (e)" name="verification_scale_interval_e" rules={[{ required: true, message: 'Required' }]}>
            <InputNumber style={{ width: '100%' }} min={0} stringMode />
          </Form.Item>
          <Form.Item label="Actual scale interval (d)" name="actual_scale_interval_d" rules={[{ required: true, message: 'Required' }]}>
            <InputNumber style={{ width: '100%' }} min={0} stringMode />
          </Form.Item>
          <Form.Item label="Number of scale intervals (n)" name="num_scale_intervals_n" rules={[{ required: true, message: 'Required' }]}>
            <InputNumber style={{ width: '100%' }} min={1} />
          </Form.Item>

          <div style={{ borderTop: '1px solid #e8e8e8', marginTop: 24, marginBottom: 24 }} />
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, marginTop: 0 }}>Additional</h2>

          <Form.Item label="Tare device type" name="tare_device_type">
            <Select allowClear options={[
              { value: 'additive', label: 'Additive' },
              { value: 'subtractive', label: 'Subtractive' },
              { value: 'both', label: 'Both' },
              { value: 'none', label: 'None' },
            ]} />
          </Form.Item>
          <Form.Item label="Max additive tare (T+)" name="max_additive_tare">
            <InputNumber style={{ width: '100%' }} min={0} stringMode />
          </Form.Item>
          <Form.Item label="Max safe load (Lim)" name="max_safe_load">
            <InputNumber style={{ width: '100%' }} min={0} stringMode />
          </Form.Item>
          <Form.Item label="Multi-interval instrument" name="is_multi_interval" valuePropName="checked">
            <Switch />
          </Form.Item>

          {isMultiInterval && (
            <Form.List name="multi_interval_config" initialValue={[{ max: undefined, e: undefined }]}>
              {(fields, { add, remove }) => (
                <div>
                  <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Multi-interval ranges</h2>
                  {fields.map((field, index) => (
                    <div key={field.key} style={{ display: 'flex', gap: 12, marginBottom: 12, alignItems: 'start' }}>
                      <Form.Item
                        {...field}
                        label={`Range ${index + 1} Max`}
                        name={[field.name, 'max']}
                        rules={[{ required: true, message: 'Required' }]}
                        style={{ flex: 1 }}
                      >
                        <InputNumber style={{ width: '100%' }} min={0} />
                      </Form.Item>
                      <Form.Item
                        {...field}
                        label={`Range ${index + 1} e`}
                        name={[field.name, 'e']}
                        rules={[{ required: true, message: 'Required' }]}
                        style={{ flex: 1 }}
                      >
                        <InputNumber style={{ width: '100%' }} min={0} />
                      </Form.Item>
                      {fields.length > 1 && (
                        <Button type="link" danger onClick={() => remove(field.name)} style={{ marginTop: 30 }}>
                          Remove
                        </Button>
                      )}
                    </div>
                  ))}
                  <Button type="link" onClick={() => add()}>+ Add range</Button>
                </div>
              )}
            </Form.List>
          )}

          {error && <div style={{ color: '#cf1322', fontSize: 12, marginBottom: 16 }}>{error}</div>}

          <Form.Item style={{ marginTop: 24, textAlign: 'right' }}>
            <Button type="primary" htmlType="submit" loading={mutation.isPending}>
              Register instrument
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  );
}
