import React from 'react';

interface CardProps {
  children: React.ReactNode;
  padding?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
  style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({
  children,
  padding = 'lg',
  variant = 'default',
  style = {}
}) => {
  const getPaddingValue = () => {
    switch (padding) {
      case 'sm': return 'var(--spacing-sm)';
      case 'md': return 'var(--spacing-md)';
      case 'lg': return 'var(--spacing-lg)';
      default: return 'var(--spacing-lg)';
    }
  };

  const getVariantStyles = () => {
    switch (variant) {
      case 'primary': return { background: '#e3f2fd', border: '2px solid var(--primary)' };
      case 'success': return { background: '#e8f5e8', border: '2px solid var(--success)' };
      case 'warning': return { background: '#fff3cd', border: '1px solid var(--warning)' };
      case 'danger': return { background: '#f8d7da', border: '1px solid var(--danger)' };
      default: return { background: 'white', border: 'none' };
    }
  };

  return (
    <div style={{
      ...getVariantStyles(),
      padding: getPaddingValue(),
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-md)',
      ...style
    }}>
      {children}
    </div>
  );
};