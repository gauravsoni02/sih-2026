import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, InputNumber, Button } from 'antd';
import { submitObservations } from '@/api/sessions';
import StatusTag from '@/components/common/StatusTag';
import type { TestResult } from '@/types/session';

interface Row {
  key: string;
  label: string;
  test_point_load: string;
  reading_before: string;
  reading_after: string;
}

interface Props {
  sessionId: number;
  results?: TestResult[];
}

export default function SensitivityForm({ sessionId, results }: Props) {
  const queryClient = useQueryClient();
  const [rows, setRows] = useState<Row[]>([
    { key: 'zero', label: 'At zero', test_point_load: '0', reading_before: '', reading_after: '' },
    { key: 'max', label: 'At Max', test_point_load: '', reading_before: '', reading_after: '' },
  ]);

  const sensResults = (results ?? []).filter((r) => r.test_type === 'sensitivity');

  const mutation = useMutation({
    mutationFn: (obs: Parameters<typeof submitObservations>[1]) => submitObservations(sessionId, obs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['results', sessionId] }),
  });

  const updateRow = (key: string, field: keyof Row, value: string) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, [field]: value } : r)));
  };

  const saveObservations = () => {
    const obs = rows.filter((r) => r.reading_before && r.reading_after).flatMap((r, i) => [
      { test_type: 'sensitivity' as const, test_point_load: r.test_point_load, indicated_value: r.reading_before, correction: '0', trial_number: i + 1, direction: 'increasing' as const },
      { test_type: 'sensitivity' as const, test_point_load: r.test_point_load, indicated_value: r.reading_after, correction: '0', trial_number: i + 1, direction: 'decreasing' as const },
    ]);
    if (obs.length > 0) mutation.mutate(obs);
  };

  return (
    <div>
      <p style={{ fontSize: 12, color: '#999999', marginBottom: 16 }}>
        Record reading before and after adding 1d at zero and Max.
      </p>
      <Table
        dataSource={rows}
        columns={[
          { title: 'Point', dataIndex: 'label', width: 100 },
          {
            title: 'Load',
            dataIndex: 'test_point_load',
            width: 140,
            render: (v: string, r: Row) => (
              <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'test_point_load', String(val ?? ''))} />
            ),
          },
          {
            title: 'Reading before',
            dataIndex: 'reading_before',
            render: (v: string, r: Row) => (
              <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'reading_before', String(val ?? ''))} />
            ),
          },
          {
            title: 'Reading after +1d',
            dataIndex: 'reading_after',
            render: (v: string, r: Row) => (
              <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'reading_after', String(val ?? ''))} />
            ),
          },
        ]}
        rowKey="key"
        size="small"
        pagination={false}
        bordered={false}
      />
      <div style={{ marginTop: 16 }}>
        <Button onClick={saveObservations} loading={mutation.isPending}>Save observations</Button>
      </div>

      {sensResults.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Results</h3>
          <Table
            dataSource={sensResults}
            columns={[
              { title: 'Error', dataIndex: 'computed_error', align: 'right' as const },
              { title: 'MPE', dataIndex: 'mpe_applicable', align: 'right' as const },
              { title: 'Status', dataIndex: 'compliance_status', render: (s: string) => <StatusTag status={s} /> },
            ]}
            rowKey="id"
            size="small"
            pagination={false}
            bordered={false}
          />
        </div>
      )}
    </div>
  );
}
