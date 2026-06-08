import React, { useState, useRef } from 'react';
import { AgentState } from 'types/medical';
import { Card } from 'components/common/Card';
import { Button } from 'components/common/Button';
import { PageHeader } from 'components/layout/PageHeader';
import { ApiService } from 'services/api';

import { MedicalReportService } from 'services/report';
import { useAuth } from 'contexts/AuthContext';

interface FinalReportPageProps {
  workflowState: AgentState | null;
  loading: boolean;
  onReset: () => void;
}

export const FinalReportPage: React.FC<FinalReportPageProps> = ({
  workflowState,
  loading,
  onReset
}) => {
  const { loggedIn } = useAuth();

  const [showExportOptions, setShowExportOptions] = useState(false);
  const [showStorageOptions, setShowStorageOptions] = useState(false);
  const [exportFormat, setExportFormat] = useState<'pdf' | 'word' | 'text'>('pdf');
  const [includeDetails, setIncludeDetails] = useState(true);
  const [agreedToStorage, setAgreedToStorage] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  
  const reportRef = useRef<HTMLDivElement>(null);
  const [accountLoading, setAccountLoading] = useState(false);


  const handleExport = async (format: 'pdf' | 'word' | 'text') => {
    const timestamp = new Date().toISOString().split('T')[0];
    const diagnosis = workflowState?.overall_analysis?.final_diagnosis?.replace(/[^a-zA-Z0-9]/g, '_') || 'diagnosis';
    const filename = `medical-report-${diagnosis}-${timestamp}`;
    
    try {
      if (format === 'text') {
        //Frontend for txt only: Keep text export (lightweight)
        exportToText(filename);
        alert(`✅ Text file downloaded: ${filename}.txt`);
      } else {
        // 🔧 BACKEND: Use ApiService.exportMedicalReport
        if (!workflowState?.session_id) {
          throw new Error('No session ID available for export');
        }

        const reportData = {
          overall_analysis: workflowState.overall_analysis,
          medical_report: workflowState.medical_report,
          session_metadata: {
            session_id: workflowState.session_id,
            workflow_stage: workflowState.current_workflow_stage,
            timestamp: new Date().toISOString()
          }
        };

        console.log(`📄 Exporting ${format.toUpperCase()} via ApiService...`);
        
        const blob = await ApiService.exportMedicalReport(
          workflowState.session_id,
          format,
          reportData,
          includeDetails
        );

        // Download the generated file
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.${format === 'word' ? 'docx' : 'pdf'}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        alert(`✅ ${format.toUpperCase()} file downloaded: ${filename}.${format === 'word' ? 'docx' : 'pdf'}`);
      }
      
    } catch (error) {
      console.error(`❌ ${format.toUpperCase()} export failed:`, error);
      alert(`❌ ${format.toUpperCase()} export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setExportLoading(false); // 🔧 FIX: Now properly used
    }
  };

  //Text export (frontend only)
  const exportToText = (filename: string) => {
    const overallAnalysis = workflowState?.overall_analysis;
    const medicalReport = workflowState?.medical_report;
    
    let content = `MEDICAL ANALYSIS REPORT\n`;
    content += `Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}\n`;
    content += `${'='.repeat(50)}\n\n`;
    
    // Primary Diagnosis
    content += `PRIMARY DIAGNOSIS: ${overallAnalysis?.final_diagnosis || 'Not available'}\n`;
    content += `CONFIDENCE: ${((overallAnalysis?.final_confidence || 0) * 100).toFixed(1)}%\n`;
    content += `SEVERITY: ${overallAnalysis?.final_severity || 'unknown'}\n`;
    content += `SPECIALIST: ${overallAnalysis?.specialist_recommendation?.replace('_', ' ') || 'general practitioner'}\n\n`;
    
    // User Explanation
    if (overallAnalysis?.user_explanation) {
      content += `WHAT IS IT?\n${overallAnalysis.user_explanation}\n\n`;
    }
    
    // Clinical Reasoning
    if (overallAnalysis?.clinical_reasoning) {
      content += `CLINICAL REASONING:\n${overallAnalysis.clinical_reasoning}\n\n`;
    }
    
    // Full Report
    if (medicalReport) {
      content += `DETAILED MEDICAL REPORT:\n${'-'.repeat(30)}\n${medicalReport}\n\n`;
    }
    
    // Disclaimer
    content += `${'='.repeat(50)}\n`;
    content += `MEDICAL DISCLAIMER:\n`;
    content += `This report is for informational purposes only. Always consult healthcare professionals for medical advice.\n`;
    
    // Download
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

const handleAccountStorage = async () => {  
  if (!loggedIn) {
    alert('❌ Please log in to save your medical report to your account.');
    return;
  }

  if (!workflowState?.session_id) {
    alert('❌ No session data available to save.');
    return;
  }

  try {
    setAccountLoading(true);
    
    const reportTitle = `Medical Report - ${new Date().toLocaleDateString()} - ${workflowState.overall_analysis?.final_diagnosis || 'Diagnosis'}`;
    
    const result = await MedicalReportService.saveMedicalReport(
      workflowState.session_id, 
      workflowState,
      reportTitle
    );
    
    alert(`✅ Medical report saved successfully!\n\nReport: ${result.report.report_title}\n\nYou can view and manage all your saved reports in your profile page.`);
    setShowStorageOptions(false);

  } catch (error) {
    alert(`❌ Failed to save medical report: ${error instanceof Error ? error.message : 'Unknown error'}`);
  } finally {
    setAccountLoading(false);
  }
};

  // Extract stats from workflowState
  const stats = {
    finalDiagnosis: workflowState?.overall_analysis?.final_diagnosis || 'Not available',
    finalConfidence: workflowState?.overall_analysis?.final_confidence || 0,
    totalStages: 6, // Assuming 6 stages based on the UI
    specialist: workflowState?.overall_analysis?.specialist_recommendation || 'general_practitioner'
  };

  const hasReport = workflowState?.medical_report;

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <PageHeader
        title="📄 Final Medical Report"
        subtitle="Your comprehensive AI medical analysis is complete"
        step={{
          current: 5,
          total: 5,
          description: "Medical report generation"
        }}
        variant="success"
      />

      {/* Report Summary Card */}
      <Card variant="success" style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-lg)' }}>
          <h2 style={{ 
            margin: '0 0 var(--spacing-sm) 0', 
            fontSize: '1.6rem',
            color: 'var(--success)'
          }}>
            🎉 Analysis Complete!
          </h2>
          <p style={{ margin: 0, color: 'var(--secondary)' }}>
            Your comprehensive medical analysis report is ready
          </p>
        </div>

        {/* Quick Summary Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--spacing-md)',
          marginBottom: 'var(--spacing-lg)'
        }}>
          <Card padding="md" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '12px', color: 'var(--secondary)', marginBottom: '4px' }}>
              FINAL DIAGNOSIS
            </div>
            <div style={{ 
              fontSize: '1rem', 
              fontWeight: '600',
              color: 'var(--dark)'
            }}>
              {stats.finalDiagnosis}
            </div>
          </Card>

          <Card padding="md" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '12px', color: 'var(--secondary)', marginBottom: '4px' }}>
              CONFIDENCE LEVEL
            </div>
            <div style={{ 
              fontSize: '1.2rem', 
              fontWeight: '700',
              color: stats.finalConfidence >= 0.8 ? 'var(--success)' : 
                     stats.finalConfidence >= 0.6 ? 'var(--warning)' : 'var(--danger)'
            }}>
              {(stats.finalConfidence * 100).toFixed(1)}%
            </div>
          </Card>

          <Card padding="md" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '12px', color: 'var(--secondary)', marginBottom: '4px' }}>
              STAGES COMPLETED
            </div>
            <div style={{ 
              fontSize: '1.2rem', 
              fontWeight: '600',
              color: 'var(--primary)'
            }}>
              {stats.totalStages}/6
            </div>
          </Card>

          <Card padding="md" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '12px', color: 'var(--secondary)', marginBottom: '4px' }}>
              RECOMMENDED SPECIALIST
            </div>
            <div style={{ 
              fontSize: '1rem', 
              fontWeight: '600',
              color: 'var(--primary)',
              textTransform: 'capitalize'
            }}>
              {stats.specialist.replace('_', ' ')}
            </div>
          </Card>
        </div>
      </Card>

      {/* Full Medical Report */}
      {hasReport ? (
        <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
            <h3 style={{ 
              margin: 0,
              color: 'var(--dark)',
              fontSize: '1.3rem'
            }}>
              📋 Detailed Medical Report
            </h3>
            
            {/* Export Button */}
            <Button
              onClick={() => setShowExportOptions(!showExportOptions)}
              variant="primary"
              size="sm"
            >
              📤 Export Report
            </Button>
          </div>

          {/* Export Options */}
          {showExportOptions && (
            <Card variant="primary" style={{ marginBottom: 'var(--spacing-lg)' }}>
              <h4 style={{ margin: '0 0 var(--spacing-md) 0', color: 'var(--dark)' }}>
                📄 Export Options
              </h4>
              
              <div style={{ marginBottom: 'var(--spacing-md)' }}>
                <label style={{ fontSize: '14px', color: 'var(--dark)', display: 'block', marginBottom: '8px' }}>
                  Choose format:
                </label>
                <div style={{ display: 'flex', gap: 'var(--spacing-sm)', flexWrap: 'wrap' }}>
                  {(['pdf', 'word', 'text'] as const).map((format) => (
                    <label key={format} style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="radio"
                        name="exportFormat"
                        value={format}
                        checked={exportFormat === format}
                        onChange={(e) => setExportFormat(e.target.value as any)}
                      />
                      <span style={{ fontSize: '14px', textTransform: 'uppercase' }}>
                        {format === 'pdf' ? '📄 PDF' : format === 'word' ? '📝 Word' : '📃 Text'}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div style={{ marginBottom: 'var(--spacing-md)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }}>
                  <input
                    type="checkbox"
                    checked={includeDetails}
                    onChange={(e) => setIncludeDetails(e.target.checked)}
                  />
                  Include detailed analysis and reasoning
                </label>
              </div>

              <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                <Button
                  onClick={() => handleExport(exportFormat)}
                  variant="primary"
                  size="sm"
                >
                  📥 Download {exportFormat.toUpperCase()}
                </Button>
                <Button
                  onClick={() => setShowExportOptions(false)}
                  variant="secondary"
                  size="sm"
                >
                  Cancel
                </Button>
              </div>
            </Card>
          )}

          {/* Report Content */}
          <div 
            ref={reportRef}
            style={{
              background: '#ffffff',
              padding: 'var(--spacing-xl)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #e9ecef',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              fontFamily: 'Georgia, serif', // More professional for medical reports
              lineHeight: '1.6'
            }}
          >
            <div style={{ 
              borderBottom: '3px solid var(--primary)', 
              paddingBottom: 'var(--spacing-md)', 
              marginBottom: 'var(--spacing-xl)',
              textAlign: 'center'
            }}>
              <h1 style={{ margin: 0, color: 'var(--dark)', fontSize: '1.6rem' }}>
                Medical Analysis Report
              </h1>
              <div style={{ 
                fontSize: '14px', 
                color: 'var(--secondary)', 
                marginTop: 'var(--spacing-sm)' 
              }}>
                AI-Generated Medical Assessment
              </div>
              <div style={{ fontSize: '12px', color: 'var(--secondary)', marginTop: '4px' }}>
                Generated on {new Date().toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })} at {new Date().toLocaleTimeString()}
              </div>
            </div>

            <div style={{ 
              whiteSpace: 'pre-wrap', 
              fontSize: '14px',
              lineHeight: '1.8',
              margin: 0
            }}>
              {workflowState?.medical_report}
            </div>
          </div>
        </Card>
      ) : (
        <Card>
          <p>⏳ Report generation in progress...</p>
        </Card>
      )}

      {/* Account Storage Options */}
      <Card style={{ marginBottom: 'var(--spacing-lg)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-md)' }}>
          <h4 style={{ 
            margin: 0,
            color: 'var(--dark)',
            fontSize: '1.2rem'
          }}>
            💾 Save to Personal Medical History
          </h4>
          
          <Button
            onClick={() => setShowStorageOptions(!showStorageOptions)}
            variant="secondary"
            size="sm"
          >
            {showStorageOptions ? 'Hide Options' : 'Show Options'}
          </Button>
        </div>

        {showStorageOptions && (
          <Card variant="primary" style={{ marginTop: 'var(--spacing-md)' }}>
            <div style={{ marginBottom: 'var(--spacing-md)', fontSize: '14px', lineHeight: '1.6' }}>
              <p style={{ margin: '0 0 var(--spacing-sm) 0' }}>
                <strong>Benefits of saving your report:</strong>
              </p>
              <ul style={{ margin: 0, paddingLeft: 'var(--spacing-lg)' }}>
                <li>🤖 AI chatbot will remember your medical history for personalized advice</li>
                <li>📈 Track health trends and symptom patterns over time</li>
                <li>🏥 Easy sharing with healthcare providers</li>
                <li>📱 Access from any device with your account</li>
                <li>🔒 Secure, encrypted storage compliant with medical privacy standards</li>
              </ul>
            </div>

            <div style={{ marginBottom: 'var(--spacing-md)' }}>
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', cursor: 'pointer', fontSize: '14px' }}>
                <input
                  type="checkbox"
                  checked={agreedToStorage}
                  onChange={(e) => setAgreedToStorage(e.target.checked)}
                  style={{ marginTop: '2px' }}
                />
                <span>
                  I agree to store this medical report in my personal account and understand that 
                  this data will be used to enhance future AI consultations. 
                  <strong> (Account creation required)</strong>
                </span>
              </label>
            </div>

            <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
              <Button
                onClick={handleAccountStorage}
                variant="primary"
                size="sm"
                disabled={!agreedToStorage || accountLoading} // Add accountLoading here
              >
                {accountLoading ? '💾 Saving...' : '💾 Save to Account'} {/* Show loading text */}
              </Button>
              <Button
                onClick={() => setShowStorageOptions(false)}
                variant="secondary"
                size="sm"
              >
                Not Now
              </Button>
            </div>
          </Card>
        )}
      </Card>

      {/* Action Buttons */}
      <div style={{ 
        display: 'flex', 
        gap: 'var(--spacing-md)', 
        justifyContent: 'center',
        marginBottom: 'var(--spacing-xl)'
      }}>
        <Button
          onClick={() => window.print()}
          variant="secondary"
        >
          🖨️ Print Report
        </Button>
        
        <Button
          onClick={onReset}
          variant="primary"
        >
          🆕 New Diagnosis
        </Button>
      </div>

      {/* Medical Disclaimer */}
      <Card variant="warning" style={{ textAlign: 'center' }}>
        <h5 style={{ margin: '0 0 var(--spacing-sm) 0', color: 'var(--warning)' }}>
          ⚠️ Important Medical Disclaimer
        </h5>
        <p style={{ 
          margin: 0, 
          fontSize: '14px', 
          lineHeight: '1.6',
          color: 'var(--dark)'
        }}>
          This AI-generated report is for informational purposes only and should not replace 
          professional medical advice, diagnosis, or treatment. Always consult with qualified 
          healthcare professionals for medical concerns. In case of emergency, contact your 
          local emergency services immediately.
        </p>
      </Card>
    </div>
  );
};