import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Table, Spin, Button } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined,
  ExperimentOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import {
  fetchDashboardStats,
  fetchMonthlyTests,
  fetchRecentSessions,
  fetchPassFailSummary,
  fetchErrorProfile,
} from '@/api/dashboard';
import type { RecentSession } from '@/api/dashboard';
import PageHeader from '@/components/common/PageHeader';
import StatusTag from '@/components/common/StatusTag';
import EmptyState from '@/components/common/EmptyState';
import MetricCard from '@/components/common/MetricCard';
import MeasurementErrorChart from '@/components/charts/MeasurementErrorChart';
import TestingTrendChart from '@/components/charts/TestingTrendChart';
import PassFailPieChart from '@/components/charts/PassFailPieChart';

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: stats, isLoading: statsLoading, isError: statsError, refetch: refetchStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
  });

  const { data: monthly, isLoading: monthlyLoading, isError: monthlyError } = useQuery({
    queryKey: ['dashboard-monthly'],
    queryFn: () => fetchMonthlyTests(),
  });

  const { data: recent, isLoading: recentLoading, isError: recentError } = useQuery({
    queryKey: ['dashboard-recent'],
    queryFn: fetchRecentSessions,
  });

  const { data: passFail, isError: passFailError } = useQuery({
    queryKey: ['dashboard-pass-fail'],
    queryFn: fetchPassFailSummary,
  });

  const { data: errorProfile } = useQuery({
    queryKey: ['dashboard-error-profile'],
    queryFn: () => fetchErrorProfile(),
  });

  if (statsLoading || monthlyLoading || recentLoading) {
    return <div style={{ textAlign: 'center', padding: 64 }}><Spin size="large" /></div>;
  }

  if (statsError) {
    return (
      <div>
        <PageHeader title="Dashboard" />
        <EmptyState
          message="Could not load dashboard data."
          hint="The server may be waking up — this can take up to a minute on free hosting."
          action={<Button type="primary" onClick={() => refetchStats()}>Retry</Button>}
        />
      </div>
    );
  }

  const columns: ColumnsType<RecentSession> = [
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
      title: 'Engineer',
      dataIndex: 'engineer',
      key: 'engineer',
      width: 140,
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
      width: 90,
      render: (v: string | null) => v ? <StatusTag status={v} /> : '—',
    },
  ];

  const instrumentChange = stats ? stats.total_instruments - stats.prev_instruments : undefined;
  const sessionChange = stats ? stats.sessions_this_month - stats.prev_sessions : undefined;
  const reportChange = stats ? stats.reports_generated - stats.prev_reports : undefined;
  const passRateChange = stats ? +(stats.pass_rate - stats.prev_pass_rate).toFixed(1) : undefined;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        extra={
          <div style={{ display: 'flex', gap: 8 }}>
            <Button icon={<ExperimentOutlined />} onClick={() => navigate('/sessions/new')}>
              Start test
            </Button>
            <Button icon={<PlusOutlined />} onClick={() => navigate('/instruments/new')}>
              Register instrument
            </Button>
            <Button icon={<FileTextOutlined />} onClick={() => navigate('/reports')}>
              Review reports
            </Button>
          </div>
        }
      />

      <div style={{ display: 'flex', gap: 24, marginBottom: 32 }}>
        <MetricCard
          label="Total instruments"
          value={stats?.total_instruments ?? 0}
          change={instrumentChange}
          changeLabel="vs last month"
        />
        <MetricCard
          label="Sessions this month"
          value={stats?.sessions_this_month ?? 0}
          change={sessionChange}
          changeLabel="vs last month"
        />
        <MetricCard
          label="Reports generated"
          value={stats?.reports_generated ?? 0}
          change={reportChange}
          changeLabel="vs last month"
        />
        <MetricCard
          label="Pass rate"
          value={stats?.pass_rate ?? 0}
          suffix="%"
          change={passRateChange}
          changeLabel="pp vs last month"
        />
      </div>

      {!(monthlyError && passFailError) && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, marginBottom: 32 }}>
          {!monthlyError && monthly && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: '#1a1a1a', marginBottom: 16 }}>Testing trends</h2>
              <TestingTrendChart data={monthly.slice(-6)} />
            </div>
          )}
          {!passFailError && passFail && (
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 600, color: '#1a1a1a', marginBottom: 16 }}>This month</h2>
              <PassFailPieChart data={passFail} />
            </div>
          )}
        </div>
      )}

      {errorProfile && errorProfile.points.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: '#1a1a1a', marginBottom: 4 }}>
            Measurement error profile
          </h2>
          <div style={{ fontSize: 12, color: '#999999', marginBottom: 12 }}>
            {errorProfile.instrument?.name} ({errorProfile.instrument?.serial_number}) — {errorProfile.session_date}
          </div>
          <MeasurementErrorChart
            data={errorProfile.points}
            unit={errorProfile.instrument?.unit ?? 'g'}
            height={280}
          />
        </div>
      )}

      {!recentError && (
        <>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: '#1a1a1a', marginBottom: 16 }}>Recent sessions</h2>
          <Table
            dataSource={recent ?? []}
            columns={columns}
            rowKey="id"
            size="small"
            pagination={false}
            bordered={false}
            scroll={{ x: 'max-content' }}
            onRow={(record) => ({
              onClick: () => navigate(`/sessions/${record.id}`),
              style: { cursor: 'pointer' },
            })}
          />
        </>
      )}
    </div>
  );
}
