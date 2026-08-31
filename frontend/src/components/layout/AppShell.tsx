import { Outlet, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import Sidebar from './Sidebar';
import Header from './Header';
import { useAuth } from '@/hooks/useAuth';
import { useUiStore } from '@/store/uiStore';

export default function AppShell() {
  const { isAuthenticated, isLoading } = useAuth();
  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed);

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <div style={{
        flex: 1,
        marginLeft: sidebarCollapsed ? 56 : 200,
        transition: 'margin-left 0.15s',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <Header />
        <main style={{ flex: 1, padding: '16px 24px', maxWidth: 1100, width: '100%', margin: '0 auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
