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
  ShieldCheck,
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl p-6 md:p-8 my-8 text-slate-900 dark:text-slate-100 animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-start gap-4 mb-6 pb-6 border-b border-slate-200 dark:border-slate-800">
          <div className="p-3 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 rounded-xl">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight">Configure Your AI Engines</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              ThinkFree supports multiple AI backends for Socratic tutoring and validation. Provide your API keys below to unlock them.
            </p>
            <div className="flex items-center gap-2 mt-2 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-3 py-1.5 rounded-lg border border-amber-200 dark:border-amber-800/60">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>
                <strong>Zero Key Loss:</strong> Disabling an AI preserves your key on the server. You can toggle providers anytime without re-entering keys!
              </span>
            </div>
          </div>
        </div>

        {/* Provider List */}
        {isLoading ? (
          <div className="py-12 text-center text-slate-500">Loading AI providers...</div>
        ) : (
          <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-2">
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
                  className={`p-4 rounded-xl border transition-all ${
                    isSelectedActive
                      ? 'border-indigo-500 bg-indigo-50/30 dark:bg-indigo-950/20'
                      : 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-slate-500" />
                      <span className="font-semibold text-sm">{p.name}</span>
                      {hasConfigured ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                          <CheckCircle2 className="w-3 h-3" />
                          Key saved {p.masked_key ? `(${p.masked_key})` : ''}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
                          Not configured
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Enable/Disable Toggle */}
                      <button
                        type="button"
                        onClick={() =>
                          setEnabledState((prev) => ({
                            ...prev,
                            [pid]: !isEnabled,
                          }))
                        }
                        className={`text-xs px-2.5 py-1 rounded-md font-medium flex items-center gap-1 border transition-colors ${
                          isEnabled
                            ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-500 border-slate-300 dark:border-slate-700'
                        }`}
                        title="Disabling keeps key saved in memory/settings"
                      >
                        <Power className="w-3 h-3" />
                        {isEnabled ? 'Enabled' : 'Disabled'}
                      </button>

                      {/* Select as Active radio */}
                      <button
                        type="button"
                        disabled={!isEnabled && !hasConfigured}
                        onClick={() => {
                          setSelectedActive(pid);
                          setEnabledState((prev) => ({ ...prev, [pid]: true }));
                        }}
                        className={`text-xs px-2.5 py-1 rounded-md font-medium border transition-colors ${
                          isSelectedActive
                            ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                            : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:border-indigo-400 disabled:opacity-40'
                        }`}
                      >
                        {isSelectedActive ? 'Active Engine' : 'Set as Active'}
                      </button>
                    </div>
                  </div>

                  {/* Input fields */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                    <div className="sm:col-span-2 relative">
                      <div className="flex items-center">
                        <Key className="w-3.5 h-3.5 absolute left-3 text-slate-400 pointer-events-none" />
                        <input
                          type={showKey[pid] ? 'text' : 'password'}
                          placeholder={p.has_key ? 'Enter new key to replace existing' : 'Paste API Key (e.g. sk-..., AQ...)'}
                          value={keys[pid] || ''}
                          onChange={(e) => handleKeyChange(pid, e.target.value)}
                          className="w-full pl-8 pr-9 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                        />
                        <button
                          type="button"
                          onClick={() => handleToggleShowKey(pid)}
                          className="absolute right-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                        >
                          {showKey[pid] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>

                    <div>
                      <select
                        value={models[pid] || p.model || p.model_name || ''}
                        onChange={(e) =>
                          setModels((prev) => ({ ...prev, [pid]: e.target.value }))
                        }
                        className="w-full py-1.5 px-2.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                      >
                        {availModels.map((m) => (
                          <option key={m} value={m}>
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
        <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
          <button
            type="button"
            onClick={handleDismiss}
            className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 underline"
          >
            Skip for now (Use current / Mock AI)
          </button>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={handleSaveAndStart}
              disabled={isSaving}
              className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center gap-2 shadow-sm transition-all disabled:opacity-50"
            >
              {savedSuccess ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                  <span>Configured & Ready!</span>
                </>
              ) : (
                <>
                  <span>{isSaving ? 'Saving...' : 'Save & Start Learning'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
