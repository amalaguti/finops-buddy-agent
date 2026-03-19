## Why

Users benefit from a UI that matches their preference and environment—whether they want a calm light theme, a high-contrast dark mode, or a distinctive palette. Enabling themes improves accessibility, reduces eye strain, and makes the app feel more polished. Offering a small set of well-designed themes (six) keeps the implementation manageable while giving real choice.

## What Changes

- Add **theme support** in the web UI: the app applies a selected theme (CSS variables / Tailwind-aware tokens) across layout, header, sidebar, chat, and shared components.
- Provide **6 built-in themes** with distinct design and color patterns:
  - **Default (Slate)** – Current light gray/slate palette; becomes the named default.
  - **Ocean** – Cool blues and teals, calm and professional.
  - **Forest** – Greens and earth tones, easy on the eyes.
  - **Sunset** – Warm ambers and soft oranges, cozy and readable.
  - **Midnight** – Dark theme with deep blues and slate, low glare for low-light use.
  - **Neo-Matrix** – Matrix movie style meets neo-futuristic: deep black background, bright matrix green and cyan accents, high-contrast terminal/digital aesthetic with a sleek tech feel.
- Add a **theme selector** in the UI (e.g. in header or settings area) so users can switch themes; selection persists (e.g. `localStorage` or optional app settings).
- Ensure **consistent application** of each theme: background, text, borders, accents, and interactive states (buttons, inputs, badges) all follow the theme palette.

## Capabilities

### New Capabilities

- `ui-themes`: The web UI supports multiple visual themes. Users can choose from six built-in themes (Default/Slate, Ocean, Forest, Sunset, Midnight, Neo-Matrix) via a theme selector. The selected theme is applied globally and persisted across sessions. Each theme defines a coherent set of colors for backgrounds, text, borders, and accents.

### Modified Capabilities

- (none)

## Impact

- **Frontend**: New theme system (CSS variables and/or Tailwind theme extension), theme context or store, theme selector component, and updates to `LayoutSidebar`, `ChatView`, and other components to use theme tokens instead of hardcoded colors.
- **Tailwind**: `tailwind.config.js` extended with theme variants or CSS variable-driven colors; possibly a small set of theme-specific classes or data attributes.
- **Persistence**: Theme preference stored in `localStorage` (and optionally later in app settings); no backend change required for MVP.
- **Build**: No new dependencies required; use existing Tailwind and React patterns.
