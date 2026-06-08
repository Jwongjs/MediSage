import React from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  step?: { current: number; total: number; description: string };
  sessionId?: string | null;
  variant?: 'default' | 'success' | 'primary';
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  step,
  sessionId,
  variant = 'default'
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'success': return { background: '#e8f5e8', color: 'var(--success)' };
      case 'primary': return { background: '#e3f2fd', color: 'var(--primary)' };
      default: return { background: '#e3f2fd', color: 'var(--primary)' };
    }
  };

  return (
    <div style={{
      background: 'white',
      padding: 'var(--spacing-lg)',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-md)',
      marginBottom: 'var(--spacing-lg)',
      textAlign: 'center'
    }}>
      <h1 style={{ 
        color: 'var(--primary)', 
        marginBottom: 'var(--spacing-sm)',
        fontSize: '2rem'
      }}>
        {title}
      </h1>
      {subtitle && (
        <p style={{ color: 'var(--secondary)', margin: 0 }}>
          {subtitle}
        </p>
      )}
      
      {step && (
        <div style={{
          ...getVariantStyles(),
          padding: 'var(--spacing-sm)',
          borderRadius: 'var(--radius-sm)',
          marginTop: 'var(--spacing-md)',
          fontSize: '14px'
        }}>
          💡 Step {step.current} of {step.total}: {step.description}
          {variant === 'success' && ' ✅'}
        </div>
      )}
      
      {sessionId && (
        <div style={{ 
          marginTop: 'var(--spacing-sm)', 
          fontSize: '12px', 
          color: 'var(--secondary)',
          fontFamily: 'monospace'
        }}>
          Session: {sessionId}
        </div>
      )}
    </div>
  );
};