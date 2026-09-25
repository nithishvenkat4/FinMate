/**
 * Currency, Date, and Metric formatting utilities for FinMate.
 * Adheres to Indian number formatting conventions (lakhs, crores).
 */

interface FormatINROptions {
  showDecimals?: boolean | 'auto';
  signDisplay?: 'auto' | 'never' | 'always' | 'exceptZero';
}

export function formatINR(
  value: number | string | undefined | null,
  options?: FormatINROptions
): string {
  if (value === undefined || value === null) return '₹0';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '₹0';

  const showDecimals = options?.showDecimals ?? 'auto';
  let minDecimals = 0;
  let maxDecimals = 0;

  if (showDecimals === true) {
    minDecimals = 2;
    maxDecimals = 2;
  } else if (showDecimals === 'auto') {
    const hasFractions = Math.abs(num % 1) >= 0.005;
    minDecimals = hasFractions ? 2 : 0;
    maxDecimals = hasFractions ? 2 : 0;
  }

  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: minDecimals,
      maximumFractionDigits: maxDecimals,
      signDisplay: options?.signDisplay ?? 'auto',
    }).format(num);
  } catch {
    // Fallback if Intl fails
    const formatted = Math.round(num).toLocaleString('en-IN');
    return `₹${formatted}`;
  }
}

export function formatDate(dateString: string | undefined | null): string {
  if (!dateString) return '—';
  try {
    const parts = dateString.split('-');
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const dt = new Date(year, month, day);
      return dt.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    }
    const d = new Date(dateString);
    return isNaN(d.getTime())
      ? dateString
      : d.toLocaleDateString('en-IN', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        });
  } catch {
    return dateString;
  }
}

export function formatPercent(
  value: number | string | undefined | null,
  options?: { showDecimals?: boolean }
): string {
  if (value === undefined || value === null) return '0%';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '0%';
  if (options?.showDecimals === false || num % 1 === 0) {
    return `${Math.round(num)}%`;
  }
  return `${num.toFixed(1)}%`;
}
