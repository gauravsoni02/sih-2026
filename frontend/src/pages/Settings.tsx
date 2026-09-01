import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Input, Select, Button, message, Upload, Spin } from 'antd';
import { UploadOutlined, DeleteOutlined } from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';
import { fetchLaboratories, updateLaboratory } from '@/api/laboratory';
import { fetchOrgSettings, updateOrgSettings } from '@/api/settings';
import type { OrgSettings } from '@/api/settings';
import { loadPrefs, savePrefs } from '@/utils/prefs';
import apiClient from '@/api/client';
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
          <Input value={user ? `${user.first_name} ${user.last_name}`.trim() || user.username : ''} readOnly />
        </FieldGroup>
        <FieldGroup label="Role">
          <Input value={user?.role || ''} readOnly />
        </FieldGroup>
        <FieldGroup label="Email">
          <Input value={user?.email || ''} readOnly />
        </FieldGroup>
        <FieldGroup label="Officer ID">
          <Input value={user?.username || ''} readOnly />
        </FieldGroup>
      </div>
      <p style={{ fontSize: 12, color: '#999' }}>
        Profile details are managed by your administrator.
      </p>
    </div>
  );
}

function LaboratoryTab() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const canEdit = user?.role === 'admin';

  const { data: labs, isLoading } = useQuery({
    queryKey: ['laboratories'],
    queryFn: fetchLaboratories,
  });

  const [selectedLabId, setSelectedLabId] = useState<number | null>(null);
  const [form, setForm] = useState({ name: '', address: '', accreditation_number: '', contact_person: '' });

  const lab = (labs ?? []).find((l) => l.id === (selectedLabId ?? user?.laboratory)) ?? (labs ?? [])[0];

  useEffect(() => {
    if (lab) {
      setForm({
        name: lab.name,
        address: lab.address,
        accreditation_number: lab.accreditation_number,
        contact_person: lab.contact_person,
      });
    }
  }, [lab?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const mutation = useMutation({
    mutationFn: () => updateLaboratory(lab!.id, form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['laboratories'] });
      message.success('Laboratory updated');
    },
    onError: () => message.error('Failed to update laboratory'),
  });

  if (isLoading) return <Spin />;
  if (!lab) return <p style={{ fontSize: 13, color: '#999' }}>No laboratory found.</p>;

  return (
    <div>
      <SectionHeader title="Laboratory details" description="Information printed on certificates" />
      <div style={{ maxWidth: 600 }}>
        <FieldGroup label="Laboratory">
          <Select
            style={{ width: '100%' }}
            value={lab.id}
            onChange={setSelectedLabId}
            options={(labs ?? []).map((l) => ({ value: l.id, label: `${l.name} — ${l.lab_code}` }))}
          />
        </FieldGroup>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <FieldGroup label="Laboratory name">
            <Input value={form.name} disabled={!canEdit}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
          </FieldGroup>
          <FieldGroup label="Accreditation number">
            <Input value={form.accreditation_number} disabled={!canEdit}
              onChange={(e) => setForm((f) => ({ ...f, accreditation_number: e.target.value }))} />
          </FieldGroup>
          <FieldGroup label="Address">
            <Input value={form.address} disabled={!canEdit}
              onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))} />
          </FieldGroup>
          <FieldGroup label="Contact person">
            <Input value={form.contact_person} disabled={!canEdit}
              onChange={(e) => setForm((f) => ({ ...f, contact_person: e.target.value }))} />
          </FieldGroup>
        </div>
        {canEdit ? (
          <Button type="primary" loading={mutation.isPending} onClick={() => mutation.mutate()}>
            Save laboratory
          </Button>
        ) : (
          <p style={{ fontSize: 12, color: '#999' }}>Only administrators can edit laboratory details.</p>
        )}
      </div>
    </div>
  );
}

