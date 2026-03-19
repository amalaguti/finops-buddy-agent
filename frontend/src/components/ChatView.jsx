import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useProfile } from '../context/ProfileContext.jsx';
import { useTheme } from '../context/ThemeContext.jsx';
import { streamChat } from '../api/chat.js';

const TOAST_AUTO_CLOSE_MS = 10_000;

/** Stacked toast: id, message, phase (for styling), and optional removal timeout id. */
function useToasts() {
  const [toasts, setToasts] = useState([]);
  const nextIdRef = useRef(0);
  const timeoutsRef = useRef(new Map());

  const removeToast = useCallback((id) => {
    const tid = timeoutsRef.current.get(id);
    if (tid != null) {
      clearTimeout(tid);
      timeoutsRef.current.delete(id);
    }
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((message, phase = 'phase') => {
    if (!message || typeof message !== 'string') return;
    const id = ++nextIdRef.current;
    const toast = { id, message, phase };
    setToasts((prev) => [...prev, toast]);
    const tid = setTimeout(() => removeToast(id), TOAST_AUTO_CLOSE_MS);
    timeoutsRef.current.set(id, tid);
  }, [removeToast]);

  const clearAllToasts = useCallback(() => {
    timeoutsRef.current.forEach((tid) => clearTimeout(tid));
    timeoutsRef.current.clear();
    setToasts([]);
  }, []);

  return { toasts, addToast, removeToast, clearAllToasts };
}

/** Build a short label for tool name (strip namespace for display). */
function toolLabel(name) {
  if (!name || typeof name !== 'string') return name ?? '?';
  const parts = name.split(/___|\./);
  return parts[parts.length - 1] || name;
}

/** Normalize content for markdown: preserve newlines, fix line endings. */
function normalizeMarkdownContent(content) {
  if (content == null || typeof content !== 'string') return content || '…';
  return content.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim() || '…';
}

export function ChatView({ onArtifact } = {}) {
  const { profile } = useProfile();
  const { theme } = useTheme(); // subscribe so chat panel repaints when theme changes
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState({ message: null, tools: [] });
  const { toasts, addToast, removeToast, clearAllToasts } = useToasts();
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const suggestedPrompts = [
    'Show me this month’s top services and explain the main cost drivers.',
    'Find optimization opportunities for the selected account and rank them by effort versus savings.',
  ];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, progress]);

  function applySuggestedPrompt(text) {
    setInput(text);
    inputRef.current?.focus();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    if (!profile) {
      setError('Select a profile first.');
      return;
    }
    setError(null);
    setInput('');
    const userMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setProgress({ message: 'Working on your request…', tools: [] });
    let assistantContent = '';
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);
    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      history.push(userMessage);
      for await (const { event, data } of streamChat(
        profile,
        text,
        history.slice(0, -1),
      )) {
        if (event === 'progress' && data) {
          const phase = data.phase;
          const tool = data.tool;
          if (phase === 'thinking' && data.message) {
            setProgress((p) => ({ ...p, message: data.message, tools: [] }));
            addToast(data.message, 'thinking');
          } else if ((phase === 'phase' || phase === 'heartbeat') && data.message) {
            setProgress((p) => ({ ...p, message: data.message }));
            // Do not add "Still working... Xs elapsed" heartbeats to the toast stack
            if (phase !== 'heartbeat') addToast(data.message, phase);
          } else if (phase === 'mcp_loading' && data.message) {
            setProgress((p) => ({ ...p, message: data.message }));
            addToast(data.message, 'mcp_loading');
          } else if ((phase === 'tool_start' || phase === 'tool_end') && tool) {
            setProgress((p) => ({
              ...p,
              tools: [...p.tools, { phase, tool }],
            }));
          }
        } else if (event === 'artifact' && data && onArtifact) {
          onArtifact({ type: data.type, title: data.title, content: data.content });
        } else if (event === 'message' && data?.content != null) {
          assistantContent = data.content;
          setProgress({ message: null, tools: [] });
          clearAllToasts();
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = { role: 'assistant', content: assistantContent };
            return next;
          });
        } else if (event === 'error' && data?.detail) {
          setError(data.detail);
          setProgress({ message: null, tools: [] });
          clearAllToasts();
        } else if (event === 'done') {
          setProgress({ message: null, tools: [] });
          clearAllToasts();
        }
      }
    } catch (e) {
      setError(e.message);
      setMessages((prev) => prev.slice(0, -1));
      setProgress({ message: null, tools: [] });
      clearAllToasts();
    } finally {
      setLoading(false);
    }
  }

  const toolSummary = progress.tools.length
    ? [...new Set(progress.tools.map((t) => t.tool))].map(toolLabel)
    : [];

  return (
    <div className="flex h-full flex-col bg-finops-bg-surface">
      <div className="relative flex-1 overflow-y-auto">
        {toasts.length > 0 && (
          <div className="absolute right-4 top-4 z-20 flex max-w-sm flex-col gap-2">
            {toasts.map((t) => (
              <div
                key={t.id}
                className={`flex items-start gap-3 rounded-xl border bg-finops-bg-surface/95 px-4 py-3 text-sm shadow-lg backdrop-blur-sm ${t.phase === 'mcp_loading' ? 'border-finops-accent' : 'border-finops-border'}`}
              >
                {t.phase === 'mcp_loading' && (
                  <div
                    className="h-4 w-4 shrink-0 mt-0.5 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600"
                    aria-hidden
                  />
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-finops-text-primary">{t.message}</p>
                </div>
                <button
                  type="button"
                  onClick={() => removeToast(t.id)}
                  className="shrink-0 rounded p-1 text-finops-text-secondary hover:bg-finops-btn-secondary hover:text-finops-text-primary"
                  aria-label="Dismiss"
                >
                  <span aria-hidden>×</span>
                </button>
              </div>
            ))}
          </div>
        )}
        {messages.length === 0 && !loading && (
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-finops-bg-page/80 to-finops-bg-surface" />
        )}
        <div className="relative space-y-4 p-4">
          {messages.length === 0 && (
            <div className="flex min-h-full items-center justify-center py-4">
              <div className="w-full max-w-6xl overflow-hidden rounded-[2rem] border border-finops-border bg-finops-bg-surface/95 shadow-[0_28px_90px_-34px_rgba(15,23,42,0.38)] backdrop-blur-sm">
                <div className="grid items-stretch md:grid-cols-[1.2fr_0.95fr]">
                  <div className="space-y-5 p-8 lg:p-12">
                    <span className="inline-flex rounded-full bg-finops-btn-secondary px-3 py-1 text-xs font-semibold uppercase tracking-wide text-finops-accent">
                      FinOps Buddy Chat
                    </span>
                    <div className="space-y-3">
                      <h2 className="text-3xl font-semibold text-finops-text-primary lg:text-4xl">
                        Your AWS FinOps workspace is ready
                      </h2>
                      <p className="max-w-2xl text-base leading-7 text-finops-text-secondary">
                        Ask about costs, optimization opportunities, service trends, or account-specific
                        analysis. The chat will use the selected profile context shown above.
                      </p>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <button
                        type="button"
                        onClick={() => applySuggestedPrompt(suggestedPrompts[0])}
                        className="rounded-2xl border border-finops-border bg-finops-btn-secondary p-4 text-left shadow-sm transition hover:border-finops-accent hover:bg-finops-bg-page focus:outline-none focus:ring-2 focus:ring-finops-accent"
                      >
                        <p className="text-xs font-semibold uppercase tracking-wide text-finops-text-secondary">
                          Suggested prompts
                        </p>
                        <p className="mt-2 text-sm leading-6 text-finops-text-primary">
                          “{suggestedPrompts[0]}”
                        </p>
                      </button>
                      <button
                        type="button"
                        onClick={() => applySuggestedPrompt(suggestedPrompts[1])}
                        className="rounded-2xl border border-finops-border bg-finops-btn-secondary p-4 text-left shadow-sm transition hover:border-finops-accent hover:bg-finops-bg-page focus:outline-none focus:ring-2 focus:ring-finops-accent"
                      >
                        <p className="text-xs font-semibold uppercase tracking-wide text-finops-text-secondary">
                          Optimization idea
                        </p>
                        <p className="mt-2 text-sm leading-6 text-finops-text-primary">
                          “{suggestedPrompts[1]}”
                        </p>
                      </button>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div className="rounded-2xl border border-finops-border bg-finops-bg-page p-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-finops-accent">
                          Cost visibility
                        </p>
                        <p className="mt-2 text-sm text-finops-text-primary">
                          Review current-month spend and service breakdowns.
                        </p>
                      </div>
                      <div className="rounded-2xl border border-finops-border bg-finops-bg-page p-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-finops-accent">
                          Account context
                        </p>
                        <p className="mt-2 text-sm text-finops-text-primary">
                          Keep analysis aligned with the currently selected profile.
                        </p>
                      </div>
                      <div className="rounded-2xl border border-finops-border bg-finops-bg-page p-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-finops-accent">
                          Guided actions
                        </p>
                        <p className="mt-2 text-sm text-finops-text-primary">
                          Ask for prioritized recommendations and next steps.
                        </p>
                      </div>
                    </div>
                    <p className="text-xs text-finops-text-secondary">
                      Use the input bar below to start the conversation.
                    </p>
                  </div>
                  <div className="relative flex items-center justify-center overflow-hidden border-t border-finops-border bg-finops-bg-page p-8 md:border-t-0 md:border-l lg:p-10">
                    <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-finops-accent/5 to-transparent" />
                    <div className="absolute inset-y-8 left-0 hidden w-px bg-gradient-to-b from-transparent via-finops-border to-transparent md:block" />
                    <div className="relative w-full max-w-[430px] rounded-[2rem] border border-finops-border bg-finops-bg-surface/90 p-6 shadow-lg backdrop-blur-sm">
                      <div className="absolute inset-x-6 top-5 h-10 rounded-full bg-finops-accent/10 blur-xl" />
                      <img
                        src="/finops_buddy.png"
                        alt="FinOps Buddy"
                        className="relative h-auto max-h-[32rem] w-full object-contain"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === 'user'
                ? 'flex justify-end'
                : 'flex justify-start'
            }
          >
            <div
              className={
                m.role === 'user'
                  ? 'max-w-[85%] rounded-lg bg-finops-btn-primary px-3 py-2 text-sm text-finops-badge-text'
                  : 'max-w-[85%] rounded-lg bg-finops-btn-secondary px-3 py-2 text-sm text-finops-text-primary'
              }
            >
              {m.role === 'user' ? (
                m.content
              ) : (
                <div className="prose prose-sm max-w-none dark:prose-invert prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-ul:list-disc prose-ol:list-decimal prose-ul:pl-5 prose-ol:pl-5 prose-headings:font-semibold prose-headings:text-finops-text-primary prose-p:text-finops-text-primary prose-ul:text-finops-text-primary prose-ol:text-finops-text-primary prose-li:text-finops-text-primary prose-table:border-collapse prose-th:border prose-th:border-finops-border prose-th:bg-finops-btn-secondary prose-th:px-3 prose-th:py-2 prose-th:text-finops-text-primary prose-td:border prose-td:border-finops-border prose-td:px-3 prose-td:py-2 prose-td:text-finops-text-primary prose-pre:bg-finops-bg-header prose-pre:text-finops-text-header prose-code:rounded prose-code:bg-finops-btn-secondary prose-code:text-finops-text-primary prose-code:px-1 prose-code:before:content-none prose-code:after:content-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                    {normalizeMarkdownContent(m.content)}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-lg border border-finops-border bg-finops-btn-secondary px-4 py-3 shadow-sm">
              <div className="flex items-start gap-3">
                <div
                  className="h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-finops-border border-t-finops-accent"
                  aria-hidden
                />
                <div className="min-w-0 text-sm">
                  <p className="font-medium text-finops-text-primary">
                    {progress.message || 'Thinking…'}
                  </p>
                  {toolSummary.length > 0 && (
                    <p className="mt-1 text-finops-text-secondary">
                      Using: {toolSummary.join(', ')}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
        </div>
      </div>
      {error && (
        <div className="border-t border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
      <form
        onSubmit={handleSubmit}
        className="border-t border-finops-border bg-finops-bg-header/95 px-4 py-4 shadow-[0_-12px_30px_-24px_rgba(15,23,42,0.45)] backdrop-blur-sm"
      >
        <div className="flex gap-2 rounded-2xl border border-finops-border bg-finops-bg-surface p-2 shadow-sm ring-1 ring-finops-border/70">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about costs or usage…"
            className="flex-1 rounded-xl border border-transparent bg-finops-btn-secondary px-4 py-3 text-sm text-finops-text-primary placeholder:text-finops-text-secondary focus:border-finops-accent focus:bg-finops-bg-surface focus:outline-none focus:ring-2 focus:ring-finops-accent/30"
            disabled={loading || !profile}
          />
          <button
            type="submit"
            disabled={loading || !profile || !input.trim()}
            className="rounded-xl bg-finops-btn-primary px-5 py-3 text-sm font-medium text-finops-badge-text shadow-sm hover:opacity-90 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}

/** Allow data: URIs and same-origin URLs; block other external images. */
function safeImageSrc(src) {
  if (!src || typeof src !== 'string') return null;
  const s = src.trim();
  if (s.startsWith('data:')) return s;
  try {
    const u = new URL(s, window.location.origin);
    if (u.origin === window.location.origin) return s;
  } catch (_) {}
  return null;
}

const markdownComponents = {
  p: (props) => <p className="my-2 text-finops-text-primary first:mt-0 last:mb-0" {...props} />,
  ul: (props) => <ul className="my-2 list-disc pl-5 text-finops-text-primary" {...props} />,
  ol: (props) => <ol className="my-2 list-decimal pl-5 text-finops-text-primary" {...props} />,
  li: (props) => <li className="my-0.5" {...props} />,
  h2: (props) => <h2 className="mt-3 mb-1.5 text-base font-semibold text-finops-text-primary" {...props} />,
  h3: (props) => <h3 className="mt-2 mb-1 text-sm font-semibold text-finops-text-primary" {...props} />,
  img: ({ src, alt, ...props }) => {
    const safe = safeImageSrc(src);
    if (!safe) return <span className="text-finops-text-secondary italic">[image not shown]</span>;
    return (
      <img
        src={safe}
        alt={alt ?? ''}
        className="my-2 max-w-full rounded-lg shadow-md"
        style={{ maxWidth: 'min(100%, 560px)' }}
        {...props}
      />
    );
  },
  table: (props) => (
    <div className="my-3 overflow-x-auto rounded border border-finops-border">
      <table className="min-w-full text-left text-sm" {...props} />
    </div>
  ),
  thead: (props) => <thead className="bg-finops-btn-secondary" {...props} />,
  th: (props) => (
    <th
      className="border-b border-finops-border px-3 py-2 font-semibold text-finops-text-primary"
      {...props}
    />
  ),
  td: (props) => (
    <td className="border-b border-finops-border/50 px-3 py-2 text-finops-text-primary" {...props} />
  ),
  tr: (props) => <tr className="border-b border-finops-border/50 last:border-0" {...props} />,
  code: ({ inline, children, ...props }) => {
    if (inline) {
      return (
        <code
          className="rounded bg-finops-btn-secondary px-1.5 py-0.5 font-mono text-sm text-finops-text-primary"
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <code
        className="block overflow-x-auto rounded bg-finops-bg-header px-3 py-2 font-mono text-sm text-finops-text-header"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: (props) => (
    <pre
      className="my-2 overflow-x-auto rounded border border-finops-border bg-finops-bg-header px-3 py-2 text-sm text-finops-text-header"
      {...props}
    />
  ),
};
