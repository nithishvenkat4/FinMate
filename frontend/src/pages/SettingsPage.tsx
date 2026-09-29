import React, { useEffect, useState } from 'react';
import {
  ExternalLink,
  Globe,
  Shield,
  User,
  Sparkles,
  Save,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Key,
  Wallet,
  Coins,
  Calendar,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import { formatINR } from '../utils/formatters';

interface SettingsPageProps {
  onNavigateTab?: (tab: any) => void;
  onRefresh?: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ onNavigateTab, onRefresh }) => {
  // Regional & Display Preferences
  const [currency, setCurrency] = useState(() => localStorage.getItem('finmate_currency') || 'INR');
  const [numberFormat, setNumberFormat] = useState(
    () => localStorage.getItem('finmate_number_format') || 'indian'
  );
  const [dateFormat, setDateFormat] = useState(
    () => localStorage.getItem('finmate_date_format') || 'DD MMM YYYY'
  );

  // AI & LLM Intelligence
  const [llmProvider, setLlmProvider] = useState(
    () => localStorage.getItem('finmate_llm_provider') || 'gemini'
  );
  const [llmModel, setLlmModel] = useState(
    () => localStorage.getItem('finmate_llm_model') || 'gemini-1.5-flash'
  );
  const [llmApiKey, setLlmApiKey] = useState(
    () => localStorage.getItem('finmate_llm_api_key') || ''
  );
  const [showApiKey, setShowApiKey] = useState(false);

  // Financial Profile Baselines
  const [profileLoading, setProfileLoading] = useState(true);
  const [monthlyIncome, setMonthlyIncome] = useState('');
  const [monthlyFixedExpenses, setMonthlyFixedExpenses] = useState('');
  const [currentSavings, setCurrentSavings] = useState('');
  const [riskPreference, setRiskPreference] = useState('moderate');

  // UI state
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const loadProfile = async () => {
      setProfileLoading(true);
      try {
        const res = await api.getProfile();
        if (res) {
          setMonthlyIncome(res.monthly_income?.toString() || '');
          setMonthlyFixedExpenses(res.monthly_fixed_expenses?.toString() || '');
          setCurrentSavings(res.current_savings?.toString() || '');
          setRiskPreference(res.risk_preference || 'moderate');
        }
      } catch (err) {
        console.error('Failed to load profile for settings:', err);
      } finally {
        setProfileLoading(false);
      }
    };
    loadProfile();
  }, []);

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const incNum = parseFloat(monthlyIncome);
    const expNum = parseFloat(monthlyFixedExpenses);
    const savNum = parseFloat(currentSavings);

    if (isNaN(incNum) || incNum < 0) {
      setErrorMsg('Monthly income must be 0 or a positive number.');
      setSaving(false);
      return;
    }
    if (isNaN(expNum) || expNum < 0) {
      setErrorMsg('Monthly fixed expenses must be 0 or a positive number.');
      setSaving(false);
      return;
    }
    if (isNaN(savNum) || savNum < 0) {
      setErrorMsg('Current savings must be 0 or a positive number.');
      setSaving(false);
      return;
    }

    try {
      // 1. Save regional and AI preferences to localStorage
      localStorage.setItem('finmate_currency', currency);
      localStorage.setItem('finmate_number_format', numberFormat);
      localStorage.setItem('finmate_date_format', dateFormat);
      localStorage.setItem('finmate_llm_provider', llmProvider);
      localStorage.setItem('finmate_llm_model', llmModel);
      localStorage.setItem('finmate_llm_api_key', llmApiKey);

      // 2. Persist financial profile baselines to backend database
      await api.updateProfile({
        monthly_income: incNum,
        monthly_fixed_expenses: expNum,
        current_savings: savNum,
        risk_preference: riskPreference as any,
      });

      setSuccessMsg('Settings and financial profile updated successfully! All pages will reflect these values.');
      if (onRefresh) onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save settings. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const calculatedSurplus = Math.max(
    0,
    (parseFloat(monthlyIncome) || 0) - (parseFloat(monthlyFixedExpenses) || 0)
  );
  const bufferMonths =
    parseFloat(monthlyFixedExpenses) > 0
      ? ((parseFloat(currentSavings) || 0) / parseFloat(monthlyFixedExpenses)).toFixed(1)
      : 'N/A';

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Settings</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure your regional display formats, AI intelligence engine, and active financial baselines.
          </p>
        </div>
        <button
          onClick={() => handleSave()}
          disabled={saving || profileLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition disabled:opacity-50 self-start sm:self-auto"
        >
          <Save className="w-3.5 h-3.5" />
          <span>{saving ? 'Saving...' : 'Save Settings'}</span>
        </button>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2.5 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2.5 animate-fadeIn">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* 1. Regional & Display Standards (Editable) */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <Globe className="w-4 h-4 text-teal-600" />
          <h2 className="text-sm font-semibold text-slate-900">Regional & Display Standards</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="space-y-1.5">
            <label className="text-slate-600 font-medium block flex items-center gap-1.5">
              <Coins className="w-3.5 h-3.5 text-slate-400" />
              <span>Currency Standard</span>
            </label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition"
            >
              <option value="INR">INR (₹) — Indian Rupee</option>
              <option value="USD">USD ($) — US Dollar</option>
              <option value="EUR">EUR (€) — Euro</option>
              <option value="GBP">GBP (£) — British Pound</option>
            </select>
            <p className="text-[10px] text-slate-400">Used for balances and transaction entries</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-600 font-medium block flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>Number Formatting</span>
            </label>
            <select
              value={numberFormat}
              onChange={(e) => setNumberFormat(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition"
            >
              <option value="indian">Indian (Lakhs & Crores, e.g. ₹1,20,000)</option>
              <option value="international">International (Millions, e.g. 120,000.00)</option>
            </select>
            <p className="text-[10px] text-slate-400">Grouping notation for large numbers</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-600 font-medium block flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>Date Representation</span>
            </label>
            <select
              value={dateFormat}
              onChange={(e) => setDateFormat(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition"
            >
              <option value="DD MMM YYYY">DD MMM YYYY (e.g. 29 Sep 2026)</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD (e.g. 2026-09-29)</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY (e.g. 29/09/2026)</option>
            </select>
            <p className="text-[10px] text-slate-400">Date display convention throughout FinMate</p>
          </div>
        </div>
      </div>

      {/* 2. AI Intelligence & LLM Provider Configuration */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-teal-600" />
            <h2 className="text-sm font-semibold text-slate-900">AI Intelligence & LLM Configuration</h2>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-teal-50 text-teal-700 border border-teal-100">
            Phase 4 Multi-Agent Support
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1.5">
            <label className="text-slate-600 font-medium block">Active LLM Provider</label>
            <select
              value={llmProvider}
              onChange={(e) => setLlmProvider(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition"
            >
              <option value="gemini">Google Gemini (Recommended, Fast & Free tier)</option>
              <option value="openai">OpenAI (GPT-4o-mini / GPT-4o)</option>
              <option value="mock">Deterministic Local Mock (Offline testing)</option>
            </select>
            <p className="text-[10px] text-slate-400">
              Provider used for conversational reasoning and Option A/B/C synthesis
            </p>
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-600 font-medium block">Model Identifier</label>
            <input
              type="text"
              value={llmModel}
              onChange={(e) => setLlmModel(e.target.value)}
              placeholder="e.g. gemini-1.5-flash or gpt-4o-mini"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition"
            />
            <p className="text-[10px] text-slate-400">Default: gemini-1.5-flash</p>
          </div>
        </div>

        <div className="space-y-1.5 pt-2">
          <label className="text-slate-600 font-medium flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5">
              <Key className="w-3.5 h-3.5 text-slate-400" />
              <span>LLM API Key</span>
            </span>
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noreferrer"
              className="text-teal-600 hover:text-teal-700 underline flex items-center gap-1 text-[11px]"
            >
              <span>Get Free Gemini Key</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </label>
          <div className="relative">
            <input
              type={showApiKey ? 'text' : 'password'}
              value={llmApiKey}
              onChange={(e) => setLlmApiKey(e.target.value)}
              placeholder="AIzaSy... (Paste your Gemini API key here)"
              className="w-full pl-3 pr-10 py-2 rounded-xl border border-slate-200 text-xs font-mono text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition"
            >
              {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <p className="text-[10px] text-slate-400">
            Keys are transmitted securely and never shared with third parties.
          </p>
        </div>
      </div>

      {/* 3. Core Financial Profile & Baselines (Directly Editable) */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Wallet className="w-4 h-4 text-teal-600" />
            <h2 className="text-sm font-semibold text-slate-900">Financial Profile & Baselines</h2>
          </div>
          {onNavigateTab && (
            <button
              type="button"
              onClick={() => onNavigateTab('profile')}
              className="text-xs font-semibold text-teal-600 hover:text-teal-700 underline flex items-center gap-1"
            >
              <span>Detailed Profile View</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="space-y-1.5">
            <label className="text-slate-600 font-medium block">Monthly Income (₹)</label>
            <input
              type="number"
              step="100"
              value={monthlyIncome}
              onChange={(e) => setMonthlyIncome(e.target.value)}
              placeholder="e.g. 60000"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition font-mono"
            />
            <p className="text-[10px] text-slate-400">Primary recurring inflow</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-600 font-medium block">Fixed Expenses (₹)</label>
            <input
              type="number"
              step="100"
              value={monthlyFixedExpenses}
              onChange={(e) => setMonthlyFixedExpenses(e.target.value)}
              placeholder="e.g. 35000"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition font-mono"
            />
            <p className="text-[10px] text-slate-400">Rent, utilities & debt service</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-600 font-medium block">Current Liquid Savings (₹)</label>
            <input
              type="number"
              step="100"
              value={currentSavings}
              onChange={(e) => setCurrentSavings(e.target.value)}
              placeholder="e.g. 120000"
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition font-mono"
            />
            <p className="text-[10px] text-slate-400">Liquid emergency cash</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-slate-600 font-medium block">Risk Stance</label>
            <select
              value={riskPreference}
              onChange={(e) => setRiskPreference(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs font-medium text-slate-800 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition capitalize"
            >
              <option value="conservative">Conservative</option>
              <option value="moderate">Moderate</option>
              <option value="aggressive">Aggressive</option>
            </select>
            <p className="text-[10px] text-slate-400">Decision risk appetite</p>
          </div>
        </div>

        {/* Live Calculated Baseline Metrics */}
        <div className="p-4 rounded-xl bg-teal-50/50 border border-teal-100 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div>
            <span className="text-[11px] text-slate-500 block">Calculated Monthly Surplus</span>
            <span className="text-sm font-bold text-teal-800 font-mono">
              {formatINR(calculatedSurplus)}
            </span>
          </div>
          <div>
            <span className="text-[11px] text-slate-500 block">Emergency Buffer Coverage</span>
            <span className="text-sm font-bold text-slate-800 font-mono">
              {bufferMonths} {bufferMonths !== 'N/A' ? 'Months' : ''}
            </span>
          </div>
          <div>
            <span className="text-[11px] text-slate-500 block">Savings Capacity Ratio</span>
            <span className="text-sm font-bold text-slate-800 font-mono">
              {parseFloat(monthlyIncome) > 0
                ? `${((calculatedSurplus / parseFloat(monthlyIncome)) * 100).toFixed(1)}%`
                : '0%'}
            </span>
          </div>
        </div>
      </div>

      {/* 4. Security & Data Governance */}
      <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/70 text-xs text-slate-500 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-slate-700">
          <Shield className="w-3.5 h-3.5 text-teal-600" />
          <span>Security & Local Privacy</span>
        </div>
        <p className="text-[11px] leading-relaxed">
          FinMate runs deterministically with your local storage engine. Financial calculations are executed without unauthorized external transmission.
        </p>
      </div>

      {/* Save Button */}
      <div className="flex justify-end pt-2">
        <button
          onClick={() => handleSave()}
          disabled={saving || profileLoading}
          className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Saving Changes...' : 'Save All Settings'}</span>
        </button>
      </div>
    </div>
  );
};
