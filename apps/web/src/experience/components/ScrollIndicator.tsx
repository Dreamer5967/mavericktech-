import React from 'react';

interface ScrollIndicatorProps {
  targetId?: string;
}

export const ScrollIndicator: React.FC<ScrollIndicatorProps> = ({ targetId = 'approach' }) => {
  const handleClick = () => {
    const el = document.getElementById(targetId);
    el?.scrollIntoView({ behavior: 'smooth' });
  };
  return (
    <button
      onClick={handleClick}
      aria-label="Scroll to explore architecture"
      className="inline-flex flex-col items-center gap-2 text-white/50 hover:text-[#45C982] transition-colors group cursor-pointer"
    >
      <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-white/40 group-hover:text-white/70 transition-colors">
        Scroll to Explore
      </span>
      <div className="w-[1.5px] h-10 bg-white/10 relative overflow-hidden rounded-full">
        <div className="w-full h-4 bg-[#45C982] rounded-full animate-bounce" />
      </div>
    </button>
  );
};
