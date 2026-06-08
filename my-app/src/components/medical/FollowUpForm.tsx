import React, { useState, useEffect } from 'react';
import { Button } from 'components/common/Button';
import { Card } from 'components/common/Card';

interface FollowUpFormProps {
  questions: string[];
  onSubmit: (responses: Record<string, string>) => void;
  loading?: boolean;
  followupType?: 'standard' | 'skin_cancer_screening';
}

export const FollowUpForm: React.FC<FollowUpFormProps> = ({
  questions,
  onSubmit,
  loading = false,
  followupType = 'standard'
}) => {
  const [responses, setResponses] = useState<Record<string, string>>({});

  //Reset responses when questions change (page reload/transition)
  useEffect(() => {
    console.log('🔄 Questions changed, resetting responses');
    setResponses({});
  }, [questions, followupType]); // Reset when questions or type changes

  const handleResponseChange = (questionIndex: number, response: string) => {
    const question = questions[questionIndex];
    setResponses(prev => ({
      ...prev,
      [question]: response
    }));
  };

  //to handle unanswered questions on top of the onSubmitResponses logic all the way back to useDiagnosis
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate all questions are answered
    const unansweredQuestions = questions.filter((question, index) => 
      !responses[question] || responses[question].trim() === ''
    );
    
    if (unansweredQuestions.length > 0) {
      alert(`Please answer all questions. ${unansweredQuestions.length} question(s) remaining.`);
      return;
    }
    
    onSubmit(responses);
  };

  // Check if question is skin cancer screening (closed-ended)
  const isSkinCancerQuestion = (question: string) => {
    return followupType === 'skin_cancer_screening' || 
           question.toLowerCase().includes('asymmetric') ||
           question.toLowerCase().includes('border') ||
           question.toLowerCase().includes('color') ||
           question.toLowerCase().includes('diameter') ||
           question.toLowerCase().includes('changed') ||
           question.toLowerCase().includes('bleed') ||
           question.toLowerCase().includes('history');
  };

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ marginBottom: 'var(--spacing-lg)' }}>
        {questions.map((question, index) => {
          const currentResponse = responses[question] || '';
          const isSkinScreening = isSkinCancerQuestion(question);
          
          return (
            <Card key={index} style={{ 
              marginBottom: 'var(--spacing-md)',
              border: currentResponse ? '2px solid var(--success)' : '1px solid #e9ecef'
            }}>
              <div style={{ marginBottom: 'var(--spacing-sm)' }}>
                <label style={{
                  display: 'block',
                  fontWeight: '600',
                  color: 'var(--dark)',
                  fontSize: '16px',
                  lineHeight: '1.4'
                }}>
                  {index + 1}. {question}
                </label>
              </div>

              {/* Skin Cancer Screening Questions and Radio Buttons*/}
              {isSkinScreening ? (
                <div style={{ 
                  display: 'flex', 
                  gap: 'var(--spacing-md)', 
                  flexWrap: 'wrap',
                  justifyContent: 'center',
                  padding: 'var(--spacing-sm) 0'
                }}>
                  {/* Yes Option */}
                  <label style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '6px', 
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    <input
                      type="radio"
                      name={`question_${followupType}_${index}`}
                      value="yes"
                      checked={currentResponse === 'yes'}
                      onChange={(e) => handleResponseChange(index, e.target.value)}
                      style={{ 
                        marginRight: '4px',
                        transform: 'scale(1.1)'
                      }}
                    />
                    <span style={{ 
                      color: currentResponse === 'yes' ? 'var(--danger)' : 'var(--dark)',
                      fontWeight: currentResponse === 'yes' ? '600' : '500'
                    }}>
                      Yes
                    </span>
                  </label>

                  {/* Neutral/Unsure Option */}
                  <label style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '6px', 
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    <input
                      type="radio"
                      name={`question_${followupType}_${index}`}
                      value="neutral"
                      checked={currentResponse === 'neutral'}
                      onChange={(e) => handleResponseChange(index, e.target.value)}
                      style={{ 
                        marginRight: '4px',
                        transform: 'scale(1.1)'
                      }}
                    />
                    <span style={{ 
                      color: currentResponse === 'neutral' ? 'var(--warning)' : 'var(--dark)',
                      fontWeight: currentResponse === 'neutral' ? '600' : '500'
                    }}>
                      Unsure/Neutral                    
                    </span>
                  </label>

                  {/* No Option */}
                  <label style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '6px', 
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    <input
                      type="radio"
                      name={`question_${followupType}_${index}`}
                      value="no"
                      checked={currentResponse === 'no'}
                      onChange={(e) => handleResponseChange(index, e.target.value)}
                      style={{ 
                        marginRight: '4px',
                        transform: 'scale(1.1)'
                      }}
                    />
                    <span style={{ 
                      color: currentResponse === 'no' ? 'var(--success)' : 'var(--dark)',
                      fontWeight: currentResponse === 'no' ? '600' : '500'
                    }}>
                      No
                    </span>
                  </label>
                </div>
              ) : (
                /* Standard Questions - Text Area */
                <textarea
                  value={currentResponse}
                  onChange={(e) => handleResponseChange(index, e.target.value)}
                  placeholder="Please provide your answer..."
                  disabled={loading}
                  style={{
                    width: '100%',
                    minHeight: '80px',
                    padding: 'var(--spacing-sm)',
                    border: '1px solid #e9ecef',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '14px',
                    resize: 'vertical',
                    fontFamily: 'inherit'
                  }}
                />
              )}

              {/* Question Progress Indicator */}
              {currentResponse && (
                <div style={{ 
                  marginTop: 'var(--spacing-xs)',
                  fontSize: '12px',
                  color: 'var(--success)',
                  fontWeight: '500'
                }}>
                  ✓ Answered
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Form Progress */}
      <Card style={{ marginBottom: 'var(--spacing-lg)', background: '#f8f9fa' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          fontSize: '14px'
        }}>
          <span style={{ color: 'var(--secondary)' }}>
            Progress: {Object.keys(responses).length} of {questions.length} questions answered
          </span>
          <div style={{
            width: '100px',
            height: '6px',
            background: '#e9ecef',
            borderRadius: '3px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${questions.length > 0 ? (Object.keys(responses).length / questions.length) * 100 : 0}%`,
              height: '100%',
              background: Object.keys(responses).length === questions.length ? 'var(--success)' : 'var(--primary)',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>
      </Card>

      {/* Skin Cancer Screening Info */}
      {followupType === 'skin_cancer_screening' && (
        <Card variant="primary" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <h5 style={{ margin: '0 0 var(--spacing-sm) 0', color: 'var(--primary)' }}>
            📋 Screening Guide
          </h5>
          <div style={{ fontSize: '14px', color: 'var(--dark)' }}>
            <p style={{ margin: '0 0 var(--spacing-sm) 0' }}>
              <strong>Response Guide:</strong>
            </p>
            <ul style={{ margin: 0, paddingLeft: 'var(--spacing-lg)' }}>
              <li><strong>Yes:</strong> The characteristic is clearly present</li>
              <li><strong>Unsure/Neutral:</strong> You're not certain or the characteristic is somewhat present</li>
              <li><strong>No:</strong> The characteristic is definitely not present</li>
            </ul>
          </div>
        </Card>
      )}

      {/* Submit Button */}
      <div style={{ textAlign: 'center' }}>
        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={loading}
          disabled={Object.keys(responses).length !== questions.length}
          style={{ minWidth: '200px' }}
        >
          {followupType === 'skin_cancer_screening' ? 
            '🔍 Complete Screening Assessment' : 
            '📊 Submit Follow-Up Responses' 
          }
        </Button>
      </div>
    </form>
  );
};