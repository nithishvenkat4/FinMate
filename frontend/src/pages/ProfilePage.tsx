import React, { useEffect, useState } from 'react';
import { CheckCircle2, UserCheck, Shield, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { FinancialProfile } from '../types';
import { formatINR } from '../utils/formatters';

interface ProfilePageProps {
  refreshKey: number;
  onRefresh: () => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ refreshKey, onRefresh }) => {
  const [profile, setProfile] = useState<FinancialProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    monthly_income: '',
    monthly_fixed_expenses: '',
    current_savings: '',
    risk_preference: 'moderate',
  });
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true);
      try {
        const res = await api.getProfile();
        setProfile(res);
        setFormData({
          monthly_income: res.monthly_income.toString(),
          monthly_fixed_expenses: res.monthly_fixed_expenses.toString(),
          current_savings: res.current_savings.toString(),
          risk_preference: res.risk_preference,
        });
      } catch (err) {
        console.error('Failed to load profile:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [refreshKey]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const income = parseFloat(formData.monthly_income);
    const fixed = parseFloat(formData.monthly_fixed_expenses);
    const savings = parseFloat(formData.current_savings);

    if (isNaN(income) || income < 0) {
      setErrorMsg('Monthly income must be zero or a positive number.');
      return;
    }
    if (isNaN(fixed) || fixed < 0) {
      setErrorMsg('Fixed expenses must be zero or a positive number.');
      return;
    }
    if (isNaN(savings) || savings < 0) {
      setErrorMsg('Current savings must be zero or a positive number.');
      return;
    }

    setSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const updated = await api.updateProfile({
        monthly_income: income,
        monthly_fixed_expenses: fixed,
        current_savings: savings,
        risk_preference: formData.risk_preference as any,
      });
      setProfile(updated);
      setSuccessMsg('Financial profile updated successfully!');
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-3xl">
      <div>
        <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Financial Profile</h2>
        <p className="text-sm text-slate-400">
          Maintain your core financial baseline parameters. Used by deterministic cash flow services.
        </p>
      </div>

      {successMsg && (
        <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-300 text-xs flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-300 text-xs flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-6">
        <form onSubmit={handleSubmit} className="space-y-5 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Gross Monthly Income (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.monthly_income}
                onChange={(e) => setFormData({ ...formData, monthly_income: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 font-mono text-sm focus:outline-none focus:border-emerald-500/50"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">Expected regular monthly earnings</span>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Fixed Monthly Expenses (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.monthly_fixed_expenses}
                onChange={(e) => setFormData({ ...formData, monthly_fixed_expenses: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 font-mono text-sm focus:outline-none focus:border-emerald-500/50"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">Rent, loan EMIs, insurance, utility baselines</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Current Liquid Savings (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.current_savings}
                onChange={(e) => setFormData({ ...formData, current_savings: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 font-mono text-sm focus:outline-none focus:border-emerald-500/50"
              />
              <span className="text-[11px] text-slate-500 mt-1 block">Readily available bank/emergency funds</span>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">Declared Risk Appetite</label>
              <select
                value={formData.risk_preference}
                onChange={(e) => setFormData({ ...formData, risk_preference: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 text-sm focus:outline-none focus:border-emerald-500/50 capitalize"
              >
                <option value="conservative">Conservative</option>
                <option value="moderate">Moderate</option>
                <option value="aggressive">Aggressive</option>
              </select>
              <span className="text-[11px] text-slate-500 mt-1 block">User-stated guidance reference only</span>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-semibold bg-emerald-600 hover:bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-600/20 disabled:opacity-50 transition"
            >
              {saving && <RefreshCw className="w-4 h-4 animate-spin" />}
              <span>{saving ? 'Saving...' : 'Save Profile Changes'}</span>
            </button>
          </div>
        </form>
      </div>

      <div className="p-4 rounded-xl border border-slate-800/80 bg-slate-900/40 text-xs text-slate-500 space-y-1">
        <span className="font-semibold text-slate-400">Important Advisory Note:</span>
        <p>
          Declared risk preference in FinMate is a user-supplied personal parameter. It does not constitute a certified professional financial risk assessment.
        </p>
      </div>
    </div>
  );
};
