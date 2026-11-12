import React from 'react';
import { Layers, ArrowRight } from 'lucide-react';
import { useNavigation } from '../../routes/Router';
import { useAegisSnapshot } from '../../hooks/useAegisSnapshot';

interface ExperienceNavProps {
  onSectionClick?: (sectionId: string) => void;
}

export const ExperienceNav: React.FC<ExperienceNavProps> = ({ onSectionClick }) => {
  const { navigate } = useNavigation();
  const { data: snapshot, connectionStatus } = useAegisSnapshot();

  const isConnected = connectionStatus === 'CONNECTED';
  const navLinks = [
    { label: 'Overview', href: '#overview' },
    { label: 'Approach', href: '#approach' },
    { label: 'Intelligence', href: '#intelligence' },
    { label: 'Digital Twin', href: '#digital-twin' },
    { label: 'Impact', href: '#impact' },
    { label: 'Team', href: '#team' },
  ];

  const handleLinkClick = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    e.preventDefault();
    const targetId = href.replace('#', '');
    if (onSectionClick) {
      onSectionClick(targetId);
    } else {
      const el = document.getElementById(targetId);
      el?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#080D10]/85 backdrop-blur-md border-b border-white/[0.08]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/experience')}
            className="flex items-center gap-2.5 text-left group"
          >
            <div className="w-8 h-8 rounded bg-gradient-to-br from-[#45C982] to-[#23865A] flex items-center justify-center text-[#080D10] font-bold shadow-sm shadow-[#45C982]/20">
              <Layers className="w-4 h-4 stroke-[2.5]" />
            </div>
            <div>
              <span className="font-display font-bold text-base tracking-tight text-white block leading-none">
                AEGIS
              </span>
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/50 block mt-0.5">
                Urban Traffic Platform
              </span>
            </div>
          </button>
        </div>

        {/* Navigation links */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              onClick={(e) => handleLinkClick(e, link.href)}
              className="text-xs font-mono uppercase tracking-widest text-white/70 hover:text-[#45C982] transition-colors"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Right Actions: Status & Dashboard Link */}
        <div className="flex items-center gap-4">
          {/* Live system status indicator backed by actual backend state */}
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full border border-white/10 bg-white/[0.03]">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected
                  ? 'bg-[#45C982] shadow-[0_0_8px_#45C982]'
                  : 'bg-[#E9A23B]'
              }`}
            />
            <span className="text-[11px] font-mono text-white/80">
              {isConnected
                ? `LIVE SIM · REV #${snapshot?.state_revision ?? 0}`
                : 'STANDALONE DEMO'}
            </span>
          </div>

          {/* Operator Console Link */}
          <button
            onClick={() => navigate('/dashboard')}
            className="px-3.5 py-1.5 rounded border border-[#45C982]/30 bg-[#45C982]/10 hover:bg-[#45C982]/20 text-[#45C982] text-xs font-mono font-medium tracking-wide transition-all flex items-center gap-1.5 group"
          >
            <span>Operator Console</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </header>
  );
};
