'use client';

interface CardGridProps {
  data: Array<{ label: string; value: string; change?: string }>;
}

export default function CardGrid({ data }: CardGridProps) {
  if (!Array.isArray(data)) return null;

  return (
    <div className="card-grid">
      {data.map((item, i) => (
        <div key={i} className="metric-card">
          <div className="metric-label">{item.label}</div>
          <div className="metric-value">{item.value}</div>
          {item.change && (
            <div className={`metric-change ${item.change.startsWith('-') ? 'negative' : 'positive'}`}>
              {item.change.startsWith('-') ? '' : '+'}{item.change}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
