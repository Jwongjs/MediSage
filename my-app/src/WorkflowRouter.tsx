import React from 'react';
import { AgentState } from 'types/medical';
import { DiagnosisFormPage } from 'pages/diagnosis/DiagnosisFormPage';
import { FollowUpQuestionsPage } from 'pages/diagnosis/FollowUpQuestionsPage';
import { ImageAnalysisPage } from 'pages/diagnosis/ImageAnalysisPage';
import { AnalysisProgressPage } from 'pages/diagnosis/AnalysisProgressPage';
import { FinalReportPage } from 'pages/diagnosis/FinalReportPage';
import { ErrorPage } from 'pages/diagnosis/ErrorPage';

interface WorkflowRouterProps {
  workflowState: AgentState | null;
  loading: boolean;
  error: string | null;
  sessionId: string | null;
  workflowInfo?: any | null;
  onStartDiagnosis: (symptoms: string) => Promise<void>;
  onSubmitFollowUp: (responses: Record<string, string>) => Promise<void>;
  onSubmitImage: (image: File) => Promise<void>;
  onReset: () => void;
  onContinue: () => void; 
}

export const WorkflowRouter: React.FC<WorkflowRouterProps> = ({
  workflowState,
  loading,
  error,
  sessionId,
  workflowInfo,
  onStartDiagnosis,
  onSubmitFollowUp,
  onSubmitImage,
  onReset,
  onContinue
}) => {
  
  // Handle error state
  if (error) {
    return (
      <ErrorPage 
        error={error}
        onReset={onReset}
      />
    );
  }

  // Handle initial state (no workflow started)
  if (!workflowState && !loading) {
    return (
      <DiagnosisFormPage
        onSubmit={onStartDiagnosis}
        onContinue={onContinue}
        loading={loading}
        sessionId={sessionId}
        workflowState={null}
        workflowInfo={workflowInfo}
      />
    );
  }

  // Get current workflow stage
  const currentStage = workflowState?.current_workflow_stage || 'textual_analysis';
  
  console.log('🔄 Current workflow stage:', currentStage);

  // Route to appropriate page based on workflow stage
  switch (currentStage) {
    //INITIAL DIAGNOSIS: Show form and results
    case 'textual_analysis':
    case 'textual_analysis_complete':
      return (
        <DiagnosisFormPage
          onSubmit={onStartDiagnosis}
          onContinue={onContinue}
          loading={loading}
          sessionId={sessionId}
          workflowState={workflowState}
          workflowInfo={workflowInfo}
        />
      );

    // FOLLOW-UP QUESTIONS: Generate or collect responses
    // case 'generating_followup_questions':
    case 'awaiting_followup_responses':
    case 'processing_followup_responses':
    case 'followup_analysis_complete':
    return (
      <FollowUpQuestionsPage
        workflowState={workflowState}
        workflowInfo={workflowInfo} 
        loading={loading}
        onSubmitResponses={onSubmitFollowUp}
        onContinue={onContinue}    
        onReset={onReset}
      />
    );

    // IMAGE ANALYSIS: Upload and analyze image    
    case 'awaiting_image_upload':
    case 'analyzing_image':
    case 'image_analysis_complete':
      return (
        <ImageAnalysisPage
          workflowState={workflowState}
          loading={loading}
          onSubmitImage={onSubmitImage} 
          onReset={onReset}
          onContinue={onContinue}
        />
      );

    // OVERALL ANALYSIS: Processing all data
    case 'performing_overall_analysis':
    case 'overall_analysis_complete': 
      return (
        <AnalysisProgressPage
          workflowState={workflowState}
          loading={loading}
          onReset={onReset}
          onContinue={onContinue}
        />
      );

    // FINAL MEDICAL REPORT
    case 'generating_medical_report':
    case 'workflow_complete':
      return (
        <FinalReportPage
          workflowState={workflowState}
          loading={loading}
          onReset={onReset}
        />
      );

  default:
    console.warn('⚠️ Unknown workflow stage:', currentStage);
    return (
      <ErrorPage 
        error={`Unknown workflow stage: ${currentStage}`}
        onReset={onReset}
      />
    );
  }
};