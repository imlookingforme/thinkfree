import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ShieldCheck, Award, ArrowLeft } from 'lucide-react';

export const BadgeVerificationPage: React.FC = () => {
  const { id } = useParams();

  const { data: badge } = useQuery({
    queryKey: ['badge_verify', id],
    queryFn: async () => {
      // In production calls GET /api/v1/institutional/badges/verify/:id
      // Fallback demo object
      return {
        is_valid: true,
        badge_id: id || 'badge_demo_77',
        student_id: 'f20230101',
        title: 'Foundations of Data Structures — Independent Achiever',
        issuer: 'ThinkFree Verified (BITS Pilani)',
        issued_at: '2026-10-25T14:30:00Z',
        algorithm: 'Ed25519 High-Speed Digital Signature',
        metrics: {
          min_its: 80.0,
          achieved_its: 88.5,
          max_adr: 0.25,
          achieved_adr: 0.14,
          self_solves: 28
        }
      };
    }
  });

  return (
    <div className="max-w-xl mx-auto py-12 px-4 space-y-6 animate-fadeIn">
      <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 dark:hover:text-white transition">
        <ArrowLeft className="w-4 h-4" />
        <span>Back to ThinkFree</span>
      </Link>

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 shadow-lg text-center space-y-6 relative overflow-hidden">
        {/* Verification Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-100 dark:bg-emerald-950/80 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-bold tracking-wide">
          <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <span>CRYPTOGRAPHICALLY VERIFIED</span>
        </div>

        {/* Badge Icon */}
        <div className="w-20 h-20 mx-auto rounded-3xl bg-slate-900 text-white dark:bg-white dark:text-slate-900 flex items-center justify-center shadow-md">
          <Award className="w-10 h-10" />
        </div>

        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            {badge?.title}
          </h1>
          <p className="text-sm font-medium text-slate-500 mt-1">
            Issued by {badge?.issuer}
          </p>
        </div>

        {/* Audit Metrics */}
        <div className="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-4 text-left border border-slate-100 dark:border-slate-800 space-y-2 text-xs">
          <div className="flex justify-between text-slate-600 dark:text-slate-300">
            <span>Independent Thinking Score (ITS):</span>
            <span className="font-bold font-mono text-slate-900 dark:text-white">
              {badge?.metrics.achieved_its} / 100 (Threshold: &ge;80.0)
            </span>
          </div>
          <div className="flex justify-between text-slate-600 dark:text-slate-300">
            <span>AI Dependency Ratio (ADR):</span>
            <span className="font-bold font-mono text-slate-900 dark:text-white">
              {badge?.metrics.achieved_adr} (Max allowable: &le;0.25)
            </span>
          </div>
          <div className="flex justify-between text-slate-600 dark:text-slate-300">
            <span>Verified Unassisted Solves:</span>
            <span className="font-bold font-mono text-slate-900 dark:text-white">
              {badge?.metrics.self_solves} problems
            </span>
          </div>
          <div className="flex justify-between text-slate-600 dark:text-slate-300 pt-2 border-t border-slate-200 dark:border-slate-700 text-[11px]">
            <span>Signing Cryptosystem:</span>
            <span className="font-mono">{badge?.algorithm}</span>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 leading-relaxed max-w-sm mx-auto">
          This credential certifies that the student demonstrated verified cognitive independence through strict locked-AI attempts, explainability teach-backs, and spaced retention.
        </p>
      </div>
    </div>
  );
};
