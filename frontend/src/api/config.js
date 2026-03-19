/**
 * API base URL for the FinOps backend (finops serve).
 * Set VITE_API_BASE in .env or .env.local to override.
 * When unset, the hosted runtime uses same-origin and Vite dev uses localhost:8000.
 */
const explicitApiBase = import.meta.env.VITE_API_BASE;
const defaultApiBase =
  import.meta.env.DEV ? 'http://127.0.0.1:8000' : window.location.origin;

export const API_BASE = explicitApiBase || defaultApiBase;
