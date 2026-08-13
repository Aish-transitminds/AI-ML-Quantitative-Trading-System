import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useStore } from '../stores/useStore';
import { api } from '../api/client';
import { formatPrice, formatCompact } from '../utils/formatters';
import { ArrowLeft, Star, TrendingUp, TrendingDown, Info } from 'lucide-react';
import LightweightChart from '../components/charts/LightweightChart';

export default function StockDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const { watchlist, addToWatchlist, removeFromWatchlist } = useStore();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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

  const isBuy = data.signal === 'BUY';
  const confidence = data.ml_probability ? (data.ml_probability * 100).toFixed(0) : '--';
  const openTrade = (data.related_trades || []).find((t: any) => t.status === 'OPEN');
  
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
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button 
            onClick={() => navigate(-1)}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', background: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: '50%', cursor: 'pointer' }}
          >
            <ArrowLeft size={20} color="var(--text-primary)" />
          </button>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{data.symbol}</h1>
            <div style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>{data.exchange}</div>
          </div>
        </div>
        
        <button 
          onClick={toggleWatchlist}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', background: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: '24px', cursor: 'pointer', fontWeight: 600, color: isWatchlisted ? '#FFB800' : 'var(--text-primary)' }}
        >
          <Star fill={isWatchlisted ? '#FFB800' : 'none'} size={18} />
          {isWatchlisted ? 'Watchlisted' : 'Add to Watchlist'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '32px' }}>
        
        {/* Left Column: Chart & Stats */}
        <div>
          <div style={{ fontSize: '42px', fontWeight: 700, fontFamily: 'monospace', color: 'var(--text-primary)', marginBottom: '8px' }}>
            {formatPrice(data.ltp)}
          </div>
          <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '32px' }}>
            Current Market Price
          </div>

          <div style={{ height: '400px', border: '1px solid var(--border-default)', borderRadius: '12px', overflow: 'hidden', marginBottom: '32px' }}>
            <LightweightChart data={chartData} />
          </div>

          <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>Market Depth</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '16px', background: 'var(--bg-card)', padding: '24px', borderRadius: '12px', border: '1px solid var(--border-default)' }}>
            <div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Bid Price</div>
              <div style={{ fontSize: '16px', fontWeight: 600 }}>{formatPrice(data.bid_price)}</div>
            </div>
            <div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Bid Qty</div>
              <div style={{ fontSize: '16px', fontWeight: 600 }}>{formatCompact(data.bid_quantity)}</div>
            </div>
            <div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Ask Price</div>
              <div style={{ fontSize: '16px', fontWeight: 600 }}>{formatPrice(data.ask_price)}</div>
            </div>
            <div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Ask Qty</div>
              <div style={{ fontSize: '16px', fontWeight: 600 }}>{formatCompact(data.ask_quantity)}</div>
            </div>
          </div>
        </div>

        {/* Right Column: AI Insights & Execution */}
        <div>
          <div style={{ background: 'var(--bg-card)', padding: '32px', borderRadius: '16px', border: '1px solid var(--border-default)', boxShadow: 'var(--shadow-lg)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <div style={{ background: 'rgba(0,0,0,0.05)', padding: '8px', borderRadius: '50%' }}>
                <Info size={24} color="var(--text-primary)" />
              </div>
              <h2 style={{ fontSize: '20px', fontWeight: 600, margin: 0 }}>QuantumGrow AI</h2>
            </div>
            
            <div style={{ background: 'var(--bg-surface)', padding: '20px', borderRadius: '12px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '4px' }}>AI Prediction</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: isBuy ? 'var(--profit)' : 'var(--loss)' }}>{isBuy ? 'Bullish' : 'Bearish'}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Confidence</div>
                <div style={{ fontSize: '20px', fontWeight: 700 }}>{confidence}%</div>
              </div>
            </div>

            <div style={{ marginBottom: '32px' }}>
              <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Why did the AI choose this?</h3>
              <ul style={{ paddingLeft: '20px', margin: 0, color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.6' }}>
                <li style={{ marginBottom: '8px' }}>
                  {isBuy ? <TrendingUp size={14} color="var(--profit)" style={{ marginRight: '8px', verticalAlign: 'middle' }} /> : <TrendingDown size={14} color="var(--loss)" style={{ marginRight: '8px', verticalAlign: 'middle' }} />}
                  The 20-period moving average has crossed {isBuy ? 'above' : 'below'} the 120-period average.
                </li>
                <li>
                  Order flow imbalance shows {data.bid_quantity > data.ask_quantity ? 'strong buying pressure' : 'strong selling pressure'}.
                </li>
              </ul>
            </div>

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
                  style={{ padding: '16px', background: 'var(--text-primary)', color: 'var(--bg-card)', border: 'none', borderRadius: '12px', fontSize: '16px', fontWeight: 600, cursor: 'pointer' }}
                >
                  CLOSE POSITION
                </button>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <button 
                  onClick={() => handleExecute('BUY')}
                  style={{ padding: '16px', background: 'var(--profit)', color: 'white', border: 'none', borderRadius: '12px', fontSize: '16px', fontWeight: 600, cursor: 'pointer' }}
                >
                  BUY
                </button>
                <button 
                  onClick={() => handleExecute('SELL')}
                  style={{ padding: '16px', background: 'var(--loss)', color: 'white', border: 'none', borderRadius: '12px', fontSize: '16px', fontWeight: 600, cursor: 'pointer' }}
                >
                  SELL
                </button>
              </div>
            )}
            <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
              Simulated Execution
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
