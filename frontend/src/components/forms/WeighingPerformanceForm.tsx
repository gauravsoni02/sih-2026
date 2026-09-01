import { useState, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, InputNumber, Button, Select } from 'antd';
import { submitObservations } from '@/api/sessions';
import StatusTag from '@/components/common/StatusTag';
import DeviceCapturePanel from '@/components/forms/DeviceCapturePanel';
import { getDemoObservations } from '@/utils/demoData';
import { getMpe } from '@/utils/mpe';
import MeasurementErrorChart from '@/components/charts/MeasurementErrorChart';
import type { ErrorChartPoint } from '@/components/charts/MeasurementErrorChart';
import type { TestResult } from '@/types/session';

interface Row {
  key: number;
  test_point_load: string;
  indicated_value: string;
  correction: string;
  direction: 'increasing' | 'decreasing';
  /** Optional changeover-point extra load ΔL (half-division method). */
  delta_load?: string;
}

interface LiveResult {
  error: number | null;
  mpe: number | null;
  status: 'pass' | 'fail' | null;
}

interface Props {
  sessionId: number;
  results?: TestResult[];
  instrumentDetail?: {
    max_capacity?: string;
    min_capacity?: string;
    verification_scale_interval_e?: string;
    accuracy_class?: string;
    unit?: string;
  };
}

function computeLiveResult(
  row: Row,
  accuracyClass: string,
  e: number,
): LiveResult {
  const load = parseFloat(row.test_point_load);
  const indicated = parseFloat(row.indicated_value);
  const correction = parseFloat(row.correction || '0');

  if (isNaN(load) || isNaN(indicated) || !accuracyClass || !e) {
    return { error: null, mpe: null, status: null };
  }

  const reference = load + correction;
  const error = indicated - reference;

  try {
    const mpe = getMpe(accuracyClass as 'I' | 'II' | 'III' | 'IIII', load, e);
    const status = Math.abs(error) <= mpe + 1e-9 ? 'pass' : 'fail';
    return { error, mpe, status };
  } catch {
    return { error, mpe: null, status: null };
  }
}

