import { useState, useEffect } from 'react';
import { useProfile } from '../context/ProfileContext.jsx';
import { getContext } from '../api/client.js';

export function AccountContext() {
  const { profile, markAccountLoaded } = useProfile();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!profile) {
      setData(null);
      setError(null);
      return;
    }
    const forProfile = profile;
    let cancelled = false;
    setError(null);
    getContext(profile)
      .then((ctx) => {
        if (!cancelled) setData(ctx);
        markAccountLoaded(forProfile);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
        markAccountLoaded(forProfile);
      });
    return () => { cancelled = true; };
  }, [profile, markAccountLoaded]);

  if (!profile) return <p className="text-sm text-finops-text-secondary">Select a profile</p>;
  if (error) return <p className="text-sm text-red-600">Context: {error}</p>;
  if (!data) return <p className="text-sm text-finops-text-secondary">Loading…</p>;
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-2 gap-y-1 text-sm">
      <dt className="text-finops-text-secondary">Account</dt>
      <dd className="font-mono text-finops-text-primary">{data.account_id}</dd>
      <dt className="text-finops-text-secondary">Role</dt>
      <dd className="text-finops-text-primary">{data.role}</dd>
      <dt className="text-finops-text-secondary">ARN</dt>
      <dd className="truncate font-mono text-finops-text-primary" title={data.arn}>{data.arn}</dd>
    </dl>
  );
}
