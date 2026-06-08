import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import { useAuth } from 'contexts/AuthContext';

const ProfileWrapper = styled.div`
  position: relative;
  display: flex;
  align-items: center;
`;

const ProfileButton = styled.button`
  background: #f3f3f3;
  border: none;
  border-radius: 50%;
  width: 2.5rem;
  height: 2.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-left: 2rem;
  transition: background 0.2s;
  &:hover {
    background: #e0e0e0;
  }
`;

const Dropdown = styled.div`
  position: absolute;
  top: 3.2rem;
  right: 0;
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 0.5rem;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  min-width: 140px;
  z-index: 100;
  padding: 0.5rem 0;
`;

const DropdownItem = styled.button`
  width: 100%;
  background: none;
  border: none;
  text-align: left;
  padding: 0.75rem 1.25rem;
  font-size: 1rem;
  color: #212529;
  cursor: pointer;
  &:hover {
    background: #f3f3f3;
  }
`;

const LoginButton = styled.button`
  background: #007bff;
  color: #fff;
  border: none;
  border-radius: 1.2rem;
  padding: 0.6rem 1.5rem;
  font-size: 1rem;
  font-weight: bold;
  margin-left: 2rem;
  cursor: pointer;
  transition: background 0.2s;
  &:hover {
    background: #0056b3;
  }
`;

interface ProfileDropdownProps {
  loggedIn: boolean;
}

const ProfileDropdown: React.FC<ProfileDropdownProps> = ({ loggedIn }) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { logout } = useAuth();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownOpen]);

  if (!loggedIn) {
    return (
      <LoginButton onClick={() => navigate('/login')}>
        Login
      </LoginButton>
    );
  }

  return (
    <ProfileWrapper ref={profileRef}>
      <ProfileButton onClick={() => setDropdownOpen((prev) => !prev)} title="Profile">
        <span role="img" aria-label="profile">👤</span>
      </ProfileButton>
      {dropdownOpen && (
        <Dropdown>
          <DropdownItem onClick={() => { setDropdownOpen(false); navigate('/profile'); }}>
            Profile
          </DropdownItem>
          <DropdownItem onClick={async () => { 
            setDropdownOpen(false); 
            await logout();
            navigate('/');
          }}>
            Logout
          </DropdownItem>
        </Dropdown>
      )}
    </ProfileWrapper>
  );
};

export default ProfileDropdown;