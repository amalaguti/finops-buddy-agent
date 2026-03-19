import { useState, useEffect } from 'react';
import { useProfile } from '../context/ProfileContext.jsx';
import { getCosts } from '../api/client.js';

export function CostsSection() {
  const { profile, markCostsLoaded } = useProfile();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!profile) {
      setRows([]);
      setError(null);
      return;
    }
    const forProfile = profile;
    let cancelled = false;
    setError(null);
    getCosts(profile)
      .then((list) => {
        if (!cancelled) setRows(Array.isArray(list) ? list : []);
        markCostsLoaded(forProfile);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
        markCostsLoaded(forProfile);
      });
    return () => { cancelled = true; };
  }, [profile, markCostsLoaded]);

  if (!profile) return <p className="text-sm text-finops-text-secondary">Select a profile</p>;
  if (error) return <p className="text-sm text-red-600">Costs: {error}</p>;
  if (!rows.length) return <p className="text-sm text-finops-text-secondary">No cost data</p>;

  const total = rows.reduce((s, r) => s + (Number(r.cost) || 0), 0);
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-finops-text-primary" title="Costs from the 1st of the month through today.">
        Month to date costs
      </h3>
      <div className="overflow-x-auto rounded border border-finops-border">
        <table className="min-w-full text-sm">
          <thead className="bg-finops-btn-secondary text-left">
            <tr>
              <th className="px-3 py-2 font-medium text-finops-text-primary">Service</th>
              <th className="px-3 py-2 font-medium text-finops-text-primary text-right">Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-finops-border">
            {rows.map((r) => (
              <tr key={r.service}>
                <td className="px-3 py-2 text-finops-text-primary">{r.service}</td>
                <td className="px-3 py-2 text-right font-mono text-finops-text-primary">
                  {Number(r.cost).toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-finops-bg-page font-medium">
            <tr>
              <td className="px-3 py-2 text-finops-text-primary">Total</td>
              <td className="px-3 py-2 text-right font-mono text-finops-text-primary">
                {total.toFixed(2)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
