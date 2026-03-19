import { useState, useEffect } from 'react';
import { ThemeProvider } from './context/ThemeContext.jsx';
import { DemoModeProvider } from './context/DemoModeContext.jsx';
import { ProfileProvider } from './context/ProfileContext.jsx';
import { LayoutSidebar } from './layouts/LayoutSidebar.jsx';
import { McpToolingStatusPage } from './pages/McpToolingStatusPage.jsx';

function usePath() {
  const [path, setPath] = useState(
    () => window.location.pathname.replace(/\/+$/, '') || '/',
  );
  useEffect(() => {
    const onPop = () =>
      setPath(window.location.pathname.replace(/\/+$/, '') || '/');
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);
  const navigate = (newPath) => {
    setPath(newPath);
    window.history.pushState({}, '', newPath);
  };
  return [path, navigate];
}

function App() {
  const [path, navigate] = usePath();
  const isMcpToolingStatus =
    path === '/mcp_tooling_status' || path === '/demo/mcp_tooling_status';

  return (
    <ThemeProvider>
      <DemoModeProvider>
        <ProfileProvider>
        <div
          style={{ display: isMcpToolingStatus ? 'none' : 'block' }}
          className="h-screen"
        >
          <LayoutSidebar navigate={navigate} />
        </div>
        <div
          style={{ display: isMcpToolingStatus ? 'block' : 'none' }}
          className="h-screen"
        >
          <McpToolingStatusPage navigate={navigate} />
        </div>
        </ProfileProvider>
      </DemoModeProvider>
    </ThemeProvider>
  );
}

export default App;
