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

export default function ZeroTrackingForm({ sessionId, results }: Props) {
  const queryClient = useQueryClient();
  const [readingBefore, setReadingBefore] = useState('');
  const [readingAfter, setReadingAfter] = useState('');

  const zeroResults = (results ?? []).filter((r) => r.test_type === 'zero_tracking');

  const mutation = useMutation({
    mutationFn: (obs: Parameters<typeof submitObservations>[1]) => submitObservations(sessionId, obs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['results', sessionId] }),
  });

  const saveObservations = () => {
    if (!readingBefore || !readingAfter) return;
    mutation.mutate([
      { test_type: 'zero_tracking', test_point_load: '0', indicated_value: readingBefore, correction: '0', trial_number: 1, direction: 'increasing' as const },
      { test_type: 'zero_tracking', test_point_load: '0', indicated_value: readingAfter, correction: '0', trial_number: 2, direction: 'decreasing' as const },
    ]);
  };

  return (
    <div>
      <p style={{ fontSize: 12, color: '#999999', marginBottom: 16 }}>
        After removing load that has been on the instrument for 30 minutes, deviation from zero must be &le; 0.5e.
      </p>
      <div style={{ display: 'flex', gap: 24, marginBottom: 24 }}>
        <div>
          <label style={{ display: 'block', fontSize: 14, color: '#666666', marginBottom: 4 }}>Zero reading (before load)</label>
          <InputNumber value={readingBefore || undefined} size="small" style={{ width: 200 }} stringMode onChange={(v) => setReadingBefore(String(v ?? ''))} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 14, color: '#666666', marginBottom: 4 }}>Zero reading (after removing load)</label>
          <InputNumber value={readingAfter || undefined} size="small" style={{ width: 200 }} stringMode onChange={(v) => setReadingAfter(String(v ?? ''))} />
        </div>
      </div>
      <Button onClick={saveObservations} loading={mutation.isPending}>Save observations</Button>

      {zeroResults.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Results</h3>
          <Table dataSource={zeroResults} columns={[
            { title: 'Error', dataIndex: 'computed_error', align: 'right' as const },
            { title: 'MPE', dataIndex: 'mpe_applicable', align: 'right' as const },
            { title: 'Status', dataIndex: 'compliance_status', render: (s: string) => <StatusTag status={s} /> },
          ]} rowKey="id" size="small" pagination={false} bordered={false} />
        </div>
      )}
    </div>
  );
}
