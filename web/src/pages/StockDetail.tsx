import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useStore } from '../stores/useStore';
import { api } from '../api/client';
import { formatPrice, formatCompact } from '../utils/formatters';
import { ArrowLeft, Star, Info } from 'lucide-react';
import LightweightChart from '../components/charts/LightweightChart';

export default function StockDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const { watchlist, addToWatchlist, removeFromWatchlist } = useStore();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (!symbol) return;
    api.getStockDetail(symbol)
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [symbol]);

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Loading details...</div>;
  }

  if (!data || data.error) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2>Stock not found</h2>
        <button onClick={() => navigate(-1)} style={{ padding: '8px 16px', marginTop: '16px', background: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: '8px', cursor: 'pointer' }}>Go Back</button>
      </div>
    );
  }

  const isWatchlisted = watchlist.includes(symbol!);
  const toggleWatchlist = () => {
    if (isWatchlisted) removeFromWatchlist(symbol!);
    else addToWatchlist(symbol!);
  };

  const handleExecute = async (signal: string) => {
    try {
      await api.executeTrade({ symbol, signal });
      alert(`Successfully executed simulated ${signal} for ${symbol}!`);
      navigate('/investments'); // Go to portfolio to see it
    } catch (err) {
      alert('Failed to execute trade.');
      console.error(err);
    }
  };

  const handleAnalyze = async () => {
    if (!symbol) return;
    setAnalyzing(true);
    try {
      const res = await api.analyzeSignal(symbol);
      setData((prev: any) => ({ ...prev, explanation: res.explanation }));
    } catch (err) {
      alert('Failed to run AI analysis.');
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };


  const isBuy = data.signal === 'BUY';
  const confidence = data.ml_probability ? (data.ml_probability * 100).toFixed(0) : '--';
  const openTrade = (data.related_trades || []).find((t: any) => t.status === 'OPEN');
  const isMobile = typeof window !== 'undefined' && window.innerWidth <= 768;
  
  // Transform bars for LightweightChart
  const chartData = (data.bars || []).map((b: any) => ({
    time: Math.floor(new Date(b.timestamp).getTime() / 1000),
    open: b.open,
    high: b.high,
    low: b.low,
    close: b.close
  }));

  return (
    <div className="page-content" style={{ padding: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: isMobile ? '20px' : '32px', gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '12px' : '16px' }}>
          <button 
            onClick={() => navigate(-1)}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', background: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: '50%', cursor: 'pointer' }}
          >
            <ArrowLeft size={20} color="var(--text-primary)" />
          </button>
          <div>
            <h1 style={{ fontSize: isMobile ? 'clamp(18px, 5vw, 28px)' : '28px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{data.symbol}</h1>
            <div style={{ color: 'var(--text-secondary)', fontSize: 'clamp(12px, 2vw, 14px)' }}>{data.exchange}</div>
          </div>
        </div>
        
        <button 
          onClick={toggleWatchlist}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: isMobile ? '8px 12px' : '10px 20px', background: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: '24px', cursor: 'pointer', fontWeight: 600, color: isWatchlisted ? '#FFB800' : 'var(--text-primary)', fontSize: 'clamp(12px, 2vw, 14px)', whiteSpace: 'nowrap' }}
        >
          <Star fill={isWatchlisted ? '#FFB800' : 'none'} size={isMobile ? 16 : 18} />
          {!isMobile && (isWatchlisted ? 'Watchlisted' : 'Add to Watchlist')}
          {isMobile && (isWatchlisted ? 'Saved' : 'Save')}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2fr 1fr', gap: isMobile ? '16px' : '32px' }}>
        
        {/* Left Column: Chart & Stats */}
        <div>
          <div style={{ fontSize: isMobile ? 'clamp(24px, 7vw, 42px)' : '42px', fontWeight: 700, fontFamily: 'monospace', color: 'var(--text-primary)', marginBottom: '8px', lineHeight: 1.2 }}>
            {formatPrice(data.ltp)}
          </div>
          <div style={{ fontSize: 'clamp(12px, 2vw, 14px)', color: 'var(--text-secondary)', marginBottom: isMobile ? '20px' : '32px' }}>
            Current Market Price
          </div>

          <div style={{ height: isMobile ? '250px' : '400px', border: '1px solid var(--border-default)', borderRadius: '12px', overflow: 'hidden', marginBottom: isMobile ? '20px' : '32px' }}>
            <LightweightChart data={chartData} />
          </div>

          <h2 style={{ fontSize: isMobile ? 'clamp(14px, 3vw, 18px)' : '18px', fontWeight: 600, marginBottom: '16px' }}>Market Depth</h2>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: isMobile ? '12px' : '16px', background: 'var(--bg-card)', padding: isMobile ? '16px' : '24px', borderRadius: '12px', border: '1px solid var(--border-default)' }}>
            <div>
              <div style={{ fontSize: 'clamp(11px, 2vw, 13px)', color: 'var(--text-secondary)' }}>Bid Price</div>
              <div style={{ fontSize: 'clamp(14px, 3vw, 16px)', fontWeight: 600 }}>{formatPrice(data.bid_price)}</div>
            </div>
            <div>
              <div style={{ fontSize: 'clamp(11px, 2vw, 13px)', color: 'var(--text-secondary)' }}>Bid Qty</div>
              <div style={{ fontSize: 'clamp(14px, 3vw, 16px)', fontWeight: 600 }}>{formatCompact(data.bid_quantity)}</div>
            </div>
            <div>
              <div style={{ fontSize: 'clamp(11px, 2vw, 13px)', color: 'var(--text-secondary)' }}>Ask Price</div>
              <div style={{ fontSize: 'clamp(14px, 3vw, 16px)', fontWeight: 600 }}>{formatPrice(data.ask_price)}</div>
            </div>
            <div>
              <div style={{ fontSize: 'clamp(11px, 2vw, 13px)', color: 'var(--text-secondary)' }}>Ask Qty</div>
              <div style={{ fontSize: 'clamp(14px, 3vw, 16px)', fontWeight: 600 }}>{formatCompact(data.ask_quantity)}</div>
            </div>
          </div>
        </div>

        {/* Right Column: AI Insights & Execution */}
        <div>
          <div style={{ background: 'var(--bg-card)', padding: isMobile ? '20px' : '32px', borderRadius: '16px', border: '1px solid var(--border-default)', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: 'rgba(0,0,0,0.05)', padding: '8px', borderRadius: '50%' }}>
                <Info size={isMobile ? 20 : 24} color="var(--text-primary)" />
              </div>
              <h2 style={{ fontSize: isMobile ? 'clamp(14px, 3vw, 18px)' : '20px', fontWeight: 600, margin: 0 }}>QuantumGrow AI</h2>
            </div>
            
            <div style={{ background: 'var(--bg-surface)', padding: isMobile ? '16px' : '20px', borderRadius: '12px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
              <div>
                <div style={{ fontSize: 'clamp(12px, 2vw, 14px)', color: 'var(--text-secondary)', marginBottom: '4px' }}>AI Prediction</div>
                <div style={{ fontSize: isMobile ? 'clamp(16px, 4vw, 20px)' : '20px', fontWeight: 700, color: isBuy ? 'var(--profit)' : 'var(--loss)' }}>{isBuy ? 'Bullish' : 'Bearish'}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 'clamp(12px, 2vw, 14px)', color: 'var(--text-secondary)', marginBottom: '4px' }}>Confidence</div>
                <div style={{ fontSize: isMobile ? 'clamp(16px, 4vw, 20px)' : '20px', fontWeight: 700 }}>{confidence}%</div>
              </div>
            </div>

            {data.explanation ? (
              <div style={{ marginBottom: '24px', background: 'rgba(0, 102, 255, 0.05)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(0, 102, 255, 0.1)' }}>
                <h3 style={{ fontSize: isMobile ? '14px' : '16px', fontWeight: 600, marginBottom: '8px', color: '#0066FF' }}>NVIDIA Nemotron Analysis</h3>
                <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px' }}>{data.explanation.summary}</p>
                
                {data.explanation.supporting_factors && data.explanation.supporting_factors.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px', fontWeight: 600 }}>Supporting Factors</div>
                    <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--profit)' }}>
                      {data.explanation.supporting_factors.map((f: string, i: number) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                )}
                
                {data.explanation.risk_factors && data.explanation.risk_factors.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px', fontWeight: 600 }}>Risk Factors</div>
                    <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--loss)' }}>
                      {data.explanation.risk_factors.map((f: string, i: number) => <li key={i}>{f}</li>)}
                    </ul>
                  </div>
                )}
                
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px', fontWeight: 600 }}>Reasoning</div>
                <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.5 }}>{data.explanation.reasoning}</p>
                
                <div style={{ marginTop: '16px', textAlign: 'center' }}>
                  <button 
                    onClick={handleAnalyze}
                    disabled={analyzing}
                    style={{ padding: '8px 16px', background: 'transparent', color: '#0066FF', border: '1px solid #0066FF', borderRadius: '8px', cursor: analyzing ? 'wait' : 'pointer', fontWeight: 600, fontSize: '13px', opacity: analyzing ? 0.7 : 1 }}
                  >
                    {analyzing ? 'Analyzing with Nemotron AI...' : 'Refresh AI Analysis'}
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ marginBottom: '24px', textAlign: 'center' }}>
                <button 
                  onClick={handleAnalyze}
                  disabled={analyzing}
                  style={{ padding: '10px 20px', background: '#0066FF', color: 'white', border: 'none', borderRadius: '8px', cursor: analyzing ? 'wait' : 'pointer', fontWeight: 600, width: '100%', opacity: analyzing ? 0.7 : 1 }}
                >
                  {analyzing ? 'Analyzing with Nemotron AI...' : 'Ask AI Analyst for Explanation'}
                </button>
              </div>
            )}

            {openTrade ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                <button 
                  onClick={async () => {
                    try {
                      await api.closeTrade(openTrade.id);
                      alert(`Successfully closed position for ${symbol}!`);
                      navigate('/investments');
                    } catch (err) {
                      alert('Failed to close trade.');
                      console.error(err);
                    }
                  }}
                  style={{ padding: isMobile ? '12px 16px' : '16px', background: 'var(--text-primary)', color: 'var(--bg-card)', border: 'none', borderRadius: '12px', fontSize: isMobile ? '14px' : '16px', fontWeight: 600, cursor: 'pointer', minHeight: '44px' }}
                >
                  CLOSE POSITION
                </button>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <button 
                  onClick={() => handleExecute('BUY')}
                  style={{ padding: isMobile ? '12px 16px' : '16px', background: 'var(--profit)', color: 'white', border: 'none', borderRadius: '12px', fontSize: isMobile ? '14px' : '16px', fontWeight: 600, cursor: 'pointer', minHeight: '44px' }}
                >
                  BUY
                </button>
                <button 
                  onClick={() => handleExecute('SELL')}
                  style={{ padding: isMobile ? '12px 16px' : '16px', background: 'var(--loss)', color: 'white', border: 'none', borderRadius: '12px', fontSize: isMobile ? '14px' : '16px', fontWeight: 600, cursor: 'pointer', minHeight: '44px' }}
                >
                  SELL
                </button>
              </div>
            )}
            <div style={{ textAlign: 'center', marginTop: '16px', fontSize: 'clamp(10px, 2vw, 12px)', color: 'var(--text-muted)' }}>
              Simulated Execution
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
