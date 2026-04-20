'use client';

import { useState, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import { api, ResearchResult } from '@/lib/api';
import SectionRenderer from '@/components/dashboard/SectionRenderer';
import ExplainabilityPanel from '@/components/dashboard/ExplainabilityPanel';

export default function ReportDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const report = await api.getReport(id);
        setQuery(report.query);
        // The result is stored as the full ResearchResult
        const researchResult = report.result as unknown as ResearchResult;
        setResult(researchResult);
      } catch {
        router.push('/reports');
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [id, router]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <div className="loading-text">Loading report...</div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <button className="btn btn-ghost btn-sm" onClick={() => router.push('/reports')} id="back-to-reports">
          ← Back to Reports
        </button>
      </div>

      <div className="page-header">
        <h1 className="page-title" style={{ fontSize: 'var(--font-size-2xl)' }}>{query}</h1>
      </div>

      {result && (
        <>
          <ExplainabilityPanel
            reasoning={result.reasoning}
            confidence={result.confidence}
            executionSteps={result.execution_steps || []}
          />

          {result.sections?.map((section, i) => (
            <SectionRenderer key={i} section={section} index={i} />
          ))}
        </>
      )}
    </div>
  );
}
