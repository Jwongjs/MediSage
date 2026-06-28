import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { AuthService } from 'services/auth';
import { UserProfile } from 'types/auth';
import { Loader2 } from 'lucide-react';

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
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
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