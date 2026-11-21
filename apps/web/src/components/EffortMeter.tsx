import React from 'react';
import { ShieldCheck, Lock } from 'lucide-react';

interface EffortMeterProps {
  effortScore: number; // 0.0 to 1.0
  threshold?: number;  // default 0.35
  timeSpentSeconds: number;
  timeMinSeconds?: number; // default 180 (3 min)
  canUnlock: boolean;
}

export const EffortMeter: React.FC<EffortMeterProps> = ({
  effortScore,
  threshold = 0.35,
  timeSpentSeconds,
  timeMinSeconds = 180,
  canUnlock
}) => {
  // Effort percentage towards unlock threshold
  const percentToUnlock = Math.min(100, Math.round((effortScore / threshold) * 100));
  const timeProgress = Math.min(100, Math.round((timeSpentSeconds / timeMinSeconds) * 100));

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div
      className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm transition-all"
      role="region"
      aria-label="Effort Meter"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {canUnlock ? (
            <ShieldCheck className="w-5 h-5 text-emerald-500" aria-hidden="true" />
          ) : (
            <Lock className="w-5 h-5 text-slate-400" aria-hidden="true" />
          )}
          <span className="font-semibold text-sm tracking-tight text-slate-800 dark:text-slate-200">
            Effort Tracker
          </span>
        </div>
        <span className="text-xs font-mono font-medium px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
          {formatTime(timeSpentSeconds)} / {formatTime(timeMinSeconds)}
        </span>
      </div>

      {/* Progress Bars */}
      <div className="space-y-2 mb-3">
        <div>
          <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
            <span>Cognitive Effort (E)</span>
            <span className="font-mono">{Math.round(effortScore * 100)}% / {Math.round(threshold * 100)}%</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                effortScore >= threshold ? 'bg-emerald-500' : 'bg-slate-700 dark:bg-slate-300'
              }`}
              style={{ width: `${Math.min(100, (effortScore / 1.0) * 100)}%` }}
              role="progressbar"
              aria-valuenow={Math.round(effortScore * 100)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Cognitive effort: ${Math.round(effortScore * 100)}%`}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
            <span>Time on Problem</span>
            <span className="font-mono">{timeProgress}%</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full bg-slate-400 dark:bg-slate-600 rounded-full transition-all duration-300"
              style={{ width: `${timeProgress}%` }}
              role="progressbar"
              aria-valuenow={timeProgress}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Time requirement: ${timeProgress}%`}
            />
          </div>
        </div>
      </div>

      {/* Status banner */}
      <div className="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800">
        {canUnlock ? (
          <p className="text-emerald-600 dark:text-emerald-400 font-medium">
            Threshold reached! You have put in the thinking work. AI guidance is ready to unlock.
          </p>
        ) : (
          <p>
            Keep going, you're <strong className="text-slate-900 dark:text-white">{percentToUnlock}%</strong> to unlocking guidance. Write steps or test code.
          </p>
        )}
      </div>
    </div>
  );
};
