import React from 'react';

interface StageIndicatorProps {
  stage: string;
  title: string;
  description: string;
  stepNumber?: number;
  totalSteps?: number;
  isComplete?: boolean;
}

export const StageIndicator: React.FC<StageIndicatorProps> = ({
  stage, 
  title, 
  description, 
  stepNumber = 1, 
  totalSteps = 6,
  isComplete = false
}) => {
  return (
    <div style={{
      background: isComplete ? '#e8f5e8' : '#e3f2fd',
      padding: 'var(--spacing-sm)',
      borderRadius: 'var(--radius-sm)',
      marginTop: 'var(--spacing-md)',
      fontSize: '14px',
      color: isComplete ? 'var(--success)' : 'var(--primary)'
    }}>
      💡 Step {stepNumber} of {totalSteps}: {description}
      {isComplete && ' ✅'}
    </div>
  );
};