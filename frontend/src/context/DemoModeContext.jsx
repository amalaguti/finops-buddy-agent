import { createContext, useContext, useMemo } from 'react';

const DemoModeContext = createContext(false);

export function DemoModeProvider({ children }) {
  const isDemoMode = useMemo(() => {
    const path = window.location.pathname;
    return path.startsWith('/demo');
  }, []);

  return (
    <DemoModeContext.Provider value={isDemoMode}>
      {children}
    </DemoModeContext.Provider>
  );
}

export function useDemoMode() {
  return useContext(DemoModeContext);
}
