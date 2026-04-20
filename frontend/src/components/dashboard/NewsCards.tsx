'use client';

interface NewsCardsProps {
  data: Array<{
    title: string;
    source: string;
    sentiment: string;
    summary: string;
    url?: string;
  }>;
}

export default function NewsCards({ data }: NewsCardsProps) {
  if (!Array.isArray(data)) return null;

  return (
    <div className="news-list">
      {data.map((item, i) => (
        <div key={i} className="news-item">
          <div className={`news-sentiment-dot ${item.sentiment || 'neutral'}`} title={item.sentiment} />
          <div style={{ flex: 1 }}>
            <div className="news-title">
              {item.url ? (
                <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: 'inherit' }}>
                  {item.title}
                </a>
              ) : (
                item.title
              )}
            </div>
            <div className="news-meta">{item.source}</div>
            {item.summary && <div className="news-summary">{item.summary}</div>}
          </div>
        </div>
      ))}
    </div>
  );
}
