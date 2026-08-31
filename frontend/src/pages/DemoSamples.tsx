import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, Button, Spin, Modal, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { fetchDemoSamples, loadDemoSamples, clearDemoSamples } from '@/api/dashboard';
import type { DemoSample } from '@/api/dashboard';
import { deleteSession } from '@/api/sessions';
import PageHeader from '@/components/common/PageHeader';
import StatusTag from '@/components/common/StatusTag';

export default function DemoSamples() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [messageApi, contextHolder] = message.useMessage();

  const { data, isLoading } = useQuery({
    queryKey: ['demo-samples'],
    queryFn: fetchDemoSamples,
  });

  const loadMutation = useMutation({
    mutationFn: loadDemoSamples,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['demo-samples'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-recent'] });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['instruments'] });
      messageApi.success(`Loaded ${result.count} demo samples`);
    },
    onError: () => messageApi.error('Failed to load demo samples'),
  });

  const clearMutation = useMutation({
    mutationFn: clearDemoSamples,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['demo-samples'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['instruments'] });
      messageApi.success('Demo samples cleared');
    },
    onError: () => messageApi.error('Failed to clear demo samples'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['demo-samples'] });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      messageApi.success('Session deleted');
    },
    onError: () => messageApi.error('Failed to delete session'),
  });

  const handleDelete = (id: number, name: string) => {
    Modal.confirm({
      title: 'Delete test session?',
      content: `This will delete the session for "${name}". This action cannot be undone.`,
      okText: 'Delete',
      okType: 'danger',
      onOk: () => deleteMutation.mutateAsync(id),
    });
  };

  const handleClear = () => {
    Modal.confirm({
      title: 'Clear all demo samples?',
      content: 'This will permanently delete all demo instruments and their test sessions.',
      okText: 'Clear all',
      okType: 'danger',
      onOk: () => clearMutation.mutateAsync(),
    });
  };

  const samples = data?.samples ?? [];
  const passCount = samples.filter((s) => s.overall_verdict === 'pass').length;
  const failCount = samples.filter((s) => s.overall_verdict === 'fail').length;

  const columns: ColumnsType<DemoSample> = [
    {
      title: '#',
      key: 'index',
      width: 50,
      render: (_, __, i) => i + 1,
    },
    {
      title: 'Instrument',
      dataIndex: 'instrument_name',
      key: 'instrument',
    },
    {
      title: 'Serial',
      dataIndex: 'serial_number',
      key: 'serial',
      width: 120,
    },
    {
      title: 'Class',
      dataIndex: 'accuracy_class',
      key: 'class',
      width: 70,
    },
    {
      title: 'Date',
      dataIndex: 'session_date',
      key: 'date',
      width: 110,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 110,
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
      width: 140,
      render: (_, record) => (
        <div style={{ display: 'flex', gap: 8 }} onClick={(e) => e.stopPropagation()}>
          <Button size="small" onClick={() => navigate(`/sessions/${record.id}`)}>
            View
          </Button>
          <Button size="small" danger onClick={() => handleDelete(record.id, record.instrument_name)}>
            Delete
          </Button>
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>;
  }

  return (
    <div>
      {contextHolder}
      <PageHeader
        title="Demo Samples"
        extra={
          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              type="primary"
              loading={loadMutation.isPending}
              onClick={() => loadMutation.mutate()}
            >
              Load 20 demo samples
            </Button>
            {samples.length > 0 && (
              <Button
                danger
                loading={clearMutation.isPending}
                onClick={handleClear}
              >
                Clear all
              </Button>
            )}
          </div>
        }
      />

      {samples.length > 0 && (
        <div style={{ marginBottom: 16, fontSize: 14, color: '#666666' }}>
          {samples.length} samples — <span style={{ color: '#389e0d' }}>{passCount} pass</span>
          {' / '}
          <span style={{ color: '#cf1322' }}>{failCount} fail</span>
        </div>
      )}

      {samples.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#999999', fontSize: 14 }}>
          No demo samples loaded yet. Click "Load 20 demo samples" to generate test data.
        </div>
      ) : (
        <Table
          dataSource={samples}
          columns={columns}
          rowKey="id"
          size="small"
          bordered={false}
          pagination={false}
          onRow={(record) => ({
            onClick: () => navigate(`/sessions/${record.id}`),
            style: { cursor: 'pointer' },
          })}
          rowClassName={(_, i) => (i % 2 === 1 ? 'alt-row' : '')}
        />
      )}
    </div>
  );
}
