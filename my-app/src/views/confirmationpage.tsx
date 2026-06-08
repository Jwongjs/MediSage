import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AuthService } from 'services/auth';
import { useAuth } from 'contexts/AuthContext';
import { LoadingSpinner } from 'components/common/LoadingSpinner';

const ConfirmationPending: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();

  const registrationData = location.state?.registrationData;

  useEffect(() => {
    if (!registrationData) {
      navigate('/register');
      return;
    }

    // Auto-register when page loads
    processRegistration();
  }, [registrationData, navigate]);

  const processRegistration = async () => {
    if (!registrationData) return;

    setLoading(true);
    setError(null);

    try {
      console.log('Starting registration process...');
      const response = await AuthService.register(registrationData);
      console.log('Registration response:', response);

      if (response.email_confirmation_required) {
        setSuccess('Registration successful! Please check your email to confirm your account, then try logging in.');
      } else {
        // Registration complete without email confirmation
        await login(); // Update auth context
        navigate('/');
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      setError(error.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  if (!registrationData) {
    return <div>Redirecting...</div>;
  }

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      minHeight: '100vh',
      padding: '2rem'
    }}>
      <div style={{
        maxWidth: '500px',
        width: '100%',
        textAlign: 'center',
        background: '#fff',
        padding: '2rem',
        borderRadius: '8px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.1)'
      }}>
        {loading && (
          <>
            <LoadingSpinner size="lg" />
            <h2 style={{ margin: '1rem 0', color: '#007bff' }}>
              Creating your account...
            </h2>
            <p style={{ color: '#666' }}>
              Please wait while we set up your medical profile.
            </p>
          </>
        )}

        {error && (
          <>
            <h2 style={{ color: '#dc3545' }}>Registration Failed</h2>
            <p style={{ color: '#dc3545', marginBottom: '1.5rem' }}>{error}</p>
            <button
              onClick={() => navigate('/register')}
              style={{
                padding: '0.75rem 1.5rem',
                background: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '1rem'
              }}
            >
              Try Again
            </button>
          </>
        )}

        {success && (
          <>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✅</div>
            <h2 style={{ color: '#28a745' }}>Almost There!</h2>
            <p style={{ color: '#666', marginBottom: '1.5rem' }}>{success}</p>
            <button
              onClick={() => navigate('/login')}
              style={{
                padding: '0.75rem 1.5rem',
                background: '#28a745',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '1rem'
              }}
            >
              Go to Login
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default ConfirmationPending;