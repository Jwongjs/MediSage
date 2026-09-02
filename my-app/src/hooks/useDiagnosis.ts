"use client";

import { useState, useCallback } from 'react';
import { DiagnosisView, Answer } from 'types/diagnosis';
import { DiagnosisService } from 'services/diagnosis';
import { FlowStep } from 'WorkflowRouter';

interface DiagnosisState {
  step: FlowStep;
  view: DiagnosisView | null;
  loading: boolean;
  error: string | null;
  sessionId: string | null;
}

const INITIAL_STATE: DiagnosisState = {
  step: 'form',
  view: null,
  loading: false,
  error: null,
  sessionId: null,
};

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
      setState(prev => ({ ...prev, loading: false, error: messageOf(error, 'Could not build your summary') }));
    }
  }, [state.sessionId]);

  const reset = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  return {
    step: state.step,
    view: state.view,
    loading: state.loading,
    error: state.error,
    sessionId: state.sessionId,
    startDiagnosis,
    goToQuestions,
    submitAnswers,
    finalize,
    reset,
  };
};
