import { API_BASE } from './config.js';

function isDemoMode() {
  return window.location.pathname.startsWith('/demo');
}

function url(path, profile, query = {}) {
  const u = new URL(path, API_BASE);
  if (profile) u.searchParams.set('profile', profile);
  Object.entries(query).forEach(([k, v]) => {
    if (v != null && v !== '') u.searchParams.set(k, String(v));
  });
  return u.toString();
}

function headers(profile) {
  const h = { 'Content-Type': 'application/json' };
  if (profile) h['X-AWS-Profile'] = profile;
  if (isDemoMode()) h['X-Demo-Mode'] = 'true';
  return h;
}

export async function getVersion() {
  const res = await fetch(url('/version'), { headers: headers() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getProfiles() {
  const res = await fetch(url('/profiles'), { headers: headers() });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return {
    profiles: Array.isArray(data) ? data : (data.profiles || []),
    masterProfile: Array.isArray(data) ? null : (data.master_profile || null),
  };
}

export async function getContext(profile) {
  const res = await fetch(url('/context', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

/** In-memory cache for costs: key = `${profileKey}:${YYYY-MM-DD}`, value = list of { service, cost } */
const costsCache = new Map();

function todayKey() {
  return new Date().toISOString().slice(0, 10);
}

export async function getCosts(profile) {
  const profileKey = profile || 'default';
  const dateKey = todayKey();
  const cacheKey = `${profileKey}:${dateKey}`;
  const cached = costsCache.get(cacheKey);
  if (cached !== undefined) return cached;

  const res = await fetch(url('/costs', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  costsCache.set(cacheKey, data);
  return data;
}

/** In-memory cache for dashboard: key = `${profileKey}:${dateKey}`, value = dashboard object (includes 1m/2m/3m savings plans). Cached for session so period selector does not refetch. */
const dashboardCache = new Map();

export async function getCostsDashboard(profile) {
  const profileKey = profile || 'default';
  const dateKey = todayKey();
  const cacheKey = `${profileKey}:${dateKey}`;
  const cached = dashboardCache.get(cacheKey);
  if (cached !== undefined) return cached;

  const res = await fetch(url('/costs/dashboard', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  dashboardCache.set(cacheKey, data);
  return data;
}

/** Cache keys for dashboard slices: `${profileKey}:${dateKey}:sliceName`. */
function dashboardSliceCacheKey(profile, sliceName) {
  const profileKey = profile || 'default';
  const dateKey = todayKey();
  return `${profileKey}:${dateKey}:${sliceName}`;
}

const dashboardByServiceCache = new Map();
export async function getCostsDashboardByService(profile) {
  const key = dashboardSliceCacheKey(profile, 'by-service');
  const cached = dashboardByServiceCache.get(key);
  if (cached !== undefined) return cached;
  const res = await fetch(url('/costs/dashboard/by-service', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  dashboardByServiceCache.set(key, data);
  return data;
}

const dashboardByAccountCache = new Map();
export async function getCostsDashboardByAccount(profile) {
  const key = dashboardSliceCacheKey(profile, 'by-account');
  const cached = dashboardByAccountCache.get(key);
  if (cached !== undefined) return cached;
  const res = await fetch(url('/costs/dashboard/by-account', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  dashboardByAccountCache.set(key, data);
  return data;
}

const dashboardByMarketplaceCache = new Map();
export async function getCostsDashboardByMarketplace(profile) {
  const key = dashboardSliceCacheKey(profile, 'by-marketplace');
  const cached = dashboardByMarketplaceCache.get(key);
  if (cached !== undefined) return cached;
  const res = await fetch(url('/costs/dashboard/by-marketplace', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  dashboardByMarketplaceCache.set(key, data);
  return data;
}

const dashboardRecommendationsCache = new Map();
export async function getCostsDashboardRecommendations(profile) {
  const key = dashboardSliceCacheKey(profile, 'recommendations');
  const cached = dashboardRecommendationsCache.get(key);
  if (cached !== undefined) return cached;
  const res = await fetch(url('/costs/dashboard/recommendations', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  dashboardRecommendationsCache.set(key, data);
  return data;
}

const dashboardAnomaliesCache = new Map();
export async function getCostsDashboardAnomalies(profile) {
  const key = dashboardSliceCacheKey(profile, 'anomalies');
  const cached = dashboardAnomaliesCache.get(key);
  if (cached !== undefined) return cached;
  const res = await fetch(url('/costs/dashboard/anomalies', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  dashboardAnomaliesCache.set(key, data);
  return data;
}

const dashboardSavingsPlansCache = new Map();
export async function getCostsDashboardSavingsPlans(profile) {
  const key = dashboardSliceCacheKey(profile, 'savings-plans');
  const cached = dashboardSavingsPlansCache.get(key);
  if (cached !== undefined) return cached;
  const res = await fetch(url('/costs/dashboard/savings-plans', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  dashboardSavingsPlansCache.set(key, data);
  return data;
}

/** In-memory cache for service/account breakdown: key = `${profileKey}:${dateKey}:${service}`. */
const serviceAccountsCache = new Map();

export async function getServiceAccountsForService(profile, service) {
  const profileKey = profile || 'default';
  const dateKey = todayKey();
  const cacheKey = `${profileKey}:${dateKey}:${service}`;
  const cached = serviceAccountsCache.get(cacheKey);
  if (cached !== undefined) return cached;

  const res = await fetch(
    url('/costs/by-service-accounts', profile, { service }),
    { headers: headers(profile) }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  serviceAccountsCache.set(cacheKey, data);
  return data;
}

/** In-memory cache for account/service breakdown: key = `${profileKey}:${dateKey}:${accountId}`. */
const accountServicesCache = new Map();

export async function getServicesForAccount(profile, accountId) {
  const profileKey = profile || 'default';
  const dateKey = todayKey();
  const cacheKey = `${profileKey}:${dateKey}:${accountId}`;
  const cached = accountServicesCache.get(cacheKey);
  if (cached !== undefined) return cached;

  const res = await fetch(
    url('/costs/by-account-services', profile, { account_id: accountId }),
    { headers: headers(profile) }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const data = await res.json();
  accountServicesCache.set(cacheKey, data);
  return data;
}

export async function getStatus(profile) {
  const res = await fetch(url('/status', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export async function getTooling(profile) {
  const res = await fetch(url('/tooling', profile), { headers: headers(profile) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}
