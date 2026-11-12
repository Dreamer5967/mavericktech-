import React, { useState, useEffect } from 'react';
import { ArrowUpRight } from 'lucide-react';

interface FloatingNavProps {
  onNavigateToDashboard?: () => void;
  scrollProgress?: number;
}

export const FloatingNav: React.FC<FloatingNavProps> = ({
  onNavigateToDashboard,
  scrollProgress = 0,
}) => {
  const [activeSection, setActiveSection] = useState('overview');
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      setIsScrolled(scrollY > 30);

      const sections = ['overview', 'simulator', 'capabilities', 'pipeline', 'architecture', 'benchmarks', 'faq'];
      for (const sectionId of sections) {
        const el = document.getElementById(sectionId);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 200 && rect.bottom >= 80) {
            setActiveSection(sectionId);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { id: 'overview', label: 'Overview' },
    { id: 'simulator', label: 'Simulator' },
    { id: 'capabilities', label: 'Capabilities' },
    { id: 'pipeline', label: 'Pipeline' },
    { id: 'architecture', label: 'Architecture' },
    { id: 'benchmarks', label: 'Benchmarks' },
    { id: 'faq', label: 'FAQ' },
  ];

  return (
    <>
      {/* Top thin progress bar */}
      <div className="fixed top-0 left-0 right-0 h-[2px] z-[100] bg-slate-100">
        <div
          className="h-full bg-orange-500 transition-all duration-150 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, scrollProgress * 100))}%` }}
        />
      </div>

      {/* Floating Header */}
      <header className="fixed top-4 left-0 right-0 z-50 flex justify-center px-4 pointer-events-none">
        <nav
          className={`
            pointer-events-auto flex items-center justify-between gap-4 px-4 py-2.5 rounded-xl
            transition-all duration-200 max-w-5xl w-full
            ${
              isScrolled
                ? 'bg-white/95 backdrop-blur-md border border-slate-200 shadow-md shadow-slate-900/5'
                : 'bg-white/80 backdrop-blur-sm border border-slate-200/80 shadow-sm'
            }
          `}
        >
          {/* Logo & Operational Status */}
          <a href="#overview" className="flex items-center gap-2.5 text-slate-900 group">
            <div className="w-7 h-7 rounded-lg bg-orange-500 text-white flex items-center justify-center font-bold text-xs tracking-tight shadow-sm shadow-orange-500/20">
              AG
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm tracking-tight text-slate-900">AEGIS</span>
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                Live Grid v2.1
              </span>
            </div>
          </a>

          {/* Nav Items */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = activeSection === item.id;
              return (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className={`
                    px-3 py-1 rounded-md text-xs font-medium transition-colors
                    ${
                      isActive
                        ? 'text-orange-600 font-semibold bg-orange-50'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    }
                  `}
                >
                  {item.label}
                </a>
              );
            })}
          </div>

          {/* Action Button */}
          <div className="flex items-center gap-2">
            {onNavigateToDashboard && (
              <button
                onClick={onNavigateToDashboard}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium text-white bg-orange-500 hover:bg-orange-600 transition shadow-sm hover:shadow"
              >
                <span>Operations Console</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </nav>
      </header>
    </>
  );
};
