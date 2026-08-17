/**
 * Number & string formatting utilities for the trading dashboard.
 */

/** Format price with ₹ symbol */
export function formatPrice(value: number | null | undefined): string {
  if (value == null) return '—';
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/** Format large numbers with K/M/B suffixes */
export const formatCompact = (value: number) => {
  if (value === undefined || value === null) return '-';
  if (Math.abs(value) >= 1e7) return `${(value / 1e7).toFixed(2)}Cr`;
  if (Math.abs(value) >= 1e5) return `${(value / 1e5).toFixed(2)}L`;
  if (Math.abs(value) >= 1e3) return `${(value / 1e3).toFixed(1)}k`;
  return value.toLocaleString('en-IN');
};

/** Format percentage (0.65 → "65.0%") */
export function formatPercent(value: number | null | undefined, decimals = 1): string {
  if (value == null) return '—';
  return `${(value * 100).toFixed(decimals)}%`;
}

/** Format P&L with sign and color class */
export function formatPnL(value: number | null | undefined): { text: string; className: string } {
  if (value == null) return { text: '—', className: '' };
  const sign = value >= 0 ? '+' : '';
  return {
    text: `${sign}₹${value.toFixed(2)}`,
    className: value > 0 ? 'profit' : value < 0 ? 'loss' : '',
  };
}

/** Format timestamp to readable time */
export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return iso;
  }
}

/** Format timestamp to readable date+time */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

/** Get signal color class */
export function signalClass(signal: string | null | undefined): string {
  if (!signal) return '';
  switch (signal.toUpperCase()) {
    case 'BUY': return 'profit';
    case 'SELL': return 'loss';
    default: return '';
  }
}

/** Get decision badge class */
export function decisionBadgeClass(decision: string | null | undefined): string {
  if (!decision) return 'badge-pending';
  switch (decision.toUpperCase()) {
    case 'ACCEPT': return 'badge-accept';
    case 'AVOID': return 'badge-avoid';
    default: return 'badge-pending';
  }
}

/** Humanize feature name (smma_slope_20 → "SMMA Slope 20") */
export function humanizeFeature(name: string): string {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
    .replace(/Smma/g, 'SMMA')
    .replace(/Etq/g, 'ETQ')
    .replace(/Ltq/g, 'LTQ')
    .replace(/Ltp/g, 'LTP')
    .replace(/Pnl/g, 'P&L');
}
