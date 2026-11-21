import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Brain, Moon, Sun, Shield, Award, FolderGit2, Cpu, LogIn, LogOut } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { apiClient } from '../api/client';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { user, logout, openAuthModal } = useAuthStore();
  const [isDark, setIsDark] = useState(() => {
    return document.documentElement.classList.contains('dark') ||
      window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const { data: aiData } = useQuery({
    queryKey: ['ai-providers'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/providers');
      return res.data;
    },
    staleTime: 1000 * 30,
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  const toggleTheme = () => setIsDark(!isDark);

  const navItems = [
    { name: 'Dashboard', path: '/', icon: Brain },
    { name: 'Cohort Portal', path: '/professor', icon: Shield },
    { name: 'Team Collab & DPDP', path: '/collab', icon: FolderGit2 },
    { name: 'Badge Verify', path: '/verify/badge_demo_77', icon: Award },
    { name: 'AI Models', path: '/settings/ai', icon: Cpu },
  ];

  const providersList = Array.isArray(aiData) ? aiData : (aiData?.providers || []);
  const activeProvider = providersList.find((p: any) => p.is_active);

  return (
    <nav className="border-b border-slate-200/60 dark:border-white/[0.06] bg-white/70 dark:bg-[#07090e]/80 backdrop-blur-xl sticky top-0 z-50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-400 text-white flex items-center justify-center shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
                <Brain className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="font-extrabold text-base tracking-tight text-slate-900 dark:text-white font-sans">
                  ThinkFree
                </span>
                <span className="text-[9px] font-mono tracking-widest uppercase text-indigo-600 dark:text-indigo-400 -mt-1 font-semibold">
                  Cognitive AI
                </span>
              </div>
            </Link>

            {/* Nav links */}
            <div className="hidden md:flex items-center gap-1 bg-slate-100/60 dark:bg-white/[0.03] p-1 rounded-xl border border-slate-200/50 dark:border-white/[0.04]">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                      isActive
                        ? 'bg-white dark:bg-white/[0.1] text-slate-900 dark:text-white shadow-xs border border-slate-200/60 dark:border-white/[0.08]'
                        : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white/40 dark:hover:bg-white/[0.04]'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Right controls */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Active AI Pill */}
            <Link
              to="/settings/ai"
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-100/80 dark:bg-white/[0.04] text-slate-800 dark:text-slate-200 border border-slate-200/80 dark:border-white/[0.08] hover:border-indigo-500/50 dark:hover:border-indigo-400/50 transition-all shadow-xs group"
              title="Click to switch or configure AI models"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-mono text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                {activeProvider ? activeProvider.name : 'Configuring...'}
              </span>
              <span className="hidden sm:inline text-[10px] text-indigo-500 dark:text-indigo-400 font-mono font-medium group-hover:translate-x-0.5 transition-transform">
                Switch →
              </span>
            </Link>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/[0.05] transition-colors border border-transparent hover:border-slate-200 dark:hover:border-white/[0.06]"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Auth State */}
            {user ? (
              <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200/60 dark:border-white/[0.06]">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center text-xs font-bold shadow-xs">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div className="hidden lg:block text-left">
                  <div className="text-xs font-bold text-slate-900 dark:text-white leading-tight truncate max-w-[130px]">
                    {user.name}
                  </div>
                  <div className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 capitalize font-medium">
                    {user.role}
                  </div>
                </div>
                <button
                  onClick={() => logout()}
                  title="Sign out"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors ml-1"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => openAuthModal('login')}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20 transition-all hover:scale-[1.02]"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
