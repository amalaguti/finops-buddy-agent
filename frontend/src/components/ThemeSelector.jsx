import { useState, useRef, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext.jsx';

const THEMES = [
  { id: 'slate', name: 'Slate', swatch: '#64748b' },
  { id: 'ocean', name: 'Ocean', swatch: '#0d9488' },
  { id: 'forest', name: 'Forest', swatch: '#16a34a' },
  { id: 'sunset', name: 'Sunset', swatch: '#d97706' },
  { id: 'midnight', name: 'Midnight', swatch: '#38bdf8' },
  { id: 'neo-matrix', name: 'Neo-Matrix', swatch: '#00ff41' },
];

export function ThemeSelector() {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [open]);

  const current = THEMES.find((t) => t.id === theme) ?? THEMES[0];

  return (
    <div className="relative shrink-0" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-md border border-finops-border/50 bg-black/10 px-2.5 py-1.5 text-sm font-medium text-finops-text-header shadow-sm hover:bg-black/20 focus:outline-none focus:ring-2 focus:ring-finops-accent"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label="Select theme"
      >
        <span
          className="h-4 w-4 shrink-0 rounded-full border border-finops-border"
          style={{ backgroundColor: current.swatch }}
          aria-hidden
        />
        <span>{current.name}</span>
      </button>
      {open && (
        <ul
          className="absolute right-0 top-full z-50 mt-1 min-w-[10rem] rounded border border-finops-border bg-finops-bg-surface py-1 shadow-lg"
          role="listbox"
          aria-label="Theme options"
        >
          {THEMES.map((t) => (
            <li key={t.id} role="option" aria-selected={theme === t.id}>
              <button
                type="button"
                onClick={() => {
                  setTheme(t.id);
                  setOpen(false);
                }}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-finops-text-primary hover:bg-finops-border focus:bg-finops-border focus:outline-none"
              >
                <span
                  className="h-3.5 w-3.5 shrink-0 rounded-full border border-finops-border"
                  style={{ backgroundColor: t.swatch }}
                  aria-hidden
                />
                {t.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
