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
    neutral: 'bg-[#F5F5F5] text-[#262626] border-[#E5E5E5]',
    success: 'bg-[#EAF4EE] text-[#23865A] border-[#D1E8DA]',
    warning: 'bg-[#FFFBEB] text-[#B7791F] border-[#FDE68A]',
    danger: 'bg-[#FDF2F2] text-[#C0392B] border-[#FECACA]',
    outline: 'bg-white text-[#737373] border-[#E5E5E5]',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border transition-colors ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
