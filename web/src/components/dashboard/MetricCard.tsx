import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  accent?: 'cyan' | 'profit' | 'loss' | 'gold' | 'default';
  numericValue?: number;
  prefix?: string;
  suffix?: string;
  index?: number;
}

export default function MetricCard({ label, value, accent = 'cyan', index = 0 }: MetricCardProps) {
  return (
    <motion.div
      className="glass-card metric-card"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.06, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="metric-label">{label}</div>
      <div className={`metric-value ${accent}`}>{value}</div>
    </motion.div>
  );
}

/* Animated counter variant */
export function AnimatedMetric({ label, target, format, accent = 'cyan', index = 0 }: {
  label: string;
  target: number;
  format?: (n: number) => string;
  accent?: string;
  index?: number;
}) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, v => format ? format(v) : Math.round(v).toString());

  useEffect(() => {
    const controls = animate(count, target, { duration: 1.2, ease: [0.16, 1, 0.3, 1] });
    return controls.stop;
  }, [target]);

  return (
    <motion.div
      className="glass-card metric-card"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: (index || 0) * 0.06, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="metric-label">{label}</div>
      <motion.div className={`metric-value ${accent}`}>{rounded}</motion.div>
    </motion.div>
  );
}
