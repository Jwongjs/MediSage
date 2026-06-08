import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import styled from 'styled-components';
import Navbar from 'components/homepage/Navbar';
import { Button } from 'components/common/Button';
import { Input } from 'components/common/Input';
import { useAuth } from 'contexts/AuthContext';
import { AuthService } from 'services/auth';


const RegisterPageWrapper = styled.div`
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
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
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

const LoginText = styled.p`
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

const Row = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
`;

const Select = styled.select`
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
  background: #fff;
`;

const Label = styled.label`
  font-weight: 600;
  margin-bottom: 0.5rem;
  display: block;
`;

const ageOptions = [
  '', 'Under 18', '18-25', '26-35', '36-45', '46-60', '61+'
];
const genderOptions = [
  '', 'Male', 'Female', 'Prefer not to say'
];

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [age, setAge] = useState('');        
  const [gender, setGender] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (!name || !email || !password || !age || !gender) {
      setError("All fields are required");
      return;
    }

    setLoading(true);

    // Save form data and navigate to confirmation page
    // This ensures the page transition happens first as requested
    navigate('/confirmation-pending', { 
      state: { 
        registrationData: { name, email, age, gender, password }
      } 
    });
  };

  return (
    <>
      <Navbar loggedIn={false} />
      <RegisterPageWrapper>
        <FormContainer>
          <Title>Register</Title>
          {error && <ErrorText>{error}</ErrorText>}
          <form onSubmit={handleSubmit}>
            <Input
              type="text"
              value={name}
              onChange={setName}
              placeholder="Username"
              disabled={loading}
            />
            <Input
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="Email"
              disabled={loading}
              style={{ marginTop: '1rem' }}
            />
            <Row>
              <div style={{ flex: 1 }}>
                <Label htmlFor="age">Age</Label>
                <Select
                  id="age"
                  value={age}
                  onChange={e => setAge(e.target.value)}
                  disabled={loading}
                >
                  {ageOptions.map(opt => (
                    <option key={opt} value={opt}>{opt || 'Select age'}</option>
                  ))}
                </Select>
              </div>
              <div style={{ flex: 1 }}>
                <Label htmlFor="gender">Gender</Label>
                <Select
                  id="gender"
                  value={gender}
                  onChange={e => setGender(e.target.value)}
                  disabled={loading}
                >
                  {genderOptions.map(opt => (
                    <option key={opt} value={opt}>{opt || 'Select gender'}</option>
                  ))}
                </Select>
              </div>
            </Row>
            <Input
              type="password"
              value={password}
              onChange={setPassword}
              placeholder="Password"
              disabled={loading}
              style={{ marginTop: '1rem' }}
            />
            <Input
              type="password"
              value={confirmPassword}
              onChange={setConfirmPassword}
              placeholder="Confirm Password"
              disabled={loading}
              style={{ marginTop: '1rem' }}
            />
            <Button
              type="submit"
              disabled={loading}
              variant="primary"
              style={{ width: '100%', marginTop: '1.5rem' }}
            >
              {loading ? 'Registering...' : 'Register'}
            </Button>
          </form>
          <LoginText>
            Already have an account? <StyledLink to="/login">Login</StyledLink>
          </LoginText>
        </FormContainer>
      </RegisterPageWrapper>
    </>
  );
};

export default RegisterPage;