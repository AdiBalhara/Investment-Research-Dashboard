'use client';

import { ResearchSection } from '@/lib/api';
import CardGrid from './CardGrid';
import TableSection from './TableSection';
import NewsCards from './NewsCards';
import LineChartSection from '../charts/LineChart';
import BarChartSection from '../charts/BarChart';

interface SectionRendererProps {
  section: ResearchSection;
  index: number;
}

type SectionSource = string | string[] | Record<string, unknown> | undefined;

const formatSource = (source: SectionSource) => {
  if (!source) return null;
  if (typeof source === 'string') return source;
  if (Array.isArray(source)) return source.join(', ');
  return JSON.stringify(source);
};

export default function SectionRenderer({ section, index }: SectionRendererProps) {
  const sourceText = formatSource(section.source);
  const explanationText = section.explanation?.trim();

  const renderContent = () => {
    switch (section.render_as) {
      case 'card_grid':
        return <CardGrid data={section.data as Array<{ label: string; value: string; change?: string }>} />;

      case 'table':
        return <TableSection data={section.data as { headers: string[]; rows: string[][] }} />;

      case 'line_chart':
        return <LineChartSection data={section.data as { labels: string[]; series: Array<{ name: string; values: number[] }> }} />;

      case 'bar_chart':
        return <BarChartSection data={section.data as { labels: string[]; series: Array<{ name: string; values: number[] }> }} />;

      case 'news_cards':
        return <NewsCards data={section.data as Array<{ title: string; source: string; sentiment: string; summary: string; url?: string }>} />;

      case 'text':
        return (
          <div style={{ color: 'var(--color-text-secondary)', lineHeight: 1.8, fontSize: 'var(--font-size-sm)' }}>
            {(section.data as { content: string })?.content || JSON.stringify(section.data)}
          </div>
        );

      default:
        return (
          <pre style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)', overflow: 'auto' }}>
            {JSON.stringify(section.data, null, 2)}
          </pre>
        );
    }
  };

  const getIcon = () => {
    switch (section.type) {
      case 'company_overview': return '🏢';
      case 'stock_performance': return '📈';
      case 'financial_comparison': return '📊';
      case 'news_sentiment': return '📰';
      case 'risk_analysis': return '⚠️';
      case 'summary': return '💡';
      default: return '📋';
    }
  };

  return (
    <div className="section-card" style={{ animationDelay: `${index * 100}ms` }}>
      <h3 className="section-title">
        <span>{getIcon()}</span>
        {section.title || section.type}
      </h3>
      {sourceText && (
        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
          Source: {sourceText}
        </div>
      )}
      {renderContent()}
      {explanationText && (
        <div style={{ marginTop: '1rem', color: 'var(--color-text-secondary)', fontSize: '0.9rem', lineHeight: 1.6 }}>
          <strong>Why:</strong> {explanationText}
        </div>
      )}
    </div>
  );
}
