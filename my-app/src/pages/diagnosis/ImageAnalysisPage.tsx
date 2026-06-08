import React from 'react';
import { PageHeader } from 'components/layout/PageHeader';
import { ImageUploadForm } from 'components/medical/ImageUploadForm';
import { ImageAnalysisResults } from 'components/medical/ImageAnalysisResults'; // Add this import
import { Card } from 'components/common/Card';
import { Button } from 'components/common/Button';
import { AgentState } from 'types/medical';

interface ImageAnalysisPageProps {
  workflowState: AgentState | null;
  loading: boolean;
  onSubmitImage: (image: File) => Promise<void>;
  onReset: () => void;
  onContinue?: () => void; 
}

export const ImageAnalysisPage: React.FC<ImageAnalysisPageProps> = ({
  workflowState,
  loading,
  onSubmitImage,
  onReset,
  onContinue
}) => {
  const currentStage = workflowState?.current_workflow_stage || '';
  const isAnalyzing = currentStage === 'analyzing_image';
  const hasResults = workflowState?.skin_lesion_analysis && currentStage === 'image_analysis_complete';

  if (!workflowState) {
    return (
      <div style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <p>⏳ Loading image analysis...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <PageHeader
        title="📸 Medical Image Analysis"
        subtitle={hasResults ? 
          '✅ Image analysis complete - Review results below' :
          'Upload a medical image for AI-powered analysis'
        }
        step={{
          current: 3,
          total: 6,
          description: currentStage.replace('_', ' ')
        }}
        variant={hasResults ? 'success' : 'default'}
      />

      {/* Show Results if Analysis is Complete */}
      {hasResults && (
        <ImageAnalysisResults
          workflowState={workflowState}
          onContinue={onContinue}
          loading={loading}
        />
      )}

      {/* Upload Form - Show if no results yet */}
      {!hasResults && (
        <Card>
          {workflowState?.skin_cancer_risk_detected && (
            <div style={{ 
              background: '#fff3cd', 
              border: '1px solid #ffeaa7',
              padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-md)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              <h4 style={{ margin: '0 0 var(--spacing-sm) 0', color: '#856404' }}>
                ⚠️ Skin Cancer Risk Detected
              </h4>
              <p style={{ margin: 0, fontSize: '14px', color: '#856404' }}>
                Based on your responses, we recommend uploading a clear image of the skin area for AI analysis. 
                This will help determine if further medical evaluation is needed.
              </p>
            </div>
          )}
          
          <ImageUploadForm
            onSubmit={onSubmitImage}
            loading={loading || isAnalyzing}
          />
        </Card>
      )}

      {/* Reset Button */}
      <div style={{ textAlign: 'center', marginTop: 'var(--spacing-md)' }}>
        <Button onClick={onReset} variant="secondary" size="sm">
          🔄 Start Over
        </Button>
      </div>
    </div>
  );
};