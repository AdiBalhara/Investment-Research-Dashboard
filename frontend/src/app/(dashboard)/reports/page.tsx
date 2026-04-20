'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api, ReportListItem } from '@/lib/api';

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const data = await api.listReports(search || undefined);
      setReports(data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleSearch = () => {
    fetchReports();
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this report?')) return;
    try {
      await api.deleteReport(id);
      setReports((prev) => prev.filter((r) => r.id !== id));
    } catch {
      alert('Failed to delete report');
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Saved Reports</h1>
        <p className="page-subtitle">Your research history</p>
      </div>

      <div className="flex gap-3" style={{ marginBottom: 'var(--space-6)' }}>
        <input
          type="text"
          className="input-field"
          placeholder="Search reports..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          id="reports-search"
          style={{ flex: 1 }}
        />
        <button className="btn btn-ghost" onClick={handleSearch} id="reports-search-btn">
          🔍 Search
        </button>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner" />
          <div className="loading-text">Loading reports...</div>
        </div>
      ) : reports.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-text">No reports saved yet. Run a research query and save the results!</div>
        </div>
      ) : (
        <div className="reports-list">
          {reports.map((report) => (
            <div
              key={report.id}
              className="report-item"
              onClick={() => router.push(`/reports/${report.id}`)}
              id={`report-${report.id}`}
            >
              <div>
                <div className="report-query">{report.query}</div>
                <div className="report-date">
                  {new Date(report.created_at).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                  {report.confidence !== null && (
                    <span style={{ marginLeft: '12px', color: report.confidence >= 0.7 ? 'var(--color-positive)' : 'var(--color-warning)' }}>
                      {Math.round(report.confidence * 100)}% confidence
                    </span>
                  )}
                </div>
              </div>
              <button
                className="btn btn-danger btn-sm"
                onClick={(e) => handleDelete(report.id, e)}
                id={`delete-report-${report.id}`}
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
