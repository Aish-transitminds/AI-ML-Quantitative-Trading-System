import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { COLORS, CHART_THEME } from '../../utils/constants';
import { humanizeFeature } from '../../utils/formatters';

interface Props {
  features: { name: string; importance: number }[];
  maxItems?: number;
}

export default function FeatureImportanceChart({ features, maxItems = 15 }: Props) {
  const data = useMemo(() =>
    features.slice(0, maxItems).reverse().map(f => ({
      name: humanizeFeature(f.name),
      value: f.importance,
    })),
  [features, maxItems]);

  if (!data.length) return null;

  const maxVal = Math.max(...data.map(d => d.value));

  return (
    <div style={{ width: '100%', height: maxItems * 32 + 40 }}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="name"
            width={140}
            tick={{ fill: CHART_THEME.textColor, fontSize: 11, fontFamily: 'Inter' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: CHART_THEME.tooltipBg,
              border: `1px solid ${CHART_THEME.tooltipBorder}`,
              borderRadius: 8,
              fontSize: 12,
              color: COLORS.textPrimary,
            }}
            formatter={(value: any) => [Number(value).toFixed(4), 'Importance']}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={`rgba(0, 212, 255, ${0.3 + (entry.value / maxVal) * 0.7})`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
