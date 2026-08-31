import { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  extra?: ReactNode;
}

export default function PageHeader({ title, extra }: PageHeaderProps) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 24,
    }}>
      <h1 style={{ fontSize: 20, fontWeight: 600, color: '#1a1a1a', margin: 0 }}>{title}</h1>
      {extra && <div>{extra}</div>}
    </div>
  );
}
