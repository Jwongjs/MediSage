import React from 'react';
import { Card } from 'components/common/Card';
import { Button } from 'components/common/Button';
import { AgentState } from 'types/medical';

interface ImageAnalysisResultsProps {
  workflowState: AgentState | null;
  onContinue?: () => void;
  loading?: boolean;
  title?: string;
  subtitle?: string;
}

export const ImageAnalysisResults: React.FC<ImageAnalysisResultsProps> = ({
  workflowState,
  onContinue,
  loading = false,
  title = "📸 Image Analysis Results",
  subtitle = "AI-powered medical image analysis complete"
}) => {
  
  if (!workflowState?.skin_lesion_analysis) {
    return (
      <Card>
        <p style={{ textAlign: 'center', color: 'var(--secondary)' }}>
          ⏳ No image analysis results available
        </p>
      </Card>
    );
  }

  const imageAnalysis = workflowState.skin_lesion_analysis;
  const imageDiagnosis = imageAnalysis.image_diagnosis || 'No diagnosis available';
  const confidenceScores = imageAnalysis.confidence_score || {};
  
  // Calculate highest confidence score
  const maxConfidence = Object.keys(confidenceScores).length > 0 
    ? Math.max(...Object.values(confidenceScores))
    : 0;

  // Check if this is an error result
  const isError = imageDiagnosis.toLowerCase().includes('error') || 
                  imageDiagnosis.toLowerCase().includes('failed') ||
                  imageDiagnosis === 'No image provided';

  // Determine confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'var(--success)';
    if (confidence >= 60) return 'var(--warning)';
    return 'var(--danger)';
  };

  return (
    <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
      {/* Header */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: 'var(--spacing-lg)',
        paddingBottom: 'var(--spacing-md)',
        borderBottom: '2px solid var(--primary)'
      }}>
        <h3 style={{ 
          margin: '0 0 var(--spacing-sm) 0',
          color: isError ? 'var(--danger)' : 'var(--success)',
          fontSize: '1.4rem'
        }}>
          {title}
        </h3>
        <p style={{ 
          margin: 0, 
          color: 'var(--secondary)',
          fontSize: '14px'
        }}>
          {subtitle}
        </p>
      </div>

      {/* Error State */}
      {isError && (
        <Card variant="danger" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <h4 style={{ margin: '0 0 var(--spacing-sm) 0', color: 'var(--danger)' }}>
            ❌ Analysis Error
          </h4>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--danger)' }}>
            {imageDiagnosis}
          </p>
        </Card>
      )}

      {/* Successful Analysis Results */}
      {!isError && (
        <>
          {/* Primary Diagnosis */}
          <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
            <h4 style={{ 
              margin: '0 0 var(--spacing-md) 0',
              color: 'var(--primary)',
              fontSize: '1.2rem'
            }}>
              🎯 AI Image Diagnosis
            </h4>
            
            <div style={{
              fontSize: '1.1rem',
              fontWeight: '600',
              color: 'var(--dark)',
              marginBottom: 'var(--spacing-lg)',
              lineHeight: '1.4',
              padding: 'var(--spacing-md)',
              background: '#f8f9fa',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #e9ecef'
            }}>
              {imageDiagnosis}
            </div>

            {/* Confidence Score */}
            {maxConfidence > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ 
                  fontSize: '14px', 
                  color: 'var(--secondary)', 
                  marginBottom: '8px' 
                }}>
                  CONFIDENCE LEVEL
                </div>
                <div style={{ 
                  fontSize: '2rem', 
                  fontWeight: '700',
                  color: getConfidenceColor(maxConfidence)
                }}>
                  {maxConfidence.toFixed(1)}%
                </div>
                <div style={{ 
                  fontSize: '12px', 
                  color: 'var(--secondary)', 
                  marginTop: '4px' 
                }}>
                  Based on image analysis
                </div>
              </div>
            )}
          </Card>

          {/* Detailed Confidence Breakdown */}
          {Object.keys(confidenceScores).length > 1 && (
            <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
              <details style={{ cursor: 'pointer' }}>
                <summary style={{ 
                  fontWeight: '600', 
                  color: 'var(--secondary)',
                  fontSize: '1.1rem',
                  marginBottom: 'var(--spacing-sm)'
                }}>
                  📊 Detailed Classification Results
                </summary>
                <div style={{ 
                  background: '#f8f9fa', 
                  padding: 'var(--spacing-md)', 
                  borderRadius: 'var(--radius-md)',
                  marginTop: 'var(--spacing-sm)'
                }}>
                  {Object.entries(confidenceScores)
                    .sort(([,a], [,b]) => b - a) // Sort by confidence descending
                    .map(([condition, confidence], index) => (
                      <div key={condition} style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: 'var(--spacing-sm)',
                        marginBottom: index < Object.keys(confidenceScores).length - 1 ? '8px' : '0',
                        background: index === 0 ? 'rgba(40, 167, 69, 0.1)' : 'white',
                        borderRadius: '4px',
                        border: index === 0 ? '1px solid var(--success)' : '1px solid #e9ecef'
                      }}>
                        <div>
                          <strong style={{ 
                            color: 'var(--dark)',
                            textTransform: 'capitalize' 
                          }}>
                            {index === 0 ? '🏆 ' : ''}
                            {condition.replace(/_/g, ' ')}
                          </strong>
                          {index === 0 && (
                            <div style={{ 
                              fontSize: '12px', 
                              color: 'var(--success)', 
                              marginTop: '2px' 
                            }}>
                              Most likely diagnosis
                            </div>
                          )}
                        </div>
                        <div style={{
                          background: getConfidenceColor(confidence),
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '14px',
                          fontWeight: '600'
                        }}>
                          {confidence.toFixed(1)}%
                        </div>
                      </div>
                    ))}
                </div>
              </details>
            </Card>
          )}

          {/* Skin Cancer Risk Context */}
          {workflowState?.skin_cancer_risk_detected && (
            <Card variant="warning" style={{ marginBottom: 'var(--spacing-lg)' }}>
              <h5 style={{ margin: '0 0 var(--spacing-sm) 0', color: '#856404' }}>
                🔍 Skin Cancer Screening Context
              </h5>
              <p style={{ margin: 0, fontSize: '14px', color: '#856404' }}>
                This image analysis was performed because your screening responses indicated 
                potential skin cancer risk factors. The AI has analyzed your image for concerning features.
              </p>
            </Card>
          )}
        </>
      )}

      {/* Medical Disclaimer */}
      <Card variant="warning" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <h5 style={{ margin: '0 0 var(--spacing-sm) 0', color: 'var(--warning)' }}>
          ⚠️ Important Medical Disclaimer
        </h5>
        <p style={{ 
          margin: 0, 
          fontSize: '14px', 
          lineHeight: '1.6',
          color: 'var(--dark)'
        }}>
          This AI image analysis is for informational purposes only and should not replace 
          professional medical evaluation. For any concerning skin changes, please consult 
          a dermatologist or healthcare provider for proper diagnosis and treatment.
        </p>
      </Card>

      {/* Continue Button */}
      {onContinue && !isError && (
        <div style={{ textAlign: 'center' }}>
          <Button
            onClick={() => {
              console.log('🔄 Continue button clicked from ImageAnalysisResults');
              if (onContinue) {
                onContinue(); 
              }
            }}
            variant="primary"
            size="lg"
            loading={loading}
            style={{ minWidth: '200px' }}
          >
            📊 Continue to Final Analysis
          </Button>
        </div>
      )}
    </Card>
  );
};