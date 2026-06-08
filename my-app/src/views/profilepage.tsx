import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import Navbar from 'components/homepage/Navbar';
import { Button } from 'components/common/Button';
import { Input } from 'components/common/Input';
import { Card } from 'components/common/Card';
import { LoadingSpinner } from 'components/common/LoadingSpinner';
import { useAuth } from 'contexts/AuthContext';
import { AuthService } from 'services/auth';
import { MedicalReportService, MedicalReport } from 'services/report';
import { UserProfile } from 'types/auth';
import { MedicalReportModal } from 'components/medical/MedicalReportModal';

const ProfileWrapper = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
`;

const ProfileHeader = styled.div`
  text-align: center;
  margin-bottom: 3rem;
  
  h1 {
    margin: 0 0 0.5rem 0;
    color: var(--dark);
    font-size: 2rem;
  }
  
  p {
    margin: 0;
    color: var(--secondary);
    font-size: 1rem;
  }
`;

const ProfileGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 2rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const SectionCard = styled(Card)`
  height: fit-content;
`;

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between; /* FIXED: was "between" */
  align-items: center;
  margin-bottom: 1.5rem;
  
  h3 {
    margin: 0;
    color: var(--dark);
    font-size: 1.3rem;
  }
`;

const FieldGroup = styled.div`
  margin-bottom: 1.5rem;
`;

const Label = styled.label`
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: var(--dark);
`;

const ErrorText = styled.p`
  color: var(--danger);
  font-size: 0.9rem;
  margin: 0.5rem 0;
`;

const SuccessText = styled.p`
  color: var(--success);
  font-size: 0.9rem;
  margin: 0.5rem 0;
`;

const ReportsContainer = styled.div`
  max-height: 600px;
  overflow-y: auto;
`;

const ReportCard = styled.div`
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  background: #f8f9fa;
  
  &:hover {
    background: #e9ecef;
    cursor: pointer;
  }
`;

const ReportHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
`;

const ReportTitle = styled.h4`
  margin: 0;
  color: var(--dark);
  font-size: 1rem;
`;

const ReportDate = styled.span`
  font-size: 0.8rem;
  color: var(--secondary);
`;

const ReportSummary = styled.div`
  font-size: 0.9rem;
  color: var(--secondary);
  margin-bottom: 0.5rem;
