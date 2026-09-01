import type { ReactNode } from 'react';

interface EmptyStateProps {
  message: string;
  hint?: string;
  action?: ReactNode;
}

export default function EmptyState({ message, hint, action }: EmptyStateProps) {
  return (
    <div style={{
      textAlign: 'center',
      padding: '64px 0',
      color: '#999999',
      fontSize: 14,
    }}>
      <div>{message}</div>
      {hint && <div style={{ fontSize: 12, marginTop: 8, color: '#bbbbbb' }}>{hint}</div>}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}
