## Context

The FinOps Buddy web UI uses Tailwind with a single implicit palette (slate grays in layout, header, chat). There is no theme abstraction; colors are hardcoded in components (e.g. `bg-slate-50`, `text-slate-800`, `bg-slate-700`). Users cannot switch appearance. Adding a small set of well-defined themes (six) will improve usability and polish without requiring a full design system overhaul.

## Goals / Non-Goals

**Goals:**

- Apply one active theme globally (background, text, borders, accents, buttons, inputs, badges).
- Expose six built-in themes: Default (Slate), Ocean, Forest, Sunset, Midnight (dark), Neo-Matrix (Matrix + neo-futuristic).
- Provide a theme selector in the UI; selection persists across sessions (localStorage for MVP).
- Keep implementation within existing stack (React, Tailwind, no new runtime deps).

**Non-Goals:**

- User-defined or custom theme creation; no color pickers or theme editor.
- Backend storage of theme preference (no API or settings schema for theme in this change).
- Per-route or per-component theme overrides.
- Automatic system light/dark detection (can be added later).

## Decisions

### 1. Theme application: CSS variables on root

- **Choice:** Define each theme as a set of CSS custom properties on `:root` (or a theme wrapper div). Components use these variables (e.g. `var(--finops-bg-page)`, `var(--finops-text-primary)`).
- **Rationale:** Single place to swap theme (change class or data attribute on root); no need to re-run Tailwind for each theme. Works with Tailwind via `theme.extend.colors` that reference the same variables, or via arbitrary values `bg-[var(--finops-bg-page)]`.
- **Alternative:** Tailwind dark mode + multiple theme configs would require building multiple CSS bundles or dynamic class toggling on many components; variables are simpler and one build.

### 2. Tailwind integration

- **Choice:** Extend `tailwind.config.js` with a small set of semantic color names that map to CSS variables (e.g. `finops-bg-page`, `finops-text-primary`, `finops-accent`). Use these semantic names in components instead of raw slate/blue/green classes where theme should apply.
- **Rationale:** Keeps Tailwind utility workflow; theme switch only updates variable values. Migrate high-impact areas (layout, header, sidebar, chat, buttons) to semantic tokens; leave low-impact or decorative classes as-is if time-constrained.
- **Alternative:** Purely inline `style={{ backgroundColor: 'var(--finops-bg-page)' }}` is possible but less consistent; semantic Tailwind classes are preferred.

### 3. Six theme palettes (design and color patterns)

- **Default (Slate):** Light gray/slate (current look). Page bg light gray, header/sidebar darker slate, text dark gray, accent slate. Neutral and professional.
- **Ocean:** Cool blues and teals. Page bg very light blue/white, header and primary surfaces teal/blue, text dark blue-gray, accent teal. Calm and readable.
- **Forest:** Greens and earth tones. Light green-tinted background, header/surfaces deeper green, text dark green-gray, accent green. Easy on the eyes.
- **Sunset:** Warm ambers and soft oranges. Cream/light amber background, header warm brown/amber, text dark brown, accent amber/orange. Cozy and distinct.
- **Midnight:** Dark theme. Dark blue/slate background, lighter text, header slightly lighter dark, accent a soft blue or teal. Reduces glare for low-light use.
- **Neo-Matrix:** Matrix movie style combined with neo-futuristic design. Deep black or near-black page and surfaces; header and panels in very dark gray/black with subtle green tint. Primary text in bright matrix green (#00ff41 or similar); secondary text in dimmer green or cyan. Borders and dividers in dark matrix green or cyan. Accents in bright green and cyan for a terminal/digital, high-contrast look—sleek and tech-forward while evoking the Matrix “digital rain” aesthetic.

Each theme defines the same semantic tokens (e.g. page bg, surface, header, text primary/secondary, border, accent, button primary/secondary, badge) so one CSS variable set per theme.

### 4. Theme selector placement and UX

- **Choice:** Theme selector in the top header (e.g. dropdown or icon button that opens a small panel) next to existing controls (ArtifactsBasket, etc.). List all six themes by name; optional small color swatch per theme. On select: update root theme class/attribute, write preference to localStorage, re-render.
- **Rationale:** Header is visible on all main views; no new settings page required for MVP.

### 5. Persistence

- **Choice:** `localStorage` key (e.g. `finops_theme`) storing theme id (e.g. `slate`, `ocean`, `forest`, `sunset`, `midnight`, `neo-matrix`). Read on app init; apply before first paint if feasible (small script in index.html or default theme in code so no flash).
- **Rationale:** No backend or app-settings change; simple and sufficient. Optional: later add theme to `config/settings.yaml` and backend so hosted UI can default from server (out of scope here).

### 6. React state and context

- **Choice:** A small `ThemeContext` (or theme slice in existing state) holding current theme id and setter. Root or layout reads from context and sets `data-theme="..."` or class on the main app container; theme CSS (variables) is applied via that attribute/class. Selector component consumes context and updates on change.
- **Rationale:** Single source of truth; any component can read theme for edge cases; selector is the only writer.

## Risks / Trade-offs

- **Risk:** Flash of wrong theme on first load (default theme applied, then localStorage overrides). **Mitigation:** Inline a tiny script in `index.html` that reads `localStorage` and sets `data-theme` on `<html>` before React boots, or ensure default in code matches most users and accept one frame of default.
- **Risk:** Some components ignore semantic tokens and keep hardcoded colors. **Mitigation:** Migrate layout, header, sidebar, chat, and shared controls first; document token names so future components use them.
- **Trade-off:** Fixed set of six themes, no customization. **Mitigation:** Document the variable set so adding more themes or optional settings-driven default is straightforward later.

## Migration Plan

- No backend or data migration. Frontend-only change.
- Deploy: ship updated frontend bundle; users get new theme selector and default (Slate) behavior. Existing users see current look until they switch theme.
- Rollback: revert frontend build; theme key in localStorage is harmless if unused.

## Open Questions

- None for MVP. Optional follow-ups: system preference (prefers-color-scheme) for defaulting to Midnight when user prefers dark; theme in app settings and backend default.
