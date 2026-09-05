import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { WorkflowRouter } from 'WorkflowRouter';
import { useDiagnosis } from 'hooks/useDiagnosis';
import { PageLayout } from 'components/layout/PageLayout';
import { ConsentGateModal } from 'components/medical/ConsentGateModal';

const DiagnosisFunction: React.FC = () => {
  const navigate = useNavigate();
  // No account exists to remember a prior agreement against, so this gate is
  // in-memory only (no localStorage) and is reset alongside the workflow
  // itself: it reappears at the start of every diagnosis session, not just
  // once per browser.
  const [agreed, setAgreed] = useState(false);

  const {
    loading,
    result,
    error,
    sessionId,
    currentStage,
    workflowInfo,
    startDiagnosis,
    submitFollowUp,
    continueToNextStep,
    reset
  } = useDiagnosis();

  const handleReset = () => {
    reset();
    setAgreed(false);
  };

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
      {!agreed && (
        <ConsentGateModal
          onAccept={() => setAgreed(true)}
          onCancel={() => navigate('/')}
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
          onReset={handleReset}
        />
        <p className="text-xs text-center text-muted-foreground">
          MediSage provides AI-assisted guidance for educational purposes and does not replace professional medical care.
        </p>
      </div>
    </PageLayout>
  );
}

export default DiagnosisFunction;
