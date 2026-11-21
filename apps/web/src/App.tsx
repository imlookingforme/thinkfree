import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { ProblemAttemptPage } from './pages/ProblemAttemptPage';
import { GuidedModePage } from './pages/GuidedModePage';
import { ValidationPage } from './pages/ValidationPage';
import { ProfessorPortalPage } from './pages/ProfessorPortalPage';
import { BadgeVerificationPage } from './pages/BadgeVerificationPage';
import { CollaborationAndPrivacyPage } from './pages/CollaborationAndPrivacyPage';
import { AISettingsPage } from './pages/AISettingsPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { CollaborativeRoomPage } from './pages/CollaborativeRoomPage';
import { AIOnboardingModal } from './components/AIOnboardingModal';
import { AuthModal } from './components/AuthModal';
import { useAuthStore } from './store/useAuthStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AIOnboardingModal />
        <AuthModal />
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="attempt/:id" element={<ProblemAttemptPage />} />
            <Route path="guided/:id" element={<GuidedModePage />} />
            <Route path="validate/:id" element={<ValidationPage />} />
            <Route path="professor" element={<ProfessorPortalPage />} />
            <Route path="collab" element={<CollaborationAndPrivacyPage />} />
            <Route path="verify/:id" element={<BadgeVerificationPage />} />
            <Route path="settings/ai" element={<AISettingsPage />} />
            <Route path="reset-password" element={<ResetPasswordPage />} />
            <Route path="collaborate" element={<CollaborativeRoomPage />} />
            <Route path="collaborate/:code" element={<CollaborativeRoomPage />} />
            <Route path="problems" element={<HomePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};
