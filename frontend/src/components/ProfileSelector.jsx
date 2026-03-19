import { useMemo } from 'react';
import { useProfile } from '../context/ProfileContext.jsx';

function sortedProfiles(list, masterProfile) {
  const master = masterProfile ? list.filter((p) => p === masterProfile) : [];
  const rest = list
    .filter((p) => p !== masterProfile)
    .sort((a, b) => a.localeCompare(b));
  return [...master, ...rest];
}

export function ProfileSelector() {
  const { profiles, masterProfile, profile, setProfile, profilesError } = useProfile();
  const ordered = useMemo(
    () => (profiles?.length ? sortedProfiles(profiles, masterProfile) : []),
    [masterProfile, profiles]
  );
  if (profilesError) {
    return <p className="text-sm text-red-600">Profiles: {profilesError}</p>;
  }
  if (!profiles?.length) {
    return <p className="text-sm text-finops-text-secondary">No profiles</p>;
  }
  return (
    <div className="flex items-center gap-2">
      <label className="text-sm font-medium">Profile</label>
      <select
        value={profile || ''}
        onChange={(e) => setProfile(e.target.value || null)}
        className="rounded border border-finops-border bg-finops-bg-surface px-2 py-1 text-sm text-finops-text-primary focus:border-finops-accent focus:outline-none focus:ring-1 focus:ring-finops-accent"
      >
        {ordered.map((p) => (
          <option key={p} value={p}>
            {p}
          </option>
        ))}
      </select>
    </div>
  );
}
