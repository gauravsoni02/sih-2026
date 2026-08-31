import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { InputNumber, Button, Table } from 'antd';
import { submitObservations } from '@/api/sessions';
import StatusTag from '@/components/common/StatusTag';
import type { TestResult } from '@/types/session';

interface Props {
  sessionId: number;
  results?: TestResult[];
}

export default function TimeDependenceForm({ sessionId, results }: Props) {
  const queryClient = useQueryClient();
  const [testLoad, setTestLoad] = useState('');
  const [reading0, setReading0] = useState('');
  const [reading15, setReading15] = useState('');
  const [reading30, setReading30] = useState('');

  const creepResults = (results ?? []).filter((r) => r.test_type === 'creep' || r.test_type === 'time_dependence');

  const mutation = useMutation({
    mutationFn: (obs: Parameters<typeof submitObservations>[1]) => submitObservations(sessionId, obs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['results', sessionId] }),
  });

  const saveObservations = () => {
    if (!testLoad || !reading0) return;
    const obs = [
      { test_type: 'creep' as const, test_point_load: testLoad, indicated_value: reading0, correction: '0', trial_number: 1, timestamp_minutes: 0 },
      ...(reading15 ? [{ test_type: 'creep' as const, test_point_load: testLoad, indicated_value: reading15, correction: '0', trial_number: 2, timestamp_minutes: 15 }] : []),
      ...(reading30 ? [{ test_type: 'creep' as const, test_point_load: testLoad, indicated_value: reading30, correction: '0', trial_number: 3, timestamp_minutes: 30 }] : []),
    ];
    mutation.mutate(obs);
  };

  return (
    <div>
      <p style={{ fontSize: 12, color: '#999999', marginBottom: 16 }}>
        Apply load and record readings at 0, 15, and 30 minutes. Drift must not exceed 0.5e (0-30 min) and 0.2e (15-30 min).
      </p>
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', fontSize: 14, color: '#666666', marginBottom: 4 }}>Test load</label>
        <InputNumber value={testLoad || undefined} size="small" style={{ width: 200 }} stringMode onChange={(v) => setTestLoad(String(v ?? ''))} />
      </div>
      <Table<{ key: string; label: string; value: string; set: (v: string) => void }>
        dataSource={[
          { key: '0', label: '0 minutes', value: reading0, set: setReading0 },
          { key: '15', label: '15 minutes', value: reading15, set: setReading15 },
          { key: '30', label: '30 minutes', value: reading30, set: setReading30 },
        ]}
        columns={[
          { title: 'Time', dataIndex: 'label', width: 140 },
          {
            title: 'Reading',
            dataIndex: 'value',
            render: (_v, r) => (
              <InputNumber value={r.value || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => r.set(String(val ?? ''))} />
            ),
          },
        ]}
        rowKey="key"
        size="small"
        pagination={false}
        bordered={false}
      />
      <div style={{ marginTop: 16 }}><Button onClick={saveObservations} loading={mutation.isPending}>Save observations</Button></div>

      {creepResults.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Results</h3>
          <Table dataSource={creepResults} columns={[
            { title: 'Error', dataIndex: 'computed_error', align: 'right' as const },
            { title: 'MPE', dataIndex: 'mpe_applicable', align: 'right' as const },
            { title: 'Status', dataIndex: 'compliance_status', render: (s: string) => <StatusTag status={s} /> },
          ]} rowKey="id" size="small" pagination={false} bordered={false} />
        </div>
      )}
    </div>
  );
}
