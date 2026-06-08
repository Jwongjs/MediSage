import React from 'react';
import { AgentState } from 'types/medical';

interface RecommendationsPageProps {
  workflowState: AgentState | null;
  loading: boolean;
  onReset: () => void;
}

export const RecommendationsPage: React.FC<RecommendationsPageProps> = ({
  workflowState,
  loading,
  onReset
}) => {
  const recommendations = workflowState?.healthcare_recommendation;
  const currentStage = workflowState?.current_workflow_stage || '';

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{
        background: 'white',
        padding: 'var(--spacing-lg)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-md)',
        marginBottom: 'var(--spacing-lg)',
        textAlign: 'center'
      }}>
        <h1 style={{ 
          color: 'var(--primary)', 
          marginBottom: 'var(--spacing-sm)',
          fontSize: '2rem'
        }}>
          🏥 Healthcare Recommendations
        </h1>
        <p style={{ color: 'var(--secondary)', margin: 0 }}>
          Personalized healthcare guidance based on your diagnosis
        </p>
        
        <div style={{
          background: '#e3f2fd',
          padding: 'var(--spacing-sm)',
          borderRadius: 'var(--radius-sm)',
          marginTop: 'var(--spacing-md)',
          fontSize: '14px',
          color: 'var(--primary)'
        }}>
          <strong>Current Stage:</strong> {currentStage.replace('_', ' ')}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div style={{
          background: 'white',
          padding: 'var(--spacing-xl)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-md)',
          textAlign: 'center'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '4px solid #f3f3f3',
            borderTop: '4px solid var(--primary)',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto var(--spacing-md) auto'
          }} />
          <p>🔍 Generating healthcare recommendations...</p>
        </div>
      )}

      {/* Recommendations Content */}
      {recommendations && (
        <div style={{
          background: 'white',
          padding: 'var(--spacing-lg)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-md)',
          marginBottom: 'var(--spacing-lg)'
        }}>
          {/* Recommendation Type */}
          <div style={{
            background: '#f0f8ff',
            border: '2px solid var(--primary)',
            borderRadius: 'var(--radius-lg)',
            padding: 'var(--spacing-lg)',
            marginBottom: 'var(--spacing-lg)'
          }}>
            <h2 style={{ 
              margin: '0 0 var(--spacing-md) 0',
              color: 'var(--primary)',
              fontSize: '1.5rem'
            }}>
              📋 Recommendation Type
            </h2>
            <p style={{ 
              margin: 0,
              fontSize: '1.1rem',
              fontWeight: '600',
              textTransform: 'capitalize'
            }}>
              {recommendations.recommendation_type.replace('_', ' ')}
            </p>
          </div>

          {/* Self-Care Advice */}
          {recommendations.self_care_advice && recommendations.self_care_advice.length > 0 && (
            <div style={{
              background: '#f8f9fa',
              border: '1px solid #e9ecef',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--spacing-lg)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              <h3 style={{ 
                margin: '0 0 var(--spacing-md) 0',
                color: 'var(--dark)',
                fontSize: '1.3rem'
              }}>
                🏠 Self-Care Recommendations
              </h3>
              <ul style={{ 
                margin: 0,
                paddingLeft: 'var(--spacing-lg)',
                lineHeight: '1.6'
              }}>
                {recommendations.self_care_advice.map((advice, index) => (
                  <li key={index} style={{ 
                    marginBottom: 'var(--spacing-sm)',
                    fontSize: '16px'
                  }}>
                    {advice}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Specialist Information */}
          {recommendations.specialist_type && (
            <div style={{
              background: '#fff3cd',
              border: '1px solid #ffeaa7',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--spacing-lg)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              <h3 style={{ 
                margin: '0 0 var(--spacing-md) 0',
                color: '#856404',
                fontSize: '1.3rem'
              }}>
                👨‍⚕️ Specialist Recommendation
              </h3>
              <p style={{ 
                margin: '0 0 var(--spacing-sm) 0',
                fontSize: '1.1rem',
                fontWeight: '600',
                textTransform: 'capitalize'
              }}>
                {recommendations.specialist_type.replace('_', ' ')}
              </p>
              {recommendations.appointment_urgency && (
                <p style={{ 
                  margin: 0,
                  fontSize: '14px',
                  color: '#856404'
                }}>
                  <strong>Urgency:</strong> {recommendations.appointment_urgency.replace('_', ' ')}
                </p>
              )}
            </div>
          )}

          {/* Nearby Facilities */}
          {recommendations.nearby_facilities && recommendations.nearby_facilities.length > 0 && (
            <div style={{
              background: '#d1ecf1',
              border: '1px solid #bee5eb',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--spacing-lg)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              <h3 style={{ 
                margin: '0 0 var(--spacing-md) 0',
                color: '#0c5460',
                fontSize: '1.3rem'
              }}>
                🗺️ Nearby Medical Facilities
              </h3>
              {recommendations.facility_search_radius && (
                <p style={{ 
                  margin: '0 0 var(--spacing-md) 0',
                  fontSize: '14px',
                  color: '#0c5460'
                }}>
                  <strong>Search Radius:</strong> {recommendations.facility_search_radius}
                </p>
              )}
              <div style={{ display: 'grid', gap: 'var(--spacing-sm)' }}>
                {recommendations.nearby_facilities.slice(0, 5).map((facility, index) => (
                  <div key={index} style={{
                    background: 'white',
                    padding: 'var(--spacing-md)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid #bee5eb'
                  }}>
                    <p style={{ margin: 0, fontWeight: '600' }}>
                      {facility.name || `Medical Facility ${index + 1}`}
                    </p>
                    {facility.address && (
                      <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: 'var(--secondary)' }}>
                        📍 {facility.address}
                      </p>
                    )}
                    {facility.rating && (
                      <p style={{ margin: '4px 0 0 0', fontSize: '14px' }}>
                        ⭐ {facility.rating}/5
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Emergency Contacts */}
          {recommendations.emergency_contacts && recommendations.emergency_contacts.length > 0 && (
            <div style={{
              background: '#f8d7da',
              border: '1px solid #f5c6cb',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--spacing-lg)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              <h3 style={{ 
                margin: '0 0 var(--spacing-md) 0',
                color: '#721c24',
                fontSize: '1.3rem'
              }}>
                🚨 Emergency Contacts
              </h3>
              <div style={{ display: 'grid', gap: 'var(--spacing-sm)' }}>
                {recommendations.emergency_contacts.map((contact, index) => (
                  <div key={index} style={{
                    background: 'white',
                    padding: 'var(--spacing-sm)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid #f5c6cb'
                  }}>
                    <strong>{contact.type || 'Emergency'}:</strong> {contact.number || contact.info}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Insurance Guidance */}
          {recommendations.insurance_guidance && recommendations.insurance_guidance.length > 0 && (
            <div style={{
              background: '#d4edda',
              border: '1px solid #c3e6cb',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--spacing-lg)',
              marginBottom: 'var(--spacing-lg)'
            }}>
              <h3 style={{ 
                margin: '0 0 var(--spacing-md) 0',
                color: '#155724',
                fontSize: '1.3rem'
              }}>
                💰 Insurance & Cost Information
              </h3>
              <ul style={{ 
                margin: 0,
                paddingLeft: 'var(--spacing-lg)',
                lineHeight: '1.6'
              }}>
                {recommendations.insurance_guidance.map((guidance, index) => (
                  <li key={index} style={{ 
                    marginBottom: 'var(--spacing-sm)',
                    fontSize: '14px'
                  }}>
                    {guidance}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* No Recommendations Yet */}
      {!recommendations && !loading && (
        <div style={{
          background: 'white',
          padding: 'var(--spacing-xl)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-md)',
          textAlign: 'center'
        }}>
          <p>⏳ Recommendations will appear here once the analysis is complete.</p>
        </div>
      )}

      {/* Action Button */}
      <div style={{ textAlign: 'center' }}>
        <button
          onClick={onReset}
          style={{
            padding: 'var(--spacing-md) var(--spacing-lg)',
            background: 'var(--secondary)',
            color: 'white',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            fontSize: '16px',
            cursor: 'pointer'
          }}
        >
          🔄 Start Over
        </button>
      </div>
    </div>
  );
};