export default function WeighingPerformanceForm({ sessionId, results, instrumentDetail }: Props) {
  const queryClient = useQueryClient();
  const [rows, setRows] = useState<Row[]>([
    { key: 1, test_point_load: '', indicated_value: '', correction: '0', direction: 'increasing' },
  ]);

  const wpResults = (results ?? []).filter((r) => r.test_type === 'weighing_performance');

  const accuracyClass = instrumentDetail?.accuracy_class || '';
  const e = parseFloat(instrumentDetail?.verification_scale_interval_e || '0');
  const unit = instrumentDetail?.unit || 'g';

  const liveResults = useMemo(() => {
    return rows.map((row) => computeLiveResult(row, accuracyClass, e));
  }, [rows, accuracyClass, e]);

  const liveChartData = useMemo<ErrorChartPoint[]>(() => {
    const points: ErrorChartPoint[] = [];
    rows.forEach((row, i) => {
      const lr = liveResults[i];
      if (lr.error !== null && lr.mpe !== null) {
        points.push({
          nominalLoad: parseFloat(row.test_point_load),
          error: lr.error,
          upperMpe: lr.mpe,
          lowerMpe: -lr.mpe,
        });
      }
    });
    points.sort((a, b) => a.nominalLoad - b.nominalLoad);
    return points;
  }, [rows, liveResults]);

  const mutation = useMutation({
    mutationFn: (obs: Parameters<typeof submitObservations>[1]) => submitObservations(sessionId, obs),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['results', sessionId] }),
  });

  const updateRow = (key: number, field: keyof Row, value: string) => {
    setRows((prev) => prev.map((r) => (r.key === key ? { ...r, [field]: value } : r)));
  };

  // The row the device capture fills: first row with a reference load entered
  // but no indicated value yet.
  const captureRow = rows.find((r) => r.test_point_load && !r.indicated_value);
  const captureRowIndex = captureRow ? rows.indexOf(captureRow) : -1;

  const handleCapture = (value: string) => {
    if (captureRow) {
      updateRow(captureRow.key, 'indicated_value', value);
    }
  };

  const addRow = () => {
    const lastDir = rows[rows.length - 1]?.direction || 'increasing';
    setRows((prev) => [
      ...prev,
      { key: Date.now(), test_point_load: '', indicated_value: '', correction: '0', direction: lastDir },
    ]);
  };

  const saveObservations = () => {
    const obs = rows
      .filter((r) => r.test_point_load && r.indicated_value)
      .map((r, i) => ({
        test_type: 'weighing_performance' as const,
        test_point_load: r.test_point_load,
        indicated_value: r.indicated_value,
        correction: r.correction || '0',
        direction: r.direction,
        trial_number: i + 1,
        ...(r.delta_load ? { delta_load: r.delta_load } : {}),
      }));
    if (obs.length > 0) mutation.mutate(obs);
  };

  const columns = [
    {
      title: '#',
      width: 50,
      render: (_: unknown, __: unknown, i: number) => i + 1,
    },
    {
      title: 'Direction',
      dataIndex: 'direction',
      width: 130,
      render: (val: string, record: Row) => (
        <Select
          value={val}
          size="small"
          style={{ width: 120 }}
          options={[
            { value: 'increasing', label: 'Increasing' },
            { value: 'decreasing', label: 'Decreasing' },
          ]}
          onChange={(v) => updateRow(record.key, 'direction', v)}
        />
      ),
    },
    {
      title: 'Reference load',
      dataIndex: 'test_point_load',
      render: (val: string, record: Row) => (
        <InputNumber
          value={val || undefined}
          size="small"
          style={{ width: '100%' }}
          stringMode
          onChange={(v) => updateRow(record.key, 'test_point_load', String(v ?? ''))}
        />
      ),
    },
    {
      title: 'Indicated value',
      dataIndex: 'indicated_value',
      render: (val: string, record: Row) => (
        <InputNumber
          value={val || undefined}
          size="small"
          style={{ width: '100%' }}
          stringMode
          onChange={(v) => updateRow(record.key, 'indicated_value', String(v ?? ''))}
        />
      ),
    },
    {
      title: 'Correction',
      dataIndex: 'correction',
      width: 120,
      render: (val: string, record: Row) => (
        <InputNumber
          value={val || undefined}
          size="small"
          style={{ width: '100%' }}
          stringMode
          onChange={(v) => updateRow(record.key, 'correction', String(v ?? '0'))}
        />
      ),
    },
    {
      title: 'Δ load (changeover)',
      dataIndex: 'delta_load',
      width: 140,
      render: (val: string | undefined, record: Row) => (
        <InputNumber
          value={val || undefined}
          size="small"
          style={{ width: '100%' }}
          stringMode
          placeholder="optional"
          onChange={(v) => updateRow(record.key, 'delta_load', String(v ?? ''))}
        />
      ),
    },
    {
      title: 'Error',
      width: 100,
      align: 'right' as const,
      render: (_: unknown, __: unknown, i: number) => {
        const lr = liveResults[i];
        if (lr.error === null) return '—';
        return (
          <span style={{
            fontVariantNumeric: 'tabular-nums',
            color: lr.status === 'fail' ? '#cf1322' : '#1a1a1a',
          }}>
            {lr.error.toFixed(4)}
          </span>
        );
      },
    },
    {
      title: 'MPE',
      width: 100,
      align: 'right' as const,
      render: (_: unknown, __: unknown, i: number) => {
        const lr = liveResults[i];
        if (lr.mpe === null) return '—';
        return (
          <span style={{ fontVariantNumeric: 'tabular-nums', color: '#666666' }}>
            ±{lr.mpe.toFixed(4)}
          </span>
        );
      },
    },
    {
      title: 'Result',
      width: 70,
      render: (_: unknown, __: unknown, i: number) => {
        const lr = liveResults[i];
        if (lr.status === null) return '—';
        return <StatusTag status={lr.status} />;
      },
    },
  ];

  const resultColumns = [
    { title: '#', width: 50, render: (_: unknown, __: unknown, i: number) => i + 1 },
    { title: 'Load', dataIndex: 'test_point_load', key: 'load', width: 100,
      render: (v: string | null) => v ?? '—' },
    {
      title: 'Error',
      dataIndex: 'computed_error',
      width: 100,
      align: 'right' as const,
      render: (v: string) => <span style={{ fontVariantNumeric: 'tabular-nums' }}>{v}</span>,
    },
    {
      title: 'MPE',
      dataIndex: 'mpe_applicable',
      width: 100,
      align: 'right' as const,
      render: (v: string) => <span style={{ fontVariantNumeric: 'tabular-nums' }}>{v}</span>,
    },
    {
      title: 'U (±) k=2',
      dataIndex: 'expanded_uncertainty',
      width: 100,
      align: 'right' as const,
      render: (v: string | null | undefined) => (
        <span style={{ fontVariantNumeric: 'tabular-nums', color: '#666666' }}>
          {v != null ? `±${v}` : '—'}
        </span>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'compliance_status',
      width: 80,
      render: (s: string) => <StatusTag status={s} />,
    },
    {
      title: 'Remarks',
      dataIndex: 'remarks',
      render: (v: string) => v || '—',
    },
  ];

  return (
    <div>
      <DeviceCapturePanel
        unit={unit}
        scaleInterval={e || 0.01}
        targetLoad={captureRow ? parseFloat(captureRow.test_point_load) : 0}
        captureHint={
          captureRowIndex >= 0
            ? `→ fills row ${captureRowIndex + 1}`
            : 'enter a reference load first'
        }
        onCapture={handleCapture}
      />
      <Table
        dataSource={rows}
        columns={columns}
        rowKey="key"
        size="small"
        pagination={false}
        bordered={false}
      />
      <div style={{ marginTop: 8 }}>
        <Button type="link" onClick={addRow} style={{ padding: 0 }}>+ Add row</Button>
      </div>
      <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
        {instrumentDetail && (
          <Button onClick={() => setRows(getDemoObservations(instrumentDetail).weighing_performance)}>
            Load sample values
          </Button>
        )}
        <Button onClick={saveObservations} loading={mutation.isPending}>
          Save observations
        </Button>
      </div>

      <div style={{ marginTop: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: '#1a1a1a', marginBottom: 8 }}>
          Live entry preview
        </h3>
        {liveChartData.length >= 2 ? (
          <MeasurementErrorChart data={liveChartData} unit={unit} height={240} />
        ) : (
          <p style={{ fontSize: 12, color: '#999999', margin: 0 }}>
            Enter observations to preview the error curve. The official calculated
            profile appears at the top of the session page after Calculate.
          </p>
        )}
      </div>

      {wpResults.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Server results</h3>
          <Table
            dataSource={wpResults}
            columns={resultColumns}
            rowKey="id"
            size="small"
            pagination={false}
            bordered={false}
            rowClassName={(_, i) => (i % 2 === 1 ? 'alt-row' : '')}
          />
        </div>
      )}
    </div>
  );
}
