import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      appName: 'ThinkFree',
      tagline: 'Thinking-first learning platform',
      attempt: {
        title: 'Problem Attempt',
        aiLockedTitle: 'AI is Locked',
        aiLockedDesc: 'Try solving yourself first. AI will unlock after your genuine attempt.',
        effortLabel: 'Effort Meter',
        keepGoing: 'Keep going, you are {{percent}}% to unlock',
        readyToUnlock: 'Effort threshold reached! You can unlock AI guidance.',
        unlockButton: 'Unlock AI Guidance',
        stuckButton: "I'm Stuck (Declare Blockers)",
        timerLabel: 'Attempt Time',
        runCode: 'Run Code',
        outputLabel: 'Output',
        scratchpadTab: 'Scratchpad / Notes',
        problemTab: 'Problem Statement',
      },
      dashboard: {
        title: 'Thinking Dashboard',
        relianceScore: 'Reliance Score',
        independentThinkingScore: 'Independent Thinking Score (ITS)',
        aiDependencyRatio: 'AI Dependency Ratio (ADR)',
        selfSolveRate: 'Self-Solves (No AI)',
        studyFlow: 'Flow State & Focus',
        promptPlaceholder: 'Get guidance in solving your question... (paste text or problem)',
        recentQuestions: 'Recent Problems',
        weakConcepts: 'Focus Review Areas',
        demoBadge: 'Demo Mode (Simulated 60-day trend)',
      },
      auth: {
        signIn: 'Sign In',
        signUp: 'Create Account',
        email: 'Email address',
        password: 'Password',
        name: 'Full Name',
        googleSignIn: 'Continue with Google',
        logout: 'Log Out',
      }
    }
  },
  hi: {
    translation: {
      appName: 'ThinkFree',
      tagline: 'स्वतंत्र चिंतन शिक्षण मंच',
    }
  },
  te: {
    translation: {
      appName: 'ThinkFree',
      tagline: 'స్వతంత్ర ఆలోచన అభ్యసన వేదిక',
    }
  }
};

i18n.use(initReactI18next).init({
  resources,
  lng: 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
