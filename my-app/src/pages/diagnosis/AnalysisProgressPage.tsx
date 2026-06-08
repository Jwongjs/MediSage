import React, { useState, useEffect } from 'react';
import { AgentState } from 'types/medical';
import { Card } from 'components/common/Card';
import { Button } from 'components/common/Button';
import { LoadingSpinner } from 'components/common/LoadingSpinner';
import { PageHeader } from 'components/layout/PageHeader';

interface AnalysisProgressPageProps {
  workflowState: AgentState | null;
  loading: boolean;
  onReset: () => void;
  onContinue?: () => void;
}

export const AnalysisProgressPage: React.FC<AnalysisProgressPageProps> = ({
  workflowState,
  loading,
  onReset,
  onContinue
}) => {
  const [showResults, setShowResults] = useState(false);
  const [animationComplete, setAnimationComplete] = useState(false);

  // Show results when overall analysis is complete
  useEffect(() => {
    if (workflowState?.overall_analysis && !loading) {
      setTimeout(() => setShowResults(true), 1000);
      setTimeout(() => setAnimationComplete(true), 2000);
    }
  }, [workflowState?.overall_analysis, loading]);

  if (!workflowState) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <LoadingSpinner message="Loading analysis..." />
      </div>
    );
  }

  const hasOverallAnalysis = workflowState.overall_analysis;
  const currentStage = workflowState.current_workflow_stage || '';
  const isAnalyzing = currentStage === 'performing_overall_analysis' || loading;
  const isComplete = currentStage === 'overall_analysis_complete';

  // Get primary diagnosis info
  const getPrimaryDiagnosis = () => {
    const workflowPath = workflowState?.workflow_path || [];
    const imageAnalysis = workflowState?.skin_lesion_analysis;
    const overallAnalysis = workflowState?.overall_analysis;
    
    // For skin cancer screening path, use image analysis result
    if (workflowPath.includes('textual_to_skin_screening') && imageAnalysis?.image_diagnosis) {
      const imageConfidenceScores = imageAnalysis.confidence_score || {};
      const imageConfidence = Object.keys(imageConfidenceScores).length > 0 
        ? Math.max(...Object.values(imageConfidenceScores)) / 100
        : 0;
      
      return {
        diagnosis: imageAnalysis.image_diagnosis,
        confidence: imageConfidence,
        source: 'Image Analysis'
      };
    }
    
    // For other paths, use overall analysis
    return {
      diagnosis: overallAnalysis?.final_diagnosis || 'Unknown',
      confidence: overallAnalysis?.final_confidence || 0,
      source: 'Comprehensive Analysis'
    };
  };

  // Get significant alternative diagnoses (confidence > 15%)
  const getSignificantAlternatives = (): any[] => {
    const workflowPath = workflowState?.workflow_path || [];
    const imageAnalysis = workflowState?.skin_lesion_analysis;
    const SIGNIFICANCE_THRESHOLD = 15; // 15% minimum confidence to show
    
    // For skin cancer screening, show image analysis alternatives
    if (workflowPath.includes('textual_to_skin_screening') && imageAnalysis?.confidence_score) {
      const confidenceScores = imageAnalysis.confidence_score;
      
      return Object.entries(confidenceScores)
        .map(([condition, confidence]) => ({
          text_diagnosis: condition.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          diagnosis_confidence: confidence / 100, // Convert percentage to decimal
          confidence_percentage: confidence
        }))
        .sort((a, b) => b.confidence_percentage - a.confidence_percentage)
        .slice(1) // Skip first (primary diagnosis)
        .filter(alt => alt.confidence_percentage >= SIGNIFICANCE_THRESHOLD); // Only significant alternatives
    }
  
    // For standard workflow, use textual/followup analysis
    const followupAnalysis = workflowState?.followup_diagnosis || [];
    const initialAnalysis = workflowState?.textual_analysis || [];
    
    const sourceAnalysis = followupAnalysis.length > 0 ? followupAnalysis : initialAnalysis;
    
    return sourceAnalysis
      .map(diagnosis => ({
        ...diagnosis,
        confidence_percentage: diagnosis.diagnosis_confidence * 100
      }))
      .sort((a, b) => b.diagnosis_confidence - a.diagnosis_confidence)
      .slice(1) // Skip first (primary diagnosis)
      .filter(alt => alt.confidence_percentage >= SIGNIFICANCE_THRESHOLD); // Only significant alternatives
  };

  const primaryDiagnosis = getPrimaryDiagnosis();
  const significantAlternatives = getSignificantAlternatives();

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <PageHeader
        title="🎯 Overall Analysis"
        subtitle="Comprehensive medical analysis results"
        step={{
          current: 4,
          total: 5,
          description: "Overall medical analysis"
        }}
        variant={isComplete ? 'success' : 'default'}
      />

      {/* Loading State */}
      {isAnalyzing && !showResults && (
        <Card style={{ textAlign: 'center' }}>
          <LoadingSpinner 
            size="lg" 
            message="🧠 AI Processing All Data..."
          />
          
          {/* Analysis Progress Steps */}
          <div style={{ textAlign: 'left', maxWidth: '400px', margin: 'var(--spacing-lg) auto 0' }}>
            <div style={{ fontSize: '14px', color: 'var(--secondary)' }}>
              <div style={{ marginBottom: '8px' }}>✅ Initial symptoms analyzed</div>
              <div style={{ marginBottom: '8px' }}>✅ Follow-up responses processed</div>
              {workflowState?.skin_lesion_analysis && (
                <div style={{ marginBottom: '8px' }}>✅ Medical image analyzed</div>
              )}
              <div style={{ marginBottom: '8px', color: 'var(--primary)' }}>🔄 Generating final diagnosis...</div>
              <div style={{ marginBottom: '8px', opacity: 0.5 }}>⏳ Determining severity & recommendations...</div>
            </div>
          </div>
        </Card>
      )}

      {/* Analysis Results */}
      {(showResults || (hasOverallAnalysis && !isAnalyzing)) && (
        <>
          {/* Main Results Card */}
          <Card variant="success" style={{
            marginBottom: 'var(--spacing-lg)',
            transform: animationComplete ? 'scale(1)' : 'scale(0.95)',
            opacity: animationComplete ? 1 : 0.8,
            transition: 'all 0.5s ease'
          }}>
            <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-lg)' }}>
              <h2 style={{ 
                margin: '0 0 var(--spacing-sm) 0', 
                fontSize: '1.5rem',
                color: 'var(--success)'
              }}>
                🏆 Final Medical Diagnosis
              </h2>
              <p style={{ margin: 0, color: 'var(--secondary)' }}>
                Comprehensive AI Analysis Complete
              </p>
            </div>

            {hasOverallAnalysis && (
              <>
                {/* Primary Diagnosis */}
                <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
                  <h3 style={{ 
                    margin: '0 0 var(--spacing-md) 0',
                    color: 'var(--success)',
                    fontSize: '1.3rem'
                  }}>
                    🎯 Primary Diagnosis
                  </h3>
                  
                  <div style={{
                    fontSize: '1.2rem',
                    fontWeight: '600',
                    color: 'var(--dark)',
                    marginBottom: 'var(--spacing-lg)',
                    lineHeight: '1.4'
                  }}>
                    {primaryDiagnosis.diagnosis}
                  </div>

                  {/* Key Metrics Grid */}
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                    gap: 'var(--spacing-md)'
                  }}>
                    <Card padding="md" style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '12px', color: 'var(--secondary)', marginBottom: '4px' }}>
                        CONFIDENCE LEVEL
                      </div>
                      <div style={{ 
                        fontSize: '1.4rem', 
                        fontWeight: '700',
                        color: primaryDiagnosis.confidence >= 0.8 ? 'var(--success)' : 
                              primaryDiagnosis.confidence >= 0.6 ? 'var(--warning)' : 'var(--danger)'
                      }}>
                        {(primaryDiagnosis.confidence * 100).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: '10px', color: 'var(--secondary)', marginTop: '2px' }}>
                        Based on {primaryDiagnosis.source.toLowerCase()}
                      </div>
                    </Card>

                    <Card padding="md" style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '12px', color: 'var(--secondary)', marginBottom: '4px' }}>
                        SEVERITY LEVEL
                      </div>
                      <div style={{ 
                        fontSize: '1.2rem', 
                        fontWeight: '600',
                        color: workflowState?.overall_analysis?.final_severity === 'severe' ? 'var(--danger)' :
                              workflowState?.overall_analysis?.final_severity === 'moderate' ? 'var(--warning)' : 'var(--success)',
                        textTransform: 'capitalize'
                      }}>
                        {workflowState?.overall_analysis?.final_severity || 'Moderate'}
                      </div>
                    </Card>

                    <Card padding="md" style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '12px', color: 'var(--secondary)', marginBottom: '4px' }}>
                        SPECIALIST
                      </div>
                      <div style={{ 
                        fontSize: '1rem', 
                        fontWeight: '600',
                        color: 'var(--primary)',
                        textTransform: 'capitalize'
                      }}>
                        {workflowState?.overall_analysis?.specialist_recommendation?.replace('_', ' ') || 'General Practitioner'}
                      </div>
                    </Card>
                  </div>
                </Card>

                {/* Significant Alternative Diagnoses */}
                {significantAlternatives.length > 0 && (
                  <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
                    <h4 style={{ 
                      margin: '0 0 var(--spacing-md) 0',
                      color: 'var(--dark)',
                      fontSize: '1.1rem'
                    }}>
                      🔍 Other Significant Possibilities
                    </h4>
                    <p style={{ 
                      fontSize: '14px', 
                      color: 'var(--secondary)', 
                      margin: '0 0 var(--spacing-md) 0' 
                    }}>
                      Other conditions that showed significant likelihood (≥15% confidence):
                    </p>
                    
                    {significantAlternatives.map((diagnosis, index) => (
                      <div key={index} style={{
                        background: '#f8f9fa',
                        border: '1px solid #e9ecef',
                        borderRadius: 'var(--radius-md)',
                        padding: 'var(--spacing-md)',
                        marginBottom: index < significantAlternatives.length - 1 ? 'var(--spacing-sm)' : '0',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <div>
                          <strong style={{ color: 'var(--dark)' }}>
                            {diagnosis.text_diagnosis}
                          </strong>
                        </div>
                        <div style={{
                          background: diagnosis.confidence_percentage >= 30 ? 'var(--warning)' : 'var(--secondary)',
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '14px',
                          fontWeight: '600'
                        }}>
                          {diagnosis.confidence_percentage.toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </Card>
                )}

                {/* Patient-Friendly Explanation */}
                <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
                  <h4 style={{ 
                    margin: '0 0 var(--spacing-md) 0',
                    color: 'var(--primary)',
                    fontSize: '1.2rem'
                  }}>
                    📋 What does this mean?
                  </h4>
                  <p style={{ 
                    margin: 0,
                    lineHeight: '1.6',
                    color: 'var(--dark)',
                    fontSize: '16px'
                  }}>
                    {workflowState.overall_analysis?.user_explanation}
                  </p>
                </Card>

                {/* Clinical Reasoning - Collapsible */}
                <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
                  <details style={{ cursor: 'pointer' }}>
                    <summary style={{ 
                      fontWeight: '600', 
                      color: 'var(--secondary)',
                      fontSize: '1.1rem',
                      marginBottom: 'var(--spacing-sm)'
                    }}>
                      🤔 Why this diagnosis? (AI reasoning)
                    </summary>
                    <div style={{ 
                      background: '#f8f9fa', 
                      padding: 'var(--spacing-md)', 
                      borderRadius: 'var(--radius-md)',
                      marginTop: 'var(--spacing-sm)'
                    }}>
                      <p style={{ 
                        margin: 0,
                        lineHeight: '1.6',
                        color: 'var(--dark)',
                        fontSize: '14px'
                      }}>
                        {workflowState.overall_analysis?.clinical_reasoning}
                      </p>
                    </div>
                  </details>
                </Card>

                {/* Image Analysis Context (if applicable) */}
                {workflowState?.skin_lesion_analysis && workflowState.workflow_path?.includes('textual_to_skin_screening') && (
                  <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
                    <h4 style={{ 
                      margin: '0 0 var(--spacing-md) 0',
                      color: 'var(--primary)',
                      fontSize: '1.2rem'
                    }}>
                      📸 Image Analysis Summary
                    </h4>
                    
                    <div style={{ 
                      background: '#f8f9fa', 
                      padding: 'var(--spacing-md)', 
                      borderRadius: 'var(--radius-md)',
                      marginBottom: 'var(--spacing-md)'
                    }}>
                      <div style={{ fontSize: '14px', color: 'var(--dark)', marginBottom: '8px' }}>
                        <strong>Skin Cancer Screening Result:</strong>
                      </div>
                      <div style={{ fontSize: '14px', color: 'var(--secondary)' }}>
                        Our AI analyzed your uploaded image using computer vision algorithms trained on 
                        dermatological datasets. The analysis assessed features including asymmetry, 
                        border irregularity, color variation, and other characteristics relevant to skin cancer screening.
                      </div>
                    </div>
                    
                    <div style={{ 
                      fontSize: '12px', 
                      color: 'var(--warning)', 
                      fontStyle: 'italic',
                      background: '#fff3cd',
                      padding: '8px',
                      borderRadius: '4px',
                      border: '1px solid #ffeaa7'
                    }}>
                      ⚠️ <strong>Important:</strong> This AI image analysis is for screening purposes only. 
                      Any concerning findings should be evaluated by a qualified dermatologist.
                    </div>
                  </Card>
                )}
              </>
            )}
          </Card>

          {/* Continue to Report Button */}
          {animationComplete && (
            <div style={{ 
              textAlign: 'center', 
              marginTop: 'var(--spacing-xl)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              <Card variant="primary" style={{ 
                background: 'linear-gradient(135deg, var(--success) 0%, var(--primary) 100%)',
                border: 'none',
                color: 'white'
              }}>
                <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-md)' }}>
                  <h4 style={{ margin: 0, color: 'white', fontSize: '1.2rem' }}>
                    🎉 Analysis Complete!
                  </h4>
                  <p style={{ margin: '8px 0 0 0', opacity: 0.9, fontSize: '14px' }}>
                    Generate your comprehensive medical report
                  </p>
                </div>
                
                <Button
                  onClick={async () => {
                    console.log('🔄 Proceeding to final report...');
                    try {
                      if (onContinue) {
                        await onContinue();
                      } else {
                        console.error('❌ onContinue not available');
                      }
                    } catch (error) {
                      console.error('❌ Failed to proceed to final report:', error);
                    }
                  }}
                  variant="primary"
                  size="lg"
                  style={{
                    background: 'rgba(255,255,255,0.2)',
                    border: '2px solid rgba(255,255,255,0.3)',
                    color: 'white',
                    fontWeight: '600',
                    padding: 'var(--spacing-md) var(--spacing-lg)',
                    fontSize: '1.1rem',
                    backdropFilter: 'blur(10px)'
                  }}
                >
                  📄 Generate Final Report
                </Button>
              </Card>
            </div>
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
          This AI-generated analysis is for informational purposes only and should not replace 
          professional medical advice, diagnosis, or treatment. Always consult with qualified 
          healthcare professionals for medical concerns.
        </p>
      </Card>

      {/* Reset Button */}
      <div style={{ textAlign: 'center', marginTop: 'var(--spacing-lg)' }}>
        <Button
          onClick={onReset}
          variant="secondary"
          size="sm"
        >
          🔄 Start New Analysis
        </Button>
      </div>
    </div>
  );
};