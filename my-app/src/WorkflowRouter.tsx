import React from 'react';
import { DiagnosisFormPage } from 'pages/diagnosis/DiagnosisFormPage';
import { EvidenceResultsPage } from 'pages/diagnosis/EvidenceResultsPage';
import { CriterionPickerPage } from 'pages/diagnosis/CriterionPickerPage';
import { FinalReportPage } from 'pages/diagnosis/FinalReportPage';
import { ErrorPage } from 'pages/diagnosis/ErrorPage';
import { DiagnosisView, Answer } from 'types/diagnosis';

export type FlowStep = 'form' | 'evidence' | 'questions' | 'summary';

interface WorkflowRouterProps {
  step: FlowStep;
  view: DiagnosisView | null;
  loading: boolean;
  error: string | null;
  sessionId: string | null;
  onStart: (patientText: string) => Promise<void>;
  onAnswerQuestions: () => void;
  onSubmitAnswers: (answers: Record<string, Answer>) => Promise<void>;
  onFinalize: () => void;
  onReset: () => void;
}

export const WorkflowRouter: React.FC<WorkflowRouterProps> = ({
  step, view, loading, error, sessionId,
  onStart, onAnswerQuestions, onSubmitAnswers, onFinalize, onReset,
}) => {
  if (error) return <ErrorPage error={error} onReset={onReset} />;

  if (step === 'form' || !view) {
    return <DiagnosisFormPage onSubmit={onStart} loading={loading} />;
  }

  switch (step) {
    case 'evidence':
      return (
        <EvidenceResultsPage
          view={view} loading={loading}
          onAnswerQuestions={onAnswerQuestions} onFinalize={onFinalize}
          onReset={onReset}
        />
      );
    case 'questions':
      return (
        <CriterionPickerPage
          view={view} loading={loading}
          onSubmit={onSubmitAnswers} onSkip={onFinalize}
        />
      );
    case 'summary':
      return (
        <FinalReportPage
          view={view} loading={loading}
          sessionId={sessionId} onReset={onReset}
        />
      );
    default:
      return <ErrorPage error={`Unknown step: ${step}`} onReset={onReset} />;
  }
};
