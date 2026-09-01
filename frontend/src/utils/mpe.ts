type AccuracyClass = 'I' | 'II' | 'III' | 'IIII';

interface MpeRange {
  lower: number;
  upper: number;
  factor: string;
}

interface R76_1_Config {
  mpe_table: Record<string, MpeRange[]>;
  verification: { subsequent_multiplier: string };
}

interface R76_2_EvalType {
  name: string;
  description: string;
  verification_type: string;
  required_tests: string[];
  weighing_performance?: {
    min_test_points_per_zone: number;
    directions: string[];
  };
  repeatability?: {
    min_repetitions: number;
    test_loads_fractions_of_max: string[];
  };
}

interface R76_2_Config {
  evaluation_types: Record<string, R76_2_EvalType>;
  environmental_conditions: Record<string, string>;
  test_sequence: string[];
}

interface StandardConfig {
  r76_1: R76_1_Config;
  r76_2: R76_2_Config;
}

let cachedConfig: StandardConfig | null = null;

const FALLBACK_MPE_TABLE: Record<AccuracyClass, [number, number, number][]> = {
  I: [
    [0, 50000, 0.5],
    [50000, 200000, 1.0],
  ],
  II: [
    [0, 5000, 0.5],
    [5000, 20000, 1.0],
    [20000, 100000, 1.5],
  ],
  III: [
    [0, 500, 0.5],
    [500, 2000, 1.0],
    [2000, 10000, 1.5],
  ],
  IIII: [
    [0, 50, 0.5],
    [50, 200, 1.0],
    [200, 1000, 1.5],
  ],
};

export async function loadStandardConfig(): Promise<void> {
  try {
    const base = import.meta.env.VITE_API_URL || '/api';
    const res = await fetch(`${base}/standard-config/`);
    // Guard against SPA rewrites serving index.html for unknown paths:
    // only accept an OK response that is actually JSON.
    const contentType = res.headers.get('content-type') ?? '';
    if (res.ok && contentType.includes('json')) {
      cachedConfig = await res.json();
    }
  } catch {
    // fallback to hardcoded table
  }
}

function getMpeTable(accuracyClass: AccuracyClass): [number, number, number][] {
  if (cachedConfig) {
    const ranges = cachedConfig.r76_1.mpe_table[accuracyClass];
    if (ranges) return ranges.map((r) => [r.lower, r.upper, parseFloat(r.factor)]);
  }
  return FALLBACK_MPE_TABLE[accuracyClass];
}

function getSubsequentMultiplier(): number {
  if (cachedConfig) return parseFloat(cachedConfig.r76_1.verification.subsequent_multiplier);
  return 2;
}

export function getMpe(
  accuracyClass: AccuracyClass,
  load: number,
  e: number,
  verificationType: 'initial' | 'subsequent' = 'initial'
): number {
  const m = load / e;
  const ranges = getMpeTable(accuracyClass);
  for (const [lower, upper, factor] of ranges) {
    if ((lower < m && m <= upper) || (lower === 0 && m === 0)) {
      let mpe = factor * e;
      if (verificationType === 'subsequent') mpe *= getSubsequentMultiplier();
      return mpe;
    }
  }
  throw new Error(`Load ${load} out of range for class ${accuracyClass}`);
}

export function getEvaluationTypes(): { value: string; label: string; description: string }[] {
  if (cachedConfig) {
    return Object.entries(cachedConfig.r76_2.evaluation_types).map(([key, et]) => ({
      value: key,
      label: et.name,
      description: et.description,
    }));
  }
  return [
    { value: 'type_evaluation', label: 'Type Evaluation', description: 'Complete testing for type approval' },
    { value: 'initial_verification', label: 'Initial Verification', description: 'Testing for initial verification' },
    { value: 'subsequent_verification', label: 'Subsequent Verification', description: 'Testing for in-service verification' },
  ];
}

export function getRequiredTests(evaluationType: string): string[] {
  if (cachedConfig) {
    const et = cachedConfig.r76_2.evaluation_types[evaluationType];
    if (et) return et.required_tests;
  }
  const defaults: Record<string, string[]> = {
    type_evaluation: [
      'weighing_performance', 'eccentricity', 'repeatability', 'discrimination',
      'sensitivity', 'tare', 'creep', 'zero_return', 'temperature', 'tilt',
      'power_supply', 'durability', 'span_stability', 'zero_tracking',
    ],
    initial_verification: ['weighing_performance', 'eccentricity', 'repeatability', 'discrimination'],
    subsequent_verification: ['weighing_performance', 'repeatability'],
  };
  return defaults[evaluationType] ?? defaults.initial_verification;
}

export function getVerificationTypeForEvaluation(evaluationType: string): 'initial' | 'subsequent' {
  if (cachedConfig) {
    const et = cachedConfig.r76_2.evaluation_types[evaluationType];
    if (et) return et.verification_type as 'initial' | 'subsequent';
  }
  return evaluationType === 'subsequent_verification' ? 'subsequent' : 'initial';
}
