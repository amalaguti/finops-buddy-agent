import { API_BASE } from './config.js';

function isDemoMode() {
  return window.location.pathname.startsWith('/demo');
}

/**
 * Send a chat message and consume the SSE stream.
 * Yields { event, data } for each SSE event (message, done, error).
 */
export async function* streamChat(profile, message, messages = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (profile) headers['X-AWS-Profile'] = profile;
  if (isDemoMode()) headers['X-Demo-Mode'] = 'true';

  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, messages: messages || undefined, profile: profile || undefined }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ') && currentEvent) {
        const raw = line.slice(6);
        let data = raw;
        try {
          data = JSON.parse(raw);
        } catch {
          // keep data as raw string if not JSON
        }
        yield { event: currentEvent, data };
        currentEvent = null;
      }
    }
  }
}
