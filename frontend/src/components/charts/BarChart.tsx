'use client';

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

interface BarChartProps {
  data: {
    labels: string[];
    series: Array<{ name: string; values: number[] }>;
  };
}

const COLORS = ['#6366f1', '#8b5cf6', '#34d399', '#fbbf24', '#f87171', '#38bdf8'];

export default function BarChartSection({ data }: BarChartProps) {
  if (!data?.labels || !data?.series) return null;

  const chartData = data.labels.map((label, i) => {
    const point: Record<string, string | number> = { name: label };
    data.series.forEach((s) => {
      point[s.name] = s.values[i] ?? 0;
    });
    return point;
  });

  return (
    <div style={{ width: '100%', height: 320 }}>
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="name"
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
          />
          <YAxis
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            width={60}
          />
          <Tooltip
            contentStyle={{
              background: '#1a2035',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '10px',
              color: '#f1f5f9',
              fontSize: '13px',
            }}
          />
          <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }} />
          {data.series.map((s, i) => (
            <Bar
              key={s.name}
              dataKey={s.name}
              fill={COLORS[i % COLORS.length]}
              radius={[4, 4, 0, 0]}
              maxBarSize={50}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
