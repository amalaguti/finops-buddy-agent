import { useState, useEffect } from 'react';
import { useProfile } from '../context/ProfileContext.jsx';
import { getTooling } from '../api/client.js';

export function ToolsPanel() {
  const { profile } = useProfile();
  const [tooling, setTooling] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!profile) {
      setTooling(null);
      setError(null);
      return;
    }
    let cancelled = false;
    setError(null);
    getTooling(profile)
      .then((t) => {
        if (!cancelled) setTooling(t);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });
    return () => { cancelled = true; };
  }, [profile]);

  if (!profile) return <p className="text-sm text-finops-text-secondary">Select a profile</p>;
  if (error) return <p className="text-sm text-red-600">Tools: {error}</p>;
  if (!tooling) return <p className="text-sm text-finops-text-secondary">Loading…</p>;
  const text = typeof tooling.tooling === 'string' ? tooling.tooling : JSON.stringify(tooling.tooling);
  return (
    <div className="space-y-1">
      <h3 className="text-sm font-semibold text-finops-text-primary">Tools available</h3>
      <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-finops-btn-secondary p-2 text-xs text-finops-text-primary">
        {text}
      </pre>
    </div>
  );
}
