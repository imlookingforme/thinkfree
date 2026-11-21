import { create } from 'zustand';
import { User } from '@thinkfree/shared';
import { apiClient } from '../api/client';

export type AuthModalMode = 'login' | 'register' | 'forgot_password';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  authModalMode: AuthModalMode;
  
  openAuthModal: (mode?: AuthModalMode) => void;
  closeAuthModal: () => void;
  setAuthModalMode: (mode: AuthModalMode) => void;

  checkAuth: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  googleLogin: (payload: { credential?: string; email?: string; name?: string }) => Promise<void>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<string>;
  resetPassword: (token: string, newPassword: string) => Promise<string>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  isAuthModalOpen: false,
  authModalMode: 'login',

  openAuthModal: (mode: AuthModalMode = 'login') =>
    set({ isAuthModalOpen: true, authModalMode: mode }),

  closeAuthModal: () => set({ isAuthModalOpen: false }),

  setAuthModalMode: (mode: AuthModalMode) => set({ authModalMode: mode }),

  checkAuth: async () => {
    try {
      set({ isLoading: true });
      const res = await apiClient.get('/auth/me');
      set({ user: res.data, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  login: async (email: string, password: string) => {
    const res = await apiClient.post('/auth/login', { email, password });
    set({
      user: res.data.user,
      isAuthenticated: true,
      isAuthModalOpen: false,
    });
  },

  register: async (name: string, email: string, password: string) => {
    const res = await apiClient.post('/auth/register', {
      name,
      email,
      password,
      role: 'student',
      locale: 'en',
    });
    set({
      user: res.data.user,
      isAuthenticated: true,
      isAuthModalOpen: false,
    });
  },

  googleLogin: async (payload: { credential?: string; email?: string; name?: string }) => {
    const res = await apiClient.post('/auth/google', payload);
    set({
      user: res.data.user,
      isAuthenticated: true,
      isAuthModalOpen: false,
    });
  },

  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      set({ user: null, isAuthenticated: false });
    }
  },

  forgotPassword: async (email: string) => {
    const res = await apiClient.post('/auth/forgot-password', { email });
    return res.data.message || 'Password reset link sent to your email.';
  },

  resetPassword: async (token: string, newPassword: string) => {
    const res = await apiClient.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
    return res.data.message || 'Password reset successfully.';
  },
}));
