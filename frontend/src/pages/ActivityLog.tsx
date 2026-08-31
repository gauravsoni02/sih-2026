import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Table, Input, Select, Spin } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { fetchAuditLog } from '@/api/dashboard';
import type { AuditLogEntry } from '@/api/dashboard';
import PageHeader from '@/components/common/PageHeader';

const ACTION_COLORS: Record<string, string> = {
  Created: '#389e0d',
  Updated: '#1677ff',
  Deleted: '#cf1322',
};

const SEVERITY_MAP: Record<string, { label: string; color: string }> = {
  info: { label: 'Info', color: '#1677ff' },
  warning: { label: 'Warning', color: '#d97706' },
  critical: { label: 'Critical', color: '#cf1322' },
};

function getSeverity(entry: AuditLogEntry): string {
  if (entry.action === 'Deleted') return 'critical';
  if (entry.action === 'Updated') return 'warning';
  return 'info';
}

export default function ActivityLog() {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  const { data: auditLog, isLoading } = useQuery({
    queryKey: ['audit-log-full'],
    queryFn: () => fetchAuditLog(200),
  });

  const filtered = (auditLog ?? []).filter((entry) => {
    const severity = getSeverity(entry);
    if (severityFilter !== 'all' && severity !== severityFilter) return false;

    if (search) {
      const q = search.toLowerCase();
      const searchable = [
        entry.action,
        entry.model,
        entry.object_label,
        entry.user ?? '',
      ].join(' ').toLowerCase();
      if (!searchable.includes(q)) return false;
    }

    return true;
  });

  const columns: ColumnsType<AuditLogEntry> = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (ts: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: 12, color: '#666666' }}>
          {new Date(ts).toLocaleString()}
        </span>
      ),
    },
    {
      title: 'Severity',
      key: 'severity',
      width: 90,
      render: (_: unknown, record: AuditLogEntry) => {
        const severity = getSeverity(record);
        const info = SEVERITY_MAP[severity];
        return (
          <span style={{
            fontSize: 12,
            fontWeight: 500,
            color: info.color,
          }}>
            {info.label}
          </span>
        );
      },
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
      width: 140,
      render: (u: string | null) => u ?? '—',
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      width: 80,
      render: (a: string) => (
        <span style={{ color: ACTION_COLORS[a] || '#1a1a1a', fontWeight: 500 }}>{a}</span>
      ),
    },
    {
      title: 'Entity',
      dataIndex: 'model',
      key: 'model',
      width: 120,
    },
    {
      title: 'Object',
      dataIndex: 'object_label',
      key: 'object',
    },
  ];

  if (isLoading) {
    return <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>;
  }

  return (
    <div>
      <PageHeader title="Activity log" />

      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Input.Search
          placeholder="Search by user, action, entity, object..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          style={{ maxWidth: 400 }}
        />
        <Select
          value={severityFilter}
          onChange={setSeverityFilter}
          style={{ width: 140 }}
          options={[
            { value: 'all', label: 'All severities' },
            { value: 'info', label: 'Info' },
            { value: 'warning', label: 'Warning' },
            { value: 'critical', label: 'Critical' },
          ]}
        />
      </div>

      <Table
        dataSource={filtered}
        columns={columns}
        rowKey="id"
        size="small"
        pagination={{ pageSize: 50, showSizeChanger: false, simple: true }}
        bordered={false}
        rowClassName={(_, i) => (i % 2 === 1 ? 'alt-row' : '')}
      />
    </div>
  );
}
