import { useState } from 'react';
import { Input, Select, Button, message } from 'antd';
import { useAuthStore } from '@/store/authStore';
import PageHeader from '@/components/common/PageHeader';

const TABS = [
  { key: 'profile', label: 'Profile' },
  { key: 'laboratory', label: 'Laboratory' },
  { key: 'preferences', label: 'Preferences' },
  { key: 'report', label: 'Report Settings' },
  { key: 'connections', label: 'Connections' },
  { key: 'about', label: 'About' },
];

function SectionHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: '#1a1a1a' }}>{title}</div>
      {description && <div style={{ fontSize: 12, color: '#999999', marginTop: 2 }}>{description}</div>}
    </div>
  );
}

function FieldGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display: 'block', fontSize: 13, color: '#666666', marginBottom: 4 }}>{label}</label>
      {children}
    </div>
  );
}

function ProfileTab() {
  const user = useAuthStore((s) => s.user);
  return (
    <div>
      <SectionHeader title="Personal information" description="Your identity as it appears on reports" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, maxWidth: 600 }}>
        <FieldGroup label="Full name">
          <Input defaultValue={user ? `${user.first_name} ${user.last_name}`.trim() || user.username : ''} readOnly />
        </FieldGroup>
        <FieldGroup label="Role">
          <Input defaultValue={user?.role || ''} readOnly />
        </FieldGroup>
        <FieldGroup label="Email">
          <Input defaultValue={user?.email || ''} readOnly />
        </FieldGroup>
        <FieldGroup label="Officer ID">
          <Input defaultValue={user?.username || ''} readOnly />
        </FieldGroup>
      </div>
    </div>
  );
}

function LaboratoryTab() {
  return (
    <div>
      <SectionHeader title="Laboratory details" description="Information about your testing facility" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, maxWidth: 600 }}>
        <FieldGroup label="Laboratory name">
          <Input placeholder="Legal Metrology Laboratory" />
        </FieldGroup>
        <FieldGroup label="Jurisdiction">
          <Input placeholder="State / District" />
        </FieldGroup>
        <FieldGroup label="Address">
          <Input placeholder="Full address" />
        </FieldGroup>
        <FieldGroup label="Report prefix">
          <Input placeholder="NAWI" />
        </FieldGroup>
      </div>
    </div>
  );
}

function PreferencesTab() {
  return (
    <div>
      <SectionHeader title="Testing defaults" description="Default values for new test sessions" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, maxWidth: 600 }}>
        <FieldGroup label="Default unit">
          <Select
            defaultValue="kg"
            style={{ width: '100%' }}
            options={[
              { value: 'mg', label: 'Milligram (mg)' },
              { value: 'g', label: 'Gram (g)' },
              { value: 'kg', label: 'Kilogram (kg)' },
              { value: 't', label: 'Tonne (t)' },
              { value: 'ct', label: 'Metric Carat (ct)' },
            ]}
          />
        </FieldGroup>
        <FieldGroup label="Stabilization period (s)">
          <Input type="number" defaultValue="30" />
        </FieldGroup>
        <FieldGroup label="Default accuracy class">
          <Select
            defaultValue="III"
            style={{ width: '100%' }}
            options={[
              { value: 'I', label: 'Class I (Special)' },
              { value: 'II', label: 'Class II (High)' },
              { value: 'III', label: 'Class III (Medium)' },
              { value: 'IIII', label: 'Class IIII (Ordinary)' },
            ]}
          />
        </FieldGroup>
        <FieldGroup label="Default evaluation type">
          <Select
            defaultValue="initial_verification"
            style={{ width: '100%' }}
            options={[
              { value: 'type_evaluation', label: 'Type Evaluation' },
              { value: 'initial_verification', label: 'Initial Verification' },
              { value: 'subsequent_verification', label: 'Subsequent Verification' },
            ]}
          />
        </FieldGroup>
      </div>
    </div>
  );
}

