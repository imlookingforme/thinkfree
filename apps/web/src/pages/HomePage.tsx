import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Radar, RadarChart, PolarGrid, PolarAngleAxis
} from 'recharts';
import {
  Mic, Sparkles, TrendingUp, Clock, Flame, Info,
  AlertCircle, BookOpen, ChevronRight, X, Search, Code2,
  Brain, ShieldCheck, Layers, Compass, ArrowRight
} from 'lucide-react';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/useAuthStore';

interface MetricExplainability {
  name: string;
  symbol: string;
  formula: string;
  plain_english: string;
  inputs: Record<string, any>;
  value: number;
}

interface DashboardData {
  student_id: string;
  its: number;
  adr: number;
  ewma_reliance_7d: number;
  ewma_reliance_30d: number;
  self_solves_count: number;
  ai_assisted_count: number;
  self_solve_rate: number;
  current_streak: number;
  peak_study_hour: number;
  flow_minutes_7d: number;
  active_minutes_7d: number;
  radar: {
    unaided_success_rate: number;
    explanation_coverage: number;
    persistence_effort: number;
    spaced_retention: number;
    consistency_score: number;
  };
  explainability: Record<string, MetricExplainability>;
}

interface ConceptItem {
  concept_id: string;
  name: string;
  subject: string;
  p_known: number;
  mastery_band: 'struggling' | 'developing' | 'mastered';
  ease: number;
  interval_days: number;
  prerequisites_unmet: string[];
}

interface ReviewItem {
  concept_id: string;
  concept_name: string;
  p_known: number;
  ease: number;
  interval_days: number;
  due_status: string;
  recommended_problem_id?: string;
  recommended_problem_title?: string;
}

