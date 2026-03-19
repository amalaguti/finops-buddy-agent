import { useCallback, useEffect, useState } from 'react';
import { getStatus, getTooling } from '../api/client.js';
import { useProfile } from '../context/ProfileContext.jsx';
import { useDemoMode } from '../context/DemoModeContext.jsx';
import { useTheme } from '../context/ThemeContext.jsx';
import { ProfileSelector } from '../components/ProfileSelector.jsx';

function formatDateTime(date) {
  if (!date) return 'n/a';
  return date.toLocaleTimeString();
}

export function McpToolingStatusPage({ navigate }) {
  const { profile } = useProfile();
  const isDemoMode = useDemoMode();
  useTheme(); // subscribe so page repaints when theme changes
  const [status, setStatus] = useState(null);
  const [tooling, setTooling] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const load = useCallback(async () => {
    if (!profile) {
      setStatus(null);
      setTooling(null);
      setError(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [statusData, toolingData] = await Promise.all([
        getStatus(profile),
        getTooling(profile),
      ]);
      setStatus(statusData);
      setTooling(toolingData);
      setLastUpdated(new Date());
    } catch (e) {
      setError(e.message || 'Failed to load MCP/tooling status.');
    } finally {
      setLoading(false);
    }
  }, [profile]);

  useEffect(() => {
    void load();
  }, [load]);

  const ready = Boolean(profile) && Boolean(status) && Boolean(tooling) && !error;
  const mcpStatusText =
    typeof status?.mcp_status === 'string'
      ? status.mcp_status
      : JSON.stringify(status?.mcp_status ?? {}, null, 2);
  const toolingText =
    typeof tooling?.tooling === 'string'
      ? tooling.tooling
      : JSON.stringify(tooling?.tooling ?? {}, null, 2);

  return (
    <div className="flex h-screen flex-col bg-finops-bg-page text-finops-text-primary">
      <header className="flex shrink-0 items-center justify-between border-b border-finops-border bg-finops-bg-header px-4 py-2 shadow-md">
        <h1 className="text-lg font-semibold text-finops-text-header">FinOps Buddy - MCP/Tooling Status</h1>
        <div className="flex items-center gap-4 text-finops-text-header">
          <button
            type="button"
            onClick={() => navigate(isDemoMode ? '/demo' : '/')}
            className="text-sm font-medium opacity-90 hover:opacity-100"
          >
            Back to chat
          </button>
          <div className="[&_label]:text-finops-text-header">
            <ProfileSelector />
          </div>
        </div>
      </header>

      <main className="flex-1 overflow-auto p-4">
        <div className="mx-auto max-w-6xl space-y-4">
          <div className="flex flex-wrap items-center gap-3 rounded-lg border border-finops-border bg-finops-bg-surface p-4">
            <span
              className={
                ready
                  ? 'rounded-full bg-finops-btn-secondary px-3 py-1 text-xs font-semibold text-finops-accent'
                  : 'rounded-full bg-finops-badge/20 px-3 py-1 text-xs font-semibold text-finops-badge'
              }
            >
              {ready ? 'MCP servers loaded / tools ready' : 'Loading or not ready'}
            </span>
            <span className="text-sm text-finops-text-secondary">Profile: {profile || 'No profile selected'}</span>
            <span className="text-sm text-finops-text-secondary">Last updated: {formatDateTime(lastUpdated)}</span>
            <button
              type="button"
              onClick={() => void load()}
              disabled={loading || !profile}
              className="ml-auto rounded bg-finops-btn-primary px-3 py-1.5 text-sm font-medium text-finops-badge-text hover:opacity-90 disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <section className="rounded-lg border border-finops-border bg-finops-bg-surface p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-finops-text-secondary">
              Agent status
            </h2>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded border border-finops-border bg-finops-bg-page p-3">
                <p className="text-xs text-finops-text-secondary">Model</p>
                <p className="text-sm font-medium text-finops-text-primary">{status?.agent?.model_id || '-'}</p>
              </div>
              <div className="rounded border border-finops-border bg-finops-bg-page p-3">
                <p className="text-xs text-finops-text-secondary">Temperature</p>
                <p className="text-sm font-medium text-finops-text-primary">
                  {status?.agent?.temperature ?? '-'}
                </p>
              </div>
              <div className="rounded border border-finops-border bg-finops-bg-page p-3">
                <p className="text-xs text-finops-text-secondary">Max completion tokens</p>
                <p className="text-sm font-medium text-finops-text-primary">
                  {status?.agent?.max_completion_tokens ?? '-'}
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-lg border border-finops-border bg-finops-bg-surface p-4">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-finops-text-secondary">
              MCP server status
            </h2>
            <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded border border-finops-border bg-finops-bg-page p-3 text-xs text-finops-text-primary">
              {mcpStatusText}
            </pre>
          </section>

          <section className="rounded-lg border border-finops-border bg-finops-bg-surface p-4">
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-finops-text-secondary">
              Tools available
            </h2>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded border border-finops-border bg-finops-bg-page p-3 text-xs text-finops-text-primary">
              {toolingText}
            </pre>
          </section>
        </div>
      </main>
    </div>
  );
}
