import React from 'react';
import { Card } from 'components/common/Card';

interface CompletionMessageProps {
  title: string;
  message: string;
  nextStep?: string;
  variant?: 'success' | 'primary' | 'warning';
  autoRedirect?: boolean;
}

export const CompletionMessage: React.FC<CompletionMessageProps> = ({
  title,
  message,
  nextStep,
  variant = 'success',
  autoRedirect = false
}) => {
  return (
    <Card variant={variant} style={{ textAlign: 'center' }}>
      <h3 style={{ color: `var(--${variant})`, margin: '0 0 var(--spacing-md) 0' }}>
        {title}
      </h3>
      <p style={{ margin: '0 0 var(--spacing-sm) 0' }}>
        {message}
      </p>
      {nextStep && (
        <div style={{
          background: 'white',
          padding: 'var(--spacing-md)',
          borderRadius: 'var(--radius-md)',
          margin: 'var(--spacing-md) 0'
        }}>
          <strong>Next Step:</strong> {nextStep}
        </div>
      )}
      {autoRedirect && (
        <p style={{ fontSize: '12px', color: 'var(--secondary)', margin: 0 }}>
          Automatically continuing in 2 seconds...
        </p>
      )}
    </Card>
  );
};