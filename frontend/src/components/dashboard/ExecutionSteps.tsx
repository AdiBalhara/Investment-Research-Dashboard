'use client';

import { ExecutionStep } from '@/lib/api';

interface ExecutionStepsProps {
  steps: ExecutionStep[];
}

export default function ExecutionStepsTimeline({ steps }: ExecutionStepsProps) {
  return (
    <div className="execution-timeline">
      {steps.map((step, i) => (
        <div key={i} className="execution-step">
          <div className={`execution-dot ${step.status}`}>
            {step.status === 'success' ? '✓' : step.status === 'error' ? '✗' : '○'}
          </div>
          <div className="execution-info">
            <div className="execution-tool">{formatToolName(step.tool)}</div>
            <div className="execution-input">{step.input}</div>
          </div>
          <div className="execution-duration">
            {step.duration_ms > 0 ? `${(step.duration_ms / 1000).toFixed(1)}s` : ''}
          </div>
        </div>
      ))}
    </div>
  );
}

function formatToolName(tool: string): string {
  return tool
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase());
}