`;

const ReportActions = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const ActionButton = styled.button`
  background: none;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
  cursor: pointer;
  
  &:hover {
    background: #e9ecef;
  }
  
  &.danger {
    color: var(--danger);
    border-color: var(--danger);
    
    &:hover {
      background: var(--danger);
      color: white;
    }
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 2rem;
  color: var(--secondary);
  
  p {
    margin: 0 0 1rem 0;
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
  background: #fff;
`;

interface EditingReport {
  id: string;
  newTitle: string;
}

const ProfilePage: React.FC = () => {
  const { loggedIn } = useAuth();
  
  // User data state
  const [userData, setUserData] = useState<UserProfile>({
    name: '',
    email: '',
    age: '',
    gender: '',
  });
  const [userEditMode, setUserEditMode] = useState(false);
  const [userLoading, setUserLoading] = useState(false);
  const [userError, setUserError] = useState<string | null>(null);
  const [userSuccess, setUserSuccess] = useState<string | null>(null);
  
  // Medical reports state
  const [medicalReports, setMedicalReports] = useState<MedicalReport[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [reportsError, setReportsError] = useState<string | null>(null);
  const [editingReport, setEditingReport] = useState<EditingReport | null>(null);
  const [selectedReport, setSelectedReport] = useState<MedicalReport | null>(null);
  
  // Age and gender options
  const ageOptions = ['', 'Under 18', '18-25', '26-35', '36-45', '46-60', '61+'];
  const genderOptions = ['', 'Male', 'Female', 'Prefer not to say'];

  // Fetch user profile data
  const fetchUserProfile = async () => {
    setUserLoading(true);
    setUserError(null);
    try {
      const data = await AuthService.getProfile();
      setUserData({
        name: data.name || '',
        email: data.email || '',
        age: data.age || '',
        gender: data.gender || '',
      });
    } catch (err: any) {
      setUserError('Failed to load profile');
    } finally {
      setUserLoading(false);
    }
  };

  // Fetch medical reports
  const fetchMedicalReports = async () => {
    setReportsLoading(true);
    setReportsError(null);
    try {
      const response = await MedicalReportService.getUserMedicalReports(20, 0);
      setMedicalReports(response.reports);
    } catch (err: any) {
      setReportsError('Failed to load medical reports');
    } finally {
      setReportsLoading(false);
    }
  };

  // Load data on mount
  useEffect(() => {
    if (loggedIn) {
      fetchUserProfile();
      fetchMedicalReports();
    }
  }, [loggedIn]);

  // Handle user profile form changes
  const handleUserChange = (field: keyof UserProfile, value: string) => {
    setUserData(prev => ({ ...prev, [field]: value }));
  };

const handleUserSave = async (e: React.FormEvent) => {
  e.preventDefault();
  
  // Only save if we're actually in edit mode
  if (!userEditMode) {
    console.log('Not in edit mode, ignoring form submission');
    return;
  }
  
  console.log('Saving user profile...');
  setUserLoading(true);
  setUserError(null);
  setUserSuccess(null);
  try {
    const updatedUser = await AuthService.updateProfile({
      ...userData,
      age: userData.age || '',
      gender: userData.gender || '',
    });
    
    console.log('✅ Profile updated:', updatedUser);
    
    setUserData({
      name: updatedUser.name || '',
      email: updatedUser.email || '',
      age: updatedUser.age || '',
      gender: updatedUser.gender || '',
    });
    
    setUserSuccess('Profile updated successfully!');
    setUserEditMode(false);
  } catch (err: any) {
    setUserError(err.message);
  } finally {
    setUserLoading(false);
  }
};

  // Handle report title editing
  const handleReportTitleEdit = (reportId: string, currentTitle: string) => {
    setEditingReport({ id: reportId, newTitle: currentTitle });
  };

  // Save report title
  const handleReportTitleSave = async (reportId: string) => {
    if (!editingReport || editingReport.id !== reportId) return;
    
    try {
      const updatedReport = await MedicalReportService.updateReportTitle(
        reportId,
        editingReport.newTitle
      );
      
      // Update local state
      setMedicalReports(prev => 
        prev.map(report => 
          report.id === reportId 
            ? { ...report, report_title: updatedReport.report_title }
            : report
        )
      );
      
      setEditingReport(null);
    } catch (err: any) {
      setReportsError(`Failed to update report title: ${err.message}`);
    }
  };

  // Delete medical report
  const handleReportDelete = async (reportId: string) => {
    if (!window.confirm('Are you sure you want to delete this medical report?')) {
      return;
    }
    
    try {
      await MedicalReportService.deleteMedicalReport(reportId);
      setMedicalReports(prev => prev.filter(report => report.id !== reportId));
    } catch (err: any) {
      setReportsError(`Failed to delete report: ${err.message}`);
    }
  };

  // View medical report
  const handleReportView = (report: MedicalReport) => {
    setSelectedReport(report);
  };

  // Format date for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!loggedIn) {
    return (
      <>
        <Navbar loggedIn={false} />
        <ProfileWrapper>
          <SectionCard>
            <ErrorText>Please log in to view your profile.</ErrorText>
          </SectionCard>
        </ProfileWrapper>
      </>
    );
  }

  return (
    <>
      <Navbar loggedIn={true} />
      <ProfileWrapper>
        <ProfileHeader>
          <h1>👤 My Profile</h1>
          <p>Manage your account settings and medical history</p>
        </ProfileHeader>

        <ProfileGrid>
          {/* User Profile Section */}
          <SectionCard>
            <SectionHeader>
              <h3>🔧 Account Settings</h3>
            </SectionHeader>
            
            {userError && <ErrorText>{userError}</ErrorText>}
            {userSuccess && <SuccessText>{userSuccess}</SuccessText>}
            
            {userLoading ? (
              <LoadingSpinner message="Loading profile..." />
            ) : (
              <div>
                <form onSubmit={handleUserSave}>
                  <FieldGroup>
                    <Label htmlFor="name">Username</Label>
                    <Input
                      id="name"
                      type="text"
                      value={userData.name}
                      onChange={val => handleUserChange('name', val)}
                      disabled={!userEditMode || userLoading}
                    />
                  </FieldGroup>
                  
                  <FieldGroup>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={userData.email}
                      onChange={val => handleUserChange('email', val)}
                      disabled={!userEditMode || userLoading}
                    />
                  </FieldGroup>
                  
                  <FieldGroup>
                    <Label htmlFor="age">Age Group</Label>
                    <Select
                      id="age"
                      value={userData.age}
                      onChange={e => handleUserChange('age', e.target.value)}
                      disabled={!userEditMode || userLoading}
                    >
                      {ageOptions.map(option => (
                        <option key={option} value={option}>
                          {option || 'Select age group'}
                        </option>
                      ))}
                    </Select>
                  </FieldGroup>
                  
                  <FieldGroup>
                    <Label htmlFor="gender">Gender</Label>
                    <Select
                      id="gender"
                      value={userData.gender}
                      onChange={e => handleUserChange('gender', e.target.value)}
                      disabled={!userEditMode || userLoading}
                    >
                      {genderOptions.map(option => (
                        <option key={option} value={option}>
                          {option || 'Select gender'}
                        </option>
                      ))}
                    </Select>
                  </FieldGroup>
                  
                  {/* ONLY show Save/Cancel buttons when in edit mode */}
                  {userEditMode && (
                    <div style={{ display: 'flex', gap: '1rem' }}>
                      <Button
                        type="submit"
                        variant="primary"
                        disabled={userLoading}
                        style={{ flex: 1 }}
                      >
                        {userLoading ? 'Saving...' : '💾 Save Changes'}
                      </Button>
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => {
                          console.log('Cancel button clicked');
                          setUserEditMode(false);
                          setUserError(null);
                          setUserSuccess(null);
                          fetchUserProfile(); // Reset to original data
                        }}
                        style={{ flex: 1 }}
                      >
                        ❌ Cancel
                      </Button>
                    </div>
                  )}
                </form>
                
                {!userEditMode && (
                  <div style={{ marginTop: '1rem' }}>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => {
                        console.log('Edit button clicked');
                        setUserError(null);
                        setUserSuccess(null);
                        setUserEditMode(true);
                      }}
                      style={{ width: '100%' }}
                    >
                      ✏️ Edit Profile
                    </Button>
                  </div>
                )}
              </div>
            )}
          </SectionCard>

          {/* Medical Reports Section */}
          <SectionCard>
            <SectionHeader>
              <h3>📋 Medical Reports</h3>
              <Button
                variant="secondary"
                size="sm"
                onClick={fetchMedicalReports}
                disabled={reportsLoading}
              >
                🔄 Refresh
              </Button>
            </SectionHeader>
            
            {reportsError && <ErrorText>{reportsError}</ErrorText>}
            
            {reportsLoading ? (
              <LoadingSpinner message="Loading medical reports..." />
            ) : (
              <ReportsContainer>
                {medicalReports.length === 0 ? (
                  <EmptyState>
                    <p>📋 No medical reports found</p>
                    <p>Complete a diagnosis to see your reports here</p>
                    <Button 
                      variant="primary" 
                      size="sm"
                      onClick={() => window.location.href = '/diagnosis'}
                    >
                      🚀 Start New Diagnosis
                    </Button>
                  </EmptyState>
                ) : (
                  medicalReports.map((report) => (
                    <ReportCard key={report.id}>
                      <ReportHeader>
                        <div style={{ flex: 1 }}>
                          {editingReport?.id === report.id ? (
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                              <Input
                                type="text"
                                value={editingReport.newTitle}
                                onChange={(value) => setEditingReport(prev => 
                                  prev ? { ...prev, newTitle: value } : null
                                )}
                                style={{ fontSize: '1rem', padding: '0.25rem 0.5rem' }}
                              />
                              <ActionButton onClick={() => handleReportTitleSave(report.id)}>
                                ✅
                              </ActionButton>
                              <ActionButton onClick={() => setEditingReport(null)}>
                                ❌
                              </ActionButton>
                            </div>
                          ) : (
                            <ReportTitle>{report.report_title}</ReportTitle>
                          )}
                        </div>
                        <ReportDate>
                          {formatDate(report.created_at)}
                        </ReportDate>
                      </ReportHeader>
                      
                      <ReportSummary>
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
                        {report.patient_symptoms && (
                          <div>
                            <strong>Symptoms:</strong> {report.patient_symptoms.substring(0, 100)}
                            {report.patient_symptoms.length > 100 && '...'}
                          </div>
                        )}
                      </ReportSummary>
                      
                      <ReportActions>
                        <ActionButton onClick={() => handleReportView(report)}>
                          👁️ View
                        </ActionButton>
                        <ActionButton 
                          onClick={() => handleReportTitleEdit(report.id, report.report_title)}
                        >
                          ✏️ Edit Title
                        </ActionButton>
                        <ActionButton 
                          className="danger"
                          onClick={() => handleReportDelete(report.id)}
                        >
                          🗑️ Delete
                        </ActionButton>
                      </ReportActions>
                    </ReportCard>
                  ))
                )}
              </ReportsContainer>
            )}
          </SectionCard>
        </ProfileGrid>
      </ProfileWrapper>
      
      {/* Medical Report Modal */}
      {selectedReport && (
        <MedicalReportModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </>
  );
};

export default ProfilePage;