"use client";

import { useState, useCallback } from 'react';
import { AgentState } from 'types/medical';
import { ApiService, DiagnosisRequest, PrivacyPolicyRequiredError } from 'services/api';

interface DiagnosisState {
  loading: boolean;
  result: AgentState | null;
  error: string | null;
  sessionId: string | null;
  currentStage: string | null;
  workflowInfo: any | null;
  privacyPolicyPending: (() => Promise<void>) | null;
}

export const useDiagnosis = () => {
  const [state, setState] = useState<DiagnosisState>({
    loading: false,
    result: null,
    error: null,
    sessionId: null,
    currentStage: null,
    workflowInfo: null,
    privacyPolicyPending: null,
  });

  //STATE ACCESSORS - prevent undefined errors
  const getResult = useCallback(() => {
    return state.result || null;
  }, [state.result]);

  const getSessionId = useCallback(() => {
    return state.sessionId || null;
  }, [state.sessionId]);

  const getCurrentStage = useCallback(() => {
    const result = getResult();
    return result?.current_workflow_stage || state.currentStage || null;
  }, [state.result, state.currentStage, getResult]);

  const getWorkflowInfo = useCallback(() => {
    return state.workflowInfo || null;
  }, [state.workflowInfo]);

  const getWorkflowPath = useCallback(() => {
    const result = getResult();
    return result?.workflow_path || [];
  }, [getResult]);

  const getRequiresUserInput = useCallback(() => {
    const result = getResult();
    return result?.requires_user_input || false;
  }, [getResult]);

  const getSkinCancerRiskDetected = useCallback(() => {
    const result = getResult();
    return result?.skin_cancer_risk_detected || false;
  }, [getResult]);

  //STATE VALIDATION
  const validateActiveSession = useCallback(() => {
    const sessionId = getSessionId();
    const result = getResult();
    
    if (!sessionId) {
      throw new Error('No active session ID available');
    }
    if (!result) {
      throw new Error('No active session result available');
    }
    
    return { sessionId, result };
  }, [getSessionId, getResult]);

  // Test backend connection
  const testConnection = useCallback(async () => {
    try {
      const healthData = await ApiService.testConnection();
      return healthData;
    } catch (error) {
      throw error;
    }
  }, []);

  //NODE 1: Start diagnosis with textual analysis
  const startDiagnosis = useCallback(async (request: DiagnosisRequest) => {
    setState(prev => ({
      ...prev,
      loading: true,
      error: null
    }));

    try {
      const response = await ApiService.startTextualAnalysis(request);
      
      //Validate response structure
      if (!response || !response.result) {
        throw new Error('Invalid response from textual analysis');
      }
      
      setState(prev => ({
        ...prev,
        loading: false,
        result: response.result,
        sessionId: response.session_id || null,
        currentStage: response.result?.current_workflow_stage || null,
        workflowInfo: response.workflow_info || null
      }));

      return response;

    } catch (error) {
      if (error instanceof PrivacyPolicyRequiredError) {
        setState(prev => ({
          ...prev,
          loading: false,
          privacyPolicyPending: async () => {
            setState(p => ({ ...p, privacyPolicyPending: null }));
            await startDiagnosis(request);
          },
        }));
        return;
      }
      const errorMessage = error instanceof Error ? error.message : 'Diagnosis failed';
      setState(prev => ({ ...prev, loading: false, error: errorMessage }));
      throw error;
    }
  }, []);

  //NODE 2: Follow-up questions
  const submitFollowUp = useCallback(async (responses: Record<string, string>) => {
    const { sessionId, result } = validateActiveSession();

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await ApiService.runFollowupQuestions(
        sessionId,
        result,
        responses
      );

      console.log('📝 Follow-up responses submitted:', responses);
      console.log('📊 Follow-up response:', response);
      
      //Validate response structure
      if (!response || !response.result) {
        throw new Error('Invalid response from follow-up questions');
      }
      
      setState(prev => ({
        ...prev,
        loading: false,
        result: response.result,
        currentStage: response.result?.current_workflow_stage || prev.currentStage,
        workflowInfo: response.workflow_info || null
      }));

      return response;

    } catch (error) {
      if (error instanceof PrivacyPolicyRequiredError) {
        setState(prev => ({
          ...prev,
          loading: false,
          privacyPolicyPending: async () => {
            setState(p => ({ ...p, privacyPolicyPending: null }));
            await submitFollowUp(responses);
          },
        }));
        return;
      }
      const errorMessage = error instanceof Error ? error.message : 'Follow-up failed';
      setState(prev => ({ ...prev, loading: false, error: errorMessage }));
      throw error;
    }
  }, [validateActiveSession]);

  //NODE 4: Overall analysis  
  const runOverallAnalysis = useCallback(async () => {
    const { sessionId, result } = validateActiveSession();

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await ApiService.runOverallAnalysis(
        sessionId,
        result
      );
      
      console.log('🎯 Overall analysis response:', response);
      
      // 🔧 Validate response structure
      if (!response || !response.result) {
        throw new Error('Invalid response from overall analysis');
      }
      
      setState(prev => ({
        ...prev,
        loading: false,
        result: response.result,
        currentStage: response.result?.current_workflow_stage || prev.currentStage,
        workflowInfo: response.workflow_info || null
      }));

      return response;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Overall analysis failed';
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));
      throw error;
    }
  }, [validateActiveSession]);

  //NODE 6: Medical report
  const runMedicalReport = useCallback(async () => {
    const { sessionId, result } = validateActiveSession();

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const response = await ApiService.runMedicalReport(
        sessionId,
        result
      );
      
      console.log('📄 Medical report response:', response);
      
      // 🔧 Validate response structure
      if (!response || !response.result) {
        throw new Error('Invalid response from medical report');
      }
      
      setState(prev => ({
        ...prev,
        loading: false,
        result: response.result,
        currentStage: response.result?.current_workflow_stage || prev.currentStage,
        workflowInfo: response.workflow_info || null
      }));

      return response;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Medical report failed';
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));
      throw error;
    }
  }, [validateActiveSession]);

  const callNextEndpoint = useCallback(async (endpoint: string) => {
    console.log('🔄 Calling next endpoint:', endpoint);
    
    // Map endpoint to API call
    switch (endpoint) {
      case '/patient/overall_analysis':
        return await runOverallAnalysis();
      case '/patient/medical_report':
        return await runMedicalReport();
      default:
        throw new Error(`Unknown endpoint: ${endpoint}`);
    }
  }, [runOverallAnalysis, runMedicalReport]);

  //AUTO-PROGRESSION: Continue to next recommended node
  const continueWorkflow = useCallback(async () => {
    console.log('🔄 continueWorkflow called');
    
    const workflowInfo = getWorkflowInfo();
    const { sessionId, result } = validateActiveSession();
    
    console.log('Current workflowInfo:', workflowInfo);

    if (!workflowInfo) {
      throw new Error('No workflow info available');
    }

    const { next_endpoint, needs_user_input, workflow_complete } = workflowInfo;

    // Check if user input is needed
    if (needs_user_input) {
      return { needsUserInput: needs_user_input };
    }

    // Check if workflow is complete
    if (workflow_complete) {
      return { workflowComplete: true };
    }

    // Continue to next step
    if (next_endpoint) {
      return await callNextEndpoint(next_endpoint);
    }

    throw new Error('No next step determined');
  }, [getWorkflowInfo, validateActiveSession, callNextEndpoint]);

  const continueToNextStep = useCallback(async () => {
    console.log('🔄 continueToNextStep called');
    
    //Get all state values
    const currentStage = getCurrentStage();
    const workflowInfo = getWorkflowInfo();
    const result = getResult();
    const sessionId = getSessionId();
    const requiresUserInput = getRequiresUserInput();
    const skinCancerRiskDetected = getSkinCancerRiskDetected();
    
    console.log('🔍 State check:', {
      currentStage,
      hasWorkflowInfo: !!workflowInfo,
      hasResult: !!result,
      hasSessionId: !!sessionId,
      requiresUserInput,
      skinCancerRiskDetected
    });

    //EARLY VALIDATION
    if (!result) {
      console.error('❌ No result available for continuation');
      throw new Error('No active session result available');
    }

    if (!sessionId) {
      console.error('❌ No session ID available');
      throw new Error('No active session ID available');
    }

    // ============================================
    // STAGE-BASED WORKFLOW PROGRESSION (ORDERED)
    // ============================================

    // ============================================
    // FOLLOW-UP COMPLETION LOGIC
    // ============================================
    
    if (currentStage === 'followup_analysis_complete') {
      //Check for requires_user_input flag to handle transitions
      if (requiresUserInput) {
        console.log('📝 Follow-up transition requires more user input - staying on follow-up page');
        return { needsFollowUpQuestions: true };
      }

      {
        // No skin cancer risk - proceed to overall analysis
        console.log('✅ Follow-up completed without skin cancer risk - proceeding to overall analysis...');
        try {
          return await runOverallAnalysis();
        } catch (error) {
          console.error('❌ Overall analysis failed:', error);
          throw error;
        }
      }
    }

    // ============================================
    // OVERALL ANALYSIS COMPLETION
    // ============================================
    
    if (currentStage === 'overall_analysis_complete') {
      console.log('🎯 Overall analysis complete, proceeding to medical report...');
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        console.log('📄 Generating medical report...');
        const reportResponse = await ApiService.runMedicalReport(
          sessionId,
          result
        );
        
        //Validate response
        if (!reportResponse || !reportResponse.result) {
          throw new Error('Invalid medical report response');
        }
        
        setState(prev => ({
          ...prev,
          loading: false,
          result: reportResponse.result,
          currentStage: reportResponse.result?.current_workflow_stage || prev.currentStage,
          workflowInfo: reportResponse.workflow_info || null
        }));
        
        console.log('✅ Medical report generation completed');
        return reportResponse;
        
      } catch (error) {
        console.error('❌ Medical report generation failed:', error);
        setState(prev => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : 'Medical report generation failed'
        }));
        throw error;
      }
    }

    // ============================================
    // WORKFLOW INFO BASED PROGRESSION
    // ============================================
    
    if (!workflowInfo) {
      console.error('❌ No workflow info available for stage:', currentStage);
      throw new Error('No workflow info available');
    }
    
    const { next_endpoint, needs_user_input, next_step_description } = workflowInfo;
    
    console.log('🔍 Workflow info details:');
    console.log('   Next endpoint:', next_endpoint);
    console.log('   Needs user input:', needs_user_input);
    console.log('   Description:', next_step_description);

    // ============================================
    // USER INPUT ROUTING
    // ============================================
    if (needs_user_input === 'followup_questions') {
      console.log('📝 Generating follow-up questions...');
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        const response = await ApiService.runFollowupQuestions(
          sessionId,
          result
          // No responses yet - this will generate questions
        );
        
        //Validate response
        if (!response || !response.result) {
          throw new Error('Invalid follow-up questions response');
        }
        
        setState(prev => ({
          ...prev,
          loading: false,
          result: response.result,
          currentStage: response.result?.current_workflow_stage || prev.currentStage,
          workflowInfo: response.workflow_info || null // Clear workflow info since we're now in a different stage
        }));
        
        console.log('✅ Follow-up questions generated successfully');
        return response;
      } catch (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : 'Failed to generate follow-up questions'
        }));
        throw error;
      }
    }
    // ============================================
    // AUTO-CONTINUE TO NEXT ENDPOINT
    // ============================================
    else if (!needs_user_input && next_endpoint) {
      console.log('🔄 Auto-continuing to:', next_endpoint);
      try {
        return await callNextEndpoint(next_endpoint);
      } catch (error) {
        console.error('❌ Auto-continue failed:', error);
        throw error;
      }
    }
    // ============================================
    // FALLBACK ERROR HANDLING
    // ============================================
    else {
      console.error('❌ Unknown workflow state:', {
        stage: currentStage,
        needs_user_input,
        next_endpoint,
        next_step_description
      });
      throw new Error(`Unknown next step: ${next_step_description || 'Unknown'}`);
    }
    
  }, [
    getCurrentStage,
    getWorkflowInfo,
    getResult,
    getSessionId,
    getRequiresUserInput,
    validateActiveSession,
    callNextEndpoint,
    runOverallAnalysis
  ]);
  
  const handlePrivacyAccepted = useCallback(async () => {
    await ApiService.acceptPrivacyPolicy();
    if (state.privacyPolicyPending) {
      await state.privacyPolicyPending();
    }
  }, [state.privacyPolicyPending]);

  const dismissPrivacyModal = useCallback(() => {
    setState(prev => ({ ...prev, privacyPolicyPending: null }));
  }, []);

  // Reset diagnosis state
  const reset = useCallback(() => {
    setState({
      loading: false,
      result: null,
      error: null,
      sessionId: null,
      currentStage: null,
      workflowInfo: null,
      privacyPolicyPending: null,
    });
  }, []);

  return {
    loading: state.loading,
    result: getResult(),
    error: state.error,
    sessionId: getSessionId(),
    currentStage: getCurrentStage(),
    workflowInfo: getWorkflowInfo(),
    showPrivacyModal: !!state.privacyPolicyPending,
    handlePrivacyAccepted,
    dismissPrivacyModal,
    startDiagnosis,
    continueToNextStep,
    submitFollowUp,
    runOverallAnalysis,
    runMedicalReport,
    continueWorkflow,
    testConnection,
    reset
  };
};