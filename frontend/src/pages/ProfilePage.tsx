import React, { useEffect, useState } from 'react';
import { CheckCircle2, Shield, AlertCircle, RefreshCw, UserCheck } from 'lucide-react';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { api } from '../services/api';
import { FinancialProfile } from '../types';

interface ProfilePageProps {
  refreshKey: number;
  onRefresh: () => void;
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ refreshKey, onRefresh }) => {
  const [, setProfile] = useState<FinancialProfile | null>(null);
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

  if (loading) {
    return (
      <div className="space-y-6 animate-fadeIn max-w-3xl">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Financial Profile</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Maintain your core financial baselines used for cash flow and goal planning.
          </p>
        </div>
        <TableSkeleton rows={3} />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn max-w-3xl">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Financial Profile</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Maintain your core financial baselines used for cash flow and goal planning.
        </p>
      </div>

      {successMsg && (
        <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-800 text-xs flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Account Info Summary Card */}
      <div className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-xs flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-full bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Demo User</h3>
            <p className="text-[11px] text-slate-500">Default Household Profile • Currency: INR (₹)</p>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
          Active
        </span>
      </div>

      {/* Profile Form Card */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-6">
        <div className="border-b border-slate-100 pb-3">
          <h2 className="text-sm font-semibold text-slate-900">Financial Baseline Parameters</h2>
          <p className="text-[11px] text-slate-500">
            These values are used to evaluate your disposable income and savings capacity.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-medium mb-1.5">
                Gross Monthly Income (₹)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.monthly_income}
                onChange={(e) => setFormData({ ...formData, monthly_income: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-mono text-sm focus:outline-none focus:border-teal-500 focus:bg-white transition"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Regular expected monthly earnings
              </span>
            </div>

            <div>
              <label className="block text-slate-700 font-medium mb-1.5">
                Fixed Monthly Expenses (₹)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.monthly_fixed_expenses}
                onChange={(e) =>
                  setFormData({ ...formData, monthly_fixed_expenses: e.target.value })
                }
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-mono text-sm focus:outline-none focus:border-teal-500 focus:bg-white transition"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Rent, loan EMIs, insurance, recurring bills
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-700 font-medium mb-1.5">
                Current Liquid Savings (₹)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.current_savings}
                onChange={(e) => setFormData({ ...formData, current_savings: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-mono text-sm focus:outline-none focus:border-teal-500 focus:bg-white transition"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Readily available bank/emergency funds
              </span>
            </div>

            <div>
              <label className="block text-slate-700 font-medium mb-1.5">
                Investment Risk Preference
              </label>
              <select
                value={formData.risk_preference}
                onChange={(e) => setFormData({ ...formData, risk_preference: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 text-sm focus:outline-none focus:border-teal-500 focus:bg-white transition capitalize"
              >
                <option value="conservative">Conservative (Capital preservation focus)</option>
                <option value="moderate">Moderate (Balanced growth and stability)</option>
                <option value="aggressive">Aggressive (Long-term growth oriented)</option>
              </select>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Used to tailor advice recommendations
              </span>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs disabled:opacity-50 transition"
            >
              {saving && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
              <span>{saving ? 'Saving...' : 'Save Profile Changes'}</span>
            </button>
          </div>
        </form>
      </div>

      <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/70 text-xs text-slate-500 space-y-1">
        <div className="flex items-center gap-1.5 font-semibold text-slate-700">
          <Shield className="w-3.5 h-3.5 text-teal-600" />
          <span>Privacy & Data Control</span>
        </div>
        <p className="text-[11px] leading-relaxed">
          Your financial parameters are stored locally on your FinMate instance and never shared with third parties.
        </p>
      </div>
    </div>
  );
};
