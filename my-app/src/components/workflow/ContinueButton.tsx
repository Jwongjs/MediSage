import React from 'react';
import { Button } from 'components/common/Button';

interface ContinueButtonProps {
  onContinue: () => void;
  loading?: boolean;
  disabled?: boolean;
  nextStep?: string;
  description?: string;
}

export const ContinueButton: React.FC<ContinueButtonProps> = ({
  onContinue, 
  loading, 
  disabled, 
  nextStep,
  description
}) => (
  <div style={{ textAlign: 'center', marginTop: 'var(--spacing-lg)' }}>
    <Button
      onClick={onContinue}
      disabled={disabled}
      loading={loading}
      variant="primary"
      style={{ minWidth: '200px' }}
    >
      ➡️ Continue to {nextStep || 'Next Step'}
    </Button>
    {description && (
      <div style={{ fontSize: '12px', marginTop: '8px', color: 'var(--secondary)' }}>
        {description}
      </div>
    )}
  </div>
);