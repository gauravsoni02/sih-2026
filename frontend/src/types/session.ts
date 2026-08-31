export type SessionStatus = 'draft' | 'in_progress' | 'completed';
export type ComplianceStatus = 'pass' | 'fail' | 'not_applicable';
export type VerificationType = 'initial' | 'subsequent';
export type EvaluationType = 'type_evaluation' | 'initial_verification' | 'subsequent_verification';

export type TestType =
  | 'weighing_performance'
  | 'eccentricity'
  | 'repeatability'
  | 'discrimination'
  | 'sensitivity'
  | 'tare'
  | 'creep'
  | 'temperature'
  | 'tilt'
  | 'power_supply'
  | 'durability'
  | 'span_stability'
  | 'zero_tracking'
  | 'time_dependence';

export const TEST_TYPE_LABELS: Record<TestType, string> = {
  weighing_performance: 'Weighing Performance',
  eccentricity: 'Eccentricity',
  repeatability: 'Repeatability',
  discrimination: 'Discrimination',
  sensitivity: 'Sensitivity',
  tare: 'Tare',
  creep: 'Creep',
  temperature: 'Temperature',
  tilt: 'Tilt',
  power_supply: 'Power Supply',
  durability: 'Durability',
  span_stability: 'Span Stability',
  zero_tracking: 'Zero Tracking',
  time_dependence: 'Time Dependence',
};

export interface TestSession {
  id: number;
  instrument: number;
  instrument_detail?: {
    id: number;
    manufacturer: string;
    model_name: string;
    serial_number: string;
    accuracy_class: string;
    max_capacity: string;
    min_capacity: string;
    verification_scale_interval_e: string;
    actual_scale_interval_d: string;
    max_additive_tare?: string;
    unit: string;
  };
  laboratory: number;
  laboratory_name?: string;
  engineer: number;
  engineer_name?: string;
  session_date: string;
  temperature_start: string | null;
  temperature_end: string | null;
  humidity: string | null;
  barometric_pressure: string | null;
  evaluation_type: EvaluationType;
  verification_type: VerificationType;
  status: SessionStatus;
  overall_verdict: ComplianceStatus | null;
  created_at: string;
  updated_at: string;
}

export interface TestObservation {
  id?: number;
  session: number;
  test_type: TestType;
  test_point_load: string;
  indicated_value: string;
  reference_value?: string;
  correction: string;
  position?: string;
  trial_number?: number;
  direction?: 'increasing' | 'decreasing';
  timestamp_minutes?: number;
}

export interface TestResult {
  id: number;
  session: number;
  test_type: TestType;
  computed_error: string;
  mpe_applicable: string;
  compliance_status: ComplianceStatus;
  position?: string;
  trial_number?: number;
  remarks: string;
}
