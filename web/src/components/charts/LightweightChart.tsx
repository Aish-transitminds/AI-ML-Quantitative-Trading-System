import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartProps {
  data: { time: number; open: number; high: number; low: number; close: number }[];
}

export default function LightweightChart({ data }: ChartProps) {
  const chartData = useMemo(() => (
    (data || []).map(d => ({
      time: new Date(d.time * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      close: d.close,
    }))
  ), [data]);

  if (!chartData || chartData.length === 0) {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        No chart data available
      </div>
    );
  }

  // Calculate min and max for the Y-axis domain with some padding
  const minClose = Math.min(...chartData.map(d => d.close));
  const maxClose = Math.max(...chartData.map(d => d.close));
  const padding = (maxClose - minClose) * 0.1 || maxClose * 0.05;

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <XAxis dataKey="time" tick={{ fill: '#7C7E8C', fontSize: 12 }} tickLine={false} axisLine={false} />
          <YAxis 
            domain={[minClose - padding, maxClose + padding]} 
            tick={{ fill: '#7C7E8C', fontSize: 12 }} 
            tickLine={false} 
            axisLine={false} 
          />
          <Tooltip formatter={(value:any) => [`₹${Number(value).toFixed(2)}`, 'Close']} />
          <Line type="monotone" dataKey="close" stroke="#00D09C" strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
