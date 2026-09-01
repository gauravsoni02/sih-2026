// Per-browser user preferences, persisted in localStorage.

const STORAGE_KEY = 'nawi-preferences';

export interface UserPrefs {
  defaultUnit: string;
  defaultAccuracyClass: string;
  defaultEvaluationType: string;
  serialBaudRate: number;
}

const DEFAULTS: UserPrefs = {
  defaultUnit: 'kg',
  defaultAccuracyClass: 'III',
  defaultEvaluationType: 'initial_verification',
  serialBaudRate: 9600,
};

export function loadPrefs(): UserPrefs {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    // corrupted or unavailable storage — fall through to defaults
  }
  return { ...DEFAULTS };
}

export function savePrefs(prefs: Partial<UserPrefs>): UserPrefs {
  const merged = { ...loadPrefs(), ...prefs };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
  } catch {
    // storage unavailable — keep going, prefs just won't persist
  }
  return merged;
}
