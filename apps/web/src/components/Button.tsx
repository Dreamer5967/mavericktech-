import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      icon,
      children,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles = `
      inline-flex items-center justify-center font-medium rounded-lg
      transition-all duration-150 cursor-pointer relative overflow-hidden
      focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500
      disabled:opacity-50 disabled:cursor-not-allowed select-none
    `;

    const variantStyles = {
      primary: `
        bg-orange-500 hover:bg-orange-600 text-white
        shadow-sm shadow-orange-500/20 hover:shadow
        active:scale-[0.98]
      `,
      secondary: `
        bg-slate-100 hover:bg-slate-200 text-slate-800
        border border-slate-200
        active:scale-[0.98]
      `,
      outline: `
        border border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-50
        text-slate-800 shadow-sm
        active:scale-[0.98]
      `,
      ghost: `
        text-slate-600 hover:text-slate-900 hover:bg-slate-100
        active:scale-[0.98]
      `,
      danger: `
        bg-rose-600 hover:bg-rose-700 text-white
        shadow-sm
        active:scale-[0.98] focus:ring-rose-500
      `,
    };

    const sizeStyles = {
      sm: 'px-3 py-1.5 text-xs gap-1.5',
      md: 'px-4 py-2 text-sm gap-2',
      lg: 'px-5 py-2.5 text-base gap-2.5',
      xl: 'px-6 py-3 text-base font-semibold gap-2.5',
    };

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin h-4 w-4 mr-2"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {icon && !isLoading && icon}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
