import { useAuthStore } from '@/store/authStore';

export default function Header() {
  const user = useAuthStore((s) => s.user);

  return (
    <div style={{
      height: 48,
      borderBottom: '1px solid #e8e8e8',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'flex-end',
      padding: '0 24px',
      background: '#fff',
    }}>
      {user && (
        <span style={{ fontSize: 14, color: '#666666' }}>
          {user.first_name || user.username} — {user.role.replace('_', ' ')}
        </span>
      )}
    </div>
  );
}
