import React from 'react';
import { WorkflowRouter } from 'WorkflowRouter';
import { useDiagnosis } from 'hooks/useDiagnosis';
import { PrivacyPolicyModal } from 'components/medical/PrivacyPolicyModal';
import { ChatPanel } from 'components/medical/ChatPanel';
import { PageLayout } from 'components/layout/PageLayout';

const DiagnosisFunction: React.FC = () => {
  const {
    loading,
    result,
    error,
    sessionId,
    currentStage,
    workflowInfo,
    showPrivacyModal,
    handlePrivacyAccepted,
    dismissPrivacyModal,
    startDiagnosis,
    submitFollowUp,
    continueToNextStep,
    reset
  } = useDiagnosis();

const handleStartDiagnosis = async (symptoms: string) => {
  try {
    await startDiagnosis({
      symptoms
    });

    console.log('✅ Diagnosis completed successfully');

  } catch (err) {
    console.error('❌ Diagnosis submission failed:', err);
  }
};

const handleContinueToNext = async () => {
  try {
    const continueResult = await continueToNextStep();

    if (continueResult?.workflowComplete) {
      console.log('✅ Workflow complete');
    } else {
      console.log('🔄 Workflow step completed, continuing...');
    }

  } catch (err) {
    console.error('❌ Continue failed:', err);
  }
};

const handleSubmitFollowUp = async (responses: Record<string, string>) => {
  try {
    console.log('📝 Submitting follow-up responses:', responses);

    await submitFollowUp(responses);
    console.log('✅ Follow-up submitted successfully');

  } catch (err) {
    console.error('❌ Follow-up submission failed:', err);
  }
};

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
          workflowState={result}
          loading={loading}
          error={error}
          sessionId={sessionId}
          workflowInfo={workflowInfo}
          onStartDiagnosis={handleStartDiagnosis}
          onContinue={handleContinueToNext}
          onSubmitFollowUp={handleSubmitFollowUp}
          onReset={reset}
        />
        <section>
          <ChatPanel />
        </section>
      </div>
    </PageLayout>
  );
}

export default DiagnosisFunction;
