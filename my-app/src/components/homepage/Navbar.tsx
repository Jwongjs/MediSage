import React from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import ProfileDropdown from './ProfileDropdown';

const NavbarContainer = styled.nav`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 3rem;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border-bottom: 2px solid rgba(0,0,0,0.07);
`;

const Logo = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: #007bff;
  cursor: pointer;
`;

const NavTabs = styled.div`
  display: flex;
  gap: 2rem;
`;

const NavTab = styled.button`
  background: none;
  border: none;
  font-size: 1rem;
  color: #212529;
  font-weight: bold;
  cursor: pointer;
  padding: 0.5rem 1rem;
  &:hover {
    color: #007bff;
  }
`;

interface NavbarProps {
  loggedIn: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ loggedIn }) => {
  const navigate = useNavigate();
  return (
    <NavbarContainer>
      <Logo onClick={() => navigate('/')}>🏥 MediSage</Logo>
      {/* <NavTabs>
        <NavTab onClick={() => navigate('/chatbot')}>Chatbot</NavTab>
        <NavTab onClick={() => navigate('/medical-report')}>Medical Report</NavTab>
      </NavTabs> */}
      <ProfileDropdown loggedIn={loggedIn} />
    </NavbarContainer>
  );
};

export default Navbar;