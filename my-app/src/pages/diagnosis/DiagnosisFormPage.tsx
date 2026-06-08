import React from 'react';
import { PageHeader } from 'components/layout/PageHeader';
import { DiagnosisForm } from 'components/medical/DiagnosisForm';
import { DiagnosisResults } from 'components/medical/DiagnosisResults';
import { Card } from 'components/common/Card';
import { Button } from 'components/common/Button';
import { AgentState } from 'types/medical';

interface DiagnosisFormPageProps {
  onSubmit: (symptoms: string) => void;
  onContinue?: () => void;
  loading: boolean;
  sessionId: string | null;
  workflowState?: AgentState | null;
  workflowInfo?: any | null;
}

export const DiagnosisFormPage: React.FC<DiagnosisFormPageProps> = ({
  onSubmit,
  onContinue,
  loading,
  sessionId,
  workflowState,
  workflowInfo
}) => {
  const hasResults = workflowState?.textual_analysis && workflowState?.textual_analysis.length > 0;
  const isAnalysisComplete = workflowState?.current_workflow_stage === 'textual_analysis_complete';

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <PageHeader
        title="🩺 AI Medical Diagnosis"
        subtitle={isAnalysisComplete ? 
          '✅ Initial analysis complete - Review results below' : 
          ''
        }
        step={{
          current: 1,
          total: 6,
          description: "Initial symptom analysis"
        }}
        sessionId={sessionId}
        variant={isAnalysisComplete ? 'success' : 'default'}
      />

      {/* Results Section */}
      {hasResults && isAnalysisComplete && (
        <DiagnosisResults
          results={workflowState?.textual_analysis ?? []}
          averageConfidence={workflowState?.average_confidence || 0}
          imageRequired={workflowState.image_required || false}
          onContinue={onContinue}
          loading={loading}
          title="📋 Initial Analysis Results"
          subtitle="Primary symptom analysis completed"
          context="initial_analysis"
        />
      )}
      
      {/* Form Section */}
      {!hasResults && (
        <Card>
          <h2 style={{ 
            color: 'var(--dark)', 
            marginBottom: 'var(--spacing-md)',
            fontSize: '1.5rem'
          }}>
            Describe Your Symptoms
          </h2>
          <DiagnosisForm
            onSubmit={onSubmit}
            loading={loading}
          />
        </Card>
      )}

      {/* Reset Option */}
      {hasResults && (
        <div style={{ textAlign: 'center', marginTop: 'var(--spacing-md)' }}>
          <Button
            onClick={() => window.location.reload()}
            variant="secondary"
            size="sm"
          >
            🔄 Start New Analysis
          </Button>
        </div>
      )}
    </div>
  );
};