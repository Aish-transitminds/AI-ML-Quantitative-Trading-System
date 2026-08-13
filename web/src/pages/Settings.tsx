import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useStore } from '../stores/useStore';

export default function Settings() {
  const { config, fetchConfig, status } = useStore();

  useEffect(() => { fetchConfig(); }, []);

  const screening = config?.screening || {};
  const smma = config?.smma || {};
  const ml = config?.ml || {};
  const data = config?.data || {};
  const mode = config?.mode || status?.mode || 'OFFLINE';

  return (
    <div>
      <div className="section-header">
        <div>
          <div className="section-title">System Configuration</div>
          <div className="section-subtitle">Current operating parameters for the trading system</div>
        </div>
      </div>

      {/* Mode */}
      <motion.div
        className="glass-card"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: 24 }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className={`status-pulse ${mode === 'LIVE' ? 'live' : 'offline'}`} style={{ fontSize: 13 }}>
            <span className="pulse-dot" />
            <span>{mode}</span>
          </div>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            {mode === 'OFFLINE'
              ? 'Using simulated demo data for demonstration'
              : 'Connected to live market via broker API'}
          </span>
        </div>
      </motion.div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Screening Filters */}
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="metric-label" style={{ marginBottom: 16 }}>Stock Screening Filters</div>
          {[
            { label: 'LTP Range', value: `₹${screening.ltp_min || 30} — ₹${screening.ltp_max || 500}` },
            { label: 'Min Bid Qty', value: (screening.min_bid_qty || 1000000).toLocaleString() },
            { label: 'Min Ask Qty', value: (screening.min_ask_qty || 1000000).toLocaleString() },
          ].map(item => (
            <div key={item.label} className="stock-metric-row" style={{ padding: '6px 0' }}>
              <span className="stock-metric-label">{item.label}</span>
              <span className="stock-metric-value">{item.value}</span>
            </div>
          ))}
        </motion.div>

        {/* SMMA Parameters */}
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <div className="metric-label" style={{ marginBottom: 16 }}>SMMA Parameters</div>
          {[
            { label: 'Fast Period', value: smma.fast_period || 20 },
            { label: 'Slow Period', value: smma.slow_period || 120 },
            { label: 'Timeframe', value: smma.timeframe || '1min' },
          ].map(item => (
            <div key={item.label} className="stock-metric-row" style={{ padding: '6px 0' }}>
              <span className="stock-metric-label">{item.label}</span>
              <span className="stock-metric-value">{item.value}</span>
            </div>
          ))}
        </motion.div>

        {/* ML Configuration */}
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="metric-label" style={{ marginBottom: 16 }}>ML Configuration</div>
          {[
            { label: 'Decision Threshold', value: ml.threshold || 0.65 },
            { label: 'Min Trades for Training', value: ml.min_trades_for_training || 50 },
            { label: 'Train / Val / Test', value: `${(ml.train_ratio || 0.6) * 100}% / ${(ml.validation_ratio || 0.2) * 100}% / ${(ml.test_ratio || 0.2) * 100}%` },
          ].map(item => (
            <div key={item.label} className="stock-metric-row" style={{ padding: '6px 0' }}>
              <span className="stock-metric-label">{item.label}</span>
              <span className="stock-metric-value">{String(item.value)}</span>
            </div>
          ))}
        </motion.div>

        {/* Data Management */}
        <motion.div
          className="glass-card"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <div className="metric-label" style={{ marginBottom: 16 }}>Data Management</div>
          {[
            { label: 'Tick Buffer', value: `${data.tick_buffer_max_minutes || 90} min` },
            { label: 'Persist Interval', value: `${data.persist_interval_seconds || 300}s` },
            { label: 'Historical Bars', value: data.historical_bars_fetch || 200 },
          ].map(item => (
            <div key={item.label} className="stock-metric-row" style={{ padding: '6px 0' }}>
              <span className="stock-metric-label">{item.label}</span>
              <span className="stock-metric-value">{String(item.value)}</span>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Methodology */}
      <motion.div
        className="glass-card"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className="metric-label" style={{ marginBottom: 16 }}>Methodology Notes</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
          <p><strong style={{ color: 'var(--primary)' }}>SMMA Formula:</strong> SMMA<sub>t</sub> = (SMMA<sub>t-1</sub> × (N-1) + Price<sub>t</sub>) / N</p>
          <p><strong style={{ color: 'var(--profit)' }}>BUY Signal:</strong> SMMA(20) crosses above SMMA(120)</p>
          <p><strong style={{ color: 'var(--loss)' }}>SELL Signal:</strong> SMMA(20) crosses below SMMA(120)</p>
          <p><strong style={{ color: 'var(--accept)' }}>ML Pipeline:</strong> 25 features → Preprocessing → LR / RF / XGBoost → Probability → ACCEPT/AVOID</p>
          <p><strong style={{ color: 'var(--text-muted)' }}>ETQ ≠ Volume:</strong> ETQ = Sum of LTQ over rolling window, NOT cumulative volume</p>
        </div>
      </motion.div>

      {/* Disclaimer */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        style={{
          marginTop: 24,
          padding: '16px 20px',
          background: 'rgba(255, 51, 102, 0.04)',
          border: '1px solid rgba(255, 51, 102, 0.12)',
          borderRadius: 10,
          fontSize: 12,
          color: 'var(--text-muted)',
          lineHeight: 1.7,
        }}
      >
        ⚠️ <strong>Disclaimer:</strong> This is a technical research application. It does NOT guarantee profitable trading.
        ML predictions represent historical pattern analysis, not financial advice. Predicted probabilities are NOT certainties.
      </motion.div>
    </div>
  );
}
