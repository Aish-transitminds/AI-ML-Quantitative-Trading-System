import React, { useEffect, useState } from 'react';
import { useStore } from '../stores/useStore';
import { formatPrice, formatCompact } from '../utils/formatters';
import { api } from '../api/client';
import LightweightChart from '../components/charts/LightweightChart';

export default function ProMarketData() {
  const { stocks, fetchStocks } = useStore();
  const [filter, setFilter] = useState('all');
  
  const [expandedSymbol, setExpandedSymbol] = useState<string | null>(null);
  const [expandedData, setExpandedData] = useState<any>(null);
  const [loadingChart, setLoadingChart] = useState(false);

  useEffect(() => {
    fetchStocks();
    const interval = setInterval(fetchStocks, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleRow = async (symbol: string) => {
    if (expandedSymbol === symbol) {
      setExpandedSymbol(null);
      setExpandedData(null);
    } else {
      setExpandedSymbol(symbol);
      setExpandedData(null);
      setLoadingChart(true);
      try {
        const data = await api.getStockDetail(symbol);
        setExpandedData(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingChart(false);
      }
    }
  };

  const filteredStocks = stocks.filter((stock: any) => {
    if (filter === 'qualified') return stock.passes_ltp_filter && stock.passes_liquidity_filter;
    if (filter === 'signals') return stock.signal != null;
    return true;
  });

  return (
    <div className="page-content" style={{ maxWidth: '100vw', paddingRight: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#0066FF', marginBottom: '8px' }}>Pro: Raw Market Data</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Assignment 1 Compliance: Real-time tick analysis, market depth, and ML indicators. Click any row to expand its live graph.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={() => setFilter('all')}
            style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-default)', background: filter === 'all' ? '#0066FF' : 'var(--bg-surface)', color: filter === 'all' ? 'white' : 'var(--text-primary)', cursor: 'pointer' }}
          >
            All Stocks ({stocks.length})
          </button>
          <button 
            onClick={() => setFilter('qualified')}
            style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-default)', background: filter === 'qualified' ? '#0066FF' : 'var(--bg-surface)', color: filter === 'qualified' ? 'white' : 'var(--text-primary)', cursor: 'pointer' }}
          >
            Qualified
          </button>
        </div>
      </div>

      <div style={{ background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-default)', overflow: 'auto' }}>
        <table className="data-table" style={{ minWidth: '1400px' }}>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Status</th>
              <th>LTP</th>
              <th>Avg LTP (20m/60m)</th>
              <th>SMMA 20 / 120</th>
              <th>Bid (Prc/Qty)</th>
              <th>Ask (Prc/Qty)</th>
              <th>Spread %</th>
              <th>ETQ (5m/20m/60m)</th>
              <th>Signal</th>
              <th>ML Conf.</th>
            </tr>
          </thead>
          <tbody>
            {filteredStocks.map((stock: any) => {
              const isQualified = stock.passes_ltp_filter && stock.passes_liquidity_filter;
              const spread = stock.ask_price && stock.bid_price
                ? ((stock.ask_price - stock.bid_price) / stock.ask_price * 100)
                : 0;
              const isExpanded = expandedSymbol === stock.symbol;

              return (
                <React.Fragment key={stock.symbol}>
                  <tr 
                    onClick={() => toggleRow(stock.symbol)}
                    style={{ cursor: 'pointer', transition: 'background-color 0.2s', backgroundColor: isExpanded ? 'rgba(0, 102, 255, 0.05)' : 'transparent' }}
                    onMouseEnter={(e) => { if (!isExpanded) e.currentTarget.style.backgroundColor = 'var(--bg-hover)'; }}
                    onMouseLeave={(e) => { if (!isExpanded) e.currentTarget.style.backgroundColor = 'transparent'; }}
                    title="Click to expand graph"
                  >
                    <td style={{ fontWeight: 600, color: isExpanded ? '#0066FF' : 'var(--text-primary)' }}>{stock.symbol} {isExpanded ? '▼' : '▶'}</td>
                    <td>
                      <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', background: isQualified ? 'rgba(0, 208, 156, 0.1)' : 'var(--bg-hover)', color: isQualified ? 'var(--profit)' : 'var(--text-muted)' }}>
                        {isQualified ? 'QUALIFIED' : 'FILTERING'}
                      </span>
                    </td>
                    <td className="mono" style={{ fontWeight: 600 }}>{formatPrice(stock.ltp)}</td>
                    <td className="mono">
                      {formatPrice(stock.avg_ltp_20m)} / {formatPrice(stock.avg_ltp_60m)}
                    </td>
                    <td className="mono">
                      {stock.smma_fast?.toFixed(2) || '--'} / {stock.smma_slow?.toFixed(2) || '--'}
                    </td>
                    <td className="mono">
                      {formatPrice(stock.bid_price)} <br/> <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{formatCompact(stock.bid_quantity)}</span>
                    </td>
                    <td className="mono">
                      {formatPrice(stock.ask_price)} <br/> <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>{formatCompact(stock.ask_quantity)}</span>
                    </td>
                    <td className="mono">{spread.toFixed(3)}%</td>
                    <td className="mono">
                      {formatCompact(stock.etq_5m)} / {formatCompact(stock.etq_20m)} / {formatCompact(stock.etq_60m)}
                    </td>
                    <td>
                      {stock.signal ? (
                        <span style={{ fontWeight: 600, color: stock.signal === 'BUY' ? 'var(--profit)' : 'var(--loss)' }}>
                          {stock.signal}
                        </span>
                      ) : '--'}
                    </td>
                    <td className="mono">
                      {stock.ml_probability ? (stock.ml_probability * 100).toFixed(1) + '%' : '--'}
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr>
                      <td colSpan={11} style={{ padding: '24px', background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-default)' }}>
                        {loadingChart ? (
                          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>Loading live chart for {stock.symbol}...</div>
                        ) : expandedData ? (
                          <div style={{ display: 'flex', gap: '24px', animation: 'fadeIn 0.3s ease' }}>
                            <div style={{ flex: 1, height: '350px', background: 'var(--bg-card)', borderRadius: '12px', padding: '16px', border: '1px solid var(--border-default)', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}>
                              <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>Live Price Action ({stock.symbol})</h3>
                              <div style={{ height: '280px' }}>
                                <LightweightChart data={(expandedData.bars || []).map((b: any) => ({
                                  time: Math.floor(new Date(b.timestamp).getTime() / 1000),
                                  open: b.open, high: b.high, low: b.low, close: b.close
                                }))} />
                              </div>
                            </div>
                            <div style={{ width: '320px', background: 'var(--bg-card)', borderRadius: '12px', padding: '20px', border: '1px solid var(--border-default)', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}>
                              <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px', color: 'var(--text-primary)' }}>AI Analysis</h3>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Prediction</span>
                                <span style={{ fontWeight: 700, color: expandedData.signal === 'BUY' ? 'var(--profit)' : 'var(--loss)' }}>{expandedData.signal === 'BUY' ? 'Bullish' : 'Bearish'}</span>
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Confidence</span>
                                <span style={{ fontWeight: 700 }}>{expandedData.ml_probability ? (expandedData.ml_probability * 100).toFixed(1) + '%' : '--'}</span>
                              </div>
                              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                The 20-period moving average has crossed {expandedData.signal === 'BUY' ? 'above' : 'below'} the 120-period average. Order flow imbalance shows {expandedData.bid_quantity > expandedData.ask_quantity ? 'strong buying pressure' : 'strong selling pressure'}.
                              </p>
                            </div>
                          </div>
                        ) : (
                          <div style={{ textAlign: 'center', color: 'var(--loss)', padding: '40px' }}>Failed to load chart data.</div>
                        )}
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
        {filteredStocks.length === 0 && (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No stocks match the current filter.
          </div>
        )}
      </div>
    </div>
  );
}
