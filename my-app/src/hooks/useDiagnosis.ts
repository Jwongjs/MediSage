"use client";

import { useState, useCallback } from 'react';
import { DiagnosisView, Answer } from 'types/diagnosis';
import { DiagnosisService } from 'services/diagnosis';
import { ApiService } from 'services/api';
import { FlowStep } from 'WorkflowRouter';

interface DiagnosisState {
  step: FlowStep;
  view: DiagnosisView | null;
  loading: boolean;
  error: string | null;
  sessionId: string | null;
  privacyPolicyPending: (() => Promise<void>) | null;
}

const INITIAL_STATE: DiagnosisState = {
  step: 'form',
  view: null,
  loading: false,
  error: null,
  sessionId: null,
  privacyPolicyPending: null,
};

// The compliance gate is a 403 carrying this marker in its body; DiagnosisService
// surfaces the raw response text as the Error message.
const isPrivacyPolicyRequired = (error: unknown): boolean =>
  error instanceof Error && error.message.includes('privacy_policy_required');

const messageOf = (error: unknown, fallback: string): string =>
  error instanceof Error ? error.message : fallback;

export const useDiagnosis = () => {
  const [state, setState] = useState<DiagnosisState>(INITIAL_STATE);

  const startDiagnosis = useCallback(async (patientText: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await DiagnosisService.start(patientText);
      setState(prev => ({
        ...prev,
        loading: false,
        step: 'evidence',
        view: response.result,
        sessionId: response.session_id,
      }));
    } catch (error) {
      if (isPrivacyPolicyRequired(error)) {
        setState(prev => ({
          ...prev,
          loading: false,
          privacyPolicyPending: async () => {
            setState(p => ({ ...p, privacyPolicyPending: null }));
            await startDiagnosis(patientText);
          },
        }));
        return;
      }
      setState(prev => ({ ...prev, loading: false, error: messageOf(error, 'Diagnosis failed') }));
    }
  }, []);

  const goToQuestions = useCallback(() => {
    setState(prev => ({ ...prev, step: 'questions' }));
  }, []);

  const submitAnswers = useCallback(async (answers: Record<string, Answer>) => {
    const sessionId = state.sessionId;
    if (!sessionId) {
      setState(prev => ({ ...prev, error: 'No active session ID available' }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await DiagnosisService.submitAnswers(sessionId, answers);
      setState(prev => ({
        ...prev,
        loading: false,
        step: 'evidence',
        view: response.result,
      }));
    } catch (error) {
      if (isPrivacyPolicyRequired(error)) {
        setState(prev => ({
          ...prev,
          loading: false,
          privacyPolicyPending: async () => {
            setState(p => ({ ...p, privacyPolicyPending: null }));
            await submitAnswers(answers);
          },
        }));
        return;
      }
      setState(prev => ({ ...prev, loading: false, error: messageOf(error, 'Could not update with your answers') }));
    }
  }, [state.sessionId]);

  const finalize = useCallback(async () => {
    const sessionId = state.sessionId;
    if (!sessionId) {
      setState(prev => ({ ...prev, error: 'No active session ID available' }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null, step: 'summary' }));

    try {
      const response = await DiagnosisService.finalize(sessionId);
      setState(prev => ({
        ...prev,
        loading: false,
        step: 'summary',
        view: response.result,
      }));
    } catch (error) {
      if (isPrivacyPolicyRequired(error)) {
        setState(prev => ({
          ...prev,
          loading: false,
          privacyPolicyPending: async () => {
            setState(p => ({ ...p, privacyPolicyPending: null }));
            await finalize();
          },
        }));
        return;
      }
      setState(prev => ({ ...prev, loading: false, error: messageOf(error, 'Could not build your summary') }));
    }
  }, [state.sessionId]);

  const handlePrivacyAccepted = useCallback(async () => {
    await ApiService.acceptPrivacyPolicy();
    if (state.privacyPolicyPending) {
      await state.privacyPolicyPending();
    }
  }, [state.privacyPolicyPending]);

  const dismissPrivacyModal = useCallback(() => {
    setState(prev => ({ ...prev, privacyPolicyPending: null }));
  }, []);

  const reset = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  return {
    step: state.step,
    view: state.view,
    loading: state.loading,
    error: state.error,
    showPrivacyModal: !!state.privacyPolicyPending,
    handlePrivacyAccepted,
    dismissPrivacyModal,
    startDiagnosis,
    goToQuestions,
    submitAnswers,
    finalize,
    reset,
  };
};
