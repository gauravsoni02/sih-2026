import { useEffect, useRef, useState } from 'react';
import { Button, Select, Tag, message } from 'antd';
import { ApiOutlined, DisconnectOutlined, AimOutlined } from '@ant-design/icons';
import {
  isWebSerialSupported,
  SimulatedSource,
  WebSerialSource,
} from '@/services/readingSource';
import type { Reading, ReadingSource, SourceKind, SourceState } from '@/services/readingSource';

interface Props {
  unit: string;
  scaleInterval: number;
  // Target load for the simulator (the reference load of the row being filled).
  targetLoad?: number;
  captureHint?: string;
  onCapture: (value: string) => void;
}

export default function DeviceCapturePanel({
  unit,
  scaleInterval,
  targetLoad,
  captureHint,
  onCapture,
}: Props) {
  const [kind, setKind] = useState<SourceKind>('simulator');
  const [state, setState] = useState<SourceState>('disconnected');
  const [reading, setReading] = useState<Reading | null>(null);
  const sourceRef = useRef<ReadingSource | null>(null);

  useEffect(() => {
    return () => {
      void sourceRef.current?.disconnect();
    };
  }, []);

  useEffect(() => {
    const src = sourceRef.current;
    if (src instanceof SimulatedSource && state === 'connected') {
      src.setTarget(targetLoad ?? 0, scaleInterval);
    }
  }, [targetLoad, scaleInterval, state]);

  const connect = async () => {
    const src: ReadingSource =
      kind === 'serial' ? new WebSerialSource() : new SimulatedSource();
    sourceRef.current = src;
    src.onState(setState);
    src.onReading(setReading);
    try {
      await src.connect();
      if (src instanceof SimulatedSource) {
        src.setTarget(targetLoad ?? 0, scaleInterval);
      }
    } catch {
      message.error('Could not connect to the device');
    }
  };

  const disconnect = async () => {
    await sourceRef.current?.disconnect();
    sourceRef.current = null;
    setReading(null);
  };

  const capture = () => {
    if (reading) onCapture(String(reading.value));
  };

  const connected = state === 'connected';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        flexWrap: 'wrap',
        padding: '10px 14px',
        background: '#fafafa',
        border: '1px solid #e8e8e8',
        borderRadius: 6,
        marginBottom: 16,
      }}
    >
      <Select
        value={kind}
        size="small"
        style={{ width: 170 }}
        disabled={connected || state === 'connecting'}
        onChange={(v: SourceKind) => setKind(v)}
        options={[
          { value: 'simulator', label: 'Demo balance (simulated)' },
          {
            value: 'serial',
            label: 'USB device (Web Serial)',
            disabled: !isWebSerialSupported(),
          },
        ]}
      />
      {connected ? (
        <Button size="small" icon={<DisconnectOutlined />} onClick={disconnect}>
          Disconnect
        </Button>
      ) : (
        <Button
          size="small"
          type="primary"
          icon={<ApiOutlined />}
          loading={state === 'connecting'}
          onClick={connect}
        >
          Connect
        </Button>
      )}

      {connected && (
        <>
          <div
            style={{
              fontFamily: 'ui-monospace, Consolas, monospace',
              fontSize: 22,
              fontWeight: 600,
              fontVariantNumeric: 'tabular-nums',
              minWidth: 140,
              textAlign: 'right',
              color: reading?.stable ? '#1a1a1a' : '#999',
            }}
          >
            {reading ? `${reading.value} ${unit}` : '—'}
          </div>
          <Tag color={reading?.stable ? 'green' : 'orange'} style={{ margin: 0 }}>
            {reading?.stable ? 'STABLE' : 'SETTLING'}
          </Tag>
          <Button
            size="small"
            icon={<AimOutlined />}
            disabled={!reading?.stable}
            onClick={capture}
          >
            Capture reading
          </Button>
          {captureHint && (
            <span style={{ fontSize: 12, color: '#888' }}>{captureHint}</span>
          )}
        </>
      )}
      {state === 'error' && (
        <Tag color="red" style={{ margin: 0 }}>
          Connection error
        </Tag>
      )}
    </div>
  );
}