interface ProblemItem {
  id: string;
  title: string;
  subject: string;
  difficulty_b: number;
  type: string;
  statement_md?: string;
}

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, openAuthModal } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'overview' | 'telemetry' | 'mastery'>('overview');
  const [quickPrompt, setQuickPrompt] = useState('');
  const [problemSearch, setProblemSearch] = useState('');
  const [subjectFilter, setSubjectFilter] = useState<string>('all');
  const [activeExplainModal, setActiveExplainModal] = useState<MetricExplainability | null>(null);
  const [showRadarModal, setShowRadarModal] = useState(false);

  // Fetch live dashboard KPIs (only if authenticated)
  const { data: dashboard } = useQuery<DashboardData>({
    queryKey: ['analytics', 'dashboard'],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/dashboard');
      return res.data;
    },
    enabled: !!user,
    staleTime: 30000,
  });

  // Fetch Mastery & Weak Concepts (only if authenticated)
  const { data: masteryData } = useQuery<{ concepts: ConceptItem[]; weak_concepts: ConceptItem[] }>({
    queryKey: ['analytics', 'mastery'],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/mastery');
      return res.data;
    },
    enabled: !!user,
    staleTime: 60000,
  });

  // Fetch SM-2 Spaced Review Queue (only if authenticated)
  const { data: reviewData } = useQuery<{ total_due: number; items: ReviewItem[] }>({
    queryKey: ['analytics', 'reviews'],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/reviews');
      return res.data;
    },
    enabled: !!user,
    staleTime: 60000,
  });

  // Fetch Curriculum Problems for the workspace launcher
  const { data: problems } = useQuery<ProblemItem[]>({
    queryKey: ['problems'],
    queryFn: async () => {
      const res = await apiClient.get('/problems?limit=40');
      return res.data;
    },
    staleTime: 60000,
  });

  const handleStartPrompt = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickPrompt.trim()) return;
    if (!user) {
      openAuthModal('login');
      return;
    }
    navigate('/attempt/new?prompt=' + encodeURIComponent(quickPrompt));
  };

  const itsScore = dashboard ? Math.round(dashboard.its) : 0;
  const adrScore = dashboard ? dashboard.adr.toFixed(2) : '0.00';
  const streakDays = dashboard ? dashboard.current_streak : 0;
  const flowHours = dashboard ? Math.floor(dashboard.flow_minutes_7d / 60) : 0;
  const flowMins = dashboard ? dashboard.flow_minutes_7d % 60 : 0;
  const peakHour = dashboard ? `${dashboard.peak_study_hour}:00` : '--:--';

  const selfSolvePercent = dashboard ? Math.round(dashboard.self_solve_rate) : 0;
  const selfSolveData = [
    { name: 'Self-Solves (Unaided)', value: selfSolvePercent, color: '#6366f1' },
    { name: 'AI Guided', value: 100 - selfSolvePercent, color: '#334155' },
  ];

  const radarData = dashboard ? [
    { subject: 'Unaided Solves', value: Math.round(dashboard.radar.unaided_success_rate * 100) },
    { subject: 'Explanation Coverage', value: Math.round(dashboard.radar.explanation_coverage * 100) },
    { subject: 'Persistence Effort', value: Math.round(dashboard.radar.persistence_effort * 100) },
    { subject: 'Spaced Retention', value: Math.round(dashboard.radar.spaced_retention * 100) },
    { subject: 'Consistency', value: Math.round(dashboard.radar.consistency_score * 100) },
  ] : [
    { subject: 'Unaided Solves', value: 0 },
    { subject: 'Explanation Coverage', value: 0 },
    { subject: 'Persistence Effort', value: 0 },
    { subject: 'Spaced Retention', value: 0 },
    { subject: 'Consistency', value: 0 },
  ];

  const relianceTrendData = [
    { day: '60d ago', reliance: 0.00 },
    { day: '45d ago', reliance: 0.00 },
    { day: '30d ago', reliance: dashboard ? dashboard.ewma_reliance_30d : 0.00 },
    { day: '15d ago', reliance: 0.00 },
    { day: '7d ago', reliance: dashboard ? dashboard.ewma_reliance_7d : 0.00 },
    { day: 'Today', reliance: dashboard ? dashboard.adr : 0.00 },
  ];

  // Filter problems for the Curated Problems Container
  const filteredProblems = (problems || []).filter((p) => {
    const matchesSearch = problemSearch === '' ||
      p.title.toLowerCase().includes(problemSearch.toLowerCase()) ||
      p.subject.toLowerCase().includes(problemSearch.toLowerCase());
    const matchesSubject = subjectFilter === 'all' || p.subject.toLowerCase() === subjectFilter.toLowerCase();
    return matchesSearch && matchesSubject;
  });

  return (
    <div className="space-y-10 animate-fadeIn">
      {/* ============================================================ */}
      {/* 1. HERO & ACTION COMMAND BAR (Spacious & Minimalist)        */}
      {/* ============================================================ */}
      <section className="relative">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-mono uppercase tracking-wider text-indigo-600 dark:text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 mb-3 font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Cognitive Sovereignty Platform</span>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white">
              Autonomous Thinking
            </h1>
            <p className="text-sm sm:text-base text-slate-500 dark:text-slate-400 mt-2 max-w-2xl font-normal leading-relaxed">
              Earn AI assistance through deliberate struggle — never through passive cognitive substitution.
            </p>
          </div>

          {/* Quick Vitals Capsule */}
          <div className="flex items-center gap-3 self-start md:self-auto">
            <div className="px-4 py-2.5 rounded-2xl bg-white dark:bg-white/[0.03] border border-slate-200/80 dark:border-white/[0.07] shadow-xs text-left">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">Active Streak</div>
              <div className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-1.5 mt-0.5">
                <Flame className="w-4 h-4 text-amber-500 fill-amber-500" />
                <span>{streakDays} Days</span>
              </div>
            </div>

            <div className="px-4 py-2.5 rounded-2xl bg-white dark:bg-white/[0.03] border border-slate-200/80 dark:border-white/[0.07] shadow-xs text-left">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-semibold">ITS Index</div>
              <div className="text-lg font-extrabold text-indigo-600 dark:text-indigo-400 flex items-center gap-1 mt-0.5">
                <span>{itsScore}</span>
                <span className="text-xs text-slate-400 font-normal">/100</span>
              </div>
            </div>
          </div>
        </div>

        {/* Unauthenticated Invitation Banner */}
        {!user && (
          <div className="mb-6 p-4 rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-indigo-500/10 via-purple-500/5 to-transparent flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-2">
                <span>⚡ Welcome to ThinkFree</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-indigo-500/20 text-indigo-300 font-mono">Real User Auth</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Sign in with Google or your email to track your cognitive independence, earn verifiable badges, and record your BKT mastery graph.
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => openAuthModal('login')}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition"
              >
                Sign In / Sign Up
              </button>
            </div>
          </div>
        )}

        {/* Minimalist Floating Command Bar */}
        <form onSubmit={handleStartPrompt} className="relative group">
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 via-purple-500/10 to-indigo-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
          <div className="relative flex items-center bg-white dark:bg-[#0c101b] border border-slate-200/90 dark:border-white/[0.08] rounded-2xl p-2 shadow-lg shadow-slate-900/5 dark:shadow-black/40 transition-all">
            <div className="pl-3.5 pr-2 text-slate-400">
              <Search className="w-5 h-5" />
            </div>
            <input
              type="text"
              value={quickPrompt}
              onChange={(e) => setQuickPrompt(e.target.value)}
              placeholder="Ask a question, enter a problem statement, or launch a challenge..."
              className="w-full py-2.5 px-2 text-sm bg-transparent text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none font-sans"
            />
            <div className="flex items-center gap-2 pr-1">
              <button
                type="button"
                className="p-2 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-xl hover:bg-slate-100 dark:hover:bg-white/[0.05] transition"
                title="Voice Input (Speech-to-Text)"
                aria-label="Voice Input"
              >
                <Mic className="w-4 h-4" />
              </button>
              <button
                type="submit"
                className="px-5 py-2.5 bg-slate-950 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-200 text-white dark:text-slate-950 rounded-xl text-xs font-bold font-mono tracking-tight transition-all shadow-xs flex items-center gap-1.5"
              >
                <span>Launch</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </form>

        {/* Quick Topic Chips */}
        <div className="flex flex-wrap items-center gap-2 mt-3 pt-1">
          <span className="text-[11px] font-mono text-slate-400 font-medium mr-1">Quick topics:</span>
          {['Dynamic Programming', 'Graph Theory', 'Linear Algebra', 'Trees & Heaps', 'Discrete Math'].map((topic) => (
            <button
              key={topic}
              type="button"
              onClick={() => setQuickPrompt(topic)}
              className="px-2.5 py-1 text-[11px] font-mono font-medium rounded-lg bg-slate-100/80 dark:bg-white/[0.03] text-slate-600 dark:text-slate-400 border border-slate-200/60 dark:border-white/[0.05] hover:border-indigo-500/40 hover:text-indigo-600 dark:hover:text-indigo-300 transition-all"
            >
              #{topic}
            </button>
          ))}
        </div>
      </section>

      {/* ============================================================ */}
      {/* 2. SUBDIVIDED CONTAINER SELECTOR (Segmented View Controller) */}
      {/* ============================================================ */}
      <section className="flex items-center justify-between border-b border-slate-200/70 dark:border-white/[0.06] pb-4">
        <div className="flex items-center gap-2 bg-slate-100/70 dark:bg-white/[0.03] p-1 rounded-2xl border border-slate-200/60 dark:border-white/[0.05]">
          <button
            type="button"
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'overview'
                ? 'bg-white dark:bg-white/[0.1] text-slate-900 dark:text-white shadow-xs border border-slate-200/70 dark:border-white/[0.08]'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Overview & Practice</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('telemetry')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'telemetry'
                ? 'bg-white dark:bg-white/[0.1] text-slate-900 dark:text-white shadow-xs border border-slate-200/70 dark:border-white/[0.08]'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Cognitive Telemetry</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('mastery')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'mastery'
                ? 'bg-white dark:bg-white/[0.1] text-slate-900 dark:text-white shadow-xs border border-slate-200/70 dark:border-white/[0.08]'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Knowledge Graph (BKT)</span>
          </button>
        </div>

        <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>Real-time Telemetry Active</span>
        </div>
      </section>

      {/* ============================================================ */}
      {/* TAB 1: OVERVIEW & PRACTICE CONTAINER                         */}
      {/* ============================================================ */}
      {activeTab === 'overview' && (
        <div className="space-y-10 animate-in fade-in duration-300">
          {/* Subdivided Block A: Cognitive Vital Signs Cards */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-mono uppercase tracking-wider font-bold text-slate-400">
                Cognitive Vital Signs
              </h2>
              <span className="text-xs font-mono text-slate-400">Target Benchmark: &gt;75 Exam Ready</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* ITS Card */}
              <div className="p-5 rounded-2xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.06] shadow-xs relative group hover:border-indigo-500/40 transition-colors">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-3">
                  <span>Thinking Score (ITS)</span>
                  <button
                    onClick={() => dashboard?.explainability?.ITS && setActiveExplainModal(dashboard.explainability.ITS)}
                    className="p-1 hover:text-indigo-500 dark:hover:text-indigo-400 rounded transition"
                    title="View exact mathematical formula"
                  >
                    <Info className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white font-mono">
                    {itsScore}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">/100</span>
                </div>
                <div className="mt-3 flex items-center gap-1.5 text-[11px] font-mono text-emerald-600 dark:text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Exam Readiness Confirmed</span>
                </div>
              </div>

              {/* ADR Card */}
              <div className="p-5 rounded-2xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.06] shadow-xs relative group hover:border-indigo-500/40 transition-colors">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-3">
                  <span>AI Dependency (ADR)</span>
                  <button
                    onClick={() => dashboard?.explainability?.ADR && setActiveExplainModal(dashboard.explainability.ADR)}
                    className="p-1 hover:text-indigo-500 dark:hover:text-indigo-400 rounded transition"
                    title="View exact mathematical formula"
                  >
                    <Info className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white font-mono">
                    {adrScore}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">ratio</span>
                </div>
                <div className="mt-3 flex items-center gap-1.5 text-[11px] font-mono text-emerald-600 dark:text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Zero Reliance (Peak Autonomy)</span>
                </div>
              </div>

              {/* Streak Card */}
              <div className="p-5 rounded-2xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.06] shadow-xs relative group hover:border-indigo-500/40 transition-colors">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-3">
                  <span>Unaided Streak</span>
                  <Flame className="w-3.5 h-3.5 text-amber-500" />
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white font-mono">
                    {streakDays}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">days active</span>
                </div>
                <div className="mt-3 text-[11px] font-mono text-slate-400 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-indigo-500" />
                  <span>1 freeze token available</span>
                </div>
              </div>

              {/* Flow State Card */}
              <div className="p-5 rounded-2xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.06] shadow-xs relative group hover:border-indigo-500/40 transition-colors">
                <div className="flex items-center justify-between text-xs text-slate-400 font-mono mb-3">
                  <span>Deliberate Flow</span>
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white font-mono">
                    {flowHours}h {flowMins}m
                  </span>
                </div>
                <div className="mt-3 text-[11px] font-mono text-slate-400">
                  Peak cognitive hour: <span className="font-bold text-slate-700 dark:text-slate-300">{peakHour}</span>
                </div>
              </div>
            </div>

            {/* Autonomy Distribution Bar */}
            <div className="mt-4 p-4 rounded-2xl bg-white dark:bg-[#0c101b] border border-slate-200/70 dark:border-white/[0.05] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-600 dark:text-indigo-400">
                  <Brain className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">
                    Autonomy Breakdown: {selfSolvePercent}% Self-Solves vs {100 - selfSolvePercent}% AI Guided
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                    Measured across all attempted challenges and verified solution commits
                  </div>
                </div>
              </div>

              <div className="w-full sm:w-64">
                <div className="w-full bg-slate-200 dark:bg-white/[0.08] h-2.5 rounded-full overflow-hidden flex">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-l-full transition-all duration-500"
                    style={{ width: `${selfSolvePercent}%` }}
                    title={`Self-Solves: ${selfSolvePercent}%`}
                  />
                  <div
                    className="h-full bg-slate-400 dark:bg-slate-600 rounded-r-full transition-all duration-500"
                    style={{ width: `${100 - selfSolvePercent}%` }}
                    title={`AI Guided: ${100 - selfSolvePercent}%`}
                  />
                </div>
                <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1">
                  <span>Unaided ({selfSolvePercent}%)</span>
                  <span>AI Guided ({100 - selfSolvePercent}%)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Subdivided Block B: Today's Spaced Review Queue (SM-2) */}
          {reviewData && reviewData.items.length > 0 && (
            <div className="p-6 rounded-3xl bg-gradient-to-b from-amber-500/[0.04] to-transparent border border-amber-500/20 shadow-xs relative">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-2xl bg-amber-500/10 text-amber-500 border border-amber-500/20">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900 dark:text-white">
                        Spaced Retention Queue (SM-2 Algorithm)
                      </h3>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30">
                        {reviewData.total_due} Due Today
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                      Concepts nearing memory decay threshold. Complete a challenge to reset the retention interval.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {reviewData.items.slice(0, 3).map((item) => (
                  <div
                    key={item.concept_id}
                    onClick={() => item.recommended_problem_id && navigate(`/attempt/${item.recommended_problem_id}`)}
                    className="p-4 rounded-2xl bg-white dark:bg-[#0c101b] border border-amber-500/20 hover:border-amber-500/60 transition-all cursor-pointer shadow-xs group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400">
                          Due Review
                        </span>
                        <span className="text-[11px] font-mono text-slate-400">
                          {item.interval_days}d interval
                        </span>
                      </div>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-white group-hover:text-amber-500 transition-colors">
                        {item.concept_name}
                      </h4>
                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-mono">
                        Current Recall: <span className="font-bold text-slate-800 dark:text-slate-200">{(item.p_known * 100).toFixed(0)}%</span>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-white/[0.05] flex items-center justify-between text-xs font-semibold text-amber-600 dark:text-amber-400">
                      <span>Retain Now</span>
                      <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Subdivided Block C: Curated Problem Library Container */}
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.06] shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-100 dark:border-white/[0.06]">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Code2 className="w-4 h-4 text-indigo-500" />
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    Curated Problem Library
                  </h3>
                  <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-white/[0.05] text-slate-500">
                    40 Challenges Ready
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Select any problem to begin an autonomous session with timed attempt lock & Socratic scaffolding.
                </p>
              </div>

              {/* Filters */}
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400 pointer-events-none" />
                  <input
                    type="text"
                    value={problemSearch}
                    onChange={(e) => setProblemSearch(e.target.value)}
                    placeholder="Filter challenges..."
                    className="pl-8 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-white/[0.08] bg-slate-50 dark:bg-white/[0.03] text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono w-44 sm:w-56"
                  />
                </div>

                <select
                  value={subjectFilter}
                  onChange={(e) => setSubjectFilter(e.target.value)}
                  className="py-1.5 px-3 text-xs rounded-xl border border-slate-200 dark:border-white/[0.08] bg-slate-50 dark:bg-white/[0.03] text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                >
                  <option value="all">All Disciplines</option>
                  <option value="Computer Science">Computer Science</option>
                  <option value="Mathematics">Mathematics</option>
                  <option value="Physics">Physics</option>
                </select>
              </div>
            </div>

            {/* Problem Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredProblems.slice(0, 9).map((p) => {
                const diffLabel = p.difficulty_b > 1.2 ? 'Hard' : p.difficulty_b > 0.8 ? 'Medium' : 'Easy';
                const diffColor = p.difficulty_b > 1.2
                  ? 'text-rose-600 dark:text-rose-400 bg-rose-500/10 border-rose-500/20'
                  : p.difficulty_b > 0.8
                  ? 'text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20'
                  : 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20';

                return (
                  <div
                    key={p.id}
                    onClick={() => {
                      if (!user) {
                        openAuthModal('login');
                        return;
                      }
                      navigate(`/attempt/${p.id}`);
                    }}
                    className="p-4 rounded-2xl border border-slate-200/70 dark:border-white/[0.06] bg-slate-50/50 dark:bg-white/[0.02] hover:border-indigo-500/50 hover:bg-white dark:hover:bg-white/[0.04] transition-all cursor-pointer shadow-xs group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded-md border ${diffColor}`}>
                          {diffLabel}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          {p.subject}
                        </span>
                      </div>
                      <h4 className="font-bold text-sm text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2">
                        {p.title}
                      </h4>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-white/[0.04] flex items-center justify-between text-xs font-semibold text-slate-500 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                      <span className="font-mono text-[11px]">Solve Autonomous →</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </div>
                );
              })}
            </div>

            {filteredProblems.length === 0 && (
              <div className="py-12 text-center text-xs font-mono text-slate-400">
                No challenges found matching your filter criteria.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 2: COGNITIVE TELEMETRY CONTAINER (Charts & Trends)       */}
      {/* ============================================================ */}
      {activeTab === 'telemetry' && (
        <div className="space-y-8 animate-in fade-in duration-300">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Reliance Trend Area Chart */}
            <div className="lg:col-span-2 p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.06] shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">
                    Cognitive Dependency Curve (EWMA)
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    A downward slope proves progressive independence from external LLM assistance.
                  </p>
                </div>
                <span className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 font-bold self-start sm:self-auto">
                  60-Day Telemetry
                </span>
              </div>

              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={relianceTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="relianceGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.35}/>
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="day" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} domain={[0, 1]} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0c101b',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderRadius: '0.75rem',
                        fontSize: '12px',
                        color: '#fff',
                        fontFamily: 'monospace'
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="reliance"
                      stroke="#6366f1"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#relianceGrad)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Self-Solve Percentage Donut */}
            <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.06] shadow-xs flex flex-col justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Solution Verification
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Unaided vs Scaffolded distribution
                </p>
              </div>

              <div className="h-52 w-full flex items-center justify-center relative my-4">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={selfSolveData}
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {selfSolveData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute text-center">
                  <div className="text-3xl font-extrabold text-slate-900 dark:text-white font-mono">{selfSolvePercent}%</div>
                  <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 font-bold">Self-Solves</div>
                </div>
              </div>

              <div className="space-y-2 pt-3 border-t border-slate-100 dark:border-white/[0.06] text-xs font-mono">
                <div className="flex items-center justify-between text-slate-700 dark:text-slate-300">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                    <span>Unaided Submissions</span>
                  </div>
                  <span className="font-bold">{selfSolvePercent}%</span>
                </div>
                <div className="flex items-center justify-between text-slate-400">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-slate-600" />
                    <span>AI Guided Scaffolding</span>
                  </div>
                  <span>{100 - selfSolvePercent}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Free Thinker Radar */}
          <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.06] shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Free Thinker Radar (5 Dimensions)
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Multi-axial evaluation of cognitive perseverance and conceptual rigor.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowRadarModal(true)}
                className="text-xs font-mono text-indigo-500 hover:text-indigo-400 underline self-start sm:self-auto"
              >
                Inspect dimension definitions →
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7 h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }} />
                    <Radar name="Student" dataKey="value" stroke="#6366f1" fill="#6366f1" fillOpacity={0.35} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="lg:col-span-5 space-y-3">
                {radarData.map((d) => (
                  <div key={d.subject} className="p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-200/60 dark:border-white/[0.05]">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-900 dark:text-white">{d.subject}</span>
                      <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">{d.value}%</span>
                    </div>
                    <div className="w-full bg-slate-200 dark:bg-white/[0.08] h-1.5 rounded-full overflow-hidden mt-1.5">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${d.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 3: CONCEPT MASTERY & BKT MATRIX CONTAINER                */}
      {/* ============================================================ */}
      {activeTab === 'mastery' && (
        <div className="p-6 sm:p-8 rounded-3xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.06] shadow-xs space-y-6 animate-in fade-in duration-300">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100 dark:border-white/[0.06]">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Bayesian Knowledge Tracing (BKT) Matrix
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Real-time latent state probability P(Known) mapped across all curriculum concepts and prerequisites.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                &ge;70% Mastered
              </span>
              <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                40-69% Developing
              </span>
              <span className="px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                &lt;40% Struggling
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {masteryData?.concepts?.map((c) => {
              const bandColor = c.mastery_band === 'struggling'
                ? 'border-rose-500/20 bg-rose-500/[0.03]'
                : c.mastery_band === 'developing'
                ? 'border-amber-500/20 bg-amber-500/[0.03]'
                : 'border-slate-200/70 dark:border-white/[0.05] bg-slate-50/50 dark:bg-white/[0.02]';

              const barColor = c.p_known >= 0.70 ? 'bg-emerald-500' : c.p_known >= 0.40 ? 'bg-amber-500' : 'bg-rose-500';

              return (
                <div
                  key={c.concept_id}
                  className={`p-4 rounded-2xl border ${bandColor} flex flex-col justify-between hover:border-indigo-500/50 transition-all`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-[10px] text-slate-400 uppercase tracking-wider">{c.subject}</span>
                      <span className="font-mono text-xs font-bold text-slate-900 dark:text-white">
                        {(c.p_known * 100).toFixed(0)}%
                      </span>
                    </div>
                    <h4 className="font-bold text-sm text-slate-900 dark:text-white mb-2">{c.name}</h4>

                    <div className="w-full bg-slate-200 dark:bg-white/[0.08] h-2 rounded-full overflow-hidden mb-2">
                      <div className={`h-full rounded-full ${barColor}`} style={{ width: `${Math.round(c.p_known * 100)}%` }} />
                    </div>

                    <div className="text-[11px] font-mono text-slate-400 flex justify-between">
                      <span>Interval: {c.interval_days}d</span>
                      <span>Ease: {c.ease.toFixed(2)}</span>
                    </div>
                  </div>

                  {c.prerequisites_unmet && c.prerequisites_unmet.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-rose-500/10 text-[10px] text-rose-600 dark:text-rose-400 flex items-center gap-1 font-mono">
                      <AlertCircle className="w-3 h-3 shrink-0" />
                      <span>Unmet: {c.prerequisites_unmet.join(', ')}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* MATHEMATICAL EXPLAINABILITY MODAL                             */}
      {/* ============================================================ */}
      {activeExplainModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-white dark:bg-[#0c101b] border border-slate-200 dark:border-white/[0.08] rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-white/[0.06] pb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {activeExplainModal.name} ({activeExplainModal.symbol})
                </h3>
                <span className="text-xs font-mono text-indigo-500 dark:text-indigo-400">Mathematical Transparency Standard</span>
              </div>
              <button
                onClick={() => setActiveExplainModal(null)}
                className="p-1 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-sm">
              <div>
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider font-semibold">Formula Definition</span>
                <div className="font-mono bg-slate-100 dark:bg-black/40 px-3.5 py-2.5 rounded-xl text-slate-900 dark:text-indigo-300 text-xs mt-1 border border-slate-200 dark:border-white/[0.06]">
                  {activeExplainModal.formula}
                </div>
              </div>

              <div>
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider font-semibold">Plain English Explanation</span>
                <p className="text-slate-600 dark:text-slate-300 text-xs mt-1 leading-relaxed">
                  {activeExplainModal.plain_english}
                </p>
              </div>

              <div>
                <span className="text-xs font-mono text-slate-400 uppercase tracking-wider font-semibold">Live Parametric Inputs</span>
                <div className="mt-1 bg-slate-50 dark:bg-white/[0.02] rounded-xl p-3.5 space-y-1.5 text-xs border border-slate-200/60 dark:border-white/[0.05]">
                  {Object.entries(activeExplainModal.inputs).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-slate-600 dark:text-slate-300 font-mono">
                      <span>{k}:</span>
                      <span className="font-semibold text-slate-900 dark:text-white">{String(v)}</span>
                    </div>
                  ))}
                  <div className="pt-2 border-t border-slate-200 dark:border-white/[0.06] flex justify-between font-bold text-slate-900 dark:text-white font-mono">
                    <span>Resulting Value:</span>
                    <span className="text-indigo-600 dark:text-indigo-400">{activeExplainModal.value}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setActiveExplainModal(null)}
                className="px-5 py-2 bg-slate-950 text-white dark:bg-white dark:text-slate-950 rounded-xl text-xs font-bold font-mono tracking-tight"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* FREE THINKER RADAR DIMENSION MODAL                           */}
      {/* ============================================================ */}
      {showRadarModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-white dark:bg-[#0c101b] border border-slate-200 dark:border-white/[0.08] rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-white/[0.06] pb-3">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Free Thinker Radar Dimensions</h3>
              <button onClick={() => setShowRadarModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
              <div>
                <strong className="text-slate-900 dark:text-white font-mono">1. Unaided Solves:</strong> Percentage of problems solved without asking for tutor scaffolding.
              </div>
              <div>
                <strong className="text-slate-900 dark:text-white font-mono">2. Explanation Coverage:</strong> Rubric coverage verified during the validation teach-back phase.
              </div>
              <div>
                <strong className="text-slate-900 dark:text-white font-mono">3. Persistence Effort:</strong> Normalized keystrokes, compiler runs, and time spent grappling prior to assistance.
              </div>
              <div>
                <strong className="text-slate-900 dark:text-white font-mono">4. Spaced Retention:</strong> Recall stability across SM-2 scheduled review cycles.
              </div>
              <div>
                <strong className="text-slate-900 dark:text-white font-mono">5. Consistency:</strong> Stylistic and syntactic alignment between your attempt code and your explanation vocabulary.
              </div>
            </div>
            <div className="flex justify-end pt-3">
              <button
                onClick={() => setShowRadarModal(false)}
                className="px-5 py-2 bg-slate-950 text-white dark:bg-white dark:text-slate-950 rounded-xl text-xs font-bold font-mono tracking-tight"
              >
                Acknowledge
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
