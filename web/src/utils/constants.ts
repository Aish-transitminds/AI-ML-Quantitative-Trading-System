/* Color palette constants (Groww Theme) */
export const COLORS = {
  primary: '#00D09C', /* Groww Teal */
  profit: '#00D09C',  /* Groww Teal for positive */
  loss: '#EB5B3C',    /* Groww Red */
  accept: '#00D09C',
  bgBase: '#FFFFFF',
  bgCard: '#FFFFFF',
  bgSurface: '#F9FAFB',
  textPrimary: '#44475B', /* Groww dark slate text */
  textSecondary: '#7C7E8C',
  textMuted: '#A0A2AE',
} as const;

/* Recharts theme (Groww Theme) */
export const CHART_THEME = {
  backgroundColor: COLORS.bgCard,
  textColor: COLORS.textSecondary,
  gridColor: '#E5E7EB',
  tooltipBg: '#FFFFFF',
  tooltipBorder: '#E5E7EB',
};

/* Animation presets (for Framer Motion) */
export const MOTION = {
  fadeInUp: {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] },
  },
  stagger: {
    animate: { transition: { staggerChildren: 0.06 } },
  },
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] },
  },
} as const;

/* API base URL — empty string uses Vite proxy in dev, same-origin in production */
export const API_BASE = import.meta.env.VITE_API_URL || '';
export const WS_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;

/* Navigation items */
export const NAV_ITEMS = [
  { path: '/',            icon: '◈',  label: 'Dashboard',   section: 'overview' },
  { path: '/trades',      icon: '⇄',  label: 'Trades',      section: 'overview' },
  { path: '/performance', icon: '◎',  label: 'Performance', section: 'analytics' },
  { path: '/models',      icon: '◇',  label: 'Model Lab',   section: 'analytics' },
  { path: '/settings',    icon: '⚙',  label: 'Settings',    section: 'system' },
] as const;
