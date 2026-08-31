import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Table, Input, Select, DatePicker, Spin, Button } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { searchReports } from '@/api/reports';
import type { SearchResult } from '@/api/reports';
import PageHeader from '@/components/common/PageHeader';
import StatusTag from '@/components/common/StatusTag';

const { RangePicker } = DatePicker;

export default function ReportSearch() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [accuracyClass, setAccuracyClass] = useState<string | undefined>();
  const [verdict, setVerdict] = useState<string | undefined>();
  const [manufacturer, setManufacturer] = useState('');
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);
  const [searchParams, setSearchParams] = useState<Record<string, string>>({});

  const { data, isLoading } = useQuery({
    queryKey: ['report-search', searchParams],
    queryFn: () => searchReports(searchParams),
  });

  const handleSearch = () => {
    const params: Record<string, string> = {};
    if (query.trim()) params.q = query.trim();
    if (accuracyClass) params.accuracy_class = accuracyClass;
    if (verdict) params.verdict = verdict;
    if (manufacturer.trim()) params.manufacturer = manufacturer.trim();
    if (dateRange) {
      params.date_from = dateRange[0];
      params.date_to = dateRange[1];
    }
    setSearchParams(params);
  };

  const handleReset = () => {
    setQuery('');
    setAccuracyClass(undefined);
    setVerdict(undefined);
    setManufacturer('');
    setDateRange(null);
    setSearchParams({});
  };

  const columns: ColumnsType<SearchResult> = [
    {
      title: 'Report No.',
      dataIndex: 'report_number',
      key: 'report_number',
      width: 200,
    },
    {
      title: 'Date',
      dataIndex: 'session_date',
      key: 'date',
      width: 110,
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
      width: 140,
    },
    {
      title: 'Class',
      dataIndex: 'accuracy_class',
      key: 'class',
      width: 60,
    },
    {
      title: 'Lab',
      dataIndex: 'laboratory_name',
      key: 'lab',
      width: 160,
    },
    {
      title: 'Verdict',
      dataIndex: 'overall_verdict',
      key: 'verdict',
      width: 90,
      render: (v: string) => <StatusTag status={v} />,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (s: string) => <StatusTag status={s} />,
    },
  ];

  return (
    <div>
      <PageHeader title="Search Reports" />

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24, alignItems: 'flex-end' }}>
        <div>
          <div style={{ fontSize: 12, color: '#999999', marginBottom: 4 }}>Search</div>
          <Input
            placeholder="Report number, manufacturer, serial..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 260 }}
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: '#999999', marginBottom: 4 }}>Accuracy class</div>
          <Select
            placeholder="Any"
            allowClear
            value={accuracyClass}
            onChange={setAccuracyClass}
            style={{ width: 100 }}
            options={[
              { value: 'I', label: 'I' },
              { value: 'II', label: 'II' },
              { value: 'III', label: 'III' },
              { value: 'IIII', label: 'IIII' },
            ]}
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: '#999999', marginBottom: 4 }}>Verdict</div>
          <Select
            placeholder="Any"
            allowClear
            value={verdict}
            onChange={setVerdict}
            style={{ width: 120 }}
            options={[
              { value: 'pass', label: 'Pass' },
              { value: 'fail', label: 'Fail' },
            ]}
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: '#999999', marginBottom: 4 }}>Manufacturer</div>
          <Input
            placeholder="e.g. Mettler"
            value={manufacturer}
            onChange={(e) => setManufacturer(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 160 }}
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: '#999999', marginBottom: 4 }}>Date range</div>
          <RangePicker
            onChange={(_, dateStrings) => {
              if (dateStrings[0] && dateStrings[1]) {
                setDateRange([dateStrings[0], dateStrings[1]]);
              } else {
                setDateRange(null);
              }
            }}
            style={{ width: 240 }}
          />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button type="primary" onClick={handleSearch}>Search</Button>
          <Button onClick={handleReset}>Reset</Button>
        </div>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>
      ) : (
        <>
          <div style={{ fontSize: 12, color: '#999999', marginBottom: 12 }}>
            {data?.count ?? 0} result{data?.count !== 1 ? 's' : ''}
          </div>
          <Table
            dataSource={data?.results ?? []}
            columns={columns}
            rowKey="id"
            size="small"
            pagination={false}
            bordered={false}
            onRow={(record) => ({
              onClick: () => navigate(`/reports/${record.id}`),
              style: { cursor: 'pointer' },
            })}
          />
        </>
      )}
    </div>
  );
}
