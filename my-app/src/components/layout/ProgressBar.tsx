// components/layout/ProgressBar.tsx
import React from 'react';

interface ProgressBarProps {
  current: number;
  total: number;
  showPercentage?: boolean;
  color?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  current,
  total,
  showPercentage = false,
  color = 'var(--primary)'
}) => {
  const percentage = Math.min((current / total) * 100, 100);

  return (
    <div style={{ marginTop: 'var(--spacing-sm)' }}>
      <div style={{
        background: 'rgba(255,255,255,0.2)',
        borderRadius: '10px',
        height: '6px',
        overflow: 'hidden'
      }}>
        <div style={{
          background: color,
          height: '100%',
          width: `${percentage}%`,
          transition: 'width 0.3s ease'
        }} />
      </div>
      {showPercentage && (
        <div style={{ 
          fontSize: '12px', 
          color: 'var(--secondary)', 
          marginTop: '4px',
          textAlign: 'center' 
        }}>
          {Math.round(percentage)}% Complete
        </div>
      )}
    </div>
  );
};