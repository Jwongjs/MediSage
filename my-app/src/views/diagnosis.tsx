import React from 'react';
import { Link } from 'react-router-dom';
import { WorkflowRouter } from 'WorkflowRouter';
import { useDiagnosis } from 'hooks/useDiagnosis';
import { PrivacyPolicyModal } from 'components/medical/PrivacyPolicyModal';
import { PageLayout } from 'components/layout/PageLayout';
import { Button } from '@/components/ui/button';
import { MessageSquare, ArrowRight } from 'lucide-react';

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
        <aside className="rounded-xl border bg-card shadow-sm p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
            <MessageSquare className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold">Questions about a past session?</p>
            <p className="text-sm text-muted-foreground">
              The MediSage assistant answers from your saved reports — without interrupting this assessment.
            </p>
          </div>
          <Button variant="outline" size="sm" asChild className="shrink-0">
            <Link to="/chatbot">Open chat<ArrowRight className="h-4 w-4 ml-1.5" /></Link>
          </Button>
        </aside>
        <p className="text-xs text-center text-muted-foreground">
          MediSage provides AI-assisted guidance for educational purposes and does not replace professional medical care.
        </p>
      </div>
    </PageLayout>
  );
}

export default DiagnosisFunction;
