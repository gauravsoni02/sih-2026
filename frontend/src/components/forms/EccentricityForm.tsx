import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { InputNumber, Button, Table } from 'antd';
import { submitObservations } from '@/api/sessions';
import StatusTag from '@/components/common/StatusTag';
import { getDemoObservations } from '@/utils/demoData';
import type { TestResult } from '@/types/session';

const POSITIONS = ['center', 'front_left', 'front_right', 'rear_left', 'rear_right'] as const;
const POSITION_LABELS: Record<string, string> = {
  center: 'Center',
  front_left: 'Front-left',
  front_right: 'Front-right',
  rear_left: 'Rear-left',
  rear_right: 'Rear-right',
};

interface Props {
  sessionId: number;
  results?: TestResult[];
  instrumentDetail?: { max_capacity?: string; max_additive_tare?: string };
}

export default function EccentricityForm({ sessionId, results, instrumentDetail }: Props) {
  const queryClient = useQueryClient();
  const [testLoad, setTestLoad] = useState<string>('');
  const [readings, setReadings] = useState<Record<string, string>>(
    Object.fromEntries(POSITIONS.map((p) => [p, '']))
  );

  const eccResults = (results ?? []).filter((r) => r.test_type === 'eccentricity');

  const mutation = useMutation({
    mutationFn: (obs: Parameters<typeof submitObservations>[1]) => submitObservations(sessionId, obs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['results', sessionId] }),
  });

  const saveObservations = () => {
    if (!testLoad) return;
    const obs = POSITIONS.filter((p) => readings[p]).map((p, i) => ({
      test_type: 'eccentricity' as const,
      test_point_load: testLoad,
      indicated_value: readings[p],
      correction: '0',
      position: p,
      trial_number: i + 1,
    }));
    if (obs.length > 0) mutation.mutate(obs);
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <label style={{ display: 'block', fontSize: 14, color: '#666666', marginBottom: 4 }}>
          Test load (1/3 x (Max + T+))
        </label>
        <InputNumber
          value={testLoad || undefined}
          size="small"
          style={{ width: 200 }}
          stringMode
          onChange={(v) => setTestLoad(String(v ?? ''))}
        />
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gridTemplateRows: '1fr 1fr 1fr',
        gap: 8,
        maxWidth: 360,
        marginBottom: 24,
      }}>
        {/* Row 1 */}
        <PositionCell label="Front-left" value={readings.front_left} onChange={(v) => setReadings((r) => ({ ...r, front_left: v }))} />
        <div />
        <PositionCell label="Front-right" value={readings.front_right} onChange={(v) => setReadings((r) => ({ ...r, front_right: v }))} />
        {/* Row 2 */}
        <div />
        <PositionCell label="Center" value={readings.center} onChange={(v) => setReadings((r) => ({ ...r, center: v }))} />
        <div />
        {/* Row 3 */}
        <PositionCell label="Rear-left" value={readings.rear_left} onChange={(v) => setReadings((r) => ({ ...r, rear_left: v }))} />
        <div />
        <PositionCell label="Rear-right" value={readings.rear_right} onChange={(v) => setReadings((r) => ({ ...r, rear_right: v }))} />
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        {instrumentDetail && (
          <Button onClick={() => {
            const ecc = getDemoObservations(instrumentDetail).eccentricity;
            setTestLoad(ecc.testLoad);
            setReadings(ecc.readings);
          }}>
            Load sample values
          </Button>
        )}
        <Button onClick={saveObservations} loading={mutation.isPending}>Save observations</Button>
      </div>

      {eccResults.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Results</h3>
          <Table
            dataSource={eccResults}
            columns={[
              { title: 'Position', dataIndex: 'position', render: (p: string) => POSITION_LABELS[p] || p },
              { title: 'Error', dataIndex: 'computed_error', align: 'right' as const,
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

function PositionCell({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div style={{ border: '1px solid #e8e8e8', padding: 8, textAlign: 'center' }}>
      <div style={{ fontSize: 12, color: '#999999', marginBottom: 4 }}>{label}</div>
      <InputNumber
        value={value || undefined}
        size="small"
        style={{ width: '100%' }}
        stringMode
        onChange={(v) => onChange(String(v ?? ''))}
      />
    </div>
  );
}
