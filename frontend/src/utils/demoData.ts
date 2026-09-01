interface InstrumentInfo {
  max_capacity?: string;
  min_capacity?: string;
  verification_scale_interval_e?: string;
  actual_scale_interval_d?: string;
  max_additive_tare?: string;
  accuracy_class?: string;
}

export const DEMO_INSTRUMENTS = [
  {
    label: 'Mettler Toledo ICS465 — Class III, 30kg (g)',
    value: {
      manufacturer: 'Mettler Toledo',
      model_name: 'ICS465',
      serial_number: `DEMO-MT-${Date.now().toString(36).slice(-4).toUpperCase()}`,
      accuracy_class: 'III' as const,
      max_capacity: '30000',
      min_capacity: '400',
      verification_scale_interval_e: '20',
      actual_scale_interval_d: '20',
      num_scale_intervals_n: 1500,
      unit: 'g' as const,
      tare_device_type: 'additive',
      max_additive_tare: '30000',
      max_safe_load: '45000',
      is_multi_interval: false,
    },
  },
  {
    label: 'Sartorius Cubis II — Class II, 6.1kg (g)',
    value: {
      manufacturer: 'Sartorius',
      model_name: 'Cubis II',
      serial_number: `DEMO-SA-${Date.now().toString(36).slice(-4).toUpperCase()}`,
      accuracy_class: 'II' as const,
      max_capacity: '6100',
      min_capacity: '500',
      verification_scale_interval_e: '0.1',
      actual_scale_interval_d: '0.01',
      num_scale_intervals_n: 61000,
      unit: 'g' as const,
      tare_device_type: 'additive',
      max_additive_tare: '6100',
      max_safe_load: '9000',
      is_multi_interval: false,
    },
  },
  {
    label: 'Ohaus Explorer — Class III, 150kg (kg)',
    value: {
      manufacturer: 'Ohaus',
      model_name: 'Explorer EX150',
      serial_number: `DEMO-OH-${Date.now().toString(36).slice(-4).toUpperCase()}`,
      accuracy_class: 'III' as const,
      max_capacity: '150',
      min_capacity: '2',
      verification_scale_interval_e: '0.05',
      actual_scale_interval_d: '0.05',
      num_scale_intervals_n: 3000,
      unit: 'kg' as const,
      tare_device_type: 'none',
      max_additive_tare: '',
      max_safe_load: '225',
      is_multi_interval: false,
    },
  },
  {
    label: 'Essae DS-252 — Class III, 60kg (kg)',
    value: {
      manufacturer: 'Essae',
      model_name: 'DS-252',
      serial_number: `DEMO-ES-${Date.now().toString(36).slice(-4).toUpperCase()}`,
      accuracy_class: 'III' as const,
      max_capacity: '60',
      min_capacity: '0.4',
      verification_scale_interval_e: '0.02',
      actual_scale_interval_d: '0.02',
      num_scale_intervals_n: 3000,
      unit: 'kg' as const,
      tare_device_type: 'additive',
      max_additive_tare: '60',
      max_safe_load: '90',
      is_multi_interval: false,
    },
  },
  {
    label: 'Swastik SW-50 — Class IIII, 500kg (kg)',
    value: {
      manufacturer: 'Swastik',
      model_name: 'SW-50',
      serial_number: `DEMO-SW-${Date.now().toString(36).slice(-4).toUpperCase()}`,
      accuracy_class: 'IIII' as const,
      max_capacity: '500',
      min_capacity: '5',
      verification_scale_interval_e: '0.5',
      actual_scale_interval_d: '0.5',
      num_scale_intervals_n: 1000,
      unit: 'kg' as const,
      tare_device_type: 'none',
      max_additive_tare: '',
      max_safe_load: '750',
      is_multi_interval: false,
    },
  },
];

export const DEMO_SESSION = {
  temperature_start: 23.2,
  temperature_end: 23.5,
  humidity: 48.5,
  barometric_pressure: 1013.2,
  evaluation_type: 'initial_verification',
};

function r(value: number, decimals: number): number {
  const f = Math.pow(10, decimals);
  return Math.round(value * f) / f;
}

function decimalsFor(e: number): number {
  const s = String(e);
  const dot = s.indexOf('.');
  return dot === -1 ? 0 : s.length - dot - 1;
}

