import React from 'react';
import { PageHeader } from 'components/layout/PageHeader';
import { FollowUpForm } from 'components/medical/FollowUpForm';
import { DiagnosisResults } from 'components/medical/DiagnosisResults';
import { LoadingSpinner } from 'components/common/LoadingSpinner';
import { Card } from 'components/common/Card';
import { Button } from 'components/common/Button';
import { AgentState } from 'types/medical';

interface FollowUpQuestionsPageProps {
  workflowState?: AgentState | null;
  workflowInfo?: any | null;
  loading: boolean;
  onSubmitResponses: (responses: Record<string, string>) => void;
  onContinue?: () => void;
  onReset: () => void;
}

export const FollowUpQuestionsPage: React.FC<FollowUpQuestionsPageProps> = ({
  workflowState,
  workflowInfo,
  loading,
  onSubmitResponses,
  onContinue,
  onReset
}) => {
  const questions = workflowState?.followup_questions || [];
  const currentStage = workflowState?.current_workflow_stage || '';
  const followupType = workflowState?.followup_type || 'standard';
  
  // const isGenerating = currentStage === 'generating_followup_questions';
  const isAwaiting = currentStage === 'awaiting_followup_responses';
  const isComplete = currentStage === 'followup_analysis_complete' && !workflowState?.requires_user_input;
  
  const showForm = isAwaiting && questions.length > 0;
  const showResults = isComplete && workflowState && !workflowState?.requires_user_input;

  // Get the correct diagnosis results
  const getDiagnosisResults = () => {
    // Only show results if we have actual diagnosis (not during transition)
    if (workflowState?.requires_user_input || currentStage === 'generating_followup_questions') {
      return []; // Don't show results during transition
    }

    const followupDiagnosis = workflowState?.followup_diagnosis || [];
    const textualAnalysis = workflowState?.textual_analysis || [];

    const isPlaceholder = (diagnosis: any) => {
      return diagnosis.text_diagnosis?.includes('Placeholder') || 
             diagnosis.text_diagnosis?.includes('Further Evaluation Required') ||
             diagnosis.diagnosis_confidence === null;
    };
    
    // Priority: followup_diagnosis > textual_analysis, but exclude placeholders
    if (followupDiagnosis.length > 0 && !isPlaceholder(followupDiagnosis[0])) {
      return followupDiagnosis;
    }
    else if (textualAnalysis.length > 0 && !isPlaceholder(textualAnalysis[0])) {
      return textualAnalysis;
    }
    
    return [];
  };

  const diagnosisResults = getDiagnosisResults();

  const getPageSubtitle = () => {
    // if (isGenerating) {
    //   return 'Preparing your follow-up questions...';
    // }
    
    if (isAwaiting) {
      if (followupType === 'skin_cancer_screening') {
        return 'These questions help determine if image analysis is needed for skin cancer screening';
      } else {
        // Check if this is a transition from skin screening
        const workflowPath = workflowState?.workflow_path || [];
        if (workflowPath.includes('textual_to_skin_screening')) {
          return 'Based on your skin cancer screening results, please answer these standard follow-up questions';
        }
        return 'Please answer these questions to improve diagnosis accuracy';
      }
    }
    
    if (isComplete) {
      return '✅ Follow-up analysis complete - Review enhanced results below';
    }
    
    return 'Follow-up questions for enhanced diagnosis';
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <PageHeader
        title={followupType === 'skin_cancer_screening' ? 
          "🔍 Skin Cancer Screening Questions" : 
          "📝 Follow-Up Questions"
        }
        subtitle={getPageSubtitle()}
        step={{
          current: 2,
          total: 6,
          description: followupType === 'skin_cancer_screening' ? 
            "Skin cancer risk assessment" : 
            "Enhanced symptom analysis"
        }}
        variant={isComplete ? 'success' : 'default'}
      />

      {showForm && followupType === 'standard' && workflowState?.workflow_path?.includes('textual_to_skin_screening') && (
        <Card variant="primary" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <h5 style={{ margin: '0 0 var(--spacing-sm) 0', color: 'var(--primary)' }}>
            ✅ Skin Cancer Screening Complete
          </h5>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--primary)' }}>
            Your skin cancer screening results indicate low risk. We'll now ask some standard 
            follow-up questions to provide a more accurate diagnosis for your skin condition.
          </p>
        </Card>
      )}

      {/* Generating Questions
      {isGenerating && (
        <Card variant="primary" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <h5 style={{ margin: '0 0 var(--spacing-sm) 0', color: 'var(--primary)' }}>
            ✅ Skin Cancer Screening Complete
          </h5>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--primary)' }}>
            Your skin cancer screening results indicate <strong>low risk</strong>. We're now generating 
            standard follow-up questions to provide a more accurate diagnosis for your skin condition.
          </p>
          <div style={{ marginTop: 'var(--spacing-md)' }}>
            <LoadingSpinner 
              message="Generating personalized follow-up questions..."
              size="sm"
            />
          </div>
        </Card>
      )} */}

      {/* Questions Form */}
      {showForm && (
        <Card>
          {/* Skin Cancer Screening Info */}
          {followupType === 'skin_cancer_screening' && (
            <div style={{ 
              background: '#e3f2fd', 
              border: '1px solid #bbdefb',
              padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-md)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              <h5 style={{ margin: '0 0 var(--spacing-sm) 0', color: '#1976d2' }}>
                📋 About Skin Cancer Screening
              </h5>
              <p style={{ margin: 0, fontSize: '14px', color: '#1976d2' }}>
                We use the ABCDE criteria (Asymmetry, Border, Color, Diameter, Evolving) 
                to assess potential skin cancer risk. If our screening suggests further evaluation 
                is needed, we'll ask you to upload an image for AI analysis.
              </p>
            </div>
          )}

          <FollowUpForm
            questions={questions}
            onSubmit={onSubmitResponses}
            loading={loading}
            followupType={followupType}
          />
        </Card>
      )}

      {/* Enhanced Results Section */}
      {showResults && diagnosisResults.length > 0 && (
        <>
          {/* Skin Cancer Risk Detection Alert */}
          {workflowState?.skin_cancer_risk_detected && (
            <Card variant="warning" style={{ marginBottom: 'var(--spacing-lg)' }}>
              <h4 style={{ margin: '0 0 var(--spacing-sm) 0', color: '#856404' }}>
                ⚠️ Skin Cancer Risk Detected
              </h4>
              <p style={{ margin: 0, fontSize: '14px', color: '#856404' }}>
                Based on your screening responses, we recommend proceeding to image analysis 
                for a more detailed assessment of your skin condition.
              </p>
            </Card>
          )}

          {/* Enhanced Diagnosis Results */}
          <DiagnosisResults
            results={diagnosisResults}
            averageConfidence={workflowState.average_confidence || 0}
            imageRequired={workflowState.image_required || false}
            onContinue={onContinue}
            loading={loading}
            title={workflowState?.skin_cancer_risk_detected ? 
              "📊 Skin Cancer Risk Assessment Results" :
              "📊 Enhanced Diagnosis Results"
            }
            subtitle={workflowState?.skin_cancer_risk_detected ? 
              "Image analysis recommended for further evaluation" :
              "Results improved with follow-up information"
            }
            context="followup_complete"
            hideFollowUpMessage={true}
          />

          {/* Follow-up Q&A Summary */}
          {workflowState.followup_response && Object.keys(workflowState.followup_response).length > 0 && (
            <Card style={{ marginTop: 'var(--spacing-lg)' }}>
              <details style={{ cursor: 'pointer' }}>
                <summary style={{ 
                  fontWeight: '600', 
                  color: 'var(--primary)',
                  fontSize: '1.1rem',
                  marginBottom: 'var(--spacing-sm)'
                }}>
                  📝 Your {followupType === 'skin_cancer_screening' ? 'Screening' : 'Follow-Up'} Responses
                </summary>
                <div style={{ 
                  background: '#f8f9fa', 
                  padding: 'var(--spacing-md)', 
                  borderRadius: 'var(--radius-md)',
                  marginTop: 'var(--spacing-sm)'
                }}>
                  {Object.entries(workflowState.followup_response).map(([question, response], index) => (
                    <div key={index} style={{ marginBottom: 'var(--spacing-sm)' }}>
                      <div style={{ 
                        fontSize: '14px', 
                        fontWeight: '600', 
                        color: 'var(--dark)',
                        marginBottom: '2px'
                      }}>
                        Q{index + 1}: {question}
                      </div>
                      <div style={{ 
                        fontSize: '14px', 
                        color: 'var(--secondary)',
                        paddingLeft: 'var(--spacing-sm)',
                        borderLeft: '2px solid var(--primary)'
                      }}>
                        A: {response}
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            </Card>
          )}
        </>
      )}

      {/* Reset Option */}
      <div style={{ textAlign: 'center', marginTop: 'var(--spacing-lg)' }}>
        <Button onClick={onReset} variant="secondary" size="sm">
          🔄 Start Over
        </Button>
      </div>
    </div>
  );
};