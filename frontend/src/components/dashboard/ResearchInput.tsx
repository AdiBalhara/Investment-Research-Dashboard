'use client';

import { useState, FormEvent } from 'react';

interface ResearchInputProps {
  onSubmit: (query: string) => void;
  loading: boolean;
}

export default function ResearchInput({ onSubmit, loading }: ResearchInputProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSubmit(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="research-input-container">
      <input
        type="text"
        className="research-input"
        placeholder="Ask anything... e.g., 'Compare AAPL and MSFT revenue growth'"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={loading}
        id="research-query-input"
      />
      <button
        type="submit"
        className="btn btn-primary research-submit-btn"
        disabled={loading || !query.trim()}
        id="research-submit-btn"
      >
        {loading ? '⏳ Analyzing...' : '🔍 Research'}
      </button>
    </form>
  );
}
