'use client';

import { useState } from 'react';
import { api, ResearchResult } from '@/lib/api';

interface SaveReportButtonProps {
  result: ResearchResult;
}

export default function SaveReportButton({ result }: SaveReportButtonProps) {
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      await api.saveReport(
        result.query,
        result as unknown as Record<string, unknown>,
        result.confidence,
      );
      setSaved(true);
    } catch {
      setError('Failed to save');
    } finally {
      setSaving(false);
    }
  };

  if (saved) {
    return (
      <button className="btn btn-ghost btn-sm" disabled id="save-report-btn">
        ✅ Saved
      </button>
    );
  }

  return (
    <>
      <button
        className="btn btn-ghost btn-sm"
        onClick={handleSave}
        disabled={saving}
        id="save-report-btn"
      >
        {saving ? '💾 Saving...' : '💾 Save Report'}
      </button>
      {error && <span style={{ color: 'var(--color-negative)', fontSize: 'var(--font-size-xs)', marginLeft: '8px' }}>{error}</span>}
    </>
  );
}
