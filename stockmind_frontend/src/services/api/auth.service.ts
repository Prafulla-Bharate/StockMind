import { api } from './axios';
import type { ApiResponse, LoginRequest, RegisterRequest, AuthResponse, UserProfile } from './types';

export const authService = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await api.post<ApiResponse<AuthResponse>>('/auth/login', data);
    const { token, user } = response.data.data;
    localStorage.setItem('token', token);
    return { token, user };
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    // Include both `fullName` and `name` to satisfy different backend expectations
    const payload: Record<string, any> = {
      email: data.email,
      password: data.password,
      fullName: (data as any).fullName,
      name: (data as any).fullName,
    };

    try {
      const response = await api.post<ApiResponse<AuthResponse>>('/auth/register', payload);
      const { token, user } = response.data.data;
      localStorage.setItem('token', token);
      return { token, user };
    } catch (error: any) {
      // Normalize backend validation errors into a readable message
      const resp = error.response?.data;
      if (resp && (resp.errors || resp.message)) {
        const parts: string[] = [];
        if (resp.message) parts.push(resp.message);
        if (resp.errors && typeof resp.errors === 'object') {
          for (const [key, val] of Object.entries(resp.errors)) {
            if (Array.isArray(val)) parts.push(`${key}: ${val.join(', ')}`);
            else parts.push(`${key}: ${String(val)}`);
          }
        }

        const combined = parts.join(' | ').toLowerCase();
        // Detect common duplicate / unique-constraint messages and return a friendly message
        if (combined.includes('duplicate key') || combined.includes('already exists') || combined.includes('user with this email')) {
          throw new Error('An account with this email already exists. Try signing in or use password reset.');
        }

        throw new Error(parts.join(' | '));
      }
      throw error;
    }
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout');
    localStorage.removeItem('token');
  },

  async getProfile(): Promise<UserProfile> {
    const response = await api.get<ApiResponse<UserProfile>>('/auth/profile');
    return response.data.data;
  },

  async updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    const response = await api.patch<ApiResponse<UserProfile>>('/auth/profile', data);
    return response.data.data;
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
  }
};