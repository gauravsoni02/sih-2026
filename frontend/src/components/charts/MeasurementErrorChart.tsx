import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Legend,
} from 'recharts';

export interface ErrorChartPoint {
  nominalLoad: number;
  error: number;
  upperMpe: number | null;
  lowerMpe: number | null;
  status?: string;
}

interface MeasurementErrorChartProps {
  data: ErrorChartPoint[];
  unit?: string;
  height?: number;
}

export default function MeasurementErrorChart({ data, unit = 'g', height = 300 }: MeasurementErrorChartProps) {
  if (!data.length) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999999', fontSize: 14 }}>
        No measurement data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="nominalLoad"
          tick={{ fontSize: 12, fill: '#666666' }}
          tickLine={{ stroke: '#e8e8e8' }}
          axisLine={{ stroke: '#e8e8e8' }}
          label={{ value: `Load (${unit})`, position: 'insideBottomRight', offset: -4, fontSize: 12, fill: '#999999' }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#666666' }}
          tickLine={{ stroke: '#e8e8e8' }}
          axisLine={{ stroke: '#e8e8e8' }}
          label={{ value: `Error (${unit})`, angle: -90, position: 'insideLeft', offset: 4, fontSize: 12, fill: '#999999' }}
        />
        <Tooltip
          contentStyle={{ fontSize: 12, border: '1px solid #e8e8e8', borderRadius: 4, boxShadow: 'none' }}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={(value: any, name: any) => {
            const labels: Record<string, string> = {
              error: 'Measured error',
              upperMpe: '+ MPE',
              lowerMpe: '− MPE',
            };
            const formatted = typeof value === 'number' ? value.toFixed(4) : String(value ?? '');
            return [formatted, labels[String(name)] || String(name)];
          }}
          labelFormatter={(label) => `Load: ${label} ${unit}`}
        />
        <Legend
          verticalAlign="top"
          height={28}
          formatter={(value) => {
            const labels: Record<string, string> = {
              error: 'Measured error',
              upperMpe: '+ MPE',
              lowerMpe: '− MPE',
            };
            return <span style={{ fontSize: 12, color: '#666666' }}>{labels[value] || value}</span>;
          }}
        />
        <ReferenceLine y={0} stroke="#e8e8e8" strokeWidth={1} />
        <Line
          dataKey="upperMpe"
          stroke="#d97706"
          strokeDasharray="5 4"
          strokeWidth={1.5}
          dot={false}
          connectNulls
        />
        <Line
          dataKey="lowerMpe"
          stroke="#d97706"
          strokeDasharray="5 4"
          strokeWidth={1.5}
          dot={false}
          connectNulls
        />
        <Line
          dataKey="error"
          stroke="#2563eb"
          strokeWidth={2}
          dot={{ r: 3, fill: '#2563eb', strokeWidth: 0 }}
          activeDot={{ r: 5, fill: '#2563eb' }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
