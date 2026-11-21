import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Mic, MicOff, Sparkles,
  ArrowRight, RefreshCw, Check, ShieldCheck, Lock, AlertTriangle
} from 'lucide-react';

interface RubricScore {
  item: string;
  score: number;
  evidence_span: string;
  feedback: string;
}

interface ConsistencyState {
  score: number;
  perplexity_ratio: number;
  vocab_overlap: number;
  anomaly_flag: boolean;
  plain_english: string;
  reasons: string[];
}

export const ValidationPage: React.FC = () => {
  const navigate = useNavigate();

  // Mode Selection
  const [mode, setMode] = useState<'explain' | 'similar'>('explain');

  // Explain Mode State
  const [explanation, setExplanation] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    passed: boolean;
    coverage: number;
    confidence: number;
    confidence_band: string;
    rubric_scores: RubricScore[];
    feedback_summary: string;
  } | null>(null);

  // Feature 5: Consistency & Contestability State
  const [consistency, setConsistency] = useState<ConsistencyState>({
    score: 0.94,
    perplexity_ratio: 1.15,
    vocab_overlap: 0.48,
    anomaly_flag: false,
    plain_english: "Your explanation is well-aligned with your problem-solving attempt.",
    reasons: []
  });
  const [showContestModal, setShowContestModal] = useState(false);
  const [contestNote, setContestNote] = useState('');
  const [contestSubmitted, setContestSubmitted] = useState(false);

  // Teach-back ("Confused Junior") State
  const [teachBackTurn, setTeachBackTurn] = useState(0);
  const [juniorQuestion, setJuniorQuestion] = useState<string | null>(null);
  const [juniorReply, setJuniorReply] = useState('');
  const [isJuniorReplying, setIsJuniorReplying] = useState(false);

  // Similar Problem State
  const [variantCode, setVariantCode] = useState('def two_sum_variant(nums, target):\n    # Solve without AI\n    pass');
  const [variantSubmitted, setVariantSubmitted] = useState(false);

  // Web Speech API for live transcription
  useEffect(() => {
    let recognition: any = null;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (SpeechRecognition && isRecording) {
      recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            setExplanation((prev) => `${prev} ${event.results[i][0].transcript}`.trim());
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        setLiveTranscript(interim);
      };

      recognition.onerror = () => setIsRecording(false);
      recognition.onend = () => setIsRecording(false);
      recognition.start();
    }

    return () => {
      if (recognition) recognition.stop();
    };
  }, [isRecording]);

  const toggleRecording = () => {
    setIsRecording(!isRecording);
  };

  const handleSubmitExplanation = (e: React.FormEvent) => {
    e.preventDefault();
    if (!explanation.trim() || isValidating) return;

    setIsValidating(true);
    // Simulate backend call to /api/v1/validations/{session_id}/explain
    setTimeout(() => {
      setIsValidating(false);
      const res = {
        passed: true,
        coverage: 0.85,
        confidence: 0.88,
        confidence_band: 'High',
        rubric_scores: [
          {
            item: 'Concept & Time Complexity Identification',
            score: 1.0,
            evidence_span: 'Instead of O(n^2) nested loops, we achieve O(n) using a hash map.',
            feedback: 'Accurately recognized computational complexity difference.'
          },
          {
            item: 'Step-by-Step Justification of Invariant',
            score: 1.0,
            evidence_span: 'We compute diff = target - num and check if it was previously stored.',
            feedback: 'Solid mathematical and algorithmic justification.'
          },
          {
            item: 'Outcome & Edge Cases',
            score: 0.5,
            evidence_span: 'Return pair of indices [lookup[diff], i].',
            feedback: 'Good explanation, could mention duplicate elements handling.'
          }
        ],
        feedback_summary: 'Strong conceptual understanding demonstrated. Logic is consistent with the submitted code.'
      };
      setValidationResult(res);

      // Feature 5: Evaluate real-time understanding consistency
      const explWords = explanation.trim().split(/\s+/).filter(Boolean).length;
      if (explWords > 40 && explanation.toLowerCase().includes("hash")) {
        setConsistency({
          score: 0.92,
          perplexity_ratio: 1.12,
          vocab_overlap: 0.45,
          anomaly_flag: false,
          plain_english: "Your explanation aligns with your submitted code and effort timeline.",
          reasons: []
        });
      }

      // Trigger Confused Junior follow-up question
      setTeachBackTurn(1);
      setJuniorQuestion("Wait, why can't we just sort the array first and use two pointers? Wouldn't that also avoid nested loops?");
    }, 1100);
  };

  const handleTeachBackAnswer = (e: React.FormEvent) => {
    e.preventDefault();
    if (!juniorReply.trim()) return;

    setIsJuniorReplying(true);
    setTimeout(() => {
      setIsJuniorReplying(false);
      if (teachBackTurn === 1) {
        setTeachBackTurn(2);
        setJuniorQuestion("Ah! So sorting takes O(n log n) time and also scrambles the original index positions needed for the answer, whereas the hash map preserves indices in O(n). That makes total sense now!");
      } else {
        setJuniorQuestion("You explained this brilliantly! Thank you.");
      }
      setJuniorReply('');
    }, 700);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner (Wireframe Screen 4: "Did you actually understand?") */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Lock className="w-3 h-3 text-slate-500" />
              <span>Phase 3: Validation (AI Locked)</span>
            </span>
            <div className="flex items-center gap-1.5 text-xs font-mono font-medium">
              <span className={consistency.anomaly_flag ? "text-amber-600 dark:text-amber-400 font-bold" : "text-emerald-600 dark:text-emerald-400"}>
                Consistency: {Math.round(consistency.score * 100)}% ({consistency.anomaly_flag ? 'Advisory Anomaly' : 'Aligned Reasoning'})
              </span>
              <button
                onClick={() => setShowContestModal(true)}
                className="underline text-[11px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                title="View fairness details or contest advisory"
              >
                (Contest / Details)
              </button>
            </div>
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            Did you actually understand?
          </h1>
          <p className="text-xs text-slate-500 mt-1 max-w-xl">
            Prove that you internalized the solution. Explain your reasoning by voice or solve an isomorphic variant.
          </p>
        </div>

        {/* Mode Toggle Tabs */}
        <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
          <button
            onClick={() => setMode('explain')}
            className={`px-3 py-1.5 rounded-lg transition ${
              mode === 'explain'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Explain Mode (Voice / Text)
          </button>
          <button
            onClick={() => setMode('similar')}
            className={`px-3 py-1.5 rounded-lg transition ${
              mode === 'similar'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Similar-Problem Mode
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Panel: Recap & Rubric Items */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm space-y-4">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1">
                Recap: Two Sum Problem
              </div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">
                Find indices [i, j] such that nums[i] + nums[j] == target
              </h2>
              <div className="text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800 mt-2 font-mono">
                Your submitted solution: O(n) hash map with single-pass difference check.
              </div>
            </div>

            {/* Rubric Checklist from wireframe */}
            <div>
              <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                Understanding Rubric
              </h3>
              <div className="space-y-2 text-xs">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800">
                  <div className="font-semibold text-slate-800 dark:text-slate-200">1. Conceptual Principle</div>
                  <p className="text-slate-500 text-[11px] mt-0.5">Identifies time complexity contrast between brute-force search and hash lookup.</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800">
                  <div className="font-semibold text-slate-800 dark:text-slate-200">2. Invariant Justification</div>
                  <p className="text-slate-500 text-[11px] mt-0.5">Explains why single pass is sufficient and why complement is looked up.</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-100 dark:border-slate-800">
                  <div className="font-semibold text-slate-800 dark:text-slate-200">3. Edge Case Ownership</div>
                  <p className="text-slate-500 text-[11px] mt-0.5">Accounts for distinct indices and same-element reuse restrictions.</p>
                </div>
              </div>
            </div>

            {/* Confidence Meter Widget */}
            {validationResult && (
              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">Confidence Meter</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                    validationResult.confidence_band === 'High'
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                      : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                  }`}>
                    {validationResult.confidence_band} ({Math.round(validationResult.confidence * 100)}%)
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-700"
                    style={{ width: `${Math.round(validationResult.confidence * 100)}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-500">
                  Calculated from coverage, specific domain terminology, and vocal fluency.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Explanation or Similar Problem Mode */}
        <div className="lg:col-span-7 space-y-4">
          {mode === 'explain' ? (
            <div className="space-y-4">
              {/* Voice / Text Explanation Input */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                    <span className="text-sm font-bold text-slate-900 dark:text-white">
                      Explain Your Solution
                    </span>
                  </div>
                  {/* Microphone Toggle */}
                  <button
                    type="button"
                    onClick={toggleRecording}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                      isRecording
                        ? 'bg-rose-500 text-white animate-pulse'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
                    }`}
                  >
                    {isRecording ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
                    <span>{isRecording ? 'Listening (Click to Stop)' : 'Voice Record'}</span>
                  </button>
                </div>

                {isRecording && (
                  <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-xl text-xs text-rose-800 dark:text-rose-300 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
                    <span>Transcribing live speech... Speak naturally explaining your reasoning.</span>
                  </div>
                )}

                <form onSubmit={handleSubmitExplanation} className="space-y-3">
                  <textarea
                    value={explanation}
                    onChange={(e) => setExplanation(e.target.value)}
                    placeholder="Explain in your own words: Why does your code work? What data structure was used, what is the time complexity, and how does it prevent duplicate index use?"
                    className="w-full h-40 p-4 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400 font-sans leading-relaxed"
                  />

                  {liveTranscript && (
                    <div className="text-xs text-slate-500 italic p-2 bg-slate-50 dark:bg-slate-800/30 rounded-lg">
                      "{liveTranscript}"
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-xs text-slate-400">
                      Word count: {explanation.trim().split(/\s+/).filter(Boolean).length} words
                    </span>
                    <button
                      type="submit"
                      disabled={isValidating || !explanation.trim()}
                      className="flex items-center gap-2 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-200 dark:text-slate-900 rounded-xl text-xs font-semibold shadow-sm transition disabled:opacity-40"
                    >
                      {isValidating ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Grading against rubric...</span>
                        </>
                      ) : (
                        <>
                          <span>Submit Explanation</span>
                          <Check className="w-3.5 h-3.5" />
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              {/* Validation Feedback & Rubric Results */}
              {validationResult && (
                <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4 animate-fadeIn">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-5 h-5 text-emerald-500" />
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white">Validation Assessment</h3>
                    </div>
                    <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300">
                      PASSED (Coverage {Math.round(validationResult.coverage * 100)}%)
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    {validationResult.feedback_summary}
                  </p>

                  {/* Rubric items breakdown with evidence spans */}
                  <div className="space-y-2">
                    {validationResult.rubric_scores.map((r, i) => (
                      <div key={i} className="p-3 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800 text-xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-slate-800 dark:text-slate-200">{r.item}</span>
                          <span className="font-mono text-emerald-600 font-bold">Score: {r.score}</span>
                        </div>
                        <div className="text-[11px] text-slate-500 italic mb-1">
                          Evidence: "{r.evidence_span}"
                        </div>
                        <div className="text-[11px] text-slate-600 dark:text-slate-400">
                          {r.feedback}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Teach-Back Sub-Mode ("Confused Junior") */}
                  {juniorQuestion && (
                    <div className="p-4 bg-slate-50 dark:bg-slate-800/70 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                      <div className="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-slate-200">
                        <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                        <span>Teach-Back Check ("Confused Junior" Peer)</span>
                      </div>
                      <p className="text-xs text-slate-600 dark:text-slate-300 italic">
                        "{juniorQuestion}"
                      </p>

                      {teachBackTurn < 2 && (
                        <form onSubmit={handleTeachBackAnswer} className="flex gap-2">
                          <input
                            type="text"
                            value={juniorReply}
                            onChange={(e) => setJuniorReply(e.target.value)}
                            placeholder="Clarify this for your junior peer..."
                            className="flex-1 px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900"
                          />
                          <button
                            type="submit"
                            disabled={isJuniorReplying || !juniorReply.trim()}
                            className="px-3 py-2 bg-slate-900 text-white dark:bg-white dark:text-slate-900 rounded-xl text-xs font-semibold"
                          >
                            Reply
                          </button>
                        </form>
                      )}
                    </div>
                  )}

                  {/* Complete Button */}
                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => navigate('/')}
                      className="flex items-center gap-2 px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-200 dark:text-slate-900 rounded-xl text-xs font-semibold shadow-sm transition"
                    >
                      <span>Complete & Update Scores</span>
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Similar-Problem Mode */
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    Isomorphic Problem Variant
                  </h3>
                  <p className="text-xs text-slate-500">
                    Same concept ({'Two Sum'}), changed context and search space. Solve without AI.
                  </p>
                </div>
                <span className="text-xs px-2.5 py-1 bg-slate-100 dark:bg-slate-800 rounded-full font-mono text-slate-600 dark:text-slate-400">
                  AI Locked
                </span>
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-100 dark:border-slate-800 text-xs space-y-2">
                <div className="font-semibold text-slate-900 dark:text-white">
                  Problem: Pair Target in Shifted Array
                </div>
                <p className="text-slate-600 dark:text-slate-400">
                  Given an array of temperatures `temps = [3, 9, 12, 18, 25]` and a threshold difference `diff = 15`, find the pair of indices whose values differ by exactly `diff`.
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-500">Your Solution Code:</label>
                <textarea
                  value={variantCode}
                  onChange={(e) => setVariantCode(e.target.value)}
                  className="w-full h-44 p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 font-mono text-xs focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-xs text-slate-500">
                  {variantSubmitted ? 'Tests executed: 3/3 passed.' : 'Submit to execute against test suite.'}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setVariantSubmitted(true);
                    setTimeout(() => navigate('/'), 1200);
                  }}
                  className="flex items-center gap-2 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-200 dark:text-slate-900 rounded-xl text-xs font-semibold shadow-sm transition"
                >
                  <span>Submit Variant Solution</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Feature 5: Contestability Modal Dialogue */}
      {showContestModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Understanding-Consistency & Fairness
                </h3>
                <span className="text-xs text-slate-500">ThinkFree Ethics Charter: Advisory & Contestable</span>
              </div>
              <button onClick={() => setShowContestModal(false)} className="text-slate-400 hover:text-slate-600">
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
              <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl space-y-1">
                <div className="flex justify-between font-semibold text-slate-900 dark:text-white">
                  <span>Consistency Score:</span>
                  <span>{Math.round(consistency.score * 100)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Vocabulary Overlap:</span>
                  <span>{Math.round(consistency.vocab_overlap * 100)}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Perplexity Divergence Ratio:</span>
                  <span>{consistency.perplexity_ratio}</span>
                </div>
              </div>

              <p className="leading-relaxed">
                {consistency.plain_english}
              </p>

              {consistency.reasons.length > 0 && (
                <div className="p-2.5 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 rounded-xl space-y-1 text-amber-800 dark:text-amber-300">
                  <div className="font-semibold flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Advisory Notes:</span>
                  </div>
                  {consistency.reasons.map((r, i) => (
                    <div key={i}>• {r}</div>
                  ))}
                </div>
              )}

              <div className="border-t border-slate-100 dark:border-slate-800 pt-3 space-y-2">
                <label className="font-semibold text-slate-900 dark:text-white block">
                  Contest this signal or provide offline context:
                </label>
                <textarea
                  value={contestNote}
                  onChange={(e) => setContestNote(e.target.value)}
                  placeholder="e.g. I solved this problem yesterday in my offline notebook, or used alternative mathematical terminology."
                  className="w-full h-20 p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs focus:outline-none focus:ring-2 focus:ring-slate-900"
                />
              </div>

              {contestSubmitted && (
                <div className="p-2.5 bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 rounded-xl border border-emerald-200 text-xs font-semibold">
                  Clarification recorded in audit trail. Advisory neutralized.
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowContestModal(false)}
                className="px-4 py-2 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-semibold"
              >
                Close
              </button>
              <button
                type="button"
                disabled={!contestNote.trim()}
                onClick={() => {
                  setContestSubmitted(true);
                  setTimeout(() => setShowContestModal(false), 1200);
                }}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:text-slate-900 rounded-xl text-xs font-semibold transition disabled:opacity-40"
              >
                Submit Clarification
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