export function getDemoObservations(inst: InstrumentInfo | undefined, shouldPass = true) {
  const max = parseFloat(inst?.max_capacity || '30000');
  const min = parseFloat(inst?.min_capacity || '400');
  const e = parseFloat(inst?.verification_scale_interval_e || '20');
  const d = parseFloat(inst?.actual_scale_interval_d || '20');
  const tPlus = parseFloat(inst?.max_additive_tare || '0');
  const halfMax = r(max / 2, decimalsFor(e));
  const eccLoad = r((max + tPlus) / 3, decimalsFor(e));
  const dp = Math.max(decimalsFor(e), decimalsFor(d));

  const cls = inst?.accuracy_class || 'III';

  return {
    weighing_performance: getWeighingPerformanceDemo(min, max, e, d, dp, cls, shouldPass),
    eccentricity: getEccentricityDemo(eccLoad, e, d, dp, cls, shouldPass),
    repeatability: getRepeatabilityDemo(halfMax, e, d, dp, cls, shouldPass),
    discrimination: getDiscriminationDemo(min, halfMax, max, d, dp, shouldPass),
    sensitivity: getSensitivityDemo(max, d, e, dp, shouldPass),
    tare: getTareDemo(max, e, d, dp, cls, shouldPass),
    creep: getCreepDemo(max, e, d, dp, shouldPass),
    zero_tracking: getZeroTrackingDemo(e, d, dp, shouldPass),
    temperature: getStandardDemo([min, halfMax, max], e, d, dp, cls, shouldPass),
    tilt: getStandardDemo([halfMax, max], e, d, dp, cls, shouldPass),
    power_supply: getStandardDemo([halfMax, max], e, d, dp, cls, shouldPass),
    durability: getStandardDemo([halfMax, max], e, d, dp, cls, shouldPass),
    span_stability: getSpanStabilityDemo(max, e, d, dp, cls, shouldPass),
  };
}

function randInt(lo: number, hi: number): number {
  return Math.floor(Math.random() * (hi - lo + 1)) + lo;
}

// Random indication error in whole steps of d with |error| <= limit.
// Returns 0 when the display resolution cannot show an error within limit.
function randError(limit: number, d: number, dp: number, allowNegative = true): number {
  const maxK = Math.floor((limit + 1e-9) / d);
  if (maxK <= 0) return 0;
  const k = allowNegative ? randInt(-maxK, maxK) : randInt(0, maxK);
  return r(k * d, dp);
}

// Random error guaranteed to exceed limit (for failing demo data).
function randFailError(limit: number, d: number, dp: number): number {
  const k = Math.floor(limit / d) + 1 + randInt(1, 3);
  return r((Math.random() < 0.5 ? -1 : 1) * k * d, dp);
}

function mpeFactorFor(accuracyClass: string, m: number): number {
  // OIML R 76-1 Table 6 zone boundaries in number of intervals (m = load/e)
  const zones: Record<string, [number, number]> = {
    I: [50000, 200000],
    II: [5000, 20000],
    III: [500, 2000],
    IIII: [50, 200],
  };
  const [z1, z2] = zones[accuracyClass] ?? zones.III;
  return m <= z1 ? 0.5 : m <= z2 ? 1.0 : 1.5;
}

function getWeighingPerformanceDemo(min: number, max: number, e: number, d: number, dp: number, accuracyClass: string, shouldPass: boolean) {
  const loads = [min, r(max * 0.2, dp), r(max * 0.4, dp), r(max * 0.7, dp), max];
  const mpeOf = (load: number) => mpeFactorFor(accuracyClass, load / e) * e;
  const errorFor = (load: number) => {
    const mpe = mpeOf(load);
    if (!shouldPass) return randFailError(mpe, d, dp);
    let err = randError(mpe, d, dp);
    // Re-roll a zero once so the error profile stays visibly wavy
    if (err === 0) err = randError(mpe, d, dp);
    return err;
  };
  const rows = [
    ...loads.map((load, i) => ({
      key: i + 1,
      direction: 'increasing' as const,
      test_point_load: String(load),
      indicated_value: String(r(load + errorFor(load), dp)),
      correction: '0',
    })),
    ...[...loads].reverse().map((load, i) => ({
      key: loads.length + i + 1,
      direction: 'decreasing' as const,
      test_point_load: String(load),
      indicated_value: String(r(load + errorFor(load), dp)),
      correction: '0',
    })),
  ];
  return rows;
}

function getEccentricityDemo(testLoad: number, e: number, d: number, dp: number, cls: string, shouldPass: boolean) {
  const mpe = mpeFactorFor(cls, testLoad / e) * e;
  const err = () => (shouldPass ? randError(mpe, d, dp) : randFailError(mpe, d, dp));
  return {
    testLoad: String(testLoad),
    readings: {
      center: String(testLoad),
      front_left:  String(r(testLoad + err(), dp)),
      front_right: String(r(testLoad + err(), dp)),
      rear_left:   String(r(testLoad + err(), dp)),
      rear_right:  String(r(testLoad + err(), dp)),
    },
  };
}

