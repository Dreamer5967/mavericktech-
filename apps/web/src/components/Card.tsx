import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  interactive?: boolean;
  elevated?: boolean;
  glowing?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      interactive = false,
      elevated = false,
      glowing = false,
      className = '',
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={`
          rounded-xl p-6 transition-all duration-200 border bg-white
          ${
            elevated
              ? 'border-slate-200 shadow-md shadow-slate-100'
              : 'border-slate-200 shadow-sm'
          }
          ${
            glowing
              ? 'hover:border-orange-300'
              : ''
          }
          ${
            interactive
              ? 'cursor-pointer hover:border-orange-400 hover:shadow-lg hover:shadow-orange-500/5 hover:-translate-y-0.5'
              : ''
          }
          ${className}
        `}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';
