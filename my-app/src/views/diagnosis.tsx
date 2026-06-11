import React from 'react';
import { WorkflowRouter } from 'WorkflowRouter';
import { useDiagnosis } from 'hooks/useDiagnosis';
import { PrivacyPolicyModal } from 'components/medical/PrivacyPolicyModal';
import { ChatPanel } from 'components/medical/ChatPanel';
import Navbar from 'components/homepage/Navbar';
import { useAuth } from 'contexts/AuthContext';


const DiagnosisFunction: React.FC = () => {
  const { loggedIn } = useAuth();
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
    testConnection,
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
  console.log('🔄 handleContinueToNext called');
  console.log('Current result:', result);
  console.log('Current stage:', currentStage);
  console.log('Current workflowInfo:', workflowInfo);

  try {
    const continueResult = await continueToNextStep();
    console.log('✅ Continue result:', continueResult);

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
    
    let result = await submitFollowUp(responses);
    console.log('✅ Follow-up submitted successfully:', result);

    // skin cancer screening -> standard follow-up requires the follow-up interaction node to run twice to generate questions and process responses distinctively
    // if (result?.workflow_info?.needs_user_input === "followup_questions2") {
    //   console.log("🔁 Detected need for second follow-up submission...");
    //   result = await submitFollowUp(responses);
    //   console.log("✅ Second follow-up submitted successfully:", result);
    // }

  } catch (err) {
    console.error('❌ Follow-up submission failed:', err);
  }
};

  const handleTestConnection = async () => {
    try {
      const healthData = await testConnection();
      alert(`✅ Backend Connected!\nStatus: ${healthData.status}\nActive Connections: ${healthData.features.active_connections}`);
    } catch (err) {
      alert(`❌ Connection Failed:\n${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <>
      {showPrivacyModal && (
        <PrivacyPolicyModal
          onAccept={handlePrivacyAccepted}
          onCancel={dismissPrivacyModal}
        />
      )}
      <Navbar loggedIn={loggedIn} />
      
      <div className="App" style={{ minHeight: '100vh', position: 'relative', paddingTop: '31px' }}>

        <button
          onClick={handleTestConnection}
          style={{
            position: 'absolute',           //right corner
            top: '32px',
            right: '32px',
            padding: 'var(--spacing-sm) var(--spacing-md)',
            background: 'rgba(0,123,255,0.85)', // visible blue
            color: '#fff',
            border: '1px solid rgba(0,123,255,0.5)',
            borderRadius: 'var(--radius-md)',
            fontSize: '16px',
            cursor: 'pointer',
            fontWeight: 'bold',
            boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
            backdropFilter: 'blur(2px)',
            zIndex: 1000
          }}
        >
          🔧 Test Backend
        </button>
        

        {/* Main Content - Workflow Router */}
        <main style={{ 
          padding: '0 var(--spacing-md)',
          minHeight: '60vh'
        }}>
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
        </main>

        <section style={{ padding: '0 var(--spacing-md)', maxWidth: '800px', margin: 'var(--spacing-lg) auto 0' }}>
          <ChatPanel />
        </section>

        {/* Footer */}
        <footer style={{
          background: '#f8f9fa',
          padding: 'var(--spacing-md)',
          textAlign: 'center',
          marginTop: 'var(--spacing-xxl)',
          borderTop: '1px solid #e9ecef',
          fontSize: '12px',
          color: 'var(--secondary)'
        }}>
          <p>🔍 Debug: {sessionId} | Stage: {currentStage || 'none'}</p>
          <p>Node-Based API: Each workflow step is an independent endpoint</p>
        </footer>
      </div>
    </>
  );
}

export default DiagnosisFunction;