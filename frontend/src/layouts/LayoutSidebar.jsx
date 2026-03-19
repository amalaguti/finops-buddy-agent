import { useState, useCallback, useEffect } from 'react';
import { ProfileSelector } from '../components/ProfileSelector.jsx';
import { AccountContext } from '../components/AccountContext.jsx';
import { DashboardSection } from '../components/DashboardSection.jsx';
import { ArtifactsBasket } from '../components/ArtifactsBasket.jsx';
import { ChatView } from '../components/ChatView.jsx';
import { RefreshIndicator } from '../components/RefreshIndicator.jsx';
import { useDemoMode } from '../context/DemoModeContext.jsx';
import { useTheme } from '../context/ThemeContext.jsx';
import { getVersion } from '../api/client.js';
import { ThemeSelector } from '../components/ThemeSelector.jsx';

const SIDEBAR_MIN = 240;
const SIDEBAR_DEFAULT = 720;

export function LayoutSidebar({ navigate }) {
  useTheme(); // subscribe so layout (including chat panel background) repaints when theme changes
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    if (typeof window !== 'undefined') {
      const preferred = window.innerWidth * 0.65; // ~65% of viewport for the left panel
      return Math.max(SIDEBAR_MIN, preferred);
    }
    return SIDEBAR_DEFAULT;
  });
  const [resizing, setResizing] = useState(false);
  const [artifacts, setArtifacts] = useState([]);
  const [versionDisplay, setVersionDisplay] = useState(null);
  const [accountExpanded, setAccountExpanded] = useState(true);
  const isDemoMode = useDemoMode();

  useEffect(() => {
    getVersion()
      .then((data) => setVersionDisplay(data.display ?? data.version ?? null))
      .catch(() => setVersionDisplay(null));
  }, []);
  const addArtifact = useCallback((artifact) => {
    setArtifacts((prev) => [...prev, artifact]);
  }, []);

  const startResize = useCallback(() => setResizing(true), []);

  const onMouseMove = useCallback(
    (e) => {
      if (!resizing) return;
      const next = e.clientX;
      const maxWidth = window.innerWidth * 0.7;
      // state setter receives previous value but we only use next (cursor position)
      setSidebarWidth(() => Math.max(SIDEBAR_MIN, Math.min(maxWidth, next)));
    },
    [resizing],
  );
  const onMouseUp = useCallback(() => setResizing(false), []);

  useEffect(() => {
    if (!resizing) return undefined;
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [resizing, onMouseMove, onMouseUp]);

  return (
    <div className="flex h-screen flex-col bg-finops-bg-page text-finops-text-primary">
      <RefreshIndicator />
      <header className="flex shrink-0 items-center justify-between border-b border-finops-border bg-finops-bg-header px-4 py-2 shadow-md">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-finops-text-header">FinOps Buddy</h1>
          {versionDisplay && (
            <span className="text-sm text-finops-text-header/80" aria-label="Version">
              {versionDisplay}
            </span>
          )}
          {isDemoMode && (
            <span className="rounded bg-finops-badge px-2 py-0.5 text-xs font-bold uppercase text-finops-badge-text">
              Demo
            </span>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-3 text-finops-text-header">
          <ThemeSelector />
          <ArtifactsBasket artifacts={artifacts} />
          <button
            type="button"
            onClick={() => navigate(isDemoMode ? '/demo/mcp_tooling_status' : '/mcp_tooling_status')}
            className="text-sm font-medium opacity-90 hover:opacity-100"
          >
            MCP/tooling status
          </button>
          <div className="[&_label]:text-finops-text-header">
            <ProfileSelector />
          </div>
        </div>
      </header>
      <div className="relative flex flex-1 overflow-hidden">
        <aside
          className="flex shrink-0 flex-col gap-4 overflow-y-auto border-r border-finops-border bg-finops-bg-surface p-4"
          style={{ width: sidebarWidth }}
        >
          <section className="rounded-lg border border-finops-border bg-finops-bg-page p-3">
            <button
              type="button"
              onClick={() => setAccountExpanded((e) => !e)}
              className="flex w-full items-center justify-between gap-2 rounded text-left hover:text-finops-text-primary"
              aria-expanded={accountExpanded}
              aria-label={accountExpanded ? 'Collapse account info' : 'Expand account info'}
            >
              <h2 className="text-xs font-semibold uppercase tracking-wide text-finops-text-secondary">
                Account
              </h2>
              <span
                className={`shrink-0 text-finops-text-secondary transition-transform ${accountExpanded ? 'rotate-180' : ''}`}
                aria-hidden
              >
                ▼
              </span>
            </button>
            {accountExpanded && (
              <div className="mt-2">
                <AccountContext />
              </div>
            )}
          </section>
          <section className="rounded-lg border border-finops-border bg-finops-bg-page p-3">
            <DashboardSection />
          </section>
        </aside>
        <button
          type="button"
          aria-label="Resize sidebar"
          onMouseDown={startResize}
          className="absolute top-0 z-10 w-1.5 shrink-0 cursor-col-resize border-0 bg-finops-resize-handle py-0 hover:bg-finops-resize-handle-hover focus:outline-none focus:ring-2 focus:ring-finops-accent"
          style={{ left: sidebarWidth - 3, height: '100%', marginLeft: 0 }}
        />
        <main className="flex-1 overflow-hidden rounded-l-lg border border-finops-border bg-finops-bg-surface shadow-sm">
          <ChatView onArtifact={addArtifact} />
        </main>
      </div>
    </div>
  );
}
