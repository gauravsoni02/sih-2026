import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, InputNumber, Button } from 'antd';
import { submitObservations } from '@/api/sessions';
import StatusTag from '@/components/common/StatusTag';
import { getDemoObservations } from '@/utils/demoData';
import type { TestResult } from '@/types/session';

interface Row {
  key: number;
  trial: number;
  test_point_load: string;
  indicated_value: string;
}

interface Props {
  sessionId: number;
  results?: TestResult[];
  instrumentDetail?: { max_capacity?: string };
}

export default function RepeatabilityForm({ sessionId, results, instrumentDetail }: Props) {
  const queryClient = useQueryClient();
  const [testLoad, setTestLoad] = useState('');
  const [rows, setRows] = useState<Row[]>(
    Array.from({ length: 6 }, (_, i) => ({ key: i + 1, trial: i + 1, test_point_load: '', indicated_value: '' }))
  );

  const repResults = (results ?? []).filter((r) => r.test_type === 'repeatability');

  const mutation = useMutation({
    mutationFn: (obs: Parameters<typeof submitObservations>[1]) => submitObservations(sessionId, obs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['results', sessionId] }),
  });

  const updateRow = (key: number, field: keyof Row, value: string) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, [field]: value } : r)));
  };

  const addRow = () => {
    setRows((prev) => [...prev, { key: Date.now(), trial: prev.length + 1, test_point_load: '', indicated_value: '' }]);
  };

  const saveObservations = () => {
    const load = testLoad || rows[0]?.test_point_load;
    const obs = rows
      .filter((r) => r.indicated_value)
      .map((r) => ({
        test_type: 'repeatability' as const,
        test_point_load: load,
        indicated_value: r.indicated_value,
        correction: '0',
        trial_number: r.trial,
      }));
    if (obs.length > 0) mutation.mutate(obs);
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', fontSize: 14, color: '#666666', marginBottom: 4 }}>Test load</label>
        <InputNumber value={testLoad || undefined} size="small" style={{ width: 200 }} stringMode onChange={(v) => setTestLoad(String(v ?? ''))} />
      </div>
      <Table
        dataSource={rows}
        columns={[
          { title: 'Trial', dataIndex: 'trial', width: 70 },
          {
            title: 'Indicated value',
            dataIndex: 'indicated_value',
            render: (val: string, record: Row) => (
              <InputNumber value={val || undefined} size="small" style={{ width: '100%' }} stringMode onChange={(v) => updateRow(record.key, 'indicated_value', String(v ?? ''))} />
            ),
          },
        ]}
        rowKey="key"
        size="small"
        pagination={false}
        bordered={false}
      />
      <div style={{ marginTop: 8 }}>
        <Button type="link" onClick={addRow} style={{ padding: 0 }}>+ Add trial</Button>
      </div>
      <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
        {instrumentDetail && (
          <Button onClick={() => {
            const rep = getDemoObservations(instrumentDetail).repeatability;
            setTestLoad(rep.testLoad);
            setRows(rep.readings.map((val, i) => ({ key: i + 1, trial: i + 1, test_point_load: rep.testLoad, indicated_value: val })));
          }}>
            Load sample values
          </Button>
        )}
        <Button onClick={saveObservations} loading={mutation.isPending}>Save observations</Button>
      </div>

      {repResults.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Results</h3>
          <Table
            dataSource={repResults}
            columns={[
              { title: 'Error (range)', dataIndex: 'computed_error', align: 'right' as const,
                render: (v: string) => <span style={{ fontVariantNumeric: 'tabular-nums' }}>{v}</span> },
              { title: 'MPE', dataIndex: 'mpe_applicable', align: 'right' as const,
                render: (v: string) => <span style={{ fontVariantNumeric: 'tabular-nums' }}>{v}</span> },
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
