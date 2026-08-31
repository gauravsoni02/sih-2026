import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import type { MonthlyTest } from '@/api/dashboard';

interface TestingTrendChartProps {
  data: MonthlyTest[];
  height?: number;
}

export default function TestingTrendChart({ data, height = 240 }: TestingTrendChartProps) {
  if (!data.length) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999999', fontSize: 14 }}>
        No test data available
      </div>
    );
  }

  const formatted = data.map((d) => ({
    ...d,
    label: d.month.slice(5),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={formatted} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 12, fill: '#666666' }}
          tickLine={false}
          axisLine={{ stroke: '#e8e8e8' }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: '#666666' }}
          tickLine={false}
          axisLine={{ stroke: '#e8e8e8' }}
          allowDecimals={false}
        />
        <Tooltip
          contentStyle={{ fontSize: 12, border: '1px solid #e8e8e8', borderRadius: 4, boxShadow: 'none' }}
        />
        <Legend
          verticalAlign="top"
          height={28}
          formatter={(value) => <span style={{ fontSize: 12, color: '#666666' }}>{value}</span>}
        />
        <Bar dataKey="passed" name="Passed" fill="#389e0d" stackId="a" radius={[0, 0, 0, 0]} />
        <Bar dataKey="failed" name="Failed" fill="#cf1322" stackId="a" radius={[0, 0, 0, 0]} />
        <Bar dataKey="pending" name="Pending" fill="#d9d9d9" stackId="a" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