function getRepeatabilityDemo(load: number, e: number, d: number, dp: number, cls: string, shouldPass: boolean) {
  const mpe = mpeFactorFor(cls, load / e) * e;
  let readings: number[];
  if (shouldPass) {
    // Non-negative offsets so the range never exceeds the MPE
    readings = Array.from({ length: 6 }, () => r(load + randError(mpe, d, dp, false), dp));
  } else {
    const spread = Math.abs(randFailError(mpe, d, dp));
    readings = [load, r(load + spread, dp), load, load, r(load + spread, dp), load];
  }
  return {
    testLoad: String(load),
    readings: readings.map(String),
  };
}

function getDiscriminationDemo(min: number, halfMax: number, max: number, d: number, dp: number, shouldPass: boolean) {
  return [
    { load: String(min),     before: String(min),     after: String(shouldPass ? r(min + d, dp) : String(min)) },
    { load: String(halfMax), before: String(halfMax), after: String(shouldPass ? r(halfMax + d, dp) : String(halfMax)) },
    { load: String(max),     before: String(max),     after: String(shouldPass ? r(max + d, dp) : String(max)) },
  ];
}

function getSensitivityDemo(max: number, d: number, _e: number, dp: number, shouldPass: boolean) {
  return [
    { key: 'zero', loadBefore: '0',          loadAfter: String(r(d, dp)),  before: '0',          after: String(shouldPass ? r(d, dp) : '0') },
    { key: 'max',  loadBefore: String(max), loadAfter: String(max),        before: String(max), after: String(shouldPass ? r(max + d, dp) : String(max)) },
  ];
}

function getTareDemo(max: number, e: number, d: number, dp: number, cls: string, shouldPass: boolean) {
  const tare1 = r(max * 0.1, dp);
  const net1  = r(max * (0.25 + Math.random() * 0.15), dp);
  const tare2 = r(max * 0.2, dp);
  const net2  = r(max * (0.4 + Math.random() * 0.15), dp);
  const err = (net: number) => {
    const mpe = mpeFactorFor(cls, net / e) * e;
    return shouldPass ? randError(mpe, d, dp) : randFailError(mpe, d, dp);
  };
  // A tared display indicates the net load directly
  return [
    { tare: String(tare1), net: String(net1), indicated: String(r(net1 + err(net1), dp)) },
    { tare: String(tare2), net: String(net2), indicated: String(r(net2 + err(net2), dp)) },
  ];
}

function getCreepDemo(max: number, e: number, d: number, dp: number, shouldPass: boolean) {
  // Limits: total drift <= 0.5e, drift between 15 and 30 min <= 0.2e
  const d15 = shouldPass ? randError(e * 0.2, d, dp, false) : r(e * 0.3, dp);
  const d30 = shouldPass
    ? r(d15 + randError(Math.min(e * 0.2, e * 0.45 - d15), d, dp, false), dp)
    : r(e * 0.8, dp);
  return {
    testLoad: String(max),
    reading0:  String(max),
    reading15: String(r(max + d15, dp)),
    reading30: String(r(max + d30, dp)),
  };
}

function getZeroTrackingDemo(e: number, d: number, dp: number, shouldPass: boolean) {
  // Zero return criterion: deviation <= 0.5e
  return {
    before: '0',
    after: String(shouldPass ? randError(e * 0.5, d, dp, false) : Math.abs(randFailError(e * 0.5, d, dp))),
  };
}

function getSpanStabilityDemo(
  max: number,
  e: number,
  d: number,
  dp: number,
  cls: string,
  shouldPass: boolean,
): { load: string; indicated: string; correction: string }[] {
  // Repeated measurements at Max; the spread between them is what matters
  const mpe = mpeFactorFor(cls, max / e) * e;
  const reading = () => r(max + randError(mpe, d, dp, false), dp);
  if (!shouldPass) {
    const spread = Math.abs(randFailError(mpe, d, dp));
    return [
      { load: String(max), indicated: String(max), correction: '0' },
      { load: String(max), indicated: String(r(max + spread, dp)), correction: '0' },
      { load: String(max), indicated: String(max), correction: '0' },
    ];
  }
  return [
    { load: String(max), indicated: String(reading()), correction: '0' },
    { load: String(max), indicated: String(reading()), correction: '0' },
    { load: String(max), indicated: String(reading()), correction: '0' },
  ];
}