function ReportSettingsTab() {
  return (
    <div>
      <SectionHeader title="Report configuration" description="Control report numbering and format" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, maxWidth: 600 }}>
        <FieldGroup label="Number pattern">
          <Input defaultValue="NAWI/{lab_code}/{YYYY}/{NNNN}" readOnly />
        </FieldGroup>
        <FieldGroup label="Default review status">
          <Select
            defaultValue="draft"
            style={{ width: '100%' }}
            options={[
              { value: 'draft', label: 'Draft' },
              { value: 'approved', label: 'Auto-approve' },
            ]}
          />
        </FieldGroup>
        <FieldGroup label="Signature placement">
          <Select
            defaultValue="bottom"
            style={{ width: '100%' }}
            options={[
              { value: 'bottom', label: 'Bottom of report' },
              { value: 'per_page', label: 'Each page' },
            ]}
          />
        </FieldGroup>
        <FieldGroup label="Retention note">
          <Input placeholder="Records retained for 5 years" />
        </FieldGroup>
      </div>
    </div>
  );
}

function ConnectionsTab() {
  const serialSupported = typeof navigator !== 'undefined' && 'serial' in navigator;

  return (
    <div>
      <SectionHeader title="System connections" description="API and device configuration" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, maxWidth: 600 }}>
        <FieldGroup label="API URL">
          <Input defaultValue={window.location.origin + '/api'} readOnly />
        </FieldGroup>
        <FieldGroup label="Serial baud rate">
          <Select
            defaultValue="9600"
            style={{ width: '100%' }}
            options={[
              { value: '2400', label: '2400' },
              { value: '4800', label: '4800' },
              { value: '9600', label: '9600' },
              { value: '19200', label: '19200' },
              { value: '38400', label: '38400' },
              { value: '115200', label: '115200' },
            ]}
          />
        </FieldGroup>
      </div>
      <div style={{ marginTop: 16, display: 'flex', gap: 24 }}>
        <div style={{ fontSize: 13 }}>
          <span style={{ color: '#666666' }}>API: </span>
          <span style={{ color: '#389e0d', fontWeight: 500 }}>Online</span>
        </div>
        <div style={{ fontSize: 13 }}>
          <span style={{ color: '#666666' }}>Web Serial: </span>
          <span style={{ color: serialSupported ? '#389e0d' : '#cf1322', fontWeight: 500 }}>
            {serialSupported ? 'Supported' : 'Not supported'}
          </span>
        </div>
      </div>
    </div>
  );
}

function AboutTab() {
  return (
    <div>
      <SectionHeader title="About" description="Application information" />
      <div style={{ maxWidth: 400 }}>
        {[
          ['Application', 'NAWI Test Report Generator'],
          ['Version', '0.2.0'],
          ['Standard', 'OIML R 76-1:2006'],
          ['Tech stack', 'Django + React + TypeScript'],
          ['Database', 'PostgreSQL'],
        ].map(([label, value]) => (
          <div key={label} style={{ display: 'flex', padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
            <div style={{ width: 160, color: '#666666', fontSize: 13 }}>{label}</div>
            <div style={{ fontSize: 13, color: '#1a1a1a' }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

const TAB_CONTENT: Record<string, React.FC> = {
  profile: ProfileTab,
  laboratory: LaboratoryTab,
  preferences: PreferencesTab,
  report: ReportSettingsTab,
  connections: ConnectionsTab,
  about: AboutTab,
};

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile');
  const [messageApi, contextHolder] = message.useMessage();

  const ActiveComponent = TAB_CONTENT[activeTab] || ProfileTab;

  const handleSave = () => {
    messageApi.success('Preferences saved');
  };

  return (
    <div>
      {contextHolder}
      <PageHeader
        title="Settings"
        extra={
          <Button type="primary" onClick={handleSave}>Save preferences</Button>
        }
      />

      <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: 32 }}>
        <div style={{ borderRight: '1px solid #e8e8e8', paddingRight: 16 }}>
          {TABS.map((tab) => (
            <div
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '8px 12px',
                fontSize: 13,
                color: activeTab === tab.key ? '#1677ff' : '#666666',
                fontWeight: activeTab === tab.key ? 500 : 400,
                cursor: 'pointer',
                borderRadius: 4,
                background: activeTab === tab.key ? '#f0f5ff' : 'transparent',
                marginBottom: 2,
              }}
            >
              {tab.label}
            </div>
          ))}
        </div>
        <div>
          <ActiveComponent />
        </div>
      </div>
    </div>
  );
}
