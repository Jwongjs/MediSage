import React, { useState } from 'react';
import { Input } from 'components/common/Input';
import { Button } from 'components/common/Button';
import { AgentState } from 'types/medical';

interface DiagnosisFormProps {
  onSubmit: (symptoms: string) => void;
  loading?: boolean;
  disabled?: boolean; 
  sessionId?: string | null; 
  workflowState?: AgentState | null;
  workflowInfo?: any | null;
}

export const DiagnosisForm: React.FC<DiagnosisFormProps> = ({
  onSubmit,
  loading = false,
  disabled = false,
  sessionId, 
  workflowState,
  workflowInfo
}) => {
  const [symptoms, setSymptoms] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symptoms.trim()) {
      alert('Please describe your symptoms');
      return;
    }
    onSubmit(symptoms.trim());
  };

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ marginBottom: 'var(--spacing-lg)' }}>
        <Input
          type="textarea"
          value={symptoms}
          onChange={setSymptoms}
          placeholder="Please describe your symptoms in detail (e.g., 'I have a headache, feel nauseous, and have been experiencing dizziness for the past 2 days...')"
          disabled={loading || disabled}
          maxLength={500}
        />
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 'var(--spacing-xs)',
          fontSize: '12px',
          color: 'var(--secondary)'
        }}>
          <span>💡 Be as detailed as possible for better analysis</span>
          <span>{symptoms.length}/500 characters</span>
        </div>
      </div>

      <Button
        type="submit"
        disabled={loading || !symptoms.trim()}
        loading={loading}
        variant="primary"
        style={{ width: '100%' }}
      >
        🚀 Start AI Diagnosis
      </Button>
    </form>
  );
};