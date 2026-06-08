import React from 'react';

interface ButtonProps {
  onClick?: () => void; 
  disabled?: boolean;
  loading?: boolean;
  variant?: 'primary' | 'secondary' | 'success' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  type?: 'button' | 'submit' | 'reset';
  style?: React.CSSProperties;
}

export const Button: React.FC<ButtonProps> = ({
  onClick,
  disabled = false,
  loading = false,
  variant = 'primary',
  size = 'md',
  children,
  type = 'button',
  style = {}
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary': return { background: 'var(--primary)', color: 'white' };
      case 'secondary': return { background: 'var(--secondary)', color: 'white' };
      case 'success': return { background: 'var(--success)', color: 'white' };
      case 'danger': return { background: 'var(--danger)', color: 'white' };
      default: return { background: 'var(--primary)', color: 'white' };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm': return { padding: 'var(--spacing-sm) var(--spacing-md)', fontSize: '14px' };
      case 'md': return { padding: 'var(--spacing-md) var(--spacing-lg)', fontSize: '16px' };
      case 'lg': return { padding: 'var(--spacing-lg) var(--spacing-xl)', fontSize: '18px' };
      default: return { padding: 'var(--spacing-md) var(--spacing-lg)', fontSize: '16px' };
    }
  };

  const handleClick = (e: React.MouseEvent) => {
    if (type === 'submit') {
      // For submit buttons, don't call onClick - let form handle it
      return;
    }
    if (onClick) {
      onClick();
    }
  };

  return (
    <button
      type={type}
      onClick={handleClick}
      disabled={disabled || loading}
      style={{
        ...getVariantStyles(),
        ...getSizeStyles(),
        border: 'none',
        borderRadius: 'var(--radius-md)',
        fontWeight: '600',
        cursor: (disabled || loading) ? 'not-allowed' : 'pointer',
        opacity: (disabled || loading) ? 0.6 : 1,
        transition: 'all 0.2s ease',
        fontFamily: 'inherit',
        ...style
      }}
    >
      {loading ? '⏳ Loading...' : children}
    </button>
  );
};