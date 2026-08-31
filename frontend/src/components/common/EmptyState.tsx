interface EmptyStateProps {
  message: string;
}

export default function EmptyState({ message }: EmptyStateProps) {
  return (
    <div style={{
      textAlign: 'center',
      padding: '64px 0',
      color: '#999999',
      fontSize: 14,
    }}>
      {message}
    </div>
  );
}
