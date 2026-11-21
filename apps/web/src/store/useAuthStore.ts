import { create } from 'zustand';
import { User } from '@thinkfree/shared';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: {
    id: 'student-alex-demo',
    name: 'Alex Chen (Demo Student)',
    email: 'alex.demo@thinkfree.demo',
    role: 'student',
    locale: 'en',
    created_at: new Date().toISOString(),
    consent_flags: {
      audio_retention: true,
      analytics_sharing: true,
      professor_sharing: true,
    },
  },
  isAuthenticated: true,
  isLoading: false,
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));
