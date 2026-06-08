import React from 'react';
import { TextualSymptomAnalysisResult } from 'types/medical';
import { Card } from 'components/common/Card';
import { Button } from 'components/common/Button';

interface DiagnosisResultsProps {
  results: TextualSymptomAnalysisResult[];
  averageConfidence: number;
  imageRequired: boolean;
  onContinue?: () => void;
  loading?: boolean;
  title?: string;
  subtitle?: string;
  context?: 'initial_analysis' | 'followup_complete' | 'enhanced'; 
  hideFollowUpMessage?: boolean;  
}

export const DiagnosisResults: React.FC<DiagnosisResultsProps> = ({
  results,
  averageConfidence,
  imageRequired,
  onContinue,
  loading = false,
  title = '📋 Analysis Results',
  subtitle,
  context = 'initial_analysis', 
  hideFollowUpMessage = false
}) => {
  const getButtonVariant = (): 'success' | 'primary' | 'danger' | 'secondary' => {
    return 'success'; //Always green for all continue buttons
  };

  const getNextStepInfo = () => {
    //If context is followup_complete, skip confidence check and show correct next step
    if (context === 'followup_complete' || context === 'enhanced') {
      if (imageRequired) {
        return {
          message: '📸 Medical image upload required for enhanced diagnosis',
          detail: '💡 Medical image will provide more accurate analysis',
          variant: 'warning' as const
        };
      } else {
        return {
          message: '🎯 Ready for comprehensive overall analysis',
          detail: '✅ Enhanced data ready for final diagnosis',
          variant: 'success' as const
        };
      }
    }

    //Original logic for initial analysis
    if (averageConfidence < 0.75 && !hideFollowUpMessage) {
      return {
        message: '📝 Follow-up questions needed to improve accuracy',
        detail: `⚠️ Additional questions will be asked, then image analysis if needed`,
        variant: 'warning' as const
      };
    } else if (imageRequired) {
      return {
        message: '📸 Medical image upload required for skin analysis',
        detail: '💡 Skin-related symptoms detected - image analysis will provide accurate diagnosis',
        variant: 'primary' as const
      };
    } else {
      return {
        message: '🎯 Ready for comprehensive analysis',
        detail: 'High confidence analysis - proceeding to final diagnosis',
        variant: 'success' as const
      };
    }
  };

  const nextStepInfo = getNextStepInfo();

  //Get status text based on context
  const getStatusText = () => {
    if (context === 'followup_complete' || context === 'enhanced') {
      return '✅ Enhanced';
    }
    return '✅ Complete';
  };

  return (
    <Card variant="primary">
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 'var(--spacing-md)'
      }}>
        <h3 style={{ margin: 0 }}>
          {title}
        </h3>
        {/* Show enhanced badge when context indicates it */}
        {(context === 'followup_complete' || context === 'enhanced') && (
          <div style={{
            background: '#e8f5e8',
            color: 'var(--success)',
            padding: '4px 12px',
            borderRadius: 'var(--radius-md)',
            fontSize: '12px',
            fontWeight: '600'
          }}>
            ✨ ENHANCED
          </div>
        )}
      </div>

      {/* Optional subtitle */}
      {subtitle && (
        <p style={{ 
          margin: '0 0 var(--spacing-md) 0',
          color: 'var(--secondary)',
          fontSize: '14px'
        }}>
          {subtitle}
        </p>
      )}
      
      {/* Summary Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gap: 'var(--spacing-md)',
        marginBottom: 'var(--spacing-lg)',
        padding: 'var(--spacing-md)',
        background: 'white',
        borderRadius: 'var(--radius-md)'
      }}>
        <div>
          <strong>Diagnoses Found:</strong>
          <div style={{ fontSize: '1.2rem', color: 'var(--primary)' }}>
            {results.length}
          </div>
        </div>
        
        <div>
          <strong>Average Confidence:</strong>
          <div style={{ 
            fontSize: '1.2rem', 
            color: averageConfidence >= 0.6 ? 'var(--success)' : 'var(--warning)'
          }}>
            {(averageConfidence * 100).toFixed(1)}%
          </div>
        </div>
        
        <div>
          <strong>Status:</strong>
          <div style={{ 
            fontSize: '1rem', 
            color: 'var(--success)',
            fontWeight: '600'
          }}>
            {getStatusText()}
          </div>
        </div>
      </div>

      {/* Detailed Results */}
      <h4 style={{ margin: '0 0 var(--spacing-sm) 0' }}>
        {context === 'followup_complete' || context === 'enhanced' ? 
          'Enhanced Possible Diagnoses:' : 
          'Possible Diagnoses:'
        }
      </h4>
      {results.map((diagnosis, index) => (
        <div key={index} style={{
          background: index === 0 ? '#e8f5e8' : 'white',
          border: `1px solid ${index === 0 ? 'var(--success)' : '#e9ecef'}`,
          borderRadius: 'var(--radius-md)',
          padding: 'var(--spacing-md)',
          marginBottom: 'var(--spacing-sm)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <strong style={{ color: index === 0 ? 'var(--success)' : 'var(--dark)' }}>
              {index === 0 ? '🥇 ' : `${index + 1}. `}
              {diagnosis.text_diagnosis}
            </strong>
          </div>
          <div style={{
            background: diagnosis.diagnosis_confidence >= 0.8 ? 'var(--success)' :
                       diagnosis.diagnosis_confidence >= 0.6 ? 'var(--warning)' : 'var(--danger)',
            color: 'white',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '14px',
            fontWeight: '600'
          }}>
            {(diagnosis.diagnosis_confidence * 100).toFixed(1)}%
          </div>
        </div>
      ))}

      {/*Next Step Information - Context-aware */}
      <Card variant={nextStepInfo.variant} style={{ marginTop: 'var(--spacing-md)' }}>
        <strong>Next Step:</strong> {nextStepInfo.message}
        <div style={{ fontSize: '14px', marginTop: '4px', fontStyle: 'italic' }}>
          {nextStepInfo.detail}
        </div>
      </Card>

      {/*Continue Button - Context-aware */}
      <div style={{ marginTop: 'var(--spacing-lg)', textAlign: 'center' }}>
        <Button
          onClick={onContinue}
          disabled={loading}
          loading={loading}
          variant={getButtonVariant()}
          style={{ minWidth: '200px' }}
        >
          {/* {imageRequired ? ( */}
            <>Continue</>
          {/* // ) : (
          //   context === 'followup_complete' || context === 'enhanced' ? 
          //     <>🎯 Continue to Overall Analysis</> : 
          //     <>➡️ Continue to Next Step</>
          // )} */}
        </Button>
      </div>
    </Card>
  );
};