import { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, ReferenceLine,
} from 'recharts';
import { COLORS, CHART_THEME } from '../../utils/constants';

interface Props {
  trades: any[];
  height?: number;
}

export default function CumulativePnLChart({ trades, height = 300 }: Props) {
  const data = useMemo(() => {
    let cumulative = 0;
    return trades.map((t, index) => {
      cumulative += t.pnl || 0;
      return {
        index,
        symbol: t.symbol,
        pnl: t.pnl,
        cumulative,
      };
    });
  }, [trades]);

  if (!trades.length) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        No completed trades yet.
      </div>
    );
  }

  const minVal = Math.min(...data.map(d => d.cumulative));
  const maxVal = Math.max(...data.map(d => d.cumulative));

  return (
    <div style={{ height, width: '100%' }}>
      <ResponsiveContainer>
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorPnL" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={COLORS.profit} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={COLORS.profit} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke={CHART_THEME.gridColor}
          />
          <XAxis
            dataKey="index"
            tick={{ fill: CHART_THEME.textColor, fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            minTickGap={30}
          />
          <YAxis
            domain={[minVal < 0 ? minVal * 1.1 : 0, maxVal * 1.1]}
            tick={{ fill: CHART_THEME.textColor, fontSize: 12 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `₹${value.toFixed(0)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: CHART_THEME.tooltipBg,
              borderColor: CHART_THEME.tooltipBorder,
              borderRadius: '8px',
              color: COLORS.textPrimary,
            }}
            formatter={(value: any, name: any) => [
              `₹${Number(value).toFixed(2)}`,
              name === 'cumulative' ? 'Cumulative P&L' : 'Trade P&L',
            ]}
            labelFormatter={() => ''}
          />
          <ReferenceLine y={0} stroke={COLORS.textMuted} strokeDasharray="3 3" />
          <Area
            type="monotone"
            dataKey="cumulative"
            stroke={data[data.length - 1]?.cumulative >= 0 ? COLORS.profit : COLORS.loss}
            fillOpacity={1}
            fill="url(#colorPnL)"
            strokeWidth={2}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
