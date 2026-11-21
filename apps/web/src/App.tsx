import React from 'react';
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
import { AIOnboardingModal } from './components/AIOnboardingModal';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AIOnboardingModal />
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
            <Route path="problems" element={<HomePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};
