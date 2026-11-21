import React, { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import {
  Sparkles,
  Key,
  CheckCircle2,
  Eye,
  EyeOff,
  Cpu,
  ArrowRight,
  Power
} from 'lucide-react';

interface AIProviderInfo {
  provider: string;
  name: string;
  is_enabled: boolean;
  is_active: boolean;
  has_key: boolean;
  model: string;
  available_models: string[];
  masked_key?: string | null;
}

interface AIProvidersResponse {
  active_provider: string;
  providers: AIProviderInfo[];
}

export const AIOnboardingModal: React.FC = () => {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [models, setModels] = useState<Record<string, string>>({});
  const [enabledState, setEnabledState] = useState<Record<string, boolean>>({});
  const [selectedActive, setSelectedActive] = useState<string>('gemini');
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Fetch current provider states from server
  const { data: aiData, isLoading } = useQuery<AIProvidersResponse>({
    queryKey: ['ai-providers'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/providers');
      return res.data;
    },
  });

  const providersList: any[] = Array.isArray(aiData) ? aiData : (aiData?.providers || []);

  useEffect(() => {
    // Check if onboarding was already completed
    const onboarded = localStorage.getItem('thinkfree_ai_onboarded');
    if (!onboarded) {
      setIsOpen(true);
    }
  }, []);

  useEffect(() => {
    if (aiData) {
      const active = Array.isArray(aiData)
        ? (aiData.find((p: any) => p.is_active)?.id || 'gemini')
        : (aiData.active_provider || 'gemini');
      setSelectedActive(active);
      const initialModels: Record<string, string> = {};
      const initialEnabled: Record<string, boolean> = {};
      providersList.forEach((p: any) => {
        const pid = p.provider || p.id;
        initialModels[pid] = p.model || p.model_name || '';
        initialEnabled[pid] = p.is_enabled;
      });
      setModels(initialModels);
      setEnabledState(initialEnabled);
    }
  }, [aiData]);

  // Listen to custom event to open modal from anywhere (e.g. Navbar)
  useEffect(() => {
    const handleOpen = () => setIsOpen(true);
    window.addEventListener('open-ai-onboarding', handleOpen);
    return () => window.removeEventListener('open-ai-onboarding', handleOpen);
  }, []);

  const handleKeyChange = (provider: string, val: string) => {
    setKeys((prev) => ({ ...prev, [provider]: val }));
    // Auto-enable if user enters a key
    if (val.trim().length > 0) {
      setEnabledState((prev) => ({ ...prev, [provider]: true }));
    }
  };

  const handleToggleShowKey = (provider: string) => {
    setShowKey((prev) => ({ ...prev, [provider]: !prev[provider] }));
  };

  const handleDismiss = () => {
    localStorage.setItem('thinkfree_ai_onboarded', 'true');
    setIsOpen(false);
  };

  const handleSaveAndStart = async () => {
    setIsSaving(true);
    try {
      for (const p of providersList) {
        const pid = p.provider || p.id;
        const newKey = keys[pid];
        const chosenModel = models[pid] || p.model || p.model_name;
        const isEnabled = enabledState[pid] ?? p.is_enabled;

        // Send update if key entered or model/enabled changed
        await apiClient.post('/ai/providers/update', {
          provider_id: pid,
          provider: pid,
          api_key: newKey && newKey.trim() ? newKey.trim() : undefined,
          model_name: chosenModel,
          model: chosenModel,
          is_enabled: isEnabled,
        });
      }

      // Switch to the selected active provider
      if (selectedActive) {
        await apiClient.post('/ai/providers/switch', {
          provider_id: selectedActive,
          provider: selectedActive,
          model: models[selectedActive],
        });
      }

      await queryClient.invalidateQueries({ queryKey: ['ai-providers'] });
      localStorage.setItem('thinkfree_ai_onboarded', 'true');
      setSavedSuccess(true);
      setTimeout(() => {
        setSavedSuccess(false);
        setIsOpen(false);
      }, 1000);
    } catch (err) {
      console.error('Failed to save AI configuration', err);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-white dark:bg-[#0c101b] border border-slate-200/80 dark:border-white/[0.08] rounded-3xl shadow-2xl p-6 sm:p-8 my-8 text-slate-900 dark:text-slate-100 animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="mb-6 pb-6 border-b border-slate-100 dark:border-white/[0.06]">
          <div className="flex items-center gap-2 mb-3">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-mono uppercase tracking-widest bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 font-bold">
              <Sparkles className="w-3 h-3 animate-pulse" />
              Sovereign AI Router
            </span>
            <span className="text-slate-400 dark:text-slate-600 text-xs font-mono">• Zero Key Loss Engine</span>
          </div>

          <h2 className="text-2xl font-extrabold tracking-tight font-sans">
            Configure Your AI Engines
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1.5 leading-relaxed">
            ThinkFree puts you in control. Add your API keys below to unlock multi-model Socratic tutoring. Disabling a model never purges your key from the server.
          </p>
        </div>

        {/* Provider List */}
        {isLoading ? (
          <div className="py-16 text-center text-xs font-mono text-slate-400 animate-pulse">
            Querying provider registry...
          </div>
        ) : (
          <div className="space-y-3 max-h-[50vh] overflow-y-auto pr-2">
            {providersList.map((p: any) => {
              const pid = p.provider || p.id;
              const hasConfigured = p.has_key || (keys[pid] && keys[pid].length > 0);
              const isEnabled = enabledState[pid] ?? p.is_enabled;
              const isSelectedActive = selectedActive === pid;
              const availModels: string[] = p.available_models && p.available_models.length > 0
                ? p.available_models
                : [p.model || p.model_name || 'default'];

              return (
                <div
                  key={pid}
                  className={`p-4 rounded-2xl border transition-all duration-200 ${
                    isSelectedActive
                      ? 'border-indigo-500/80 bg-indigo-500/[0.04] dark:bg-indigo-500/[0.06] shadow-sm'
                      : 'border-slate-200/60 dark:border-white/[0.05] bg-slate-50/50 dark:bg-white/[0.02] hover:border-slate-300 dark:hover:border-white/[0.09]'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className={`p-2 rounded-xl ${
                        isSelectedActive
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 dark:bg-white/[0.05] text-slate-600 dark:text-slate-400'
                      }`}>
                        <Cpu className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm tracking-tight">{p.name}</span>
                          {isSelectedActive && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border border-indigo-500/30">
                              Active
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                          {hasConfigured ? (
                            <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3" />
                              Key stored {p.masked_key ? `(${p.masked_key})` : ''}
                            </span>
                          ) : (
                            <span className="text-slate-400 dark:text-slate-500">No key set</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end sm:self-auto">
                      {/* Enable/Disable Toggle */}
                      <button
                        type="button"
                        onClick={() =>
                          setEnabledState((prev) => ({
                            ...prev,
                            [pid]: !isEnabled,
                          }))
                        }
                        className={`text-xs px-2.5 py-1.5 rounded-lg font-mono font-medium flex items-center gap-1.5 border transition-all ${
                          isEnabled
                            ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20'
                            : 'bg-slate-100 dark:bg-white/[0.05] text-slate-400 border-slate-200 dark:border-white/[0.08]'
                        }`}
                        title="Disabling keeps key saved on server"
                      >
                        <Power className="w-3 h-3" />
                        <span>{isEnabled ? 'Enabled' : 'Disabled'}</span>
                      </button>

                      {/* Select as Active */}
                      <button
                        type="button"
                        disabled={!isEnabled && !hasConfigured}
                        onClick={() => {
                          setSelectedActive(pid);
                          setEnabledState((prev) => ({ ...prev, [pid]: true }));
                        }}
                        className={`text-xs px-3 py-1.5 rounded-lg font-mono font-semibold border transition-all ${
                          isSelectedActive
                            ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                            : 'bg-white dark:bg-white/[0.04] text-slate-700 dark:text-slate-300 border-slate-200 dark:border-white/[0.08] hover:border-indigo-500/50 disabled:opacity-30'
                        }`}
                      >
                        {isSelectedActive ? 'Active' : 'Set Active'}
                      </button>
                    </div>
                  </div>

                  {/* Input fields */}
                  <div className="grid grid-cols-1 sm:grid-cols-12 gap-2.5 mt-2">
                    <div className="sm:col-span-8 relative">
                      <Key className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400 pointer-events-none" />
                      <input
                        type={showKey[pid] ? 'text' : 'password'}
                        placeholder={p.has_key ? 'Replace saved API key...' : 'Paste API Key (sk-..., AQ...)'}
                        value={keys[pid] || ''}
                        onChange={(e) => handleKeyChange(pid, e.target.value)}
                        className="w-full pl-8 pr-9 py-2 text-xs rounded-xl border border-slate-200 dark:border-white/[0.08] bg-white dark:bg-black/40 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                      />
                      <button
                        type="button"
                        onClick={() => handleToggleShowKey(pid)}
                        className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                      >
                        {showKey[pid] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      </button>
                    </div>

                    <div className="sm:col-span-4">
                      <select
                        value={models[pid] || p.model || p.model_name || ''}
                        onChange={(e) =>
                          setModels((prev) => ({ ...prev, [pid]: e.target.value }))
                        }
                        className="w-full py-2 px-2.5 text-xs rounded-xl border border-slate-200 dark:border-white/[0.08] bg-white dark:bg-black/40 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                      >
                        {availModels.map((m) => (
                          <option key={m} value={m} className="bg-slate-900 text-white">
                            {m}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer Actions */}
        <div className="mt-6 pt-5 border-t border-slate-100 dark:border-white/[0.06] flex flex-col sm:flex-row items-center justify-between gap-3">
          <button
            type="button"
            onClick={handleDismiss}
            className="text-xs font-mono text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
          >
            Skip for now → Use active default
          </button>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={handleSaveAndStart}
              disabled={isSaving}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              {savedSuccess ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                  <span>Configured & Ready!</span>
                </>
              ) : (
                <>
                  <span>{isSaving ? 'Saving...' : 'Save & Launch Workspace'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
