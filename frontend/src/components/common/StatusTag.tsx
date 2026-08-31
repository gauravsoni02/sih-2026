interface StatusTagProps {
  status: string;
}

const COLOR_MAP: Record<string, string> = {
  draft: '#999999',
  in_progress: '#1677ff',
  completed: '#389e0d',
  approved: '#389e0d',
  pass: '#389e0d',
  fail: '#cf1322',
  not_applicable: '#999999',
  active: '#389e0d',
  inactive: '#999999',
  under_test: '#1677ff',
  condemned: '#cf1322',
  due_soon: '#d97706',
  attention: '#d97706',
  archived: '#999999',
  online: '#389e0d',
  offline: '#cf1322',
  syncing: '#1677ff',
  awaiting_review: '#d97706',
  signed: '#389e0d',
  generated: '#1677ff',
  warning: '#d97706',
  pending: '#d97706',
};

const LABEL_MAP: Record<string, string> = {
  draft: 'Draft',
  in_progress: 'In Progress',
  completed: 'Completed',
  approved: 'Approved',
  pass: 'Pass',
  fail: 'Fail',
  not_applicable: 'N/A',
  active: 'Active',
  inactive: 'Inactive',
  under_test: 'Under Test',
  condemned: 'Condemned',
  due_soon: 'Due Soon',
  attention: 'Attention',
  archived: 'Archived',
  online: 'Online',
  offline: 'Offline',
  syncing: 'Syncing',
  awaiting_review: 'Awaiting Review',
  signed: 'Signed',
  generated: 'Generated',
  warning: 'Warning',
  pending: 'Pending',
};

export default function StatusTag({ status }: StatusTagProps) {
  return (
    <span style={{
      color: COLOR_MAP[status] || '#999999',
      fontWeight: 500,
      fontSize: 14,
    }}>
      {LABEL_MAP[status] || status}
    </span>
  );
}
