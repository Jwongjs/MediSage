export interface UserProfile {
  id?: string;
  name: string;
  email: string;
  age: string;
  gender: string;
}

export interface AuthResponse {
  message: string;
  user: UserProfile;
  email_confirmation_required?: boolean;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  age: string;
  gender: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface UserUpdate {
  name?: string;
  email?: string;
  age?: string;
  gender?: string;
}