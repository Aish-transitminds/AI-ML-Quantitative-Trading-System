import { motion } from 'framer-motion';
import { NavLink } from 'react-router-dom';
import { formatPrice } from '../../utils/formatters';
import { Star } from 'lucide-react';
import { useStore } from '../../stores/useStore';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';

interface StockCardProps {
  stock: any;
  index: number;
}

export default function StockCard({ stock, index }: StockCardProps) {
  const { watchlist, addToWatchlist, removeFromWatchlist } = useStore();
  const isWatchlisted = watchlist.includes(stock.symbol);

  const toggleWatchlist = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (isWatchlisted) {
      removeFromWatchlist(stock.symbol);
    } else {
      addToWatchlist(stock.symbol);
    }
  };

  const isBuy = stock.signal === 'BUY';
  const confidence = (stock.ml_probability * 100).toFixed(0);

  return (
    <motion.div
      className="glass-card stock-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.04, ease: [0.16, 1, 0.3, 1] }}
      style={{ position: 'relative', cursor: 'pointer', display: 'block', textDecoration: 'none', color: 'inherit' }}
    >
      <NavLink to={`/stock/${stock.symbol}`} style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>{stock.symbol}</div>
              {stock.passes_liquidity_filter && <span style={{ fontSize: '11px', background: 'var(--bg-hover)', color: 'var(--text-secondary)', padding: '2px 6px', borderRadius: '4px' }}>Liquid</span>}
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{stock.exchange}</div>
          </div>
          <button 
            onClick={toggleWatchlist}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: isWatchlisted ? '#FFB800' : 'var(--text-muted)' }}
          >
            <Star fill={isWatchlisted ? '#FFB800' : 'none'} size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'monospace', color: 'var(--text-primary)' }}>
            {formatPrice(stock.ltp)}
          </div>
          <div style={{ width: '80px', height: '40px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={(() => {
                // Build a meaningful sparkline from real SMMA data
                const smma120 = stock.smma_slow || stock.ltp * 0.98;
                const smma20 = stock.smma_fast || stock.ltp * 0.99;
                const ltp = stock.ltp;
                return [
                  { value: smma120 },
                  { value: (smma120 + smma20) / 2 },
                  { value: smma20 },
                  { value: (smma20 + ltp) / 2 },
                  { value: ltp },
                ];
              })()}>
                <YAxis domain={['dataMin', 'dataMax']} hide />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke={isBuy ? 'var(--profit)' : 'var(--loss)'} 
                  strokeWidth={2} 
                  dot={false} 
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-surface)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-default)' }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>AI Prediction</span>
            <span style={{ fontSize: '14px', fontWeight: 600, color: isBuy ? 'var(--profit)' : 'var(--loss)' }}>
              {isBuy ? 'Bullish' : 'Bearish'} ({confidence}%)
            </span>
          </div>
          <div style={{ background: isBuy ? 'var(--primary)' : 'var(--loss)', color: 'white', padding: '6px 12px', borderRadius: '6px', fontSize: '13px', fontWeight: 600 }}>
            {isBuy ? 'BUY' : 'SELL'}
          </div>
        </div>
      </NavLink>
    </motion.div>
  );
}
