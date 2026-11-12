import React from 'react';
import { Layers, Sparkles } from 'lucide-react';
import { useNavigation } from '../../routes/Router';

interface NavbarProps {
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab = 'overview',
  onTabChange,
}) => {
  const { navigate } = useNavigation();

  const navItems = [
    { id: 'overview', label: 'Overview', available: true },
    { id: 'intersections', label: 'Intersections', available: true },
    { id: 'cameras', label: 'Cameras', available: true },
    { id: 'incidents', label: 'Incidents', available: true },
    { id: 'assistant', label: 'AI Assistant', available: true },
    { id: 'experiments', label: 'Experiments', available: false, tag: 'P4-06' },
  ];

  return (
    <nav className="bg-[#080D10]/90 backdrop-blur-md border-b border-white/[0.08] sticky top-0 z-40 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14 gap-2">
        {/* Branding */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-7 h-7 rounded bg-gradient-to-br from-[#45C982] to-[#23865A] flex items-center justify-center text-[#080D10] font-bold shadow-sm shadow-[#45C982]/20">
            <Layers className="w-4 h-4 stroke-[2.5]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-display font-bold text-base tracking-tight text-white">AEGIS</span>
            <span className="hidden sm:inline text-xs font-mono text-white/50 border-l border-white/15 pl-2">
              Operator Console
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto py-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (item.available && onTabChange) {
                    onTabChange(item.id);
                  }
                }}
                disabled={!item.available}
                className={`relative px-3 py-1.5 text-xs font-mono font-medium rounded transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-white/10 text-white font-semibold border border-white/15'
                    : item.available
                      ? 'text-white/60 hover:text-white hover:bg-white/5'
                      : 'text-white/30 cursor-not-allowed'
                }`}
              >
                <span>{item.label}</span>
                {item.tag && (
                  <span className="text-[10px] text-white/40 font-mono px-1 py-0.2 bg-white/5 border border-white/10 rounded">
                    {item.tag}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Cinematic Experience Switcher */}
        <div className="shrink-0">
          <button
            onClick={() => navigate('/experience')}
            title="Switch to Cinematic Presentation Experience"
            className="px-2.5 py-1 text-xs font-mono font-medium text-[#080D10] bg-[#45C982] hover:bg-[#3db874] rounded transition-all flex items-center gap-1.5 shadow-sm shadow-[#45C982]/20 cursor-pointer"
          >
            <Sparkles className="w-3 h-3 text-[#080D10]" />
            <span className="hidden sm:inline">Cinematic</span>
            <span>Experience</span>
          </button>
        </div>
      </div>
    </nav>
  );
};
