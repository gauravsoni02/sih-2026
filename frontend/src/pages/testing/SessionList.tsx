import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, Button, Select, Modal, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { PlusOutlined } from '@ant-design/icons';
import { fetchSessions, deleteSession } from '@/api/sessions';
import PageHeader from '@/components/common/PageHeader';
import StatusTag from '@/components/common/StatusTag';
import EmptyState from '@/components/common/EmptyState';
import type { TestSession } from '@/types/session';

export default function SessionList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [messageApi, contextHolder] = message.useMessage();

  const { data, isLoading } = useQuery({
    queryKey: ['sessions', page, statusFilter],
    queryFn: () => fetchSessions({
      page: String(page),
      ordering: '-created_at',
      ...(statusFilter ? { status: statusFilter } : {}),
    }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      messageApi.success('Session deleted');
    },
    onError: () => messageApi.error('Failed to delete session'),
  });

  const handleDelete = (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    Modal.confirm({
      title: 'Delete test session?',
      content: 'This will delete the test session. This action cannot be undone.',
      okText: 'Delete',
      okType: 'danger',
      onOk: () => deleteMutation.mutateAsync(id),
    });
  };

  const columns: ColumnsType<TestSession> = [
    { title: 'Date', dataIndex: 'session_date', key: 'date', width: 120 },
    {
      title: 'Instrument',
      key: 'instrument',
      render: (_, r) =>
        r.instrument_detail
          ? `${r.instrument_detail.manufacturer} ${r.instrument_detail.model_name} (${r.instrument_detail.serial_number})`
          : `#${r.instrument}`,
    },
    {
      title: 'Class',
      key: 'class',
      width: 70,
      render: (_, r) => r.instrument_detail?.accuracy_class ?? '—',
    },
    {
      title: 'Evaluation',
      dataIndex: 'evaluation_type',
      key: 'evaluation_type',
      width: 140,
      render: (v: string) => {
        const labels: Record<string, string> = {
          type_evaluation: 'Type Eval',
          initial_verification: 'Initial',
          subsequent_verification: 'Subsequent',
        };
        return labels[v] ?? v ?? '—';
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (s: string) => <StatusTag status={s} />,
    },
    {
      title: 'Verdict',
      dataIndex: 'overall_verdict',
      key: 'verdict',
      width: 100,
      render: (v: string | null) => v ? <StatusTag status={v} /> : '—',
    },
    {
      title: '',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Button size="small" danger onClick={(e) => handleDelete(record.id, e)}>
          Delete
        </Button>
      ),
    },
  ];

  return (
    <div>
      {contextHolder}
      <PageHeader
        title="Test Sessions"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/sessions/new')}>
            New test session
          </Button>
        }
      />
      <div style={{ marginBottom: 16 }}>
        <Select
          placeholder="Filter by status"
          allowClear
          style={{ width: 160 }}
          options={[
            { value: 'draft', label: 'Draft' },
            { value: 'in_progress', label: 'In Progress' },
            { value: 'completed', label: 'Completed' },
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
        scroll={{ x: 'max-content' }}
        locale={{
          emptyText: isLoading ? ' ' : (
            <EmptyState
              message={statusFilter ? 'No test sessions match this filter' : 'No test sessions yet'}
              hint='Start one with the "New test session" button above'
            />
          ),
        }}
        onRow={(r) => ({ onClick: () => navigate(`/sessions/${r.id}`), style: { cursor: 'pointer' } })}
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
