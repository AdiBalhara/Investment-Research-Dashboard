'use client';

interface ConfidenceScoreProps {
  confidence: number;
}

export default function ConfidenceScore({ confidence }: ConfidenceScoreProps) {
  const percentage = Math.round(confidence * 100);
  const level = percentage >= 70 ? 'high' : percentage >= 50 ? 'medium' : 'low';

  return (
    <div className="confidence-container">
      <div className="confidence-bar">
        <div
          className={`confidence-fill ${level}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className={`confidence-label ${level}`}>
        {percentage}%
      </span>
    </div>
  );
}
