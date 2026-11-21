import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Radar, RadarChart, PolarGrid, PolarAngleAxis
} from 'recharts';
import {
  Mic, Sparkles, TrendingUp, Clock, Flame, Info, ArrowUpRight,
  AlertCircle, BookOpen, ChevronRight, X
} from 'lucide-react';
import { apiClient } from '../api/client';

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

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [quickPrompt, setQuickPrompt] = useState('');
  const [activeExplainModal, setActiveExplainModal] = useState<MetricExplainability | null>(null);
  const [showRadarModal, setShowRadarModal] = useState(false);

  // Fetch live dashboard KPIs
  const { data: dashboard } = useQuery<DashboardData>({
    queryKey: ['analytics', 'dashboard'],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/dashboard');
      return res.data;
    },
    staleTime: 30000,
  });

  // Fetch Mastery & Weak Concepts
  const { data: masteryData } = useQuery<{ concepts: ConceptItem[]; weak_concepts: ConceptItem[] }>({
    queryKey: ['analytics', 'mastery'],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/mastery');
      return res.data;
    },
    staleTime: 60000,
  });

  // Fetch SM-2 Spaced Review Queue
  const { data: reviewData } = useQuery<{ total_due: number; items: ReviewItem[] }>({
    queryKey: ['analytics', 'reviews'],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/reviews');
      return res.data;
    },
    staleTime: 60000,
  });

  const handleStartPrompt = (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickPrompt.trim()) return;
    navigate('/attempt/new?prompt=' + encodeURIComponent(quickPrompt));
  };

  const itsScore = dashboard ? Math.round(dashboard.its) : 82;
  const adrScore = dashboard ? dashboard.adr.toFixed(2) : '0.19';
  const streakDays = dashboard ? dashboard.current_streak : 12;
  const flowHours = dashboard ? Math.floor(dashboard.flow_minutes_7d / 60) : 2;
  const flowMins = dashboard ? dashboard.flow_minutes_7d % 60 : 25;
  const peakHour = dashboard ? `${dashboard.peak_study_hour}:00` : '16:00';

  const selfSolvePercent = dashboard ? Math.round(dashboard.self_solve_rate) : 72;
  const selfSolveData = [
    { name: 'Self-Solves (Unaided)', value: selfSolvePercent, color: '#0f172a' },
    { name: 'AI Guided', value: 100 - selfSolvePercent, color: '#94a3b8' },
  ];

  const radarData = dashboard ? [
    { subject: 'Unaided Solves', value: Math.round(dashboard.radar.unaided_success_rate * 100) },
    { subject: 'Explanation Coverage', value: Math.round(dashboard.radar.explanation_coverage * 100) },
    { subject: 'Persistence Effort', value: Math.round(dashboard.radar.persistence_effort * 100) },
    { subject: 'Spaced Retention', value: Math.round(dashboard.radar.spaced_retention * 100) },
    { subject: 'Consistency', value: Math.round(dashboard.radar.consistency_score * 100) },
  ] : [
    { subject: 'Unaided Solves', value: 80 },
    { subject: 'Explanation Coverage', value: 84 },
    { subject: 'Persistence Effort', value: 92 },
    { subject: 'Spaced Retention', value: 78 },
    { subject: 'Consistency', value: 88 },
  ];

  const relianceTrendData = [
    { day: '60d ago', reliance: 0.62 },
    { day: '45d ago', reliance: 0.51 },
    { day: '30d ago', reliance: dashboard ? dashboard.ewma_reliance_30d : 0.42 },
    { day: '15d ago', reliance: 0.31 },
    { day: '7d ago', reliance: dashboard ? dashboard.ewma_reliance_7d : 0.24 },
    { day: 'Today', reliance: dashboard ? dashboard.adr : 0.19 },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner / Prompt box */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>ThinkFree Guidance Engine</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Independent Thinking Dashboard
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-6 max-w-2xl">
          Track your cognitive independence. AI assistance is earned through deliberate effort, not cognitive substitution.
        </p>

        <form onSubmit={handleStartPrompt} className="relative flex items-center">
          <input
            type="text"
            value={quickPrompt}
            onChange={(e) => setQuickPrompt(e.target.value)}
            placeholder="Get guidance in solving your question... (paste text or type problem)"
            className="w-full pl-4 pr-24 py-3.5 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400"
          />
          <div className="absolute right-2 flex items-center gap-1.5">
            <button
              type="button"
              className="p-2 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition"
              title="Voice Input"
              aria-label="Voice Input"
            >
              <Mic className="w-4 h-4" />
            </button>
            <button
              type="submit"
              className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-200 dark:text-slate-900 rounded-lg text-xs font-semibold transition"
            >
              Solve
            </button>
          </div>
        </form>
      </div>

      {/* KPI Cards with Transparency Popover Modals */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* ITS Card */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm relative group">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span>Independent Thinking Score</span>
            <button
              onClick={() => dashboard?.explainability?.ITS && setActiveExplainModal(dashboard.explainability.ITS)}
              className="p-1 hover:text-slate-900 dark:hover:text-white rounded"
              title="View exact mathematical formula"
            >
              <Info className="w-4 h-4 text-slate-400" />
            </button>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {itsScore}<span className="text-lg font-normal text-slate-400">/100</span>
          </div>
          <div className="mt-2 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>Target: &gt;75 (Exam Readiness)</span>
          </div>
        </div>

        {/* ADR Card */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span>AI Dependency Ratio (ADR)</span>
            <button
              onClick={() => dashboard?.explainability?.ADR && setActiveExplainModal(dashboard.explainability.ADR)}
              className="p-1 hover:text-slate-900 dark:hover:text-white rounded"
              title="View exact mathematical formula"
            >
              <Info className="w-4 h-4 text-slate-400" />
            </button>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">{adrScore}</div>
          <div className="mt-2 text-xs text-emerald-600 dark:text-emerald-400">
            EWMA Trend: {dashboard ? dashboard.ewma_reliance_7d.toFixed(2) : '0.22'}
          </div>
        </div>

        {/* Unaided Streak */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span>Unaided Streak</span>
            <Flame className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {streakDays} <span className="text-sm font-normal text-slate-400">days</span>
          </div>
          <div className="mt-2 text-xs text-slate-500">
            1 freeze token available per week
          </div>
        </div>

        {/* Flow State */}
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span>Flow State & Study</span>
            <Clock className="w-4 h-4 text-slate-700 dark:text-slate-300" />
          </div>
          <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {flowHours}h {flowMins}m
          </div>
          <div className="mt-2 text-xs text-slate-500">
            Peak performance: {peakHour}
          </div>
        </div>
      </div>

      {/* Spaced Review Queue Card (Feature 4 & 6) */}
      {reviewData && reviewData.items.length > 0 && (
        <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 shadow-md">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <BookOpen className="w-5 h-5 text-amber-400" />
              <div>
                <h2 className="text-base font-bold">Today's Spaced Review Queue (SM-2)</h2>
                <p className="text-xs text-slate-300">
                  {reviewData.total_due} concepts are due for reinforcement to lock knowledge into long-term memory.
                </p>
              </div>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-amber-400/20 text-amber-300 rounded-full border border-amber-400/30">
              {reviewData.total_due} Due
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {reviewData.items.slice(0, 3).map((item) => (
              <div
                key={item.concept_id}
                onClick={() => item.recommended_problem_id && navigate(`/attempt/${item.recommended_problem_id}`)}
                className="bg-white/10 hover:bg-white/15 border border-white/10 rounded-xl p-3.5 cursor-pointer transition flex items-center justify-between"
              >
                <div>
                  <div className="text-sm font-semibold text-white">{item.concept_name}</div>
                  <div className="text-xs text-slate-300 mt-0.5">
                    Mastery: {(item.p_known * 100).toFixed(0)}% · Interval: {item.interval_days}d
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reliance Trend Area Chart */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">Reliance Score Trend</h2>
              <p className="text-xs text-slate-500">Decreasing curve signifies accelerating cognitive independence</p>
            </div>
            <span className="text-xs font-mono font-medium px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded">60-Day View</span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={relianceTrendData}>
                <defs>
                  <linearGradient id="relianceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#475569" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#475569" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="day" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 1]} />
                <Tooltip />
                <Area type="monotone" dataKey="reliance" stroke="#334155" strokeWidth={2} fillOpacity={1} fill="url(#relianceGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Self-Solve Percentage Donut */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-1">Self-Solves vs AI Guided</h2>
            <p className="text-xs text-slate-500">Distribution across completed problem attempts</p>
          </div>
          <div className="h-48 w-full flex items-center justify-center relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={selfSolveData}
                  innerRadius={55}
                  outerRadius={75}
                  paddingAngle={4}
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
              <div className="text-2xl font-bold text-slate-900 dark:text-white">{selfSolvePercent}%</div>
              <div className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">Self-Solves</div>
            </div>
          </div>
          <div className="flex justify-around text-xs pt-2 border-t border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-900 dark:bg-slate-100" />
              <span>Self-Solves ({selfSolvePercent}%)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
              <span>AI Guided ({100 - selfSolvePercent}%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Free Thinker Radar & Concept Weakness Heat Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Free Thinker Radar */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">Free Thinker Radar</h2>
            <button
              onClick={() => setShowRadarModal(true)}
              className="text-xs text-slate-500 hover:text-slate-900 dark:hover:text-white underline"
            >
              See details
            </button>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#cbd5e1" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10 }} />
                <Radar name="Student" dataKey="value" stroke="#0f172a" fill="#334155" fillOpacity={0.4} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Concept Mastery & Weakness Heat-Grid (Feature 4) */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                Concept Knowledge Tracing (BKT)
              </h2>
              <p className="text-xs text-slate-500">
                P(Known) mastery scores with prerequisite dependency tracking
              </p>
            </div>
            <button
              onClick={() => navigate('/problems')}
              className="text-xs font-medium text-slate-600 dark:text-slate-300 hover:underline flex items-center gap-1"
            >
              Browse practice problems <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-1">
            {masteryData?.concepts?.map((c) => (
              <div
                key={c.concept_id}
                className={`p-3 rounded-lg border text-xs flex flex-col justify-between ${
                  c.mastery_band === 'struggling'
                    ? 'border-rose-200 bg-rose-50/50 dark:border-rose-900/40 dark:bg-rose-950/20'
                    : c.mastery_band === 'developing'
                    ? 'border-amber-200 bg-amber-50/50 dark:border-amber-900/40 dark:bg-amber-950/20'
                    : 'border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-slate-900 dark:text-white">{c.name}</span>
                  <span className="font-mono text-[11px] font-bold">{(c.p_known * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 h-1.5 rounded-full overflow-hidden my-1">
                  <div
                    className={`h-full rounded-full ${
                      c.p_known >= 0.70 ? 'bg-emerald-500' : c.p_known >= 0.40 ? 'bg-amber-500' : 'bg-rose-500'
                    }`}
                    style={{ width: `${Math.round(c.p_known * 100)}%` }}
                  />
                </div>
                {c.prerequisites_unmet && c.prerequisites_unmet.length > 0 && (
                  <div className="mt-1 text-[10px] text-rose-600 dark:text-rose-400 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3 flex-shrink-0" />
                    <span>Unmet prereqs: {c.prerequisites_unmet.join(', ')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Formula & Explainability Modal */}
      {activeExplainModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {activeExplainModal.name} ({activeExplainModal.symbol})
                </h3>
                <span className="text-xs text-slate-500">Mathematical Transparency & Ethics Standard</span>
              </div>
              <button
                onClick={() => setActiveExplainModal(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Formula</span>
                <div className="font-mono bg-slate-100 dark:bg-slate-800 px-3 py-2 rounded-lg text-slate-900 dark:text-slate-100 text-xs mt-1">
                  {activeExplainModal.formula}
                </div>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Plain English</span>
                <p className="text-slate-600 dark:text-slate-300 text-xs mt-1 leading-relaxed">
                  {activeExplainModal.plain_english}
                </p>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Your Inputs</span>
                <div className="mt-1 bg-slate-50 dark:bg-slate-800/50 rounded-lg p-3 space-y-1 text-xs">
                  {Object.entries(activeExplainModal.inputs).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-slate-600 dark:text-slate-300">
                      <span>{k}:</span>
                      <span className="font-mono font-semibold">{String(v)}</span>
                    </div>
                  ))}
                  <div className="pt-2 border-t border-slate-200 dark:border-slate-700 flex justify-between font-bold text-slate-900 dark:text-white">
                    <span>Resulting Value:</span>
                    <span>{activeExplainModal.value}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setActiveExplainModal(null)}
                className="px-4 py-2 bg-slate-900 text-white dark:bg-white dark:text-slate-900 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Free Thinker Radar Dimension Modal */}
      {showRadarModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Free Thinker Radar Dimensions</h3>
              <button onClick={() => setShowRadarModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
              <div>
                <strong className="text-slate-900 dark:text-white">1. Unaided Solves:</strong> Percentage of problems solved without progressing past the attempt lock or asking for tutor help.
              </div>
              <div>
                <strong className="text-slate-900 dark:text-white">2. Explanation Coverage:</strong> Rubric coverage verified during the validation teach-back or explanation phase.
              </div>
              <div>
                <strong className="text-slate-900 dark:text-white">3. Persistence Effort:</strong> Normalized active keystrokes, test runs, and time spent grappling before requesting tutor assistance.
              </div>
              <div>
                <strong className="text-slate-900 dark:text-white">4. Spaced Retention:</strong> Recall stability across SM-2 scheduled review cycles.
              </div>
              <div>
                <strong className="text-slate-900 dark:text-white">5. Consistency:</strong> Stylistic and syntactic alignment between your attempt code and your explanation vocabulary.
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowRadarModal(false)}
                className="px-4 py-2 bg-slate-900 text-white dark:bg-white dark:text-slate-900 rounded-lg text-xs font-semibold"
              >
                Got It
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
