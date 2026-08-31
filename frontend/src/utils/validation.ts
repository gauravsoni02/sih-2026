export function requiredRule(label: string) {
  return { required: true, message: `${label} is required` };
}

export function positiveNumberRule(label: string) {
  return {
    validator: (_: unknown, value: string | number | undefined) => {
      if (value === undefined || value === '') return Promise.resolve();
      const num = Number(value);
      if (isNaN(num) || num <= 0) return Promise.reject(new Error(`${label} must be a positive number`));
      return Promise.resolve();
    },
  };
}

export function nonNegativeNumberRule(label: string) {
  return {
    validator: (_: unknown, value: string | number | undefined) => {
      if (value === undefined || value === '') return Promise.resolve();
      const num = Number(value);
      if (isNaN(num) || num < 0) return Promise.reject(new Error(`${label} must be non-negative`));
      return Promise.resolve();
    },
  };
}
