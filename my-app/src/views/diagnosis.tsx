import React from 'react';
import { WorkflowRouter } from 'WorkflowRouter';
import { useDiagnosis } from 'hooks/useDiagnosis';
import { PrivacyPolicyModal } from 'components/medical/PrivacyPolicyModal';
import { PageLayout } from 'components/layout/PageLayout';

const DiagnosisFunction: React.FC = () => {
  const {
    step,
    view,
    loading,
    error,
    showPrivacyModal,
    handlePrivacyAccepted,
    dismissPrivacyModal,
    startDiagnosis,
    goToQuestions,
    submitAnswers,
    finalize,
    reset
  } = useDiagnosis();

  return (
    <PageLayout>
      {showPrivacyModal && (
        <PrivacyPolicyModal
          onAccept={handlePrivacyAccepted}
          onCancel={dismissPrivacyModal}
        />
      )}
      <div className="container mx-auto max-w-3xl px-4 py-8 space-y-8">
        <WorkflowRouter
          step={step}
          view={view}
          loading={loading}
          error={error}
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
