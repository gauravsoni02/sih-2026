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

  return {
    weighing_performance: getWeighingPerformanceDemo(min, max, e, d, dp, inst?.accuracy_class || 'III', shouldPass),
    eccentricity: getEccentricityDemo(eccLoad, e, dp, shouldPass),
    repeatability: getRepeatabilityDemo(halfMax, e, dp, shouldPass),
    discrimination: getDiscriminationDemo(min, halfMax, max, d, dp, shouldPass),
    sensitivity: getSensitivityDemo(max, d, e, dp, shouldPass),
    tare: getTareDemo(max, e, dp, shouldPass),
    creep: getCreepDemo(max, e, dp, shouldPass),
    zero_tracking: getZeroTrackingDemo(e, dp, shouldPass),
    temperature: getStandardDemo([min, halfMax, max], e, dp, shouldPass),
    tilt: getStandardDemo([halfMax, max], e, dp, shouldPass),
    power_supply: getStandardDemo([halfMax, max], e, dp, shouldPass),
    durability: getStandardDemo([halfMax, max], e, dp, shouldPass),
    span_stability: getSpanStabilityDemo(max, e, dp, shouldPass),
  };
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
  const mpeFactor = loads.map((load) => mpeFactorFor(accuracyClass, load / e));
  // A real display indicates in multiples of d: quantize the error to d and
  // aim for ~half the MPE so the profile is visible but always compliant.
  const passError = (i: number, sign: number) => {
    const mpe = mpeFactor[i] * e;
    let err = Math.round((mpe * 0.5) / d) * d;
    while (err > mpe + 1e-12) err -= d;
    return r(sign * Math.max(err, 0), dp);
  };
  const failError = () => r(Math.round((e * 3) / d) * d, dp);
  const signsInc = [0, 1, 1, -1, 1];
  const signsDec = [1, -1, 1, 1, 0];
  const rows = [
    ...loads.map((load, i) => ({
      key: i + 1,
      direction: 'increasing' as const,
      test_point_load: String(load),
      indicated_value: String(shouldPass
        ? r(load + passError(i, signsInc[i]), dp)
        : r(load + failError(), dp)),
      correction: '0',
    })),
    ...[...loads].reverse().map((load, i) => ({
      key: loads.length + i + 1,
      direction: 'decreasing' as const,
      test_point_load: String(load),
      indicated_value: String(shouldPass
        ? r(load + passError(loads.length - 1 - i, signsDec[i]), dp)
        : r(load + failError(), dp)),
      correction: '0',
    })),
  ];
  return rows;
}

function getEccentricityDemo(testLoad: number, e: number, dp: number, shouldPass: boolean) {
  const small = r(e * 0.1, dp);
  const big = r(e * 5, dp);
  return {
    testLoad: String(testLoad),
    readings: {
      center: String(testLoad),
      front_left:  String(r(testLoad + (shouldPass ? small : big), dp)),
      front_right: String(r(testLoad - (shouldPass ? small : big), dp)),
      rear_left:   String(r(testLoad + (shouldPass ? small * 2 : big), dp)),
      rear_right:  String(r(testLoad - (shouldPass ? small * 2 : big), dp)),
    },
  };
}

function getRepeatabilityDemo(load: number, e: number, dp: number, shouldPass: boolean) {
  const tiny = r(e * 0.05, dp);
  const spread = r(e * 3, dp);
  const v = shouldPass ? tiny : spread;
  return {
    testLoad: String(load),
    readings: [load, r(load + v, dp), load, load, r(load + v, dp), load].map(String),
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

function getTareDemo(max: number, e: number, dp: number, shouldPass: boolean) {
  const tare1 = r(max * 0.1, dp);
  const net1  = r(max * 0.3, dp);
  const tare2 = r(max * 0.2, dp);
  const net2  = r(max * 0.5, dp);
  const small = r(e * 0.1, dp);
  const big   = r(e * 3, dp);
  // A tared display indicates the net load directly
  return [
    { tare: String(tare1), net: String(net1), indicated: String(r(net1 + (shouldPass ? small : big), dp)) },
    { tare: String(tare2), net: String(net2), indicated: String(r(net2 + (shouldPass ? 0 : big), dp)) },
  ];
}

function getCreepDemo(max: number, e: number, dp: number, shouldPass: boolean) {
  return {
    testLoad: String(max),
    reading0:  String(max),
    reading15: String(r(max + (shouldPass ? e * 0.05 : e * 0.3), dp)),
    reading30: String(r(max + (shouldPass ? e * 0.1  : e * 0.8), dp)),
  };
}

function getZeroTrackingDemo(e: number, dp: number, shouldPass: boolean) {
  return {
    before: '0',
    after: String(shouldPass ? r(e * 0.1, dp) : r(e * 3, dp)),
  };
}

function getSpanStabilityDemo(
  max: number,
  e: number,
  dp: number,
  shouldPass: boolean,
): { load: string; indicated: string; correction: string }[] {
  // Repeated measurements at Max; the spread between them is what matters
  const drift = shouldPass ? r(e * 0.1, dp) : r(e * 3, dp);
  return [
    { load: String(max), indicated: String(max), correction: '0' },
    { load: String(max), indicated: String(r(max + drift, dp)), correction: '0' },
    { load: String(max), indicated: String(max), correction: '0' },
  ];
}

function getStandardDemo(
  loads: number[],
  e: number,
  dp: number,
  shouldPass: boolean
): { load: string; indicated: string; correction: string }[] {
  const offset = shouldPass ? r(e * 0.1, dp) : r(e * 3, dp);
  return loads.map((load) => ({
    load: String(load),
    indicated: String(r(load + offset, dp)),
    correction: '0',
  }));
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
