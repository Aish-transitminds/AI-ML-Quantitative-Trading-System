import { useEffect, useState } from 'react';
import { useStore } from '../stores/useStore';
import { formatPrice } from '../utils/formatters';

export default function ProTradeLogs() {
  const { trades, fetchTrades } = useStore();
  const [filter, setFilter] = useState('ALL'); // ALL, OPEN, CLOSED

  useEffect(() => {
    fetchTrades();
    const interval = setInterval(fetchTrades, 10000);
    return () => clearInterval(interval);
  }, []);

  const filteredTrades = trades.filter((t: any) => filter === 'ALL' || t.status === filter);

  return (
    <div className="page-content" style={{ maxWidth: '100vw', paddingRight: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0066FF', marginBottom: '8px' }}>Pro: Execution Logs</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Assignment 1 Compliance: Raw algorithmic trade executions and AI/ML acceptance criteria.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={() => setFilter('ALL')}
            style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-default)', background: filter === 'ALL' ? '#0066FF' : 'var(--bg-surface)', color: filter === 'ALL' ? 'white' : 'var(--text-primary)', cursor: 'pointer' }}
          >
            All Logs
          </button>
          <button 
            onClick={() => setFilter('OPEN')}
            style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-default)', background: filter === 'OPEN' ? '#0066FF' : 'var(--bg-surface)', color: filter === 'OPEN' ? 'white' : 'var(--text-primary)', cursor: 'pointer' }}
          >
            Open Only
          </button>
          <button 
            onClick={() => setFilter('CLOSED')}
            style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-default)', background: filter === 'CLOSED' ? '#0066FF' : 'var(--bg-surface)', color: filter === 'CLOSED' ? 'white' : 'var(--text-primary)', cursor: 'pointer' }}
          >
            Closed Only
          </button>
        </div>
      </div>

      <div style={{ background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-default)', overflow: 'auto' }}>
        <table className="data-table" style={{ minWidth: '1200px' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Time</th>
              <th>Symbol</th>
              <th>Signal</th>
              <th>Status</th>
              <th>Entry Price</th>
              <th>Exit Price</th>
              <th>P&L</th>
              <th>ML Conf.</th>
              <th>AI Decision / Reason</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrades.map((trade: any) => {
              const entryTime = new Date(trade.entry_timestamp).toLocaleTimeString();
              const isProfit = trade.pnl && trade.pnl > 0;
              
              return (
                <tr key={trade.id}>
                  <td style={{ color: 'var(--text-muted)' }}>#{trade.id}</td>
                  <td>{entryTime}</td>
                  <td style={{ fontWeight: 600 }}>{trade.symbol}</td>
                  <td>
                    <span style={{ fontWeight: 600, color: trade.signal === 'BUY' ? 'var(--profit)' : 'var(--loss)' }}>
                      {trade.signal}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', background: trade.status === 'OPEN' ? 'rgba(0, 102, 255, 0.1)' : 'var(--bg-hover)', color: trade.status === 'OPEN' ? '#0066FF' : 'var(--text-muted)' }}>
                      {trade.status}
                    </span>
                  </td>
                  <td className="mono">{formatPrice(trade.entry_price)}</td>
                  <td className="mono">{trade.exit_price ? formatPrice(trade.exit_price) : '--'}</td>
                  <td className="mono">
                    {trade.pnl != null ? (
                      <span style={{ color: isProfit ? 'var(--profit)' : 'var(--loss)', fontWeight: 600 }}>
                        {isProfit ? '+' : ''}{formatPrice(trade.pnl)}
                      </span>
                    ) : '--'}
                  </td>
                  <td className="mono">
                    {trade.ml_probability ? (trade.ml_probability * 100).toFixed(1) + '%' : '--'}
                  </td>
                  <td>
                    {trade.ml_decision === 'ACCEPT' ? (
                      <span style={{ color: 'var(--profit)', fontWeight: 600 }}>✅ ACCEPTED (High Conviction)</span>
                    ) : trade.ml_decision === 'AVOID' ? (
                      <span style={{ color: 'var(--loss)', fontWeight: 600 }}>❌ REJECTED (Low Conviction / Poor ETQ)</span>
                    ) : trade.ml_decision === 'MANUAL' ? (
                      <span style={{ color: '#0066FF', fontWeight: 600 }}>👤 MANUAL EXECUTION</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>PENDING</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filteredTrades.length === 0 && (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No execution logs found.
          </div>
        )}
      </div>
    </div>
  );
}
