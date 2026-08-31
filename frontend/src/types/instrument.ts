export type AccuracyClass = 'I' | 'II' | 'III' | 'IIII';
export type Unit = 'mg' | 'g' | 'kg' | 't' | 'ct';
export type InstrumentStatus = 'active' | 'inactive' | 'under_test' | 'condemned';

export interface MultiIntervalRange {
  max: number;
  e: number;
}

export interface Instrument {
  id: number;
  manufacturer: string;
  model_name: string;
  serial_number: string;
  accuracy_class: AccuracyClass;
  max_capacity: string;
  min_capacity: string;
  verification_scale_interval_e: string;
  actual_scale_interval_d: string;
  num_scale_intervals_n: number;
  unit: Unit;
  tare_device_type: string;
  max_additive_tare: string;
  max_safe_load: string;
  is_multi_interval: boolean;
  multi_interval_config: MultiIntervalRange[] | null;
  status: InstrumentStatus;
  created_at: string;
  updated_at: string;
}

export interface InstrumentCreatePayload {
  manufacturer: string;
  model_name: string;
  serial_number: string;
  accuracy_class: AccuracyClass;
  max_capacity: string;
  min_capacity: string;
  verification_scale_interval_e: string;
  actual_scale_interval_d: string;
  num_scale_intervals_n: number;
  unit: Unit;
  tare_device_type?: string;
  max_additive_tare?: string;
  max_safe_load?: string;
  is_multi_interval?: boolean;
  multi_interval_config?: MultiIntervalRange[];
}
