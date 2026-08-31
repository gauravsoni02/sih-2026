type ConnectionState = 'unsupported' | 'disconnected' | 'connecting' | 'connected' | 'error';

type StateListener = (state: ConnectionState) => void;

class WebSerialService {
  private port: SerialPort | null = null;
  private reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  private state: ConnectionState = 'disconnected';
  private listeners: Set<StateListener> = new Set();

  constructor() {
    if (typeof navigator === 'undefined' || !('serial' in navigator)) {
      this.state = 'unsupported';
    }
  }

  get isSupported(): boolean {
    return this.state !== 'unsupported';
  }

  get connectionState(): ConnectionState {
    return this.state;
  }

  subscribe(listener: StateListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private setState(state: ConnectionState): void {
    this.state = state;
    this.listeners.forEach((fn) => fn(state));
  }

  async connect(baudRate = 9600): Promise<void> {
    if (!this.isSupported) return;

    try {
      this.setState('connecting');
      this.port = await navigator.serial.requestPort();
      await this.port.open({ baudRate });
      this.setState('connected');
    } catch {
      this.setState('error');
    }
  }

  async disconnect(): Promise<void> {
    try {
      if (this.reader) {
        await this.reader.cancel();
        this.reader = null;
      }
      if (this.port) {
        await this.port.close();
        this.port = null;
      }
    } catch {
      // ignore close errors
    }
    this.setState('disconnected');
  }

  async readMeasurement(): Promise<string | null> {
    if (!this.port || this.state !== 'connected') return null;

    try {
      const readable = this.port?.readable;
      if (!readable) return null;
      this.reader = readable.getReader();
      const { value } = await this.reader!.read();
      this.reader.releaseLock();
      this.reader = null;

      if (value) {
        return new TextDecoder().decode(value).trim();
      }
    } catch {
      this.setState('error');
    }
    return null;
  }
}

export const webSerialService = new WebSerialService();
