import React, { createContext, useContext, useEffect, useState } from 'react';

interface NavigationContextType {
  currentPath: string;
  navigate: (path: string) => void;
}

const NavigationContext = createContext<NavigationContextType>({
  currentPath: '/',
  navigate: () => { },
});

function getActivePath(): string {
  if (typeof window === 'undefined') return '/';

  const path = window.location.pathname.toLowerCase();
  const hash = window.location.hash.toLowerCase();
  const search = window.location.search.toLowerCase();

  // Explicit check for /experience in pathname, hash, or query params
  if (
    path === '/experience' ||
    path.startsWith('/experience') ||
    hash === '#/experience' ||
    hash === '#experience' ||
    hash.startsWith('#/experience') ||
    search.includes('view=experience') ||
    search.includes('experience')
  ) {
    return '/experience';
  }

  return '/dashboard';
}

export const NavigationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentPath, setCurrentPath] = useState<string>(getActivePath);

  useEffect(() => {
    const handleLocationChange = () => {
      setCurrentPath(getActivePath());
    };

    window.addEventListener('popstate', handleLocationChange);
    window.addEventListener('hashchange', handleLocationChange);

    return () => {
      window.removeEventListener('popstate', handleLocationChange);
      window.removeEventListener('hashchange', handleLocationChange);
    };
  }, []);

  const navigate = (path: string) => {
    if (typeof window !== 'undefined') {
      try {
        window.history.pushState({}, '', path);
      } catch (e) {
        console.warn('Navigation pushState fallback:', e);
      }
      setCurrentPath(path.startsWith('/experience') ? '/experience' : path);
      window.scrollTo(0, 0);
    }
  };

  return (
    <NavigationContext.Provider value={{ currentPath, navigate }}>
      {children}
    </NavigationContext.Provider>
  );
};

export function useNavigation() {
  return useContext(NavigationContext);
}
