'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api, WatchlistItem } from '@/lib/api';

export default function WatchlistPage() {
  const router = useRouter();
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [ticker, setTicker] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState('');

  const fetchWatchlist = async () => {
    try {
      const data = await api.listWatchlist();
      setItems(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleAdd = async () => {
    if (!ticker.trim() || !companyName.trim()) return;
    setAdding(true);
    setError('');
    try {
      const item = await api.addToWatchlist(ticker.trim().toUpperCase(), companyName.trim());
      setItems((prev) => [item, ...prev]);
      setTicker('');
      setCompanyName('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add');
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (id: string) => {
    try {
      await api.removeFromWatchlist(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch {
      alert('Failed to remove');
    }
  };

  const handleResearch = (item: WatchlistItem) => {
    // Navigate to dashboard with pre-filled query via URL params
    const query = `Analyze ${item.company_name} (${item.ticker})`;
    router.push(`/?q=${encodeURIComponent(query)}`);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Watchlist</h1>
        <p className="page-subtitle">Track companies for quick research access</p>
      </div>

      {/* Add to watchlist form */}
      <div className="glass-card" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="flex gap-3" style={{ flexWrap: 'wrap' }}>
          <input
            type="text"
            className="input-field"
            placeholder="Ticker (e.g., AAPL)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            style={{ width: '140px' }}
            id="watchlist-ticker"
          />
          <input
            type="text"
            className="input-field"
            placeholder="Company Name (e.g., Apple Inc.)"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            style={{ flex: 1, minWidth: '200px' }}
            id="watchlist-company"
          />
          <button
            className="btn btn-primary"
            onClick={handleAdd}
            disabled={adding || !ticker.trim() || !companyName.trim()}
            id="watchlist-add-btn"
          >
            {adding ? 'Adding...' : '+ Add'}
          </button>
        </div>
        {error && <p className="form-error" style={{ marginTop: 'var(--space-2)' }}>{error}</p>}
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner" />
          <div className="loading-text">Loading watchlist...</div>
        </div>
      ) : items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">⭐</div>
          <div className="empty-state-text">Your watchlist is empty. Add companies above to track them!</div>
        </div>
      ) : (
        <div className="watchlist-grid">
          {items.map((item) => (
            <div key={item.id} className="watchlist-card" id={`watchlist-${item.ticker}`}>
              <div className="watchlist-ticker">{item.ticker}</div>
              <div className="watchlist-name">{item.company_name}</div>
              <div className="watchlist-actions">
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => handleResearch(item)}
                  id={`research-${item.ticker}`}
                >
                  🔍 Research
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleRemove(item.id)}
                  id={`remove-${item.ticker}`}
                >
                  🗑️
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
