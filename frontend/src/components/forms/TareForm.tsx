import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, InputNumber, Button } from 'antd';
import { submitObservations } from '@/api/sessions';
import StatusTag from '@/components/common/StatusTag';
import type { TestResult } from '@/types/session';

interface Row {
  key: number;
  tare_load: string;
  net_load: string;
  indicated_value: string;
}

interface Props {
  sessionId: number;
  results?: TestResult[];
}

export default function TareForm({ sessionId, results }: Props) {
  const queryClient = useQueryClient();
  const [rows, setRows] = useState<Row[]>([
    { key: 1, tare_load: '', net_load: '', indicated_value: '' },
  ]);

  const tareResults = (results ?? []).filter((r) => r.test_type === 'tare');

  const mutation = useMutation({
    mutationFn: (obs: Parameters<typeof submitObservations>[1]) => submitObservations(sessionId, obs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['results', sessionId] }),
  });

  const updateRow = (key: number, field: keyof Row, value: string) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, [field]: value } : r)));
  };

  const addRow = () => {
    setRows((prev) => [...prev, { key: Date.now(), tare_load: '', net_load: '', indicated_value: '' }]);
  };

  const saveObservations = () => {
    const obs = rows.filter((r) => r.net_load && r.indicated_value).map((r, i) => ({
      test_type: 'tare' as const,
      test_point_load: r.net_load,
      indicated_value: r.indicated_value,
      correction: r.tare_load || '0',
      trial_number: i + 1,
    }));
    if (obs.length > 0) mutation.mutate(obs);
  };

  return (
    <div>
      <Table
        dataSource={rows}
        columns={[
          { title: '#', width: 50, render: (_: unknown, __: unknown, i: number) => i + 1 },
          { title: 'Tare load', dataIndex: 'tare_load', render: (v: string, r: Row) => <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'tare_load', String(val ?? ''))} /> },
          { title: 'Net load', dataIndex: 'net_load', render: (v: string, r: Row) => <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'net_load', String(val ?? ''))} /> },
          { title: 'Indicated (net)', dataIndex: 'indicated_value', render: (v: string, r: Row) => <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'indicated_value', String(val ?? ''))} /> },
        ]}
        rowKey="key"
        size="small"
        pagination={false}
        bordered={false}
      />
      <div style={{ marginTop: 8 }}><Button type="link" onClick={addRow} style={{ padding: 0 }}>+ Add row</Button></div>
      <div style={{ marginTop: 16 }}><Button onClick={saveObservations} loading={mutation.isPending}>Save observations</Button></div>

      {tareResults.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Results</h3>
          <Table dataSource={tareResults} columns={[
            { title: 'Error', dataIndex: 'computed_error', align: 'right' as const },
            { title: 'MPE', dataIndex: 'mpe_applicable', align: 'right' as const },
            { title: 'Status', dataIndex: 'compliance_status', render: (s: string) => <StatusTag status={s} /> },
          ]} rowKey="id" size="small" pagination={false} bordered={false} />
        </div>
      )}
    </div>
  );
}
