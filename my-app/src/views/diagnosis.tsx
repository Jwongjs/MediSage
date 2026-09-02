import React from 'react';
import { WorkflowRouter } from 'WorkflowRouter';
import { useDiagnosis } from 'hooks/useDiagnosis';
import { PageLayout } from 'components/layout/PageLayout';

const DiagnosisFunction: React.FC = () => {
  const {
    step,
    view,
    loading,
    error,
    sessionId,
    startDiagnosis,
    goToQuestions,
    submitAnswers,
    finalize,
    reset
  } = useDiagnosis();

  return (
    <PageLayout>
      <div className="container mx-auto max-w-3xl px-4 py-8 space-y-8">
        <WorkflowRouter
          step={step}
          view={view}
          loading={loading}
          error={error}
          sessionId={sessionId}
          onStart={startDiagnosis}
          onAnswerQuestions={goToQuestions}
          onSubmitAnswers={submitAnswers}
          onFinalize={finalize}
          onReset={reset}
        />
        <p className="text-xs text-center text-muted-foreground">
          MediSage provides AI-assisted guidance for educational purposes and does not replace professional medical care.
        </p>
      </div>
    </PageLayout>
  );
}

export default DiagnosisFunction;
