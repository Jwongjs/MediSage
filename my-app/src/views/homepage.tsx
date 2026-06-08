import React from 'react';
import { Helmet } from 'react-helmet';
import { useNavigate } from 'react-router-dom';
import styled, { createGlobalStyle } from 'styled-components';

import Hero from 'pages/homepage/Hero';

import BasicSection from 'components/homepage/BasicSection';
import Button from 'components/homepage/Button';
import ButtonGroup from 'components/homepage/ButtonGroup';
import ProfileDropdown from 'components/homepage/ProfileDropdown';
import Navbar from 'components/homepage/Navbar';
import { useAuth } from 'contexts/AuthContext';

const WhiteBackgroundContainer = styled.div`
  background: #fff;
`;

const CustomButtonGroup = styled(ButtonGroup)`
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 4rem;
  button {
    font-size: 1.4rem;
    padding: 1.2rem 3rem;
    border-radius: 2rem;
    box-shadow: 0 8px 32px rgba(0, 123, 255, 0.25), 0 1.5px 6px rgba(0,0,0,0.08);
    transition: transform 0.2s, box-shadow 0.2s;
    background: linear-gradient(90deg, #007bff 0%, #00c6ff 100%);
    color: #fff;
    font-weight: bold;
    letter-spacing: 0.05em;
    border: none;
  }
  button:hover {
    transform: scale(1.08);
    box-shadow: 0 12px 40px rgba(0, 123, 255, 0.35), 0 2px 8px rgba(0,0,0,0.12);
    background: linear-gradient(90deg, #0056b3 0%, #00c6ff 100%);
  }
`;

const HomepageWrapper = styled.div`
  & > :last-child {
    margin-bottom: 15rem;
  }
`;

const Homepage: React.FC = () => {
  const { loggedIn } = useAuth();
  const navigate = useNavigate();

  const handleChatbotClick = () => {
    // For now, it will navigate to a placeholder or show an alert
    // This will be updated when implemented the chatbot page
    alert('🤖 Chatbot feature coming soon!\n\nThis will provide interactive medical assistance and answer your health questions.');
    
    // navigate('/chatbot');
  };

  return (
    <>
      <Helmet>
        <title>MediSage</title>
        <meta name="description" content="Welcome to our smart diagnosis system." />
      </Helmet>
      <Navbar loggedIn={loggedIn} />
      <WhiteBackgroundContainer>
        <Hero />
        <CustomButtonGroup>
          <Button onClick={() => navigate('/diagnosis')} style={{ marginTop: 0 }}>
            🩺 Start Diagnosis <span>&rarr;</span>
          </Button>
          <Button 
            onClick={handleChatbotClick}
            className="secondary-button"
            style={{ marginTop: 0 }}
          >
            🤖 Medical Chatbot <span>&rarr;</span>
          </Button>
        </CustomButtonGroup>
      </WhiteBackgroundContainer>
    </>
  );
};

export default Homepage;