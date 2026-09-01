import { Button } from 'antd';
import { MenuFoldOutlined, MenuUnfoldOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';
import { useUiStore } from '@/store/uiStore';

export default function Header() {
  const user = useAuthStore((s) => s.user);
  const { sidebarCollapsed, toggleSidebar } = useUiStore();

  return (
    <div style={{
      height: 48,
      borderBottom: '1px solid #e8e8e8',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px 0 12px',
      background: '#fff',
    }}>
      <Button
        type="text"
        aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        onClick={toggleSidebar}
      />
      {user && (
        <span style={{ fontSize: 14, color: '#666666' }}>
          {user.first_name || user.username} — {user.role.replace('_', ' ')}
        </span>
      )}
    </div>
  );
}
