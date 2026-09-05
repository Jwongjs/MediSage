import React from 'react';
import { DiagnosisFormPage } from 'pages/diagnosis/DiagnosisFormPage';
import { EvidenceResultsPage } from 'pages/diagnosis/EvidenceResultsPage';
import { FinalReportPage } from 'pages/diagnosis/FinalReportPage';
import { ErrorPage } from 'pages/diagnosis/ErrorPage';
import { DiagnosisView } from 'types/diagnosis';

export type FlowStep = 'form' | 'evidence' | 'summary';

interface WorkflowRouterProps {
  step: FlowStep;
  view: DiagnosisView | null;
  loading: boolean;
  error: string | null;
  sessionId: string | null;
  onStart: (patientText: string) => Promise<void>;
  onFinalize: (checked: string[]) => void;
  onReset: () => void;
}

export const WorkflowRouter: React.FC<WorkflowRouterProps> = ({
  step, view, loading, error, sessionId,
  onStart, onFinalize, onReset,
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
          onFinalize={onFinalize} onReset={onReset}
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
