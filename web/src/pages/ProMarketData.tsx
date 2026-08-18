import { useEffect, useState, useRef } from 'react';
import { useStore } from '../stores/useStore';
import { formatPrice, formatCompact } from '../utils/formatters';
import { api } from '../api/client';
import LightweightChart from '../components/charts/LightweightChart';

function StockMarketCard({ stock, isQualified }: { stock: any, isQualified: boolean }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !hasFetched && !loading) {
        setLoading(true);
        api.getStockDetail(stock.symbol).then(d => {
          setData(d);
        }).catch(err => {
          console.error(err);
        }).finally(() => {
          setLoading(false);
          setHasFetched(true);
        });
      }
    }, { rootMargin: '400px' });

    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [stock.symbol, hasFetched, loading]);

  const spread = stock.ask_price && stock.bid_price
    ? ((stock.ask_price - stock.bid_price) / stock.ask_price * 100)
    : 0;

  return (
    <div ref={containerRef} style={{ background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-default)', padding: '24px', marginBottom: '24px', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
      {/* Top Stats Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid var(--border-default)', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>{stock.symbol}</h2>
          <span style={{ fontSize: '11px', padding: '4px 8px', borderRadius: '6px', background: isQualified ? 'rgba(0, 208, 156, 0.1)' : 'var(--bg-hover)', color: isQualified ? 'var(--profit)' : 'var(--text-muted)', fontWeight: 600 }}>
            {isQualified ? 'QUALIFIED' : 'FILTERING'}
          </span>
        </div>
        
        <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>LTP</span>
            <span style={{ fontSize: '16px', fontWeight: 600, fontFamily: 'monospace' }}>{formatPrice(stock.ltp)}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Spread</span>
            <span style={{ fontSize: '16px', fontWeight: 600, fontFamily: 'monospace' }}>{spread.toFixed(3)}%</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>SMMA (20/120)</span>
            <span style={{ fontSize: '16px', fontWeight: 600, fontFamily: 'monospace' }}>{stock.smma_fast?.toFixed(2) || '--'} / {stock.smma_slow?.toFixed(2) || '--'}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>ETQ (20m/60m)</span>
            <span style={{ fontSize: '16px', fontWeight: 600, fontFamily: 'monospace' }}>{formatCompact(stock.etq_20m)} / {formatCompact(stock.etq_60m)}</span>
          </div>
        </div>
      </div>

      {/* Chart & AI Analysis */}
      {loading ? (
        <div style={{ height: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', background: 'var(--bg-surface)', borderRadius: '12px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <div className="spinner"></div>
            <span>Loading AI Analysis & Live Data...</span>
          </div>
        </div>
      ) : data ? (
        <div style={{ display: 'flex', gap: '24px', animation: 'fadeIn 0.3s ease', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 500px', height: '350px', background: 'var(--bg-surface)', borderRadius: '12px', padding: '16px', border: '1px solid var(--border-default)' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>Live Price Action ({stock.symbol})</h3>
            <div style={{ height: '280px' }}>
              <LightweightChart data={(data.bars || []).map((b: any) => ({
                time: Math.floor(new Date(b.timestamp).getTime() / 1000),
                open: b.open, high: b.high, low: b.low, close: b.close
              }))} />
            </div>
          </div>
          <div style={{ width: '320px', flexGrow: 1, maxWidth: '400px', background: 'var(--bg-surface)', borderRadius: '12px', padding: '20px', border: '1px solid var(--border-default)' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: 'var(--text-primary)' }}>AI Analysis</h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Prediction</span>
              <span style={{ fontWeight: 700, color: data.signal === 'BUY' ? 'var(--profit)' : (data.signal === 'SELL' ? 'var(--loss)' : 'var(--text-secondary)') }}>
                {data.signal === 'BUY' ? 'Bullish' : (data.signal === 'SELL' ? 'Bearish' : 'Neutral')}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Confidence</span>
              <span style={{ fontWeight: 700 }}>{data.ml_probability ? (data.ml_probability * 100).toFixed(1) + '%' : '--'}</span>
            </div>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {data.signal ? (
                <>The 20-period moving average has crossed {data.signal === 'BUY' ? 'above' : 'below'} the 120-period average. Order flow imbalance shows {data.bid_quantity > data.ask_quantity ? 'strong buying pressure' : 'strong selling pressure'}.</>
              ) : (
                <>No clear directional signal. Order flow is currently balanced and moving averages are not indicating a strong trend.</>
              )}
            </p>
          </div>
        </div>
      ) : (
        <div style={{ height: '350px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', background: 'var(--bg-surface)', borderRadius: '12px' }}>
          <span style={{ opacity: 0.5 }}>Scroll to load chart data...</span>
        </div>
      )}
    </div>
  );
}

export default function ProMarketData() {
  const { stocks, fetchStocks } = useStore();
  const [filter, setFilter] = useState('all');
  
  useEffect(() => {
    fetchStocks();
    const interval = setInterval(fetchStocks, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredStocks = stocks.filter((stock: any) => {
    if (filter === 'qualified') return stock.passes_ltp_filter && stock.passes_liquidity_filter;
    if (filter === 'signals') return stock.signal != null;
    return true;
  });

  return (
    <div className="page-content" style={{ maxWidth: '100vw', paddingRight: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0066FF', marginBottom: '8px' }}>Pro: Market Data & AI Analysis</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Live charts and AI predictions are automatically displayed for every stock.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={() => setFilter('all')}
            style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-default)', background: filter === 'all' ? '#0066FF' : 'var(--bg-surface)', color: filter === 'all' ? 'white' : 'var(--text-primary)', cursor: 'pointer', transition: 'all 0.2s' }}
          >
            All Stocks ({stocks.length})
          </button>
          <button 
            onClick={() => setFilter('qualified')}
            style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-default)', background: filter === 'qualified' ? '#0066FF' : 'var(--bg-surface)', color: filter === 'qualified' ? 'white' : 'var(--text-primary)', cursor: 'pointer', transition: 'all 0.2s' }}
          >
            Qualified
          </button>
          <button 
            onClick={() => setFilter('signals')}
            style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-default)', background: filter === 'signals' ? '#0066FF' : 'var(--bg-surface)', color: filter === 'signals' ? 'white' : 'var(--text-primary)', cursor: 'pointer', transition: 'all 0.2s' }}
          >
            Signals Only
          </button>
        </div>
      </div>

      <div style={{ paddingBottom: '40px' }}>
        {filteredStocks.length > 0 ? (
          filteredStocks.map((stock: any) => (
            <StockMarketCard 
              key={stock.symbol} 
              stock={stock} 
              isQualified={stock.passes_ltp_filter && stock.passes_liquidity_filter} 
            />
          ))
        ) : (
          <div style={{ padding: '60px', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-default)', textAlign: 'center', color: 'var(--text-muted)' }}>
            No stocks match the current filter.
          </div>
        )}
      </div>
    </div>
  );
}
