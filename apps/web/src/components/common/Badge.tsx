import React from 'react';

interface BadgeProps {
  variant?: 'neutral' | 'success' | 'warning' | 'danger' | 'outline';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  children,
  className = '',
}) => {
  const variantStyles = {
    neutral: 'bg-white/[0.06] text-white/80 border-white/10',
    success: 'bg-[#45C982]/10 text-[#45C982] border-[#45C982]/25',
    warning: 'bg-[#E9A23B]/10 text-[#E9A23B] border-[#E9A23B]/25',
    danger: 'bg-red-500/10 text-red-400 border-red-500/25',
    outline: 'bg-transparent text-white/60 border-white/15',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium border transition-colors ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