function PreferencesTab() {
  const [prefs, setPrefs] = useState(loadPrefs);

  const update = (patch: Partial<ReturnType<typeof loadPrefs>>) => {
    setPrefs(savePrefs(patch));
    message.success('Preference saved');
  };

  return (
    <div>
      <SectionHeader
        title="Testing defaults"
        description="Applied automatically when creating new instruments and sessions (saved in this browser)"
      />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, maxWidth: 600 }}>
        <FieldGroup label="Default unit">
          <Select
            value={prefs.defaultUnit}
            style={{ width: '100%' }}
            onChange={(v) => update({ defaultUnit: v })}
            options={[
              { value: 'mg', label: 'Milligram (mg)' },
              { value: 'g', label: 'Gram (g)' },
              { value: 'kg', label: 'Kilogram (kg)' },
              { value: 't', label: 'Tonne (t)' },
              { value: 'ct', label: 'Metric Carat (ct)' },
            ]}
          />
        </FieldGroup>
        <FieldGroup label="Default accuracy class">
          <Select
            value={prefs.defaultAccuracyClass}
            style={{ width: '100%' }}
            onChange={(v) => update({ defaultAccuracyClass: v })}
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
            value={prefs.defaultEvaluationType}
            style={{ width: '100%' }}
            onChange={(v) => update({ defaultEvaluationType: v })}
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
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const canEdit = user?.role === 'admin' || user?.role === 'lab_manager';

  const { data, isLoading } = useQuery({
    queryKey: ['org-settings'],
    queryFn: fetchOrgSettings,
  });

  const [form, setForm] = useState<Partial<OrgSettings>>({});
  const [remarksText, setRemarksText] = useState('');

  useEffect(() => {
    if (data) {
      setForm(data);
      setRemarksText((data.default_remarks ?? []).join('\n'));
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: () =>
      updateOrgSettings({
        ...form,
        default_remarks: remarksText.split('\n').map((r) => r.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['org-settings'] });
      message.success('Report settings saved — applied to newly generated certificates');
    },
    onError: (err: unknown) => {
      const data = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      const first = data ? Object.values(data)[0] : null;
      message.error(Array.isArray(first) ? first[0] : 'Failed to save settings');
    },
  });

  const handleLogoUpload = (file: File) => {
    if (file.size > 300 * 1024) {
      message.error('Logo must be under 300 KB');
      return false;
    }
    const reader = new FileReader();
    reader.onload = () => setForm((f) => ({ ...f, logo_data_uri: reader.result as string }));
    reader.readAsDataURL(file);
    return false; // prevent antd auto-upload
  };

  if (isLoading) return <Spin />;

  return (
    <div>
      <SectionHeader
        title="Certificate configuration"
        description="Branding and document control printed on every generated certificate"
      />
      <div style={{ maxWidth: 600 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <FieldGroup label="Report number prefix">
            <Input value={form.report_prefix ?? ''} disabled={!canEdit}
              onChange={(e) => setForm((f) => ({ ...f, report_prefix: e.target.value }))} />
          </FieldGroup>
          <FieldGroup label="Number pattern (preview)">
            <Input value={`${form.report_prefix || 'NAWI'}/{lab_code}/{YYYY}/{NNNN}`} readOnly />
          </FieldGroup>
          <FieldGroup label="Jurisdiction / department">
            <Input value={form.jurisdiction ?? ''} disabled={!canEdit}
              onChange={(e) => setForm((f) => ({ ...f, jurisdiction: e.target.value }))} />
          </FieldGroup>
          <FieldGroup label="Document control number">
            <Input value={form.doc_control_number ?? ''} disabled={!canEdit}
              onChange={(e) => setForm((f) => ({ ...f, doc_control_number: e.target.value }))} />
          </FieldGroup>
          <FieldGroup label="Issue number">
            <Input value={form.doc_issue_number ?? ''} disabled={!canEdit}
              onChange={(e) => setForm((f) => ({ ...f, doc_issue_number: e.target.value }))} />
          </FieldGroup>
          <FieldGroup label="Revision number">
            <Input value={form.doc_rev_number ?? ''} disabled={!canEdit}
              onChange={(e) => setForm((f) => ({ ...f, doc_rev_number: e.target.value }))} />
          </FieldGroup>
          <FieldGroup label="Document issue date">
            <Input value={form.doc_issue_date ?? ''} disabled={!canEdit} placeholder="01.01.2026"
              onChange={(e) => setForm((f) => ({ ...f, doc_issue_date: e.target.value }))} />
          </FieldGroup>
        </div>

        <FieldGroup label="Laboratory logo (optional, shown top-left on certificates)">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {form.logo_data_uri ? (
              <img src={form.logo_data_uri} alt="Lab logo" style={{ height: 48, border: '1px solid #e8e8e8', borderRadius: 4, padding: 2 }} />
            ) : (
              <span style={{ fontSize: 12, color: '#999' }}>No logo — text-only header is used</span>
            )}
            {canEdit && (
              <>
                <Upload beforeUpload={handleLogoUpload} showUploadList={false} accept="image/png,image/jpeg,image/webp">
                  <Button size="small" icon={<UploadOutlined />}>Upload</Button>
                </Upload>
                {form.logo_data_uri && (
                  <Button size="small" icon={<DeleteOutlined />} onClick={() => setForm((f) => ({ ...f, logo_data_uri: '' }))}>
                    Remove
                  </Button>
                )}
              </>
            )}
          </div>
        </FieldGroup>

        <FieldGroup label="Default remarks (one per line; blank = built-in OIML remarks)">
          <Input.TextArea
            rows={6}
            value={remarksText}
            disabled={!canEdit}
            placeholder="Leave empty to use the 7 standard OIML/NABL remarks"
            onChange={(e) => setRemarksText(e.target.value)}
          />
        </FieldGroup>

        {canEdit ? (
          <Button type="primary" loading={mutation.isPending} onClick={() => mutation.mutate()}>
            Save report settings
          </Button>
        ) : (
          <p style={{ fontSize: 12, color: '#999' }}>Only admins and lab managers can change report settings.</p>
        )}
      </div>
    </div>
  );
}

function ConnectionsTab() {
  const serialSupported = typeof navigator !== 'undefined' && 'serial' in navigator;
  const [prefs, setPrefs] = useState(loadPrefs);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'unreachable'>('checking');

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get('/health/')
      .then(() => { if (!cancelled) setApiStatus('online'); })
      .catch(() => { if (!cancelled) setApiStatus('unreachable'); });
    return () => { cancelled = true; };
  }, []);

  const statusColor =
    apiStatus === 'online' ? '#389e0d' : apiStatus === 'unreachable' ? '#cf1322' : '#d9d9d9';
  const statusLabel =
    apiStatus === 'online' ? 'Online' : apiStatus === 'unreachable' ? 'Unreachable' : 'Checking…';

  return (
    <div>
      <SectionHeader title="System connections" description="API and device configuration" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, maxWidth: 600 }}>
        <FieldGroup label="API URL">
          <Input value={import.meta.env.VITE_API_URL || window.location.origin + '/api'} readOnly />
        </FieldGroup>
        <FieldGroup label="Serial baud rate (used when connecting a USB balance)">
          <Select
            value={String(prefs.serialBaudRate)}
            style={{ width: '100%' }}
            onChange={(v) => {
              setPrefs(savePrefs({ serialBaudRate: parseInt(v, 10) }));
              message.success('Baud rate saved');
            }}
            options={['2400', '4800', '9600', '19200', '38400', '115200'].map((b) => ({ value: b, label: b }))}
          />
        </FieldGroup>
      </div>
      <div style={{ marginTop: 16, display: 'flex', gap: 24 }}>
        <div style={{ fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ color: '#666666' }}>API server: </span>
          <span
            aria-hidden
            style={{
              display: 'inline-block',
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: statusColor,
            }}
          />
          <span style={{ color: statusColor, fontWeight: 500 }}>{statusLabel}</span>
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
          ['Application', '76 Labs'],
          ['Version', __APP_VERSION__],
          ['Standard', 'OIML R 76-1:2006'],
          ['Tech stack', 'Django + React + TypeScript'],
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
  const ActiveComponent = TAB_CONTENT[activeTab] || ProfileTab;

  return (
    <div>
      <PageHeader title="Settings" />
      <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: 32 }}>
        <div role="tablist" aria-label="Settings sections" style={{ borderRight: '1px solid #e8e8e8', paddingRight: 16 }}>
          {TABS.map((tab) => (
            <div
              key={tab.key}
              role="tab"
              tabIndex={0}
              aria-selected={activeTab === tab.key}
              onClick={() => setActiveTab(tab.key)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setActiveTab(tab.key);
                }
              }}
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
