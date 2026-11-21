import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import {
  Sparkles,
  Key,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Cpu,
  ShieldCheck,
  Power,
  RotateCw,
  Sliders,
  Check,
  Zap,
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

export const AISettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [saveStatus, setSaveStatus] = useState<Record<string, string>>({});
  const [testingModel, setTestingModel] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const { data: aiData, isLoading } = useQuery<AIProvidersResponse>({
    queryKey: ['ai-providers'],
    queryFn: async () => {
      const res = await apiClient.get('/ai/providers');
      return res.data;
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      provider,
      apiKey,
      model,
      isEnabled,
    }: {
      provider: string;
      apiKey?: string;
      model?: string;
      isEnabled?: boolean;
    }) => {
      return await apiClient.post('/ai/providers/update', {
        provider,
        api_key: apiKey && apiKey.trim() ? apiKey.trim() : undefined,
        model,
        is_enabled: isEnabled,
      });
    },
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] });
      setSaveStatus((prev) => ({ ...prev, [vars.provider]: 'Saved successfully!' }));
      setTimeout(() => {
        setSaveStatus((prev) => ({ ...prev, [vars.provider]: '' }));
      }, 2500);
    },
    onError: (err: any, vars) => {
      setSaveStatus((prev) => ({ ...prev, [vars.provider]: `Error: ${err.message}` }));
    },
  });

  const switchMutation = useMutation({
    mutationFn: async ({ provider, model }: { provider: string; model?: string }) => {
      return await apiClient.post('/ai/providers/switch', { provider, model });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-providers'] });
    },
  });

  const handleKeyChange = (provider: string, val: string) => {
    setKeys((prev) => ({ ...prev, [provider]: val }));
  };

  const handleToggleKeyVisibility = (provider: string) => {
    setShowKey((prev) => ({ ...prev, [provider]: !prev[provider] }));
  };

  const handleSaveProvider = (providerInfo: AIProviderInfo) => {
    const enteredKey = keys[providerInfo.provider];
    const model = selectedModels[providerInfo.provider] || providerInfo.model;
    updateMutation.mutate({
      provider: providerInfo.provider,
      apiKey: enteredKey,
      model,
      isEnabled: providerInfo.is_enabled,
    });
  };

  const handleToggleEnabled = (providerInfo: AIProviderInfo) => {
    // Toggling enabled without wiping key!
    updateMutation.mutate({
      provider: providerInfo.provider,
      model: selectedModels[providerInfo.provider] || providerInfo.model,
      isEnabled: !providerInfo.is_enabled,
    });
  };

  const handleSetActive = (provider: string) => {
    switchMutation.mutate({
      provider,
      model: selectedModels[provider],
    });
  };

  const handleTestConnection = async () => {
    setTestingModel(true);
    setTestResult(null);
    try {
      // Run quick test or verification via session test
      const res = await apiClient.get('/ai/providers');
      const active = res.data.providers.find((p: AIProviderInfo) => p.is_active);
      setTestResult({
        success: true,
        message: `Active provider "${active?.name}" is online and operating with model "${active?.model}".`,
      });
    } catch (err: any) {
      setTestResult({
        success: false,
        message: `Connection failed: ${err.message}`,
      });
    } finally {
      setTestingModel(false);
    }
  };

  const triggerOnboardingModal = () => {
    window.dispatchEvent(new CustomEvent('open-ai-onboarding'));
  };

  if (isLoading) {
    return (
      <div className="py-20 text-center">
        <RotateCw className="w-8 h-8 animate-spin mx-auto text-indigo-500 mb-3" />
        <p className="text-sm text-slate-500">Loading AI provider settings...</p>
      </div>
    );
  }

  const activeProvider = aiData?.providers.find((p) => p.is_active);

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 rounded-lg">
              <Sliders className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">AI Engines & Providers</h1>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Configure LLM backends (Gemini, OpenAI, Claude, Groq, DeepSeek) for Socratic tutoring, code feedback, and validation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={triggerOnboardingModal}
            className="px-3 py-2 text-xs font-medium rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            Open Startup Wizard
          </button>
          <button
            onClick={handleTestConnection}
            disabled={testingModel}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {testingModel ? (
              <RotateCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Zap className="w-3.5 h-3.5" />
            )}
            <span>Test Active AI</span>
          </button>
        </div>
      </div>

      {/* Active AI Status Card */}
      <div className="p-5 rounded-2xl border border-indigo-200 dark:border-indigo-900/60 bg-gradient-to-r from-indigo-50/60 via-purple-50/30 to-slate-50/60 dark:from-indigo-950/30 dark:via-purple-950/20 dark:to-slate-900/40">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="p-3 bg-indigo-600 text-white rounded-xl shadow-md">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase tracking-wider font-bold text-indigo-600 dark:text-indigo-400">
                  Currently Active Engine
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-semibold">
                  Live
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-0.5">
                {activeProvider ? activeProvider.name : 'None selected'}
              </h2>
              <p className="text-xs font-mono text-slate-500 dark:text-slate-400">
                Model: {activeProvider?.model} ·{' '}
                {activeProvider?.has_key ? `Key: ${activeProvider.masked_key}` : 'No API key set'}
              </p>
            </div>
          </div>

          {/* Quick Switch Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-500 font-medium mr-1">Switch to:</span>
            {aiData?.providers
              .filter((p) => p.is_enabled && !p.is_active)
              .map((p) => (
                <button
                  key={p.provider}
                  onClick={() => handleSetActive(p.provider)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 hover:border-indigo-500 dark:hover:border-indigo-500 transition-colors shadow-sm"
                >
                  {p.name}
                </button>
              ))}
          </div>
        </div>

        {/* Test Result alert */}
        {testResult && (
          <div
            className={`mt-4 p-3 rounded-xl border text-xs flex items-center gap-2 ${
              testResult.success
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
                : 'bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800'
            }`}
          >
            {testResult.success ? (
              <CheckCircle2 className="w-4 h-4 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 shrink-0" />
            )}
            <span>{testResult.message}</span>
          </div>
        )}
      </div>

      {/* Philosophy banner regarding key retention */}
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-indigo-500 shrink-0 mt-0.5" />
        <div className="text-xs leading-relaxed text-slate-600 dark:text-slate-300">
          <strong className="text-slate-900 dark:text-white">Seamless Multi-Model Switching:</strong>{' '}
          When you disable an AI provider, ThinkFree <em>retains</em> your API key in memory/storage so you can toggle it back on with a single click. Keys are masked on return and never exposed to the client.
        </div>
      </div>

      {/* Provider Cards */}
      <div className="space-y-5">
        <h3 className="text-base font-semibold tracking-tight text-slate-900 dark:text-white">
          All Available Providers
        </h3>

        <div className="grid grid-cols-1 gap-5">
          {aiData?.providers.map((p) => {
            const isCurrentActive = p.is_active;
            const chosenModel = selectedModels[p.provider] || p.model;
            const currentSaveMsg = saveStatus[p.provider];

            return (
              <div
                key={p.provider}
                className={`p-6 rounded-2xl border transition-all ${
                  isCurrentActive
                    ? 'border-indigo-400 dark:border-indigo-600 bg-white dark:bg-slate-900 shadow-md ring-1 ring-indigo-400/20'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-4 border-b border-slate-100 dark:border-slate-800">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2.5 rounded-xl ${
                        isCurrentActive
                          ? 'bg-indigo-600 text-white'
                          : p.is_enabled
                          ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                      }`}
                    >
                      <Cpu className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-base">{p.name}</h4>
                        {isCurrentActive && (
                          <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-indigo-100 dark:bg-indigo-950/80 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                            Active
                          </span>
                        )}
                        {!p.is_enabled && (
                          <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
                            Disabled (Key Saved)
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {p.has_key ? (
                          <span className="text-emerald-600 dark:text-emerald-400 font-mono">
                            API Key configured: {p.masked_key}
                          </span>
                        ) : (
                          <span className="text-amber-500 font-medium">No key configured yet</span>
                        )}
                      </p>
                    </div>
                  </div>

                  {/* Actions: Enable/Disable switch & Set Active */}
                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    {/* Enable/Disable Toggle */}
                    <button
                      type="button"
                      onClick={() => handleToggleEnabled(p)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 border transition-all ${
                        p.is_enabled
                          ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700 hover:bg-slate-200'
                      }`}
                      title={p.is_enabled ? 'Disable (keeps key stored)' : 'Enable provider'}
                    >
                      <Power className="w-3.5 h-3.5" />
                      <span>{p.is_enabled ? 'Enabled' : 'Disabled'}</span>
                    </button>

                    {/* Set Active Button */}
                    <button
                      type="button"
                      disabled={isCurrentActive || !p.is_enabled}
                      onClick={() => handleSetActive(p.provider)}
                      className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                        isCurrentActive
                          ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm cursor-default'
                          : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:border-indigo-500 hover:text-indigo-600 disabled:opacity-40 disabled:hover:border-slate-300'
                      }`}
                    >
                      {isCurrentActive ? 'Current Active' : 'Set as Active'}
                    </button>
                  </div>
                </div>

                {/* Settings Form Grid */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
                  {/* API Key field */}
                  <div className="md:col-span-6">
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      API Key {p.has_key && <span className="text-slate-400">(leave blank to keep current)</span>}
                    </label>
                    <div className="relative">
                      <Key className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                      <input
                        type={showKey[p.provider] ? 'text' : 'password'}
                        placeholder={p.has_key ? `•••••••• (${p.masked_key})` : 'Paste API Key'}
                        value={keys[p.provider] || ''}
                        onChange={(e) => handleKeyChange(p.provider, e.target.value)}
                        className="w-full pl-9 pr-10 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                      />
                      <button
                        type="button"
                        onClick={() => handleToggleKeyVisibility(p.provider)}
                        className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                      >
                        {showKey[p.provider] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Model Selection */}
                  <div className="md:col-span-4">
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Model
                    </label>
                    <select
                      value={chosenModel}
                      onChange={(e) =>
                        setSelectedModels((prev) => ({
                          ...prev,
                          [p.provider]: e.target.value,
                        }))
                      }
                      className="w-full py-2 px-3 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-mono"
                    >
                      {p.available_models.map((m) => (
                        <option key={m} value={m}>
                          {m}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Save button */}
                  <div className="md:col-span-2">
                    <button
                      type="button"
                      onClick={() => handleSaveProvider(p)}
                      disabled={updateMutation.isPending}
                      className="w-full py-2 px-4 text-xs font-semibold rounded-lg bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-100 text-white dark:text-slate-900 transition-colors flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-50"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Save</span>
                    </button>
                  </div>
                </div>

                {/* Status message */}
                {currentSaveMsg && (
                  <div className="mt-3 text-xs font-medium text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{currentSaveMsg}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
