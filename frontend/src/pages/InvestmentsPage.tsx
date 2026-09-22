import React, { useEffect, useState } from 'react';
import { Plus, TrendingUp, Trash2, X, Briefcase } from 'lucide-react';
import { ConfirmModal } from '../components/common/ConfirmModal';
import { api } from '../services/api';
import { Investment } from '../types';
import { formatINR } from '../utils/formatters';

interface InvestmentsPageProps {
  refreshKey: number;
  onRefresh: () => void;
}

export const InvestmentsPage: React.FC<InvestmentsPageProps> = ({ refreshKey, onRefresh }) => {
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    asset_name: '',
    investment_type: 'ETF',
    quantity: '1',
    current_value: '',
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchInvestments = async () => {
    setLoading(true);
    try {
      const res = await api.getInvestments();
      setInvestments(res || []);
    } catch (err) {
      console.error('Failed to load investments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvestments();
  }, [refreshKey]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.asset_name.trim()) {
      setFormError('Asset name is required.');
      return;
    }
    const val = parseFloat(formData.current_value);
    const qty = parseFloat(formData.quantity);
    if (isNaN(val) || val < 0) {
      setFormError('Current value must be zero or positive.');
      return;
    }
    if (isNaN(qty) || qty <= 0) {
      setFormError('Quantity must be greater than zero.');
      return;
    }

    setSubmitting(true);
    setFormError(null);
    try {
      await api.createInvestment({
        asset_name: formData.asset_name.trim(),
        investment_type: formData.investment_type,
        quantity: qty,
        current_value: val,
      });
      setIsModalOpen(false);
      onRefresh();
      fetchInvestments();
    } catch (err: any) {
      setFormError(err.message || 'Failed to save investment.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await api.deleteInvestment(deletingId);
      setDeletingId(null);
      onRefresh();
      fetchInvestments();
    } catch (err) {
      console.error('Failed to delete investment:', err);
    }
  };

  const totalValue = investments.reduce((acc, inv) => {
    const v = typeof inv.current_value === 'string' ? parseFloat(inv.current_value) : inv.current_value;
    return acc + (isNaN(v) ? 0 : v);
  }, 0);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Investments & Assets</h2>
          <p className="text-sm text-slate-400">
            Portfolio asset allocation records without automated market dependencies.
          </p>
        </div>
        <button
          onClick={() => {
            setFormData({ asset_name: '', investment_type: 'ETF', quantity: '1', current_value: '' });
            setFormError(null);
            setIsModalOpen(true);
          }}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-600/20 transition"
        >
          <Plus className="w-4 h-4" />
          <span>Add Asset</span>
        </button>
      </div>

      {/* Portfolio Value Card */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900/90 to-slate-900/50 flex items-center justify-between">
        <div>
          <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">Total Recorded Portfolio</span>
          <div className="text-3xl font-bold font-mono text-emerald-400 tracking-tight mt-1">
            {formatINR(totalValue)}
          </div>
          <p className="text-xs text-slate-500 mt-1">{investments.length} asset holdings tracked</p>
        </div>
        <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
          <Briefcase className="w-6 h-6" />
        </div>
      </div>

      {/* Holdings Table */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800 bg-slate-900/90">
              <tr>
                <th className="py-3 px-4">Asset Name</th>
                <th className="py-3 px-4">Asset Type</th>
                <th className="py-3 px-4">Quantity</th>
                <th className="py-3 px-4 text-right">Current Value</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {investments.map((inv) => (
                <tr key={inv.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-3 px-4 font-semibold text-slate-200">{inv.asset_name}</td>
                  <td className="py-3 px-4">
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                      {inv.investment_type}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-400">{inv.quantity}</td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-slate-100">
                    {formatINR(inv.current_value)}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setDeletingId(inv.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition"
                      title="Delete Asset"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {investments.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-500">
                    No investment records stored yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Asset Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-semibold text-slate-100">Add Investment Holding</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {formError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Asset Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Tata Silver ETF, Nifty 50 Index, Fixed Deposit"
                  value={formData.asset_name}
                  onChange={(e) => setFormData({ ...formData, asset_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1">Asset Type</label>
                  <select
                    value={formData.investment_type}
                    onChange={(e) => setFormData({ ...formData, investment_type: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 focus:outline-none focus:border-emerald-500/50"
                  >
                    <option value="ETF">ETF</option>
                    <option value="Mutual Fund">Mutual Fund</option>
                    <option value="Stocks">Stocks</option>
                    <option value="Fixed Deposit">Fixed Deposit</option>
                    <option value="Gold">Gold</option>
                    <option value="Bond">Bond</option>
                    <option value="Crypto">Crypto</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">Quantity *</label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0.0001"
                    required
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 font-mono focus:outline-none focus:border-emerald-500/50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1">Current Estimated Value (₹) *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  placeholder="6000.00"
                  value={formData.current_value}
                  onChange={(e) => setFormData({ ...formData, current_value: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 font-mono focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-400 hover:text-slate-200 border border-slate-800 hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl font-semibold bg-emerald-600 hover:bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-600/20 disabled:opacity-50 transition"
                >
                  {submitting ? 'Saving...' : 'Add Asset'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      <ConfirmModal
        isOpen={Boolean(deletingId)}
        title="Delete Investment Record"
        message="Are you sure you want to remove this asset holding from your portfolio records?"
        confirmLabel="Delete"
        isDangerous={true}
        onConfirm={handleDelete}
        onCancel={() => setDeletingId(null)}
      />
    </div>
  );
};
