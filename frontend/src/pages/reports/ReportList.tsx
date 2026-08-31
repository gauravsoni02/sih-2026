import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Table, Select } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { fetchReports } from '@/api/reports';
import PageHeader from '@/components/common/PageHeader';
import StatusTag from '@/components/common/StatusTag';
import type { Report } from '@/types/report';

export default function ReportList() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['reports', page, statusFilter],
    queryFn: () => fetchReports({
      page: String(page),
      ordering: '-created_at',
      ...(statusFilter ? { status: statusFilter } : {}),
    }),
  });

  const columns: ColumnsType<Report> = [
    { title: 'Report number', dataIndex: 'report_number', key: 'number', width: 240 },
    { title: 'Version', dataIndex: 'version', key: 'version', width: 80, align: 'right' },
    { title: 'Verdict', dataIndex: 'overall_verdict', key: 'verdict', width: 100,
      render: (v: string) => <StatusTag status={v} /> },
    { title: 'Status', dataIndex: 'status', key: 'status', width: 100,
      render: (s: string) => <StatusTag status={s} /> },
    { title: 'Created', dataIndex: 'created_at', key: 'created', width: 120,
      render: (d: string) => d?.slice(0, 10) },
  ];

  return (
    <div>
      <PageHeader title="Reports" />
      <div style={{ marginBottom: 16 }}>
        <Select
          placeholder="Filter by status"
          allowClear
          style={{ width: 160 }}
          options={[
            { value: 'draft', label: 'Draft' },
            { value: 'approved', label: 'Approved' },
          ]}
          onChange={(v) => { setStatusFilter(v || ''); setPage(1); }}
        />
      </div>
      <Table
        dataSource={data?.results ?? []}
        columns={columns}
        rowKey="id"
        size="small"
        loading={isLoading}
        bordered={false}
        onRow={(r) => ({ onClick: () => navigate(`/reports/${r.id}`), style: { cursor: 'pointer' } })}
        pagination={{
          current: page,
          total: data?.count ?? 0,
          pageSize: 20,
          showSizeChanger: false,
          onChange: setPage,
        }}
        rowClassName={(_, i) => (i % 2 === 1 ? 'alt-row' : '')}
      />
    </div>
  );
}
