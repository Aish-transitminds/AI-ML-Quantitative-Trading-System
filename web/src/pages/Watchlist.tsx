import { useEffect } from 'react';
import { useStore } from '../stores/useStore';
import StockCard from '../components/dashboard/StockCard';

export default function Watchlist() {
  const { watchlist, stocks, fetchWatchlist } = useStore();

  useEffect(() => {
    fetchWatchlist();
  }, []);

  // Filter full stock data for the watchlist symbols
  const watchlistedStocks = stocks.filter(s => watchlist.includes(s.symbol));

  return (
    <div className="page-content" style={{ padding: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)' }}>Watchlist</h1>
      </div>

      {watchlistedStocks.length === 0 ? (
        <div style={{ padding: '60px', background: 'var(--bg-surface)', borderRadius: '12px', textAlign: 'center', border: '1px dashed var(--border-strong)' }}>
          <div style={{ fontSize: '40px', marginBottom: '16px', opacity: 0.5 }}>⭐</div>
          <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>Your watchlist is empty</div>
          <div style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '8px' }}>Use the search bar above to find stocks and add them to your watchlist.</div>
        </div>
      ) : (
        <div className="grid-stocks">
          {watchlistedStocks.map((stock, i) => (
            <StockCard key={stock.symbol} stock={stock} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
