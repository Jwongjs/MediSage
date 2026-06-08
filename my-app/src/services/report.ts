const API_BASE_URL = 'http://localhost:8000';

export interface MedicalReport {
  id: string;
  user_id: string;
  session_id: string;
  report_title: string;
  report_date: string;
  report_status: string;
  patient_symptoms?: string;
  textual_analysis?: any;
  followup_data?: any;
  image_analysis?: any;
  overall_analysis?: any;
  healthcare_recommendations?: any;
  medical_report_content?: string;
  workflow_path?: any;
  workflow_stages_completed?: any;
  confidence_scores?: any;
  created_at: string;
  updated_at: string;
}

export interface MedicalReportsResponse {
  reports: MedicalReport[];
  total: number;
  limit: number;
  offset: number;
}

export class MedicalReportService {
  static async getUserMedicalReports(
    limit: number = 10,
    offset: number = 0
  ): Promise<MedicalReportsResponse> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/auth/patient/medical-reports?limit=${limit}&offset=${offset}`,
        {
          credentials: 'include'
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch medical reports');
      }

      return await response.json();
    } catch (error) {
      console.error('Get medical reports error:', error);
      throw error;
    }
  }

  static async getMedicalReport(reportId: string): Promise<MedicalReport> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/auth/patient/medical-reports/${reportId}`,
        {
          credentials: 'include'
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch medical report');
      }

      return await response.json();
    } catch (error) {
      console.error('Get medical report error:', error);
      throw error;
    }
  }

  static async saveMedicalReport(
    sessionId: string,
    agentState: any,
    reportTitle?: string
  ): Promise<{ message: string; report_id: string; report: MedicalReport }> {
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('agent_state', JSON.stringify(agentState));
      if (reportTitle) {
        formData.append('report_title', reportTitle);
      }

      const response = await fetch(
        `${API_BASE_URL}/auth/patient/save-medical-report`,
        {
          method: 'POST',
          body: formData,
          credentials: 'include'
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save medical report');
      }

      return await response.json();
    } catch (error) {
      console.error('Save medical report error:', error);
      throw error;
    }
  }

  static async deleteMedicalReport(reportId: string): Promise<{ message: string }> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/auth/patient/medical-reports/${reportId}`,
        {
          method: 'DELETE',
          credentials: 'include'
        }
      );

      if (!response.ok) {
        throw new Error('Failed to delete medical report');
      }

      return await response.json();
    } catch (error) {
      console.error('Delete medical report error:', error);
      throw error;
    }
  }

  static async updateReportTitle(
    reportId: string,
    newTitle: string
  ): Promise<MedicalReport> {
    try {
      const formData = new FormData();
      formData.append('new_title', newTitle);

      const response = await fetch(
        `${API_BASE_URL}/auth/patient/medical-reports/${reportId}/title`,
        {
          method: 'PUT',
          body: formData,
          credentials: 'include'
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update report title');
      }

      return await response.json();
    } catch (error) {
      console.error('Update report title error:', error);
      throw error;
    }
  }
}