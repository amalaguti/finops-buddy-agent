import { useProfile } from '../context/ProfileContext.jsx';

/**
 * Non-blocking indicator shown while account/costs data is loading.
 * The page stays visible and usable; panels show their own loading state and update when data arrives.
 */
export function RefreshIndicator() {
  const { profileDataRefreshing, profile } = useProfile();
  if (!profileDataRefreshing) return null;

  return (
    <div
      className="flex shrink-0 items-center justify-center gap-2 border-b border-finops-border bg-finops-accent/10 px-4 py-2"
      role="status"
      aria-live="polite"
      aria-label="Refreshing account and costs data"
    >
      <div className="h-4 w-4 animate-spin rounded-full border-2 border-finops-border border-t-finops-accent" />
      <p className="text-sm font-medium text-finops-text-primary">
        Updating account data and costs for <strong>{profile ?? 'selected profile'}</strong>…
      </p>
    </div>
  );
}
