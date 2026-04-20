'use client';

import { useState } from 'react';
import { ExecutionStep } from '@/lib/api';
import ConfidenceScore from './ConfidenceScore';
import ExecutionStepsTimeline from './ExecutionSteps';

interface ExplainabilityPanelProps {
  reasoning: string;
  confidence: number;
  executionSteps: ExecutionStep[];
}

export default function ExplainabilityPanel({ reasoning, confidence, executionSteps }: ExplainabilityPanelProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="explainability-panel">
      <div className="explainability-header" onClick={() => setExpanded(!expanded)} id="explainability-toggle">
        <div className="flex items-center gap-3">
          <span style={{ fontSize: '16px' }}>🧠</span>
          <span style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)' }}>AI Insights</span>
          <ConfidenceScore confidence={confidence} />
        </div>
        <span style={{ color: 'var(--color-text-muted)', fontSize: '14px', transition: 'transform 0.2s', transform: expanded ? 'rotate(180deg)' : 'none' }}>
          ▼
        </span>
      </div>

      {expanded && (
        <div className="explainability-content animate-fade-in">
          {reasoning && (
            <div style={{ marginBottom: 'var(--space-6)' }}>
              <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)' }}>
                💡 Why this result?
              </h4>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
                {reasoning}
              </p>
            </div>
          )}

          {executionSteps.length > 0 && (
            <div>
              <h4 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-3)' }}>
                ⚡ How AI processed this
              </h4>
              <ExecutionStepsTimeline steps={executionSteps} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
