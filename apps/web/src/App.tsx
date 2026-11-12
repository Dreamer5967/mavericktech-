import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from './pages/DashboardPage';
import { DarkVioletLanding } from './pages/DarkVioletLanding';
import './styles/globals.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: true,
      retry: 2,
    },
  },
});

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'landing' | 'dashboard'>(() => {
    return window.location.hash === '#dashboard' ? 'dashboard' : 'landing';
  });

  useEffect(() => {
    const handleHashChange = () => {
      setCurrentPage(window.location.hash === '#dashboard' ? 'dashboard' : 'landing');
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigateToDashboard = () => {
    window.location.hash = '#dashboard';
    setCurrentPage('dashboard');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const navigateToLanding = () => {
    window.location.hash = '';
    setCurrentPage('landing');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <QueryClientProvider client={queryClient}>
      {currentPage === 'landing' ? (
        <DarkVioletLanding onNavigateToDashboard={navigateToDashboard} />
      ) : (
        <div className="relative min-h-screen bg-slate-900">
          {/* Quick bar to switch between views */}
          <div className="bg-slate-900 border-b border-slate-800 text-xs px-4 py-2 flex items-center justify-between text-slate-300">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">🚦 AEGIS Live Operations</span>
              <span className="text-slate-600">|</span>
              <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Connected to :8000
              </span>
            </div>
            <button
              onClick={navigateToLanding}
              className="text-slate-200 hover:text-white px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded transition font-medium text-xs flex items-center gap-1.5 border border-slate-700"
            >
              ← Back to Landing Page
            </button>
          </div>
          <DashboardPage />
        </div>
      )}
    </QueryClientProvider>
  );
};

export default App;
