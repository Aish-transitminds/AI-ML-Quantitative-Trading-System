import { useEffect } from 'react';
import { useStore } from '../stores/useStore';
import StockCard from '../components/dashboard/StockCard';
import TradingLegends from '../components/dashboard/TradingLegends';

export default function Explore() {
  const { stocks, fetchStocks } = useStore();

  useEffect(() => {
    fetchStocks();
    const interval = setInterval(fetchStocks, 10000);
    return () => clearInterval(interval);
  }, []);

  // Filter top AI picks (strong Buy signals with high ML probability)
  const aiPicks = stocks
    .filter(s => s.signal === 'BUY' && s.ml_probability > 0.6)
    .sort((a, b) => b.ml_probability - a.ml_probability)
    .slice(0, 4);

  // Trending (Top Volume or highest spread for demo)
  const trending = stocks.slice(0, 8);

  return (
    <div className="page-content" style={{ padding: 0 }}>
      {/* Top AI Picks Section */}
      <section style={{ marginBottom: '40px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '24px' }}>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>Top AI Picks</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Stocks with the highest algorithmic confidence for upward momentum.</p>
          </div>
        </div>
        
        {aiPicks.length > 0 ? (
          <div className="grid-stocks" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
            {aiPicks.map((stock, i) => (
              <StockCard key={stock.symbol} stock={stock} index={i} />
            ))}
          </div>
        ) : (
          <div style={{ padding: '40px', background: 'var(--bg-surface)', borderRadius: '12px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No strong AI buy signals at the moment.
          </div>
        )}
      </section>

      {/* Trending Section */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-primary)' }}>Trending on QuantumGrow</h2>
        </div>
        
        <div className="grid-stocks" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}>
          {trending.map((stock, i) => (
            <StockCard key={stock.symbol} stock={stock} index={i} />
          ))}
        </div>
      </section>

      {/* Inspirational Trading Legends Section */}
      <TradingLegends />
    </div>
  );
}
