import { useNavigate, useLocation } from 'react-router-dom';
import { Menu } from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  ToolOutlined,
  FileTextOutlined,
  SearchOutlined,
  HistoryOutlined,
  SettingOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';
import { useUiStore } from '@/store/uiStore';

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/instruments', icon: <ToolOutlined />, label: 'Instruments' },
  { key: '/sessions', icon: <ExperimentOutlined />, label: 'Test Sessions' },
  { key: '/reports', icon: <FileTextOutlined />, label: 'Reports' },
  { key: '/reports/search', icon: <SearchOutlined />, label: 'Search' },
  { key: '/activity-log', icon: <HistoryOutlined />, label: 'Activity Log' },
  { key: '/demo-samples', icon: <DatabaseOutlined />, label: 'Demo Samples' },
  { key: '/settings', icon: <SettingOutlined />, label: 'Settings' },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuthStore((s) => s.logout);
  const { sidebarCollapsed, setSidebarCollapsed } = useUiStore();

  const selectedKey = menuItems.find((item) =>
    item.key === '/' ? location.pathname === '/' : location.pathname.startsWith(item.key)
  )?.key || '/';

  return (
    <div
      style={{
        width: sidebarCollapsed ? 56 : 200,
        height: '100vh',
        borderRight: '1px solid #e8e8e8',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.15s',
        position: 'fixed',
        left: 0,
        top: 0,
        background: '#fff',
        zIndex: 100,
      }}
      onMouseEnter={() => setSidebarCollapsed(false)}
      onMouseLeave={() => setSidebarCollapsed(true)}
    >
      <div style={{
        height: 48,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderBottom: '1px solid #e8e8e8',
        fontWeight: 600,
        fontSize: 14,
        color: '#1a1a1a',
        overflow: 'hidden',
        whiteSpace: 'nowrap',
      }}>
        {sidebarCollapsed ? 'N' : 'NAWI'}
      </div>
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        inlineCollapsed={sidebarCollapsed}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
        style={{ border: 'none', flex: 1 }}
      />
      <Menu
        mode="inline"
        inlineCollapsed={sidebarCollapsed}
        selectable={false}
        items={[
          {
            key: 'logout',
            icon: <LogoutOutlined />,
            label: 'Logout',
            onClick: () => {
              logout();
              navigate('/login');
            },
          },
        ]}
        style={{ border: 'none', borderTop: '1px solid #e8e8e8' }}
      />
    </div>
  );
}
