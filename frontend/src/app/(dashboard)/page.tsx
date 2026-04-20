'use client';

import { useState } from 'react';
import { api, ResearchResult } from '@/lib/api';
import ResearchInput from '@/components/dashboard/ResearchInput';
import SectionRenderer from '@/components/dashboard/SectionRenderer';
import ExplainabilityPanel from '@/components/dashboard/ExplainabilityPanel';
import SaveReportButton from '@/components/dashboard/SaveReportButton';

export default function DashboardPage() {
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleResearch = async (query: string) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await api.research(query);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Research failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Research Dashboard</h1>
        <p className="page-subtitle">Ask anything about companies, stocks, and markets</p>
      </div>

      <ResearchInput onSubmit={handleResearch} loading={loading} />

      {loading && (
        <div className="loading-container">
          <div className="loading-spinner" />
          <div className="loading-text">Analyzing your query with AI...</div>
        </div>
      )}

      {error && (
        <div className="section-card" style={{ borderColor: 'var(--color-negative)', background: 'var(--color-negative-bg)' }}>
          <p style={{ color: 'var(--color-negative)' }}>⚠️ {error}</p>
        </div>
      )}

      {result && (
        <div className="animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
              Results for: <strong style={{ color: 'var(--color-text-primary)' }}>{result.query}</strong>
            </div>
            <SaveReportButton result={result} />
          </div>

          <ExplainabilityPanel
            reasoning={result.reasoning}
            confidence={result.confidence}
            executionSteps={result.execution_steps}
          />

          {result.sections.map((section, i) => (
            <SectionRenderer key={i} section={section} index={i} />
          ))}
        </div>
      )}

      {!loading && !result && !error && (
        <div className="empty-state">
          <div className="empty-state-icon">🔬</div>
          <div className="empty-state-text">
            Enter a research query to get AI-powered financial insights
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', justifyContent: 'center' }}>
            {[
              'Analyze Apple stock performance',
              'Compare MSFT and GOOGL',
              'Tesla risk analysis',
              'NVIDIA earnings overview',
            ].map((q) => (
              <button
                key={q}
                className="btn btn-ghost btn-sm"
                onClick={() => handleResearch(q)}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
