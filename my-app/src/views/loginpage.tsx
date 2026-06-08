import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styled from 'styled-components';
import Navbar from 'components/homepage/Navbar';
import { Button } from 'components/common/Button';
import { Input } from 'components/common/Input';
import { useAuth } from 'contexts/AuthContext';
import { AuthService } from 'services/auth';


const LoginPageWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 4rem;
`;

const FormContainer = styled.div`
  max-width: 400px;
  width: 100%;
  margin: 2rem auto;
  padding: 2rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background: #fff;
`;

const Title = styled.h2`
  text-align: center;
  margin-bottom: 1rem;
`;

const ErrorText = styled.p`
  color: red;
  font-size: 0.9rem;
  text-align: center;
`;

const RegisterText = styled.p`
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.9rem;
`;

const StyledLink = styled(Link)`
  color: #007bff;
  text-decoration: none;
  font-weight: bold;
  &:hover {
    text-decoration: underline;
  }
`;

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await AuthService.login({ email, password });
      await login(); // Refresh global auth state from context
      navigate('/');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar loggedIn={false} />
      <LoginPageWrapper>
        <FormContainer>
          <Title>Login</Title>
          {error && <ErrorText>{error}</ErrorText>}
          <form onSubmit={handleSubmit}>
            <Input
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="Email"
              disabled={loading}
            />
            <Input
              type="password"
              value={password}
              onChange={setPassword}
              placeholder="Password"
              disabled={loading}
              style={{ marginTop: '1rem' }}
            />
            <Button
              type="submit"
              disabled={loading}
              variant="primary"
              style={{ width: '100%', marginTop: '1.5rem' }}
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </form>
          <RegisterText>
            Don&apos;t have an account? <StyledLink to="/register">Register</StyledLink>
          </RegisterText>
        </FormContainer>
      </LoginPageWrapper>
    </>
  );
};

export default Login;