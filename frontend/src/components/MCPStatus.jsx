import { useState, useEffect } from 'react';
import { useProfile } from '../context/ProfileContext.jsx';
import { getStatus } from '../api/client.js';

export function MCPStatus() {
  const { profile } = useProfile();
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!profile) {
      setStatus(null);
      setError(null);
      return;
    }
    let cancelled = false;
    setError(null);
    getStatus(profile)
      .then((s) => {
        if (!cancelled) setStatus(s);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });
    return () => { cancelled = true; };
  }, [profile]);

  if (!profile) return <p className="text-sm text-slate-500">Select a profile</p>;
  if (error) return <p className="text-sm text-red-600">Status: {error}</p>;
  if (!status) return <p className="text-sm text-slate-500">Loading…</p>;
  const text = typeof status.mcp_status === 'string' ? status.mcp_status : JSON.stringify(status.mcp_status);
  return (
    <div className="space-y-1">
      <h3 className="text-sm font-semibold text-slate-700">MCP servers</h3>
      <pre className="whitespace-pre-wrap rounded bg-slate-100 p-2 text-xs text-slate-800">
        {text}
      </pre>
    </div>
  );
}
