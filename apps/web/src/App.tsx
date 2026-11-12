import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { PageTurnTransition } from './components/layout/PageTurnTransition';
import { DashboardPage } from './pages/DashboardPage';
import { ExperiencePage } from './experience/ExperiencePage';
import { NavigationProvider, useNavigation } from './routes/Router';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: true,
      retry: 2,
    },
  },
});

const AppRoutes: React.FC = () => {
  const { currentPath } = useNavigation();

  return (
    <PageTurnTransition currentPath={currentPath}>
      {(activePath) => activePath === '/experience' ? <ExperiencePage /> : <DashboardPage />}
    </PageTurnTransition>
  );
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <NavigationProvider>
          <AppRoutes />
        </NavigationProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
