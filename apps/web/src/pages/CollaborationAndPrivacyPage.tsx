import React, { useState } from 'react';
import {
  CheckSquare, Plus,
  ShieldCheck, Download, Trash2
} from 'lucide-react';
import { apiClient } from '../api/client';

export const CollaborationAndPrivacyPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'projects' | 'external_ai' | 'privacy'>('projects');

  // External AI reporting state
  const [toolName, setToolName] = useState('ChatGPT');
  const [purpose, setPurpose] = useState('');
  const [minutesUsed, setMinutesUsed] = useState(15);
  const [reportSuccess, setReportSuccess] = useState(false);

  // Privacy export status
  const [exportJson, setExportJson] = useState<string | null>(null);

  const handleReportAI = (e: React.FormEvent) => {
    e.preventDefault();
    apiClient.post('/collab/external-ai/report', {
      tool_name: toolName,
      purpose,
      minutes_used: minutesUsed
    }).then(() => {
      setReportSuccess(true);
      setTimeout(() => setReportSuccess(false), 3000);
      setPurpose('');
    });
  };

  const handleExportData = () => {
    apiClient.get('/collab/privacy/export').then((res) => {
      setExportJson(JSON.stringify(res.data, null, 2));
    });
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Banner */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
              Team Spaces & DPDP Privacy Centre
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Linear Collaboration & Data Sovereignty
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage multi-student projects with transparent AI policy and control your personal data rights under DPDP Act 2023.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
          <button
            onClick={() => setActiveTab('projects')}
            className={`px-3 py-1.5 rounded-lg transition ${
              activeTab === 'projects'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Team Projects
          </button>
          <button
            onClick={() => setActiveTab('external_ai')}
            className={`px-3 py-1.5 rounded-lg transition ${
              activeTab === 'external_ai'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            External AI Tracker
          </button>
          <button
            onClick={() => setActiveTab('privacy')}
            className={`px-3 py-1.5 rounded-lg transition ${
              activeTab === 'privacy'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            DPDP Privacy Rights
          </button>
        </div>
      </div>

      {/* Tab 1: Linear-Style Projects */}
      {activeTab === 'projects' && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">Capstone: Autonomous Compiler</h2>
                <span className="text-xs text-slate-400">Team Policy: Guided Socratic AI</span>
              </div>
              <button className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-xs font-semibold rounded-xl">
                <Plus className="w-3.5 h-3.5" />
                <span>New Task</span>
              </button>
            </div>

            {/* Linear-Style Task List */}
            <div className="space-y-2">
              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <CheckSquare className="w-4 h-4 text-emerald-500" />
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">Write Lexer Tokenizer with Regex Invariants</div>
                    <div className="text-[11px] text-slate-400">Assigned to Aarav · Policy: Locked AI · 100% unaided contribution</div>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-slate-200 dark:bg-slate-700">Done</span>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <div className="w-4 h-4 rounded-full border-2 border-slate-400" />
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">Construct LL(1) Parsing Table</div>
                    <div className="text-[11px] text-slate-400">Assigned to Diya · Policy: Guided Tutor Rungs · Attribution logged</div>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">In Progress</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: External AI Voluntary Self-Report */}
      {activeTab === 'external_ai' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm max-w-lg space-y-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Honest AI Usage Self-Report</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Did you use ChatGPT or Claude outside ThinkFree? Voluntary disclosures boost your Metacognitive Self-Awareness score.
            </p>
          </div>

          <form onSubmit={handleReportAI} className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">External Tool:</label>
              <select
                value={toolName}
                onChange={(e) => setToolName(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
              >
                <option value="ChatGPT">ChatGPT (OpenAI)</option>
                <option value="Claude">Claude (Anthropic)</option>
                <option value="GitHub Copilot">GitHub Copilot</option>
                <option value="Perplexity">Perplexity AI</option>
              </select>
            </div>

            <div>
              <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">What did you consult it for?</label>
              <textarea
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="e.g. Explaining compiler AST tree representation or syntax error clarification..."
                className="w-full h-20 p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 dark:text-slate-300 block mb-1">Estimated minutes used:</label>
              <input
                type="number"
                value={minutesUsed}
                onChange={(e) => setMinutesUsed(Number(e.target.value))}
                className="w-full p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800"
              />
            </div>

            <button
              type="submit"
              disabled={!purpose.trim()}
              className="px-5 py-2.5 bg-slate-900 text-white dark:bg-white dark:text-slate-900 rounded-xl font-semibold shadow-xs transition disabled:opacity-40"
            >
              Submit Self-Report (+5 pts awareness)
            </button>

            {reportSuccess && (
              <div className="p-3 bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 rounded-xl border border-emerald-200 text-xs font-semibold">
                Recorded. Thank you for your cognitive honesty!
              </div>
            )}
          </form>
        </div>
      )}

      {/* Tab 3: DPDP Act 2023 Privacy Rights */}
      {activeTab === 'privacy' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4 max-w-2xl">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
            <h2 className="text-base font-bold text-slate-900 dark:text-white">Your Privacy Rights (DPDP Act, 2023)</h2>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            ThinkFree is engineered around strict data minimization and purpose limitation. We never log raw key inputs, voice recordings are automatically deleted after 30 days, and you own your complete learning record.
          </p>

          <div className="flex gap-3 pt-2">
            <button
              onClick={handleExportData}
              className="flex items-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-xl text-xs font-semibold transition"
            >
              <Download className="w-4 h-4" />
              <span>Export Personal Telemetry (JSON)</span>
            </button>

            <button
              onClick={() => {
                if (confirm('Are you sure you want to request complete account deletion under DPDP Act 2023?')) {
                  apiClient.get('/collab/privacy/account');
                  alert('Account deletion initiated.');
                }
              }}
              className="flex items-center gap-2 px-4 py-2.5 bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 rounded-xl text-xs font-semibold transition hover:bg-rose-100"
            >
              <Trash2 className="w-4 h-4" />
              <span>Right to Erasure (Delete Account)</span>
            </button>
          </div>

          {exportJson && (
            <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-mono max-h-60 overflow-y-auto">
              <pre>{exportJson}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
