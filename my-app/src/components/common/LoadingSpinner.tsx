import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = 'var(--primary)',
  message
}) => {
  const getSizeValue = () => {
    switch (size) {
      case 'sm': return '20px';
      case 'md': return '40px';
      case 'lg': return '60px';
      default: return '40px';
    }
  };

  const spinnerSize = getSizeValue();

  return (
    <div style={{ textAlign: 'center', padding: 'var(--spacing-lg)' }}>
      <div style={{
        width: spinnerSize,
        height: spinnerSize,
        border: '4px solid #f3f3f3',
        borderTop: `4px solid ${color}`,
        borderRadius: '50%',
        animation: 'spin 1s linear infinite',
        margin: '0 auto'
      }} />
      {message && (
        <p style={{ marginTop: 'var(--spacing-md)', color: 'var(--secondary)' }}>
          {message}
        </p>
      )}
    </div>
  );
};