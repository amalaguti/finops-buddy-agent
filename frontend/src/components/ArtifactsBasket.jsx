import { useState } from 'react';

/**
 * Collapsible artifacts basket: charts, exported PDFs, and Excel files from the conversation.
 * Session-only; no persistence.
 */
function downloadExtensionForDataUri(content) {
  if (!content || typeof content !== 'string') return 'bin';
  if (content.startsWith('data:image/')) {
    return content.includes('image/png') ? 'png' : 'png';
  }
  if (content.startsWith('data:application/pdf')) return 'pdf';
  if (
    content.includes('spreadsheetml') ||
    content.startsWith('data:application/vnd.openxmlformats-officedocument')
  ) {
    return 'xlsx';
  }
  return 'bin';
}

export function ArtifactsBasket({ artifacts = [] }) {
  const [open, setOpen] = useState(false);

  function downloadOne(artifact, index) {
    const c = artifact?.content;
    if (!c || typeof c !== 'string') return;
    if (
      !c.startsWith('data:image/') &&
      !c.startsWith('data:application/pdf') &&
      !c.includes('spreadsheetml')
    ) {
      return;
    }
    const ext = downloadExtensionForDataUri(c);
    const base = (artifact.title || 'artifact')
      .replace(/[^a-zA-Z0-9_.-]/g, '_')
      .slice(0, 40) || 'artifact';
    const name = `${base}_${index + 1}.${ext}`;
    const a = document.createElement('a');
    a.href = c;
    a.download = name;
    a.click();
  }

  function downloadAll() {
    artifacts.forEach((artifact, index) => {
      const c = artifact?.content;
      if (!c || typeof c !== 'string') return;
      if (
        !c.startsWith('data:image/') &&
        !c.startsWith('data:application/pdf') &&
        !c.includes('spreadsheetml')
      ) {
        return;
      }
      const ext = downloadExtensionForDataUri(c);
      const base = (artifact.title || 'artifact')
        .replace(/[^a-zA-Z0-9_.-]/g, '_')
        .slice(0, 40) || 'artifact';
      const name = `${base}_${index + 1}.${ext}`;
      const a = document.createElement('a');
      a.href = c;
      a.download = name;
      a.click();
    });
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded px-3 py-1.5 text-sm font-medium opacity-90 hover:opacity-100"
        aria-expanded={open}
        aria-haspopup="true"
      >
        <span>Artifacts</span>
        {artifacts.length > 0 && (
          <span className="rounded-full bg-finops-badge px-2 py-0.5 text-xs text-finops-badge-text">
            {artifacts.length}
          </span>
        )}
      </button>
      {open && (
        <>
          <div
            className="fixed inset-0 z-10"
            aria-hidden="true"
            onClick={() => setOpen(false)}
          />
          <div
            className="absolute right-0 top-full z-20 mt-1 w-80 overflow-hidden rounded-lg border border-finops-border bg-finops-bg-surface shadow-lg"
            role="dialog"
            aria-label="Artifacts basket"
          >
            <div className="border-b border-finops-border px-3 py-2 font-medium text-finops-text-primary">
              Artifacts
            </div>
            <div className="max-h-96 overflow-y-auto p-2">
              {artifacts.length === 0 ? (
                <p className="py-4 text-center text-sm text-finops-text-secondary">No artifacts yet</p>
              ) : (
                <ul className="space-y-2">
                  {artifacts.map((artifact, index) => (
                    <li
                      key={index}
                      className="flex items-center gap-2 rounded border border-finops-border bg-finops-bg-page p-2"
                    >
                      {artifact.content?.startsWith('data:image/') ? (
                        <img
                          src={artifact.content}
                          alt={artifact.title || 'Chart'}
                          className="h-14 w-20 shrink-0 rounded object-cover"
                        />
                      ) : artifact.content?.startsWith('data:application/pdf') ? (
                        <div
                          className="h-14 w-20 shrink-0 rounded bg-finops-btn-secondary flex items-center justify-center text-xs font-medium text-finops-text-primary"
                          title="PDF"
                        >
                          PDF
                        </div>
                      ) : artifact.content?.includes('spreadsheetml') ? (
                        <div
                          className="h-14 w-20 shrink-0 rounded bg-finops-btn-secondary flex items-center justify-center text-xs font-medium text-finops-text-primary"
                          title="Excel"
                        >
                          XLSX
                        </div>
                      ) : (
                        <div className="h-14 w-20 shrink-0 rounded bg-finops-btn-secondary flex items-center justify-center text-xs text-finops-text-secondary">
                          —
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-finops-text-primary">
                          {artifact.title || 'Artifact'}
                        </p>
                        <button
                          type="button"
                          onClick={() => downloadOne(artifact, index)}
                          className="mt-1 text-xs text-finops-accent hover:underline"
                        >
                          Download
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {artifacts.length > 0 && (
              <div className="border-t border-finops-border px-3 py-2">
                <button
                  type="button"
                  onClick={downloadAll}
                  className="w-full rounded bg-finops-btn-primary px-3 py-1.5 text-sm font-medium text-finops-badge-text hover:opacity-90"
                >
                  Download all
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
