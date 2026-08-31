import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import type { PassFailSummary } from '@/api/dashboard';

interface PassFailPieChartProps {
  data: PassFailSummary;
  height?: number;
}

const COLORS = {
  passed: '#389e0d',
  failed: '#cf1322',
  pending: '#d9d9d9',
};

export default function PassFailPieChart({ data, height = 240 }: PassFailPieChartProps) {
  if (data.total === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#999999', fontSize: 14 }}>
        No tests this month
      </div>
    );
  }

  const chartData = [
    { name: 'Passed', value: data.passed },
    { name: 'Failed', value: data.failed },
    { name: 'Pending', value: data.pending },
  ].filter((d) => d.value > 0);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={80}
          dataKey="value"
          strokeWidth={2}
          stroke="#ffffff"
        >
          {chartData.map((entry) => (
            <Cell
              key={entry.name}
              fill={COLORS[entry.name.toLowerCase() as keyof typeof COLORS] || '#d9d9d9'}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ fontSize: 12, border: '1px solid #e8e8e8', borderRadius: 4, boxShadow: 'none' }}
        />
        <Legend
          verticalAlign="bottom"
          height={28}
          formatter={(value) => <span style={{ fontSize: 12, color: '#666666' }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
