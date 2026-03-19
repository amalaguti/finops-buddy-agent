import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'finops_theme';
const VALID_THEMES = ['slate', 'ocean', 'forest', 'sunset', 'midnight', 'neo-matrix'];

function getStoredTheme() {
  if (typeof window === 'undefined') return 'slate';
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return VALID_THEMES.includes(stored) ? stored : 'slate';
}

function applyTheme(themeId) {
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', themeId);
  }
}

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(getStoredTheme);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const setTheme = useCallback((themeId) => {
    if (!VALID_THEMES.includes(themeId)) return;
    setThemeState(themeId);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, themeId);
    }
    applyTheme(themeId);
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return ctx;
}

export { VALID_THEMES, STORAGE_KEY };
