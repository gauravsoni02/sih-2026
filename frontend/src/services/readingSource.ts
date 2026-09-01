// Unified reading source for instrument data capture.
// Two implementations: WebSerialSource (real balance over USB serial) and
// SimulatedSource (demo balance for environments without hardware).

export type SourceState = 'disconnected' | 'connecting' | 'connected' | 'error';
export type SourceKind = 'serial' | 'simulator';

export interface Reading {
  value: number;
  stable: boolean;
  raw: string;
  timestamp: number;
}

export interface ReadingSource {
  readonly kind: SourceKind;
  readonly state: SourceState;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  onReading(cb: (r: Reading) => void): () => void;
  onState(cb: (s: SourceState) => void): () => void;
}

export function isWebSerialSupported(): boolean {
  return typeof navigator !== 'undefined' && 'serial' in navigator;
}

// Parses one line of balance output. Handles common protocols:
//   A&D:     "ST,+00123.45  g" / "US,+00123.45  g" (US = unstable)
//   Mettler: "S S    123.45 g" / "S D    123.45 g" (D = dynamic/unstable)
//   Generic: "123.45" or "+123.45 g"
export function parseBalanceLine(line: string): { value: number; stable: boolean } | null {
  const match = line.match(/[-+]?\d+(?:\.\d+)?/);
  if (!match) return null;
  const value = parseFloat(match[0]);
  if (isNaN(value)) return null;
  const unstable = /^US|^S\s+D/i.test(line.trim());
  return { value, stable: !unstable };
}

abstract class BaseSource implements ReadingSource {
  abstract readonly kind: SourceKind;
  protected _state: SourceState = 'disconnected';
  private readingListeners = new Set<(r: Reading) => void>();
  private stateListeners = new Set<(s: SourceState) => void>();

  get state(): SourceState {
    return this._state;
  }

  abstract connect(): Promise<void>;
  abstract disconnect(): Promise<void>;

  onReading(cb: (r: Reading) => void): () => void {
    this.readingListeners.add(cb);
    return () => this.readingListeners.delete(cb);
  }

  onState(cb: (s: SourceState) => void): () => void {
    this.stateListeners.add(cb);
    return () => this.stateListeners.delete(cb);
  }

  protected emitReading(r: Reading): void {
    this.readingListeners.forEach((fn) => fn(r));
  }

  protected setState(s: SourceState): void {
    this._state = s;
    this.stateListeners.forEach((fn) => fn(s));
  }
}

export class WebSerialSource extends BaseSource {
  readonly kind = 'serial' as const;
  private port: SerialPort | null = null;
  private reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  private baudRate: number;

  constructor(baudRate = 9600) {
    super();
    this.baudRate = baudRate;
  }

  async connect(): Promise<void> {
    if (!isWebSerialSupported()) {
      this.setState('error');
      throw new Error('Web Serial is not supported in this browser');
    }
    this.setState('connecting');
    try {
      this.port = await navigator.serial.requestPort();
      await this.port.open({ baudRate: this.baudRate });
      this.setState('connected');
      void this.readLoop();
    } catch (err) {
      this.setState(this.port ? 'error' : 'disconnected');
      this.port = null;
      throw err;
    }
  }

  private async readLoop(): Promise<void> {
    if (!this.port?.readable) return;
    const decoder = new TextDecoder();
    let buffer = '';
    this.reader = this.port.readable.getReader();
    try {
      for (;;) {
        const { value, done } = await this.reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split(/\r\n|\r|\n/);
        buffer = lines.pop() ?? '';
        for (const line of lines) {
          if (!line.trim()) continue;
          const parsed = parseBalanceLine(line);
          if (parsed) {
            this.emitReading({ ...parsed, raw: line, timestamp: Date.now() });
          }
        }
      }
    } catch {
      if (this._state === 'connected') this.setState('error');
    } finally {
      this.reader?.releaseLock();
      this.reader = null;
    }
  }

  async disconnect(): Promise<void> {
    try {
      await this.reader?.cancel();
      await this.port?.close();
    } catch {
      // ignore close errors
    }
    this.port = null;
    this.setState('disconnected');
  }
}

// Simulated balance: readings settle toward target + a small bias (within
// ±0.5d so demo results always comply), with realistic noise while settling.
export class SimulatedSource extends BaseSource {
  readonly kind = 'simulator' as const;
  private timer: ReturnType<typeof setInterval> | null = null;
  private target = 0;
  private d = 0.01;
  private bias = 0;
  private settleUntil = 0;

  setTarget(load: number, scaleInterval: number): void {
    if (load === this.target && scaleInterval === this.d) return;
    this.target = isNaN(load) ? 0 : load;
    this.d = scaleInterval > 0 ? scaleInterval : 0.01;
    this.bias = Math.round((Math.random() - 0.5) * 1.2) * this.d * 0.5;
    this.settleUntil = Date.now() + 2000;
  }

  async connect(): Promise<void> {
    this.setState('connecting');
    await new Promise((r) => setTimeout(r, 400));
    this.setState('connected');
    this.settleUntil = Date.now() + 2000;
    this.timer = setInterval(() => this.tick(), 250);
  }

  private tick(): void {
    const now = Date.now();
    const settling = now < this.settleUntil;
    let value: number;
    if (settling) {
      const progress = 1 - (this.settleUntil - now) / 2000;
      const amplitude = this.d * 8 * (1 - progress);
      value = this.target + this.bias + (Math.random() - 0.5) * 2 * amplitude;
    } else {
      const jitter = Math.random() < 0.08 ? (Math.random() < 0.5 ? -this.d : this.d) : 0;
      value = this.target + this.bias + jitter;
    }
    value = Math.round(value / this.d) * this.d;
    const decimals = this.decimals();
    this.emitReading({
      value: parseFloat(value.toFixed(decimals)),
      stable: !settling,
      raw: `${settling ? 'US' : 'ST'},${value.toFixed(decimals)}`,
      timestamp: now,
    });
  }

  private decimals(): number {
    const s = String(this.d);
    const dot = s.indexOf('.');
    return dot === -1 ? 0 : s.length - dot - 1;
  }

  async disconnect(): Promise<void> {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    this.setState('disconnected');
  }
}
