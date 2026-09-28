import React from 'react';
import {
  ExternalLink,
  Globe,
  Shield,
  User,
} from 'lucide-react';

interface SettingsPageProps {
  onNavigateTab?: (tab: any) => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ onNavigateTab }) => {
  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Settings</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Manage your application preferences, regional standards, and system connection.
        </p>
      </div>

      {/* Regional & Display Preferences Card */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
          <Globe className="w-4 h-4 text-teal-600" />
          <h2 className="text-sm font-semibold text-slate-900">Regional & Display Standards</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-400 block text-[11px] font-medium">Currency Standard</span>
            <span className="text-slate-800 font-semibold text-sm">INR (₹)</span>
            <p className="text-[11px] text-slate-500">Indian Rupee denomination</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-400 block text-[11px] font-medium">Number Formatting</span>
            <span className="text-slate-800 font-semibold text-sm">Lakhs & Crores</span>
            <p className="text-[11px] text-slate-500">e.g. ₹1,20,000 without forced decimals</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-slate-400 block text-[11px] font-medium">Date Representation</span>
            <span className="text-slate-800 font-semibold text-sm">DD MMM YYYY</span>
            <p className="text-[11px] text-slate-500">e.g. 23 Sep 2026</p>
          </div>
        </div>
      </div>

      {/* Financial Profile Shortcut */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Financial Profile & Baselines</h3>
            <p className="text-xs text-slate-500">
              Update your monthly income, fixed recurring expenses, and risk preferences.
            </p>
          </div>
        </div>
        {onNavigateTab && (
          <button
            onClick={() => onNavigateTab('profile')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition shadow-xs"
          >
            <span>Open Profile</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
          </button>
        )}
      </div>

      {/* Security & Data Governance */}
      <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/70 text-xs text-slate-500 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-slate-700">
          <Shield className="w-3.5 h-3.5 text-teal-600" />
          <span>Security & Local Privacy</span>
        </div>
        <p className="text-[11px] leading-relaxed">
          FinMate runs deterministically with your local storage engine. Financial calculations are executed without unauthorized external transmission.
        </p>
      </div>
    </div>
  );
};
