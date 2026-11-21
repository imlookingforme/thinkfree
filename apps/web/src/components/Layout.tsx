import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';

export const Layout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-[#f8fafc] dark:bg-[#07090e] text-slate-900 dark:text-slate-100 bg-grid-pattern relative selection:bg-indigo-500/20">
      {/* Subtle top ambient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-64 bg-gradient-to-b from-indigo-500/[0.04] dark:from-indigo-500/[0.07] to-transparent pointer-events-none blur-3xl" />
      
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-10 py-8 lg:py-12 relative z-10">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200/60 dark:border-white/[0.06] py-8 text-xs text-slate-500 dark:text-slate-500 backdrop-blur-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-mono text-[11px] tracking-tight">ThinkFree Engine · Course Project F102 Group 68</span>
          </div>
          <p className="text-center sm:text-right text-[11px] font-mono text-slate-400 dark:text-slate-600">
            Engineered for Cognitive Independence · Active Evaluation Mode
          </p>
        </div>
      </footer>
    </div>
  );
};