function getStandardDemo(
  loads: number[],
  e: number,
  d: number,
  dp: number,
  cls: string,
  shouldPass: boolean
): { load: string; indicated: string; correction: string }[] {
  return loads.map((load) => {
    const mpe = mpeFactorFor(cls, load / e) * e;
    const err = shouldPass ? randError(mpe, d, dp) : randFailError(mpe, d, dp);
    return {
      load: String(load),
      indicated: String(r(load + err, dp)),
      correction: '0',
    };
  });
}

export function buildAllObservations(inst: InstrumentInfo | undefined, shouldPass = true) {
  const demo = getDemoObservations(inst, shouldPass);
  const obs: Record<string, unknown>[] = [];

  demo.weighing_performance.forEach((row, i) => {
    obs.push({
      test_type: 'weighing_performance',
      test_point_load: row.test_point_load,
      indicated_value: row.indicated_value,
      correction: row.correction,
      direction: row.direction,
      trial_number: i + 1,
    });
  });

  const ecc = demo.eccentricity;
  ['center', 'front_left', 'front_right', 'rear_left', 'rear_right'].forEach((pos, i) => {
    obs.push({
      test_type: 'eccentricity',
      test_point_load: ecc.testLoad,
      indicated_value: ecc.readings[pos as keyof typeof ecc.readings],
      correction: '0',
      position: pos,
      trial_number: i + 1,
    });
  });

  const rep = demo.repeatability;
  rep.readings.forEach((val, i) => {
    obs.push({
      test_type: 'repeatability',
      test_point_load: rep.testLoad,
      indicated_value: val,
      correction: '0',
      trial_number: i + 1,
    });
  });

  demo.discrimination.forEach((row, i) => {
    obs.push({
      test_type: 'discrimination',
      test_point_load: row.load,
      indicated_value: row.before,
      correction: '0',
      trial_number: i + 1,
      direction: 'increasing',
    });
    obs.push({
      test_type: 'discrimination',
      test_point_load: row.load,
      indicated_value: row.after,
      correction: '0',
      trial_number: i + 1,
      direction: 'decreasing',
    });
  });

  demo.sensitivity.forEach((row, i) => {
    obs.push({
      test_type: 'sensitivity',
      test_point_load: row.loadBefore,
      indicated_value: row.before,
      correction: '0',
      trial_number: i + 1,
      direction: 'increasing',
    });
    obs.push({
      test_type: 'sensitivity',
      test_point_load: row.loadAfter,
      indicated_value: row.after,
      correction: '0',
      trial_number: i + 1,
      direction: 'decreasing',
    });
  });

  demo.tare.forEach((row, i) => {
    obs.push({
      test_type: 'tare',
      test_point_load: row.net,
      indicated_value: row.indicated,
      correction: row.tare,
      trial_number: i + 1,
    });
  });

  const creep = demo.creep;
  obs.push({ test_type: 'creep', test_point_load: creep.testLoad, indicated_value: creep.reading0, correction: '0', trial_number: 1, timestamp_minutes: 0 });
  obs.push({ test_type: 'creep', test_point_load: creep.testLoad, indicated_value: creep.reading15, correction: '0', trial_number: 2, timestamp_minutes: 15 });
  obs.push({ test_type: 'creep', test_point_load: creep.testLoad, indicated_value: creep.reading30, correction: '0', trial_number: 3, timestamp_minutes: 30 });

  const zt = demo.zero_tracking;
  obs.push({ test_type: 'zero_tracking', test_point_load: '0', indicated_value: zt.before, correction: '0', trial_number: 1, direction: 'increasing' });
  obs.push({ test_type: 'zero_tracking', test_point_load: '0', indicated_value: zt.after, correction: '0', trial_number: 2, direction: 'decreasing' });

  const stdTests: Array<{ key: string; data: { load: string; indicated: string; correction: string }[] }> = [
    { key: 'temperature', data: demo.temperature },
    { key: 'tilt', data: demo.tilt },
    { key: 'power_supply', data: demo.power_supply },
    { key: 'durability', data: demo.durability },
    { key: 'span_stability', data: demo.span_stability },
  ];
  for (const { key, data } of stdTests) {
    data.forEach((row, i) => {
      obs.push({
        test_type: key,
        test_point_load: row.load,
        indicated_value: row.indicated,
        correction: row.correction,
        trial_number: i + 1,
      });
    });
  }

  return obs;
}
