const API_BASE_URL = 'http://localhost:8000';

export interface DiagnosisRequest {
  symptoms: string;
  image?: File;
  location?: { lat: number; lng: number };
}

export class ApiService {
  
  // Test backend connection
  static async testConnection(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('❌ Backend connection failed:', error);
      throw new Error(`Backend connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  //NODE 1: textual analysis
  static async startTextualAnalysis(request: DiagnosisRequest): Promise<any> {
    try {
      const formData = new FormData();
      const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      formData.append('user_symptoms', request.symptoms);
      formData.append('session_id', sessionId);
      
//Comprehensive debug logging
      const fullUrl = `${API_BASE_URL}/patient/textual_analysis`;
      console.log('🔍 DETAILED API CALL DEBUG:');
      console.log('  Full URL:', fullUrl);
      console.log('  API_BASE_URL:', API_BASE_URL);
      console.log('  Method: POST');
      console.log('  Symptoms (first 100 chars):', request.symptoms.substring(0, 100) + '...');
      console.log('  Session ID:', sessionId);
      console.log('  FormData entries:', Array.from(formData.entries()).map(([key, value]) => 
        [key, typeof value === 'string' ? value.substring(0, 50) + '...' : 'FILE']
      ));

      const response = await fetch(`${API_BASE_URL}/patient/textual_analysis`, {
        method: 'POST',
        body: formData
      });

      console.log('🔍 RESPONSE DEBUG:');
      console.log('  Status Code:', response.status);
      console.log('  Status Text:', response.statusText);
      console.log('  Response OK:', response.ok);
      console.log('  Response URL:', response.url);
      console.log('  Response Type:', response.type);
      console.log('  Response Headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Textual analysis failed: HTTP ${response.status} - ${errorText}`);
      }

      const result = await response.json();
      console.log('✅ Textual analysis completed:', result);
      
      return result;

    } catch (error) {
      console.error('❌ Textual analysis failed:', error);
      throw error;
    }
  }

  //NODE 2: Follow-up questions
  static async runFollowupQuestions(sessionId: string, previousState: any, responses?: Record<string, string>): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('previous_state', JSON.stringify(previousState));
      
      if (responses) {
        formData.append('followup_responses', JSON.stringify(responses));
      }

      console.log('📝 Running follow-up questions:', { sessionId, hasResponses: !!responses });

      const response = await fetch(`${API_BASE_URL}/patient/followup_questions`, {
        method: 'POST',
        body: formData
      });

      return await response.json();

    } catch (error) {
      console.error('❌ Follow-up questions failed:', error);
      throw error;
    }
  }

  //NODE 3: Image analysis
  static async runImageAnalysis(sessionId: string, previousState: any, image?: File): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('previous_state', JSON.stringify(previousState));
      
      if (image) {
        formData.append('image_file', image);
      }

      console.log('📸 Running image analysis:', { sessionId, hasImage: !!image });

      const response = await fetch(`${API_BASE_URL}/patient/image_analysis`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Image analysis failed: HTTP ${response.status} - ${errorText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('❌ Image analysis failed:', error);
      throw error;
    }
  }

  //NODE 4: Overall analysis
  static async runOverallAnalysis(sessionId: string, previousState: any): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('previous_state', JSON.stringify(previousState));

      console.log('🎯 Running overall analysis:', { sessionId });

      const response = await fetch(`${API_BASE_URL}/patient/overall_analysis`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Overall analysis failed: HTTP ${response.status} - ${errorText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('❌ Overall analysis failed:', error);
      throw error;
    }
  }

  //NODE Final: Medical report
  static async runMedicalReport(sessionId: string, previousState: any): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('previous_state', JSON.stringify(previousState));

      console.log('📄 Running medical report:', { sessionId });

      const response = await fetch(`${API_BASE_URL}/patient/medical_report`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Medical report failed: HTTP ${response.status} - ${errorText}`);
      }

      return await response.json();

    } catch (error) {
      console.error('❌ Medical report failed:', error);
      throw error;
    }
  }
  
    //PDF/Word generation 
  static async exportMedicalReport(
    sessionId: string, 
    format: 'pdf' | 'word', 
    reportData: any,
    includeDetails: boolean = true
  ): Promise<Blob> {
    try {
      console.log(`📄 Exporting medical report as ${format.toUpperCase()}:`, { sessionId, format });

      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('format', format);
      formData.append('include_details', includeDetails.toString());
      formData.append('report_data', JSON.stringify(reportData));

      const response = await fetch(`${API_BASE_URL}/patient/export_report`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Export failed: HTTP ${response.status} - ${errorText}`);
      }

      return await response.blob();

    } catch (error) {
      console.error(`❌ ${format.toUpperCase()} export failed:`, error);
      throw error;
    }
  }
}