import React from 'react';
import styled from 'styled-components';
import { Button } from 'components/common/Button';
import { Card } from 'components/common/Card';
import { MedicalReport } from 'services/report';

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
`;

const ModalContent = styled.div`
  background: white;
  border-radius: 8px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
  
  h2 {
    margin: 0;
    color: var(--dark);
  }
`;

const ModalBody = styled.div`
  padding: 1.5rem;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  
  &:hover {
    background: #f8f9fa;
    border-radius: 4px;
  }
`;

const ReportSection = styled.div`
  margin-bottom: 2rem;
  
  h3 {
    margin: 0 0 1rem 0;
    color: var(--primary);
    font-size: 1.2rem;
  }
  
  p {
    margin: 0.5rem 0;
    line-height: 1.6;
  }
`;

const MetaInfo = styled.div`
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
  
  div {
    margin-bottom: 0.5rem;
    
    strong {
      display: inline-block;
      width: 120px;
      color: var(--dark);
    }
  }
`;

interface MedicalReportModalProps {
  report: MedicalReport | null;
  onClose: () => void;
}

export const MedicalReportModal: React.FC<MedicalReportModalProps> = ({
  report,
  onClose
}) => {
  if (!report) return null;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={(e) => e.stopPropagation()}>
        <ModalHeader>
          <h2>📋 {report.report_title}</h2>
          <CloseButton onClick={onClose}>×</CloseButton>
        </ModalHeader>
        
        <ModalBody>
          <MetaInfo>
            <div>
              <strong>Created:</strong> {formatDate(report.created_at)}
            </div>
            <div>
              <strong>Session ID:</strong> {report.session_id}
            </div>
            <div>
              <strong>Status:</strong> {report.report_status}
            </div>
            {report.overall_analysis?.final_diagnosis && (
              <div>
                <strong>Diagnosis:</strong> {report.overall_analysis.final_diagnosis}
              </div>
            )}
            {report.overall_analysis?.final_confidence && (
              <div>
                <strong>Confidence:</strong> {(report.overall_analysis.final_confidence * 100).toFixed(1)}%
              </div>
            )}
            {report.overall_analysis?.specialist_recommendation && (
              <div>
                <strong>Specialist:</strong> {report.overall_analysis.specialist_recommendation.replace('_', ' ')}
              </div>
            )}
          </MetaInfo>

          {report.patient_symptoms && (
            <ReportSection>
              <h3>🩺 Patient Symptoms</h3>
              <p>{report.patient_symptoms}</p>
            </ReportSection>
          )}

          {report.overall_analysis?.user_explanation && (
            <ReportSection>
              <h3>📖 Explanation</h3>
              <p>{report.overall_analysis.user_explanation}</p>
            </ReportSection>
          )}

          {report.overall_analysis?.clinical_reasoning && (
            <ReportSection>
              <h3>🔬 Clinical Reasoning</h3>
              <p>{report.overall_analysis.clinical_reasoning}</p>
            </ReportSection>
          )}

          {report.healthcare_recommendations && (
            <ReportSection>
              <h3>🏥 Healthcare Recommendations</h3>
              <div>
                {report.healthcare_recommendations.immediate_actions && (
                  <div>
                    <strong>Immediate Actions:</strong>
                    <p>{report.healthcare_recommendations.immediate_actions}</p>
                  </div>
                )}
                {report.healthcare_recommendations.specialist_referral && (
                  <div>
                    <strong>Specialist Referral:</strong>
                    <p>{report.healthcare_recommendations.specialist_referral}</p>
                  </div>
                )}
              </div>
            </ReportSection>
          )}

          {report.medical_report_content && (
            <ReportSection>
              <h3>📄 Full Medical Report</h3>
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                fontFamily: 'Georgia, serif',
                background: '#fff',
                padding: '1rem',
                border: '1px solid #e9ecef',
                borderRadius: '4px'
              }}>
                {report.medical_report_content}
              </div>
            </ReportSection>
          )}
        </ModalBody>
      </ModalContent>
    </ModalOverlay>
  );
};