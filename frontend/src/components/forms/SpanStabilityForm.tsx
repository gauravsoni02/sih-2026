import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, InputNumber, Button } from 'antd';
import { submitObservations } from '@/api/sessions';
import StatusTag from '@/components/common/StatusTag';
import type { TestResult } from '@/types/session';

interface Row {
  key: number;
  test_point_load: string;
  indicated_value: string;
  correction: string;
}

interface Props {
  sessionId: number;
  results?: TestResult[];
}

export default function SpanStabilityForm({ sessionId, results }: Props) {
  const queryClient = useQueryClient();
  const [rows, setRows] = useState<Row[]>([
    { key: 1, test_point_load: '', indicated_value: '', correction: '0' },
  ]);

  const spanResults = (results ?? []).filter((r) => r.test_type === 'span_stability');

  const mutation = useMutation({
    mutationFn: (obs: Parameters<typeof submitObservations>[1]) => submitObservations(sessionId, obs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['results', sessionId] }),
  });

  const updateRow = (key: number, field: keyof Row, value: string) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, [field]: value } : r)));
  };

  const addRow = () => setRows((prev) => [...prev, { key: Date.now(), test_point_load: '', indicated_value: '', correction: '0' }]);

  const saveObservations = () => {
    const obs = rows.filter((r) => r.test_point_load && r.indicated_value).map((r, i) => ({
      test_type: 'span_stability' as const, test_point_load: r.test_point_load, indicated_value: r.indicated_value, correction: r.correction || '0', trial_number: i + 1,
    }));
    if (obs.length > 0) mutation.mutate(obs);
  };

  return (
    <div>
      <p style={{ fontSize: 12, color: '#999999', marginBottom: 16 }}>
        For electronic instruments. Test load near Max, measured at intervals. Variation must not exceed MPE.
      </p>
      <Table dataSource={rows} columns={[
        { title: '#', width: 50, render: (_: unknown, __: unknown, i: number) => i + 1 },
        { title: 'Reference load', dataIndex: 'test_point_load', render: (v: string, r: Row) => <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'test_point_load', String(val ?? ''))} /> },
        { title: 'Indicated value', dataIndex: 'indicated_value', render: (v: string, r: Row) => <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'indicated_value', String(val ?? ''))} /> },
        { title: 'Correction', dataIndex: 'correction', width: 120, render: (v: string, r: Row) => <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'correction', String(val ?? '0'))} /> },
      ]} rowKey="key" size="small" pagination={false} bordered={false} />
      <div style={{ marginTop: 8 }}><Button type="link" onClick={addRow} style={{ padding: 0 }}>+ Add row</Button></div>
      <div style={{ marginTop: 16 }}><Button onClick={saveObservations} loading={mutation.isPending}>Save observations</Button></div>

      {spanResults.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Results</h3>
          <Table dataSource={spanResults} columns={[
            { title: 'Error', dataIndex: 'computed_error', align: 'right' as const },
            { title: 'MPE', dataIndex: 'mpe_applicable', align: 'right' as const },
            { title: 'Status', dataIndex: 'compliance_status', render: (s: string) => <StatusTag status={s} /> },
          ]} rowKey="id" size="small" pagination={false} bordered={false} />
        </div>
      )}
    </div>
  );
}
