import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';

interface MetricCardProps {
  label: string;
  value: number | string;
  suffix?: string;
  change?: number;
  changeLabel?: string;
}

export default function MetricCard({ label, value, suffix, change, changeLabel }: MetricCardProps) {
  let trendColor = '#999999';
  let TrendIcon = MinusOutlined;
  if (change !== undefined && change > 0) {
    trendColor = '#389e0d';
    TrendIcon = ArrowUpOutlined;
  } else if (change !== undefined && change < 0) {
    trendColor = '#cf1322';
    TrendIcon = ArrowDownOutlined;
  }

  return (
    <div style={{ minWidth: 160, flex: 1 }}>
      <div style={{ fontSize: 12, color: '#999999', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>
        {label}
      </div>
      <div style={{ fontSize: 28, fontWeight: 600, color: '#1a1a1a', fontVariantNumeric: 'tabular-nums' }}>
        {value}
        {suffix && <span style={{ fontSize: 14, fontWeight: 400, color: '#666666', marginLeft: 2 }}>{suffix}</span>}
      </div>
      {change !== undefined && (
        <div style={{ fontSize: 12, color: trendColor, marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
          <TrendIcon style={{ fontSize: 10 }} />
          <span>{change > 0 ? '+' : ''}{change}</span>
          {changeLabel && <span style={{ color: '#999999' }}>{changeLabel}</span>}
        </div>
      )}
    </div>
  );
}
