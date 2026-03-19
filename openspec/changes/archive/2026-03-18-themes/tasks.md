## 1. Branch and prep

- [x] 1.1 Create feature branch `feature/themes` (never implement on main); switch to it before implementing

## 2. Theme CSS variables and palettes

- [x] 2.1 Define semantic CSS custom properties (e.g. `--finops-bg-page`, `--finops-bg-surface`, `--finops-bg-header`, `--finops-text-primary`, `--finops-text-secondary`, `--finops-border`, `--finops-accent`, `--finops-btn-primary`, `--finops-btn-secondary`, `--finops-badge`) in a theme stylesheet (e.g. `frontend/src/theme.css` or in `index.css`)
- [x] 2.2 Add six theme blocks (Slate, Ocean, Forest, Sunset, Midnight, Neo-Matrix) that set those variables to distinct color values; apply each block via `[data-theme="slate"]`, `[data-theme="ocean"]`, …, `[data-theme="neo-matrix"]` on root or app container

## 3. Tailwind integration

- [x] 3.1 Extend `frontend/tailwind.config.js` so theme colors are available as utilities (e.g. `bg-finops-bg-page`, `text-finops-text-primary`) using the same CSS variables, so components can use Tailwind classes that resolve to `var(--finops-*)`

## 4. Theme context and persistence

- [x] 4.1 Add a React ThemeContext (e.g. `frontend/src/context/ThemeContext.jsx`) that holds current theme id (slate | ocean | forest | sunset | midnight | neo-matrix) and a setter; provide it from the app root
- [x] 4.2 On init, read theme from localStorage (key e.g. `finops_theme`); if valid, set as current theme; otherwise use `slate`; on theme change, write to localStorage and set `data-theme` on document root or main app container so CSS theme blocks apply

## 5. Theme selector component

- [x] 5.1 Create a ThemeSelector component that lists the six themes by name (and optionally a small color swatch per theme); on select, call the theme context setter so the UI updates and preference is persisted
- [x] 5.2 Add the ThemeSelector to the header in `LayoutSidebar.jsx` (e.g. next to ArtifactsBasket or other header controls)

## 6. Migrate components to semantic tokens

- [x] 6.1 Update `LayoutSidebar.jsx` to use theme semantic tokens for background, header, text, and borders (replace hardcoded slate/white classes with finops-* utilities or variable-based classes)
- [x] 6.2 Update `ChatView.jsx` and other high-visibility components (sidebar panels, DashboardSection, CostsSection, ToolsPanel, ProfileSelector, AccountContext, RefreshIndicator, ArtifactsBasket) to use theme tokens for backgrounds, text, borders, and accents
- [x] 6.3 Update buttons and badges (e.g. Demo badge, primary/secondary buttons) to use theme accent and surface tokens so they respect the active theme

## 7. Optional: prevent theme flash on load

- [x] 7.1 Optionally add a small inline script in `frontend/index.html` that reads `localStorage.getItem('finops_theme')` and sets `document.documentElement.setAttribute('data-theme', value)` before React mounts, so the correct theme is applied on first paint

## 8. Quality: Ruff and Bandit

- [x] 8.1 Run `poetry run ruff check .` and `poetry run ruff format .`; fix any issues
- [x] 8.2 Run `poetry run bandit -c pyproject.toml -r src/`; fix any medium or high severity findings (or suppress with justification)

## 9. Tests

- [x] 9.1 Add frontend unit tests for theme behavior: ThemeContext (default theme, read/write from localStorage, setTheme updates state) and ThemeSelector (renders six themes, selection updates theme); place tests in `frontend/src/` test files (e.g. `ThemeContext.test.jsx`, `ThemeSelector.test.jsx`) and run `npm test` in frontend
- [x] 9.2 Run full pytest suite (`poetry run pytest`) to ensure no regressions

## 10. Final verification

- [x] 10.1 Run `poetry run pip-audit`; address or document any reported vulnerabilities
