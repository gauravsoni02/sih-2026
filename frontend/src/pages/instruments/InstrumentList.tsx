import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Table, Button, Select, Input, Modal, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { PlusOutlined } from '@ant-design/icons';
import { fetchInstruments, deleteInstrument } from '@/api/instruments';
import PageHeader from '@/components/common/PageHeader';
import StatusTag from '@/components/common/StatusTag';
import EmptyState from '@/components/common/EmptyState';
import type { Instrument } from '@/types/instrument';

export default function InstrumentList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [messageApi, contextHolder] = message.useMessage();

  const { data, isLoading } = useQuery({
    queryKey: ['instruments', page, filters],
    queryFn: () => fetchInstruments({ page: String(page), ...filters }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteInstrument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instruments'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      messageApi.success('Instrument deleted');
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      messageApi.error(detail || 'Failed to delete instrument');
    },
  });

  const handleDelete = (id: number, name: string, e: React.MouseEvent) => {
    e.stopPropagation();
    Modal.confirm({
      title: 'Delete instrument?',
      content: `This will delete "${name}". This action cannot be undone.`,
      okText: 'Delete',
      okType: 'danger',
      onOk: () => deleteMutation.mutateAsync(id),
    });
  };

  const columns: ColumnsType<Instrument> = [
    { title: 'Serial', dataIndex: 'serial_number', key: 'serial', width: 140 },
    { title: 'Manufacturer', dataIndex: 'manufacturer', key: 'manufacturer' },
    { title: 'Model', dataIndex: 'model_name', key: 'model' },
    { title: 'Class', dataIndex: 'accuracy_class', key: 'class', width: 70 },
    {
      title: 'Max',
      key: 'max',
      width: 120,
      align: 'right' as const,
      render: (_, r) => (
        <span style={{ fontVariantNumeric: 'tabular-nums' }}>
          {r.max_capacity} {r.unit}
        </span>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <StatusTag status={status} />,
    },
    {
      title: '',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Button
          size="small"
          danger
          onClick={(e) => handleDelete(record.id, `${record.manufacturer} ${record.model_name}`, e)}
        >
          Delete
        </Button>
      ),
    },
  ];

  return (
    <div>
      {contextHolder}
      <PageHeader
        title="Instruments"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/instruments/new')}>
            Register instrument
          </Button>
        }
      />
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <Input.Search
          placeholder="Search manufacturer or serial..."
          allowClear
          style={{ width: 260 }}
          onSearch={(v) => setFilters((f) => ({ ...f, search: v }))}
        />
        <Select
          placeholder="Accuracy class"
          allowClear
          style={{ width: 140 }}
          options={[
            { value: 'I', label: 'Class I' },
            { value: 'II', label: 'Class II' },
            { value: 'III', label: 'Class III' },
            { value: 'IIII', label: 'Class IIII' },
          ]}
          onChange={(v) => setFilters((f) => ({ ...f, accuracy_class: v || '' }))}
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
              message={Object.values(filters).some(Boolean) ? 'No instruments match these filters' : 'No instruments registered yet'}
              hint='Add your first instrument with the "Register instrument" button above'
            />
          ),
        }}
        onRow={(record) => ({ onClick: () => navigate(`/instruments/${record.id}`), style: { cursor: 'pointer' } })}
        pagination={{
          current: page,
          total: data?.count ?? 0,
          pageSize: 20,
          showSizeChanger: false,
          onChange: setPage,
        }}
        rowClassName={(_, index) => (index % 2 === 1 ? 'alt-row' : '')}
      />
    </div>
  );
}
