import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, InputNumber, Button } from 'antd';
import { submitObservations } from '@/api/sessions';
import StatusTag from '@/components/common/StatusTag';
import { getDemoObservations } from '@/utils/demoData';
import type { TestResult } from '@/types/session';

interface Row {
  key: number;
  test_point_load: string;
  indicated_before: string;
  indicated_after: string;
}

interface Props {
  sessionId: number;
  results?: TestResult[];
  instrumentDetail?: { max_capacity?: string; min_capacity?: string; actual_scale_interval_d?: string };
}

export default function DiscriminationForm({ sessionId, results, instrumentDetail }: Props) {
  const queryClient = useQueryClient();
  const [rows, setRows] = useState<Row[]>([
    { key: 1, test_point_load: '', indicated_before: '', indicated_after: '' },
    { key: 2, test_point_load: '', indicated_before: '', indicated_after: '' },
    { key: 3, test_point_load: '', indicated_before: '', indicated_after: '' },
  ]);

  const discResults = (results ?? []).filter((r) => r.test_type === 'discrimination');

  const mutation = useMutation({
    mutationFn: (obs: Parameters<typeof submitObservations>[1]) => submitObservations(sessionId, obs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['results', sessionId] }),
  });

  const updateRow = (key: number, field: keyof Row, value: string) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, [field]: value } : r)));
  };

  const saveObservations = () => {
    const obs: Parameters<typeof submitObservations>[1] = [];
    rows.filter((r) => r.test_point_load && r.indicated_before).forEach((r, i) => {
      obs.push({
        test_type: 'discrimination',
        test_point_load: r.test_point_load,
        indicated_value: r.indicated_before,
        correction: '0',
        trial_number: i + 1,
        direction: 'increasing',
      });
      if (r.indicated_after) {
        obs.push({
          test_type: 'discrimination',
          test_point_load: r.test_point_load,
          indicated_value: r.indicated_after,
          correction: '0',
          trial_number: i + 1,
          direction: 'decreasing',
        });
      }
    });
    if (obs.length > 0) mutation.mutate(obs);
  };

  return (
    <div>
      <p style={{ fontSize: 12, color: '#999999', marginBottom: 16 }}>
        At each test point, record the reading before and after depositing 1.4d.
      </p>
      <Table
        dataSource={rows}
        columns={[
          { title: '#', width: 50, render: (_: unknown, __: unknown, i: number) => i + 1 },
          {
            title: 'Load',
            dataIndex: 'test_point_load',
            render: (v: string, r: Row) => (
              <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'test_point_load', String(val ?? ''))} />
            ),
          },
          {
            title: 'Reading before',
            dataIndex: 'indicated_before',
            render: (v: string, r: Row) => (
              <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'indicated_before', String(val ?? ''))} />
            ),
          },
          {
            title: 'Reading after +1.4d',
            dataIndex: 'indicated_after',
            render: (v: string, r: Row) => (
              <InputNumber value={v || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(val) => updateRow(r.key, 'indicated_after', String(val ?? ''))} />
            ),
          },
        ]}
        rowKey="key"
        size="small"
        pagination={false}
        bordered={false}
      />
      <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
        {instrumentDetail && (
          <Button onClick={() => {
            const disc = getDemoObservations(instrumentDetail).discrimination;
            setRows(disc.map((d, i) => ({ key: i + 1, test_point_load: d.load, indicated_before: d.before, indicated_after: d.after })));
          }}>
            Load sample values
          </Button>
        )}
        <Button onClick={saveObservations} loading={mutation.isPending}>Save observations</Button>
      </div>

      {discResults.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Results</h3>
          <Table
            dataSource={discResults}
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
