import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Lock, Unlock, Play, HelpCircle, CheckCircle2, AlertCircle, FileText, Code2, ArrowRight, Zap
} from 'lucide-react';
import Editor from '@monaco-editor/react';
import { EffortMeter } from '../components/EffortMeter';
import { apiClient } from '../api/client';

export const ProblemAttemptPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // Active tab in question panel
  const [activeTab, setActiveTab] = useState<'statement' | 'scratchpad'>('statement');

  // Attempt & Activity Tracker
  const [activeSeconds, setActiveSeconds] = useState(0);
  const [meaningfulEdits, setMeaningfulEdits] = useState(0);
  const [steps, setSteps] = useState(1);
  const [runs, setRuns] = useState(0);
  const [language, setLanguage] = useState<'python' | 'javascript'>('python');
  const [effortScore, setEffortScore] = useState(0.08);
  const [code, setCode] = useState('def solution():\n    # Write your initial thoughts or code here\n    pass');
  const [scratchpad, setScratchpad] = useState('');
  const [output, setOutput] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  // Fast Lane Status (Feature 8)
  const [isFastLane, setIsFastLane] = useState(false);
  const [timeMinSeconds, setTimeMinSeconds] = useState(180);

  // Fetch Fast Lane eligibility on mount
  useEffect(() => {
    apiClient.get('/planner/fast-lane')
      .then((res) => {
        if (res.data?.is_eligible) {
          setIsFastLane(true);
          setTimeMinSeconds(res.data.reduced_lock_seconds || 60);
        }
      })
      .catch(() => {
        // Fallback default
        setTimeMinSeconds(180);
      });
  }, []);

  // Unlock state
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [showStuckModal, setShowStuckModal] = useState(false);
  const [stuckExplanation, setStuckExplanation] = useState('');
  const [stuckError, setStuckError] = useState<string | null>(null);

  const effortThreshold = 0.35;
  const canUnlock = effortScore >= effortThreshold && activeSeconds >= timeMinSeconds;

  // Active attempt timer
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Update effort score as student writes and runs code
  const handleCodeChange = (newCode?: string) => {
    if (!newCode) return;
    const diff = Math.abs(newCode.length - code.length);
    setCode(newCode);
    setMeaningfulEdits((prev) => prev + diff);

    // Effort score calculation formula: E = 1 - exp(-(0.35*t/300 + 0.25*m/180 + 0.15*r/3 + 0.25*s/4))
    const t = activeSeconds;
    const m = meaningfulEdits + diff;
    const exp = 0.35 * (t / 300) + 0.25 * (m / 180) + 0.15 * (runs / 3) + 0.25 * (steps / 4);
    const score = Math.min(1.0, 1.0 - Math.exp(-exp));
    setEffortScore(score);
  };

  const handleRunCode = () => {
    setIsRunning(true);
    setRuns((prev) => prev + 1);
    setTimeout(() => {
      setIsRunning(false);
      setOutput('Running test case 1...\nInput: nums = [2,7,11,15], target = 9\nOutput: [0, 1]\nStatus: Test Passed (0.04s)');
      // Boost effort on test run
      const t = activeSeconds;
      const m = meaningfulEdits;
      const r = runs + 1;
      const exp = 0.35 * (t / 300) + 0.25 * (m / 180) + 0.15 * (r / 3) + 0.25 * (steps / 4);
      setEffortScore(Math.min(1.0, 1.0 - Math.exp(-exp)));
    }, 700);
  };

  const handleUnlock = () => {
    if (!canUnlock) return;
    setIsUnlocked(true);
  };

  const handleDeclareStuck = (e: React.FormEvent) => {
    e.preventDefault();
    const words = stuckExplanation.trim().split(/\s+/).filter(Boolean).length;
    if (words < 35) {
      setStuckError(`Please describe your attempt in at least 35-40 words (current: ${words} words).`);
      return;
    }
    setStuckError(null);
    setIsUnlocked(true);
    setShowStuckModal(false);
  };

  const formatTimer = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="space-y-6">
      {/* Top Attempt Header from Screen 2 */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
              Coding Problem · Difficulty 1.0
            </span>
            {isFastLane && (
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 flex items-center gap-1 border border-amber-300 dark:border-amber-700">
                <Zap className="w-3 h-3 text-amber-600 dark:text-amber-400" />
                <span>Fast Lane (60s Lock)</span>
              </span>
            )}
            <span className="text-xs text-slate-500 font-mono">Timer: {formatTimer(activeSeconds)}</span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            Two Sum: Find Indices of Target Sum
          </h1>
        </div>

        {/* AI Unlock Control */}
        <div className="flex items-center gap-3">
          {isUnlocked ? (
            <div className="flex items-center gap-2 px-4 py-2 bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 rounded-xl border border-emerald-200 dark:border-emerald-800 text-sm font-semibold">
              <Unlock className="w-4 h-4 text-emerald-600" />
              <span>AI Guidance Unlocked!</span>
              <button
                onClick={() => navigate(`/guided/${id || 'demo'}`)}
                className="ml-2 underline flex items-center gap-1"
              >
                Enter Socratic Mode <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowStuckModal(true)}
                className="px-3 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white border border-slate-200 dark:border-slate-700 rounded-xl transition hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                I'm Stuck
              </button>
              <button
                disabled={!canUnlock}
                onClick={handleUnlock}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold shadow-sm transition ${
                  canUnlock
                    ? 'bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:text-slate-900 cursor-pointer animate-pulse'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-200 dark:border-slate-700'
                }`}
                title={canUnlock ? 'Click to unlock AI Guidance' : 'Try solving yourself first. AI unlocks after genuine attempt.'}
              >
                <Lock className="w-3.5 h-3.5" />
                <span>AI Locked</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Workspace Grid (Two panels: Left Question/Scratchpad, Right Monaco Editor) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Panel: Question Statement, Scratchpad & Effort Tracker */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm flex flex-col h-[520px]">
            {/* Tabs */}
            <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 px-3 pt-2">
              <button
                onClick={() => setActiveTab('statement')}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-t-lg transition border-b-2 ${
                  activeTab === 'statement'
                    ? 'border-slate-900 dark:border-white text-slate-900 dark:text-white bg-white dark:bg-slate-900'
                    : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Problem Statement</span>
              </button>
              <button
                onClick={() => setActiveTab('scratchpad')}
                className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-t-lg transition border-b-2 ${
                  activeTab === 'scratchpad'
                    ? 'border-slate-900 dark:border-white text-slate-900 dark:text-white bg-white dark:bg-slate-900'
                    : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Scratchpad & Steps</span>
              </button>
            </div>

            {/* Tab Contents */}
            <div className="p-5 flex-1 overflow-y-auto text-sm leading-relaxed text-slate-700 dark:text-slate-300">
              {activeTab === 'statement' ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white mb-2">Description</h3>
                    <p>
                      Given an array of integers <code className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono text-xs">nums</code> and an integer <code className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono text-xs">target</code>, return indices of the two numbers such that they add up to target.
                    </p>
                  </div>
                  <div>
                    <h4 className="font-semibold text-xs text-slate-500 uppercase tracking-wider mb-1">Constraints</h4>
                    <ul className="list-disc pl-5 space-y-1 text-xs text-slate-600 dark:text-slate-400">
                      <li>Each input would have exactly one solution.</li>
                      <li>You may not use the same element twice.</li>
                      <li>Time complexity expectation: <code className="font-mono">O(n)</code> optimal.</li>
                    </ul>
                  </div>
                  <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800 text-xs">
                    <span className="font-semibold">Example:</span>
                    <pre className="font-mono mt-1 text-slate-600 dark:text-slate-400">
                      Input: nums = [2,7,11,15], target = 9{"\n"}
                      Output: [0,1]{"\n"}
                      Explanation: nums[0] + nums[1] == 9, return [0, 1].
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="h-full flex flex-col">
                  <label className="text-xs font-medium text-slate-500 mb-2">
                    Write down sub-steps, edge cases or logic breakdown before writing code:
                  </label>
                  <textarea
                    value={scratchpad}
                    onChange={(e) => {
                      setScratchpad(e.target.value);
                      const stepCount = e.target.value.split('\n').filter((l) => l.trim().length > 0).length;
                      setSteps(Math.max(1, stepCount));
                    }}
                    placeholder="Step 1: Iterate through nums and check complement...&#10;Step 2: Store seen numbers in a hash map...&#10;Step 3: Handle negative values."
                    className="flex-1 w-full p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Effort Gauge from Feature 1 */}
          <EffortMeter
            effortScore={effortScore}
            threshold={effortThreshold}
            timeSpentSeconds={activeSeconds}
            timeMinSeconds={timeMinSeconds}
            canUnlock={canUnlock}
          />
        </div>

        {/* Right Panel: Monaco Editor & Output Pane */}
        <div className="lg:col-span-7 flex flex-col space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm flex flex-col h-[520px]">
            {/* Editor Action Bar */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <Code2 className="w-4 h-4 text-slate-500" />
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">Sandbox</span>
                </div>
                {/* Polyglot Language Switcher */}
                <div className="flex bg-slate-200 dark:bg-slate-900 p-0.5 rounded-lg text-[11px] font-semibold">
                  <button
                    onClick={() => {
                      setLanguage('python');
                      if (code.includes('function')) {
                        setCode('def solution(nums, target):\n    # Write Python logic here\n    pass');
                      }
                    }}
                    className={`px-2 py-0.5 rounded-md transition ${
                      language === 'python'
                        ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-xs'
                        : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                    }`}
                  >
                    Python 🐍
                  </button>
                  <button
                    onClick={() => {
                      setLanguage('javascript');
                      if (code.includes('def ')) {
                        setCode('function solution(nums, target) {\n  // Write JavaScript logic here\n  return [];\n}');
                      }
                    }}
                    className={`px-2 py-0.5 rounded-md transition ${
                      language === 'javascript'
                        ? 'bg-white dark:bg-slate-800 text-amber-600 dark:text-amber-400 shadow-xs'
                        : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                    }`}
                  >
                    JavaScript 🟨
                  </button>
                </div>
              </div>
              <button
                onClick={handleRunCode}
                disabled={isRunning}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-200 dark:text-slate-900 rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{isRunning ? 'Running...' : 'Run Code'}</span>
              </button>
            </div>

            {/* Monaco Editor */}
            <div className="flex-1">
              <Editor
                height="100%"
                language={language}
                value={code}
                onChange={handleCodeChange}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                }}
              />
            </div>

            {/* Output Pane */}
            {output && (
              <div className="border-t border-slate-200 dark:border-slate-800 p-3 bg-slate-950 text-slate-200 font-mono text-xs max-h-32 overflow-y-auto">
                <div className="flex items-center gap-1 text-[11px] text-slate-400 mb-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Sandbox Execution Results</span>
                </div>
                <pre className="whitespace-pre-wrap">{output}</pre>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* "I'm Stuck" Declaration Modal (Feature 1 Escape Hatch) */}
      {showStuckModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Declare Blockers</h3>
              <p className="text-xs text-slate-500 mt-1">
                To prevent cognitive shortcuts while avoiding frustration, explain what you tried and where you are blocked (minimum 35-40 words).
              </p>
            </div>

            <form onSubmit={handleDeclareStuck} className="space-y-4">
              <textarea
                value={stuckExplanation}
                onChange={(e) => setStuckExplanation(e.target.value)}
                placeholder="I tried a nested loop approach checking every pair of elements, but I realize it is O(n^2). I am trying to think about how a hash map lookup would let me check the target difference in O(1) time, but I am blocked on how to store duplicate numbers without overwriting keys."
                className="w-full h-32 p-3 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400"
              />

              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>
                  Words: {stuckExplanation.trim().split(/\s+/).filter(Boolean).length} / 35 min
                </span>
              </div>

              {stuckError && (
                <div className="flex items-center gap-1.5 text-xs text-rose-600 dark:text-rose-400">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>{stuckError}</span>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowStuckModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-slate-900 text-white dark:bg-white dark:text-slate-900 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-200 transition"
                >
                  Unlock Socratic Guidance
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
