import React from 'react';

interface ErrorPageProps {
  error: string;
  onReset: () => void;
}

export const ErrorPage: React.FC<ErrorPageProps> = ({ error, onReset }) => {
  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
      <div style={{
        background: '#fff5f5',
        border: '2px solid #feb2b2',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--spacing-xl)',
        color: '#c53030'
      }}>
        <h2 style={{ margin: '0 0 var(--spacing-md) 0', fontSize: '1.5rem' }}>
          ❌ Error Occurred
        </h2>
        <p style={{ margin: '0 0 var(--spacing-lg) 0', fontSize: '16px' }}>
          {error}
        </p>
        <button
          onClick={onReset}
          style={{
            padding: 'var(--spacing-md) var(--spacing-lg)',
            background: 'var(--primary)',
            color: 'white',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            fontSize: '16px',
            cursor: 'pointer'
          }}
        >
          🔄 Start Over
        </button>
      </div>
    </div>
  );
};