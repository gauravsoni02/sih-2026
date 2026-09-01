import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import AppShell from '@/components/layout/AppShell';
import Login from '@/pages/Login';
import { loadStandardConfig } from '@/utils/mpe';
import Dashboard from '@/pages/Dashboard';
import InstrumentList from '@/pages/instruments/InstrumentList';
import InstrumentDetail from '@/pages/instruments/InstrumentDetail';
import InstrumentCreate from '@/pages/instruments/InstrumentCreate';
import SessionList from '@/pages/testing/SessionList';
import SessionCreate from '@/pages/testing/SessionCreate';
import SessionDetail from '@/pages/testing/SessionDetail';
import ReportList from '@/pages/reports/ReportList';
import ReportDetail from '@/pages/reports/ReportDetail';
import ReportSearch from '@/pages/reports/ReportSearch';
import DemoSamples from '@/pages/DemoSamples';
import ActivityLog from '@/pages/ActivityLog';
import Settings from '@/pages/Settings';
import VerifyCertificate from '@/pages/VerifyCertificate';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

const theme = {
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 4,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  components: {
    Table: {
      headerBg: '#ffffff',
      headerColor: '#666666',
      headerSplitColor: '#e8e8e8',
      rowHoverBg: '#fafafa',
      borderColor: '#f0f0f0',
    },
    Menu: {
      itemBg: '#ffffff',
      subMenuItemBg: '#ffffff',
    },
  },
};

export default function App() {
  useEffect(() => { loadStandardConfig(); }, []);
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={theme}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/verify/:code" element={<VerifyCertificate />} />
            <Route element={<AppShell />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/instruments" element={<InstrumentList />} />
              <Route path="/instruments/new" element={<InstrumentCreate />} />
              <Route path="/instruments/:id" element={<InstrumentDetail />} />
              <Route path="/sessions" element={<SessionList />} />
              <Route path="/sessions/new" element={<SessionCreate />} />
              <Route path="/sessions/:id" element={<SessionDetail />} />
              <Route path="/reports" element={<ReportList />} />
              <Route path="/reports/search" element={<ReportSearch />} />
              <Route path="/reports/:id" element={<ReportDetail />} />
              <Route path="/activity-log" element={<ActivityLog />} />
              <Route path="/demo-samples" element={<DemoSamples />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  );
}
