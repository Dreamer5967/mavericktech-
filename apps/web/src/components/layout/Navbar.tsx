import React from 'react';
import { Layers } from 'lucide-react';

interface NavbarProps {
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab = 'overview',
  onTabChange,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', available: true },
    { id: 'intersections', label: 'Intersections', available: true },
    { id: 'cameras', label: 'Cameras', available: true },
    { id: 'incidents', label: 'Incidents', available: true },
    { id: 'assistant', label: 'AI Assistant', available: true },
    { id: 'experiments', label: 'Experiments', available: false, tag: 'P4-06' },
  ];

  return (
    <nav className="bg-white border-b border-[#E5E5E5] sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
        {/* Branding */}
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-[#171717] rounded flex items-center justify-center text-white">
            <Layers className="w-4 h-4" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-semibold text-base tracking-tight text-[#171717]">AEGIS</span>
            <span className="hidden sm:inline text-xs text-[#737373] border-l border-[#E5E5E5] pl-2">
              Traffic Management System
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
                className={`relative px-3 py-1.5 text-xs font-medium rounded transition-colors whitespace-nowrap flex items-center gap-1.5 ${isActive
                    ? 'bg-[#F5F5F5] text-[#171717] font-semibold'
                    : item.available
                      ? 'text-[#737373] hover:text-[#171717] hover:bg-[#F5F5F5]'
                      : 'text-[#A3A3A3] cursor-not-allowed'
                  }`}
              >
                <span>{item.label}</span>
                {item.tag && (
                  <span className="text-[10px] text-[#A3A3A3] font-mono px-1 py-0.2 bg-[#F5F5F5] border border-[#E5E5E5] rounded">
                    {item.tag}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
