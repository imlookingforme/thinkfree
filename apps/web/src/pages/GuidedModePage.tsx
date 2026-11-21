import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Send, Play, ShieldCheck, Sparkles,
  Code2, ArrowRight, RefreshCw, X
} from 'lucide-react';
import Editor from '@monaco-editor/react';

type RungType = 'guide' | 'hint' | 'help' | 'critical_hint';

interface Message {
  id: string;
  role: 'student' | 'tutor';
  rung?: RungType;
  content: string;
  leak_check?: {
    passed: boolean;
    method: string;
  };
  ts: string;
}

const RUNG_CONFIG: Record<RungType, { title: string; desc: string; weight: number }> = {
  guide: { title: 'Guide', desc: 'Socratic inquiry on concept', weight: 0.15 },
  hint: { title: 'Hint', desc: 'Points to direction or invariant', weight: 0.35 },
  help: { title: 'Help', desc: 'Conceptual walkthrough with other example', weight: 0.55 },
  critical_hint: { title: 'Critical Hint', desc: 'Next single atomic step', weight: 0.80 },
};

export const GuidedModePage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // Multi-tab question state (Screen 3 wireframe: "Question Area with tabs")
  const [tabs, setTabs] = useState([
    { id: '1', title: 'Two Sum Problem', active: true },
    { id: '2', title: 'Binary Search', active: false },
  ]);
  const [activeTab, setActiveTab] = useState<'statement' | 'scratchpad'>('statement');

  // Help ladder state
  const [selectedRung, setSelectedRung] = useState<RungType>('guide');
  const [inputMessage, setInputMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [helpCost, setHelpCost] = useState(0.50);
  const hintBudget = 6;

  // Socratic conversation thread
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'm1',
      role: 'student',
      rung: 'guide',
      content: 'I know nested loops will take O(n^2). How can I find the complement faster?',
      ts: '10:32 AM',
    },
    {
      id: 'm2',
      role: 'tutor',
      rung: 'guide',
      content:
        'Great insight on recognizing the quadratic overhead! Think about what data structure allows you to query whether an item has been previously seen in O(1) average time. What key-value mapping would make sense here?',
      leak_check: { passed: true, method: 'safe' },
      ts: '10:32 AM',
    },
  ]);

  // Editor and Code Execution
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState(`def two_sum(nums, target):
    lookup = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in lookup:
            return [lookup[diff], i]
        lookup[num] = i
    return []

# Testing with sample data
print(two_sum([2, 7, 11, 15], 9))
`);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState<string | null>(null);
  const [testResults] = useState<Array<{ name: string; passed: boolean; duration: string }>>([
    { name: 'Test Case 1: nums = [2,7,11,15], target = 9', passed: true, duration: '0.03s' },
    { name: 'Test Case 2: nums = [3,2,4], target = 6', passed: true, duration: '0.02s' },
    { name: 'Test Case 3: nums = [3,3], target = 6 (Hidden)', passed: true, duration: '0.04s' },
  ]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isGenerating) return;

    const studentMsg: Message = {
      id: `s-${Date.now()}`,
      role: 'student',
      rung: selectedRung,
      content: inputMessage,
      ts: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, studentMsg]);
    setInputMessage('');
    setIsGenerating(true);

    // Simulate backend call to /api/v1/sessions/{id}/tutor/message with LeakGuard verification
    setTimeout(() => {
      setIsGenerating(false);
      setHelpCost((prev) => +(prev + RUNG_CONFIG[selectedRung].weight).toFixed(2));

      let reply = '';
      if (selectedRung === 'guide') {
        reply = 'Consider what invariant holds before you insert each number into your dictionary. If `diff in lookup` is true, what do `lookup[diff]` and `i` represent?';
      } else if (selectedRung === 'hint') {
        reply = 'Remember: as you visit each index `i`, you want to check if `target - num` was already stored in previous steps.';
      } else if (selectedRung === 'help') {
        reply = 'Worked example in a different domain: If you need pairs of words totaling 10 letters, you store seen word lengths in a map `seen[len] = word`. When a word of length 4 arrives, you check for `10 - 4 = 6`. Here, the principle is identical using arithmetic differences.';
      } else {
        reply = 'Next atomic step: write `if diff in lookup: return [lookup[diff], i]`. Next, write `lookup[num] = i` right after the check.';
      }

      const tutorMsg: Message = {
        id: `t-${Date.now()}`,
        role: 'tutor',
        rung: selectedRung,
        content: reply,
        leak_check: { passed: true, method: 'safe' },
        ts: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, tutorMsg]);
    }, 900);
  };

  const handleElaborate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      setHelpCost((prev) => +(prev + 0.25).toFixed(2));
      const elaboratedMsg: Message = {
        id: `t-elab-${Date.now()}`,
        role: 'tutor',
        rung: selectedRung,
        content: 'To elaborate further: The key insight is that a single pass (O(n)) suffices because each element is either the first or the second number in the pair. When you encounter the second number, the first is guaranteed to already be in your hash map.',
        leak_check: { passed: true, method: 'safe' },
        ts: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, elaboratedMsg]);
    }, 700);
  };

  const handleRunCode = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      setOutput('[0, 1]\nExecution finished successfully (exit code 0).\nDuration: 42ms · Memory: 8.4MB');
    }, 600);
  };

  const tutorCount = messages.filter((m) => m.role === 'tutor').length;

  return (
    <div className="space-y-6">
      {/* Top Banner (Wireframe Screen 3 Header) */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-emerald-600" />
              <span>Guided Socratic Mode</span>
            </span>
            <span className="text-xs text-slate-500 font-mono">
              Help Cost: {helpCost} · Hints: {tutorCount}/{hintBudget}
            </span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            Two Sum: Find Indices of Target Sum
          </h1>
        </div>

        {/* Action: Proceed to Validation Phase (AI Locks Again) */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(`/validate/${id || 'demo'}`)}
            className="flex items-center gap-2 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-200 dark:text-slate-900 rounded-xl text-xs font-semibold shadow-sm transition"
          >
            <span>Proceed to Validation</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Screen 3 Grid (Left: Socratic Help Ladder & Questions; Right: Monaco Sandbox) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Panel: Tabs & Socratic Help functions */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm flex flex-col h-[640px]">
            {/* Top Multi-Problem Tabs */}
            <div className="flex items-center border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 px-2 pt-2 overflow-x-auto">
              {tabs.map((t) => (
                <div
                  key={t.id}
                  onClick={() => setTabs(tabs.map((tab) => ({ ...tab, active: tab.id === t.id })))}
                  className={`flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-t-lg cursor-pointer border-b-2 transition ${
                    t.active
                      ? 'border-slate-900 dark:border-white text-slate-900 dark:text-white bg-white dark:bg-slate-900'
                      : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  <span>{t.title}</span>
                  {tabs.length > 1 && <X className="w-3 h-3 hover:text-rose-500" />}
                </div>
              ))}
            </div>

            {/* Sub Tabs: Problem Statement vs Socratic Chat */}
            <div className="flex border-b border-slate-100 dark:border-slate-800 px-4 py-2 bg-white dark:bg-slate-900 text-xs gap-3">
              <button
                onClick={() => setActiveTab('statement')}
                className={`font-medium ${activeTab === 'statement' ? 'text-slate-900 dark:text-white border-b-2 border-slate-900 dark:border-white' : 'text-slate-500'}`}
              >
                Statement & Rubric
              </button>
              <button
                onClick={() => setActiveTab('scratchpad')}
                className={`font-medium ${activeTab === 'scratchpad' ? 'text-slate-900 dark:text-white border-b-2 border-slate-900 dark:border-white' : 'text-slate-500'}`}
              >
                Scratchpad
              </button>
            </div>

            {/* Socratic Ladder Rungs Selector */}
            <div className="p-3 bg-slate-50 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-800">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
                Help Ladder Rungs (Select Guidance Level)
              </div>
              <div className="grid grid-cols-4 gap-1.5">
                {(Object.keys(RUNG_CONFIG) as RungType[]).map((r) => {
                  const cfg = RUNG_CONFIG[r];
                  const isSel = selectedRung === r;
                  return (
                    <button
                      key={r}
                      onClick={() => setSelectedRung(r)}
                      className={`p-2 rounded-xl text-left border transition ${
                        isSel
                          ? 'border-slate-900 dark:border-white bg-white dark:bg-slate-900 shadow-sm'
                          : 'border-slate-200 dark:border-slate-700 bg-white/50 dark:bg-slate-800/50 hover:bg-white dark:hover:bg-slate-800'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                        <span>{cfg.title}</span>
                        <span className="text-[10px] font-mono text-slate-400">+{cfg.weight}</span>
                      </div>
                      <div className="text-[10px] text-slate-500 truncate mt-0.5">{cfg.desc}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Message Thread */}
            <div className="p-4 flex-1 overflow-y-auto space-y-3 text-xs leading-relaxed">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex flex-col ${m.role === 'student' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[88%] p-3 rounded-2xl ${
                      m.role === 'student'
                        ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 rounded-br-sm'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-sm border border-slate-200/50 dark:border-slate-700'
                    }`}
                  >
                    {m.role === 'tutor' && (
                      <div className="flex items-center gap-1.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 mb-1">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Socratic Guard Verified · {m.rung?.toUpperCase()}</span>
                      </div>
                    )}
                    <p className="whitespace-pre-wrap">{m.content}</p>
                  </div>
                  <span className="text-[10px] text-slate-400 px-1 mt-1">{m.ts}</span>
                </div>
              ))}
              {isGenerating && (
                <div className="flex items-center gap-2 text-xs text-slate-400 italic">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Socratic tutor formulating pedagogical hint...</span>
                </div>
              )}
            </div>

            {/* Bottom Input & Elaborate Button */}
            <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={handleElaborate}
                  disabled={isGenerating || messages.length === 0}
                  className="text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white underline flex items-center gap-1"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>Elaborate last response</span>
                </button>
                <span className="text-[11px] text-slate-400">
                  {hintBudget - tutorCount} hints remaining
                </span>
              </div>

              <form onSubmit={handleSendMessage} className="relative flex items-center">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={`Ask tutor (${selectedRung} mode)...`}
                  className="w-full pl-3 pr-10 py-2.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
                <button
                  type="submit"
                  disabled={isGenerating || !inputMessage.trim()}
                  className="absolute right-1.5 p-1.5 bg-slate-900 text-white dark:bg-white dark:text-slate-900 rounded-lg disabled:opacity-40"
                  aria-label="Send Message"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Right Panel: Monaco Sandbox & Test Execution */}
        <div className="lg:col-span-7 flex flex-col space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm flex flex-col h-[640px]">
            {/* Editor Action Bar */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
              <div className="flex items-center gap-3">
                <Code2 className="w-4 h-4 text-slate-500" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="text-xs bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1 font-mono text-slate-800 dark:text-slate-200"
                >
                  <option value="python">Python 3.11</option>
                  <option value="javascript">JavaScript (Node 20)</option>
                  <option value="cpp">C++ (GCC 12)</option>
                  <option value="c">C (GCC 12)</option>
                  <option value="java">Java 17</option>
                </select>
              </div>

              <button
                onClick={handleRunCode}
                disabled={isRunning}
                className="flex items-center gap-1.5 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-200 dark:text-slate-900 rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{isRunning ? 'Executing...' : 'Run Program'}</span>
              </button>
            </div>

            {/* Monaco Editor */}
            <div className="flex-1">
              <Editor
                height="100%"
                language={language}
                value={code}
                onChange={(val) => setCode(val || '')}
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

            {/* Execution Output & Test Results */}
            <div className="border-t border-slate-200 dark:border-slate-800 p-4 bg-slate-950 text-slate-200 font-mono text-xs max-h-48 overflow-y-auto space-y-2">
              <div className="flex items-center justify-between text-slate-400 border-b border-slate-800 pb-1">
                <span>Output & Test Suite Results</span>
                <span className="text-[10px] text-emerald-400">All 3 Tests Passed (0.09s)</span>
              </div>

              {/* Test cases list */}
              <div className="space-y-1">
                {testResults.map((t, idx) => (
                  <div key={idx} className="flex items-center justify-between text-[11px] py-0.5">
                    <span className="text-slate-300">✓ {t.name}</span>
                    <span className="text-slate-500">{t.duration}</span>
                  </div>
                ))}
              </div>

              {output && (
                <div className="pt-2 border-t border-slate-800 text-slate-400">
                  <pre className="whitespace-pre-wrap">{output}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
