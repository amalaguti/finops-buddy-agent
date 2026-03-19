# Capability: ui-themes

## ADDED Requirements

### Requirement: Six built-in themes are available

The web UI SHALL provide exactly six built-in themes with distinct, coherent color palettes: Default (Slate), Ocean, Forest, Sunset, Midnight, and Neo-Matrix. Each theme SHALL define semantic tokens for page background, surfaces, header, text (primary and secondary), borders, accent, and interactive elements (e.g. primary and secondary buttons, badges) so that the entire UI can be themed consistently.

#### Scenario: All six themes are selectable

- **WHEN** the user opens the theme selector in the web UI
- **THEN** all six themes (Default/Slate, Ocean, Forest, Sunset, Midnight, Neo-Matrix) are listed and can be selected

#### Scenario: Each theme applies a distinct palette

- **WHEN** the user selects a theme (e.g. Ocean, Midnight, or Neo-Matrix)
- **THEN** the UI updates to use that theme's palette for background, text, borders, and accents across the layout, header, sidebar, and chat

### Requirement: Theme selector is visible and usable in the UI

The web UI SHALL expose a theme selector control (e.g. in the top header) that allows the user to view the current theme and choose one of the six built-in themes. The selector SHALL be visible on the main app views (e.g. layout with sidebar and chat).

#### Scenario: Theme selector appears in the header

- **WHEN** the user views the main FinOps Buddy layout (sidebar and chat)
- **THEN** a theme selector control is present in the header area

#### Scenario: Selecting a theme updates the UI immediately

- **WHEN** the user selects a different theme from the selector
- **THEN** the applied theme changes immediately without requiring a page reload

### Requirement: Selected theme is persisted across sessions

The web UI SHALL persist the user's theme selection (e.g. in localStorage) so that the chosen theme is restored on subsequent visits or page reloads. The system SHALL apply the persisted theme on load when available; otherwise it SHALL use the default theme (Slate).

#### Scenario: Theme preference is restored on reload

- **WHEN** the user has selected a theme (e.g. Ocean) and then reloads the page or returns later
- **THEN** the UI loads with that theme applied (Ocean), not the default

#### Scenario: First-time or cleared storage uses default theme

- **WHEN** no theme preference is stored (e.g. first visit or cleared localStorage)
- **THEN** the UI uses the Default (Slate) theme

### Requirement: Themed elements use semantic tokens

The layout, header, sidebar, chat view, and shared interactive components (buttons, inputs, badges) SHALL use theme-driven semantic color tokens (e.g. via CSS variables or Tailwind theme extension) so that changing the theme updates backgrounds, text, borders, and accents in those areas consistently.

#### Scenario: Header and layout reflect active theme

- **WHEN** the user switches to the Midnight or Neo-Matrix theme
- **THEN** the header, main layout background, and sidebar use that theme's palette (e.g. dark backgrounds and appropriate text contrast)

#### Scenario: Buttons and badges respect theme

- **WHEN** any theme is active
- **THEN** primary and secondary buttons and badges (e.g. Demo badge) use that theme's accent and surface colors
