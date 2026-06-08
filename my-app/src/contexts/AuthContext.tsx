import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { AuthService } from 'services/auth';
import { UserProfile } from 'types/auth';
import { LoadingSpinner } from 'components/common/LoadingSpinner';

interface AuthContextType {
  loggedIn: boolean;
  user: UserProfile | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [loggedIn, setLoggedIn] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuthStatus = async () => {
    try {
      setLoading(true);

      // Debug: Check if cookies exist
      console.log("🍪Document cookies:", document.cookie);

      const userData = await AuthService.getProfile();
      console.log("✅ Auth check: User is logged in", userData);
      setUser(userData);
      setLoggedIn(true);
    } catch (error) {
      console.log("❌ Auth check: User is not logged in");
      setUser(null);
      setLoggedIn(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const login = async () => {
    await checkAuthStatus();
  };

  const logout = async () => {
    try {
      await AuthService.logout();
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      setUser(null);
      setLoggedIn(false);
    }
  };

  const value = { loggedIn, user, login, logout };

  if (loading) {
    return <LoadingSpinner message="Checking session..." />;
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};