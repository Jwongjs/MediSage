import {
  UserProfile,
  AuthResponse,
  RegisterData,
  LoginData,
  UserUpdate
} from '../types/auth';

const API_BASE_URL = 'http://localhost:8000';

export class AuthService {
  static async register(userData: RegisterData): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/patient/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
      }

      const data: AuthResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }

  static async login(credentials: LoginData): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/patient/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data: AuthResponse = await response.json();
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  static async logout(): Promise<{ message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/patient/logout`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Logout failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  }

  static async getProfile(): Promise<UserProfile> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/patient/profile`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to get profile');
      }

      return await response.json();
    } catch (error) {
      console.error('Get profile error:', error);
      throw error;
    }
  }

  static async updateProfile(userData: UserUpdate): Promise<UserProfile> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/patient/update_profile`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Update profile failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Update profile error:', error);
      throw error;
    }
  }
}