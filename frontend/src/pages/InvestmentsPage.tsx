import React, { useEffect, useState } from 'react';
import { Briefcase, Plus, Trash2, X } from 'lucide-react';
import { ConfirmModal } from '../components/common/ConfirmModal';
import { EmptyState } from '../components/common/EmptyState';
import { api } from '../services/api';
import { Investment } from '../types';
import { formatINR } from '../utils/formatters';

interface InvestmentsPageProps {
  refreshKey: number;
  onRefresh: () => void;
}

export const InvestmentsPage: React.FC<InvestmentsPageProps> = ({
  refreshKey,
  onRefresh,
}) => {
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    asset_name: '',
    investment_type: 'Mutual Fund',
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
    const v =
      typeof inv.current_value === 'string'
        ? parseFloat(inv.current_value)
        : inv.current_value;
    return acc + (isNaN(v) ? 0 : v);
  }, 0);

  // Group portfolio allocation by asset type
  const allocation = React.useMemo(() => {
    const map: Record<string, number> = {};
    investments.forEach((inv) => {
      const v =
        typeof inv.current_value === 'string'
          ? parseFloat(inv.current_value)
          : inv.current_value;
      const type = inv.investment_type || 'Other';
      map[type] = (map[type] || 0) + (isNaN(v) ? 0 : v);
    });
    return Object.keys(map).map((type) => ({
      type,
      total: map[type],
      pct: totalValue > 0 ? (map[type] / totalValue) * 100 : 0,
    }));
  }, [investments, totalValue]);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Investments & Assets</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Track your recorded asset holdings and portfolio distribution.
          </p>
        </div>
        <button
          onClick={() => {
            setFormData({
              asset_name: '',
              investment_type: 'Mutual Fund',
              quantity: '1',
              current_value: '',
            });
            setFormError(null);
            setIsModalOpen(true);
          }}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Asset</span>
        </button>
      </div>

      {/* Portfolio Value Card */}
      <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] text-slate-500 uppercase tracking-wider font-semibold">
            Total Recorded Portfolio
          </span>
          <div className="text-3xl font-bold font-mono text-slate-900 tracking-tight mt-1">
            {formatINR(totalValue)}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {investments.length} asset holding{investments.length !== 1 ? 's' : ''} tracked
          </p>
        </div>
        <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-100 text-teal-600 flex items-center justify-center shrink-0">
          <Briefcase className="w-6 h-6" />
        </div>
      </div>

      {/* Allocation breakdown bar if assets exist */}
      {allocation.length > 0 && (
        <div className="p-4 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-2.5">
          <div className="flex justify-between items-center text-xs">
            <span className="font-semibold text-slate-800">Asset Allocation</span>
            <span className="text-slate-400">{allocation.length} categories</span>
          </div>
          <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden flex">
            {allocation.map((item, i) => {
              const colors = [
                'bg-teal-600',
                'bg-blue-500',
                'bg-purple-500',
                'bg-amber-500',
                'bg-rose-500',
                'bg-emerald-500',
              ];
              return (
                <div
                  key={item.type}
                  title={`${item.type}: ${item.pct.toFixed(1)}%`}
                  style={{ width: `${item.pct}%` }}
                  className={`h-full ${colors[i % colors.length]}`}
                />
              );
            })}
          </div>
          <div className="flex flex-wrap gap-3 pt-1">
            {allocation.map((item, i) => {
              const dots = [
                'bg-teal-600',
                'bg-blue-500',
                'bg-purple-500',
                'bg-amber-500',
                'bg-rose-500',
                'bg-emerald-500',
              ];
              return (
                <div key={item.type} className="flex items-center gap-1.5 text-[11px] text-slate-600">
                  <span className={`w-2 h-2 rounded-full ${dots[i % dots.length]}`} />
                  <span className="font-medium text-slate-700">{item.type}</span>
                  <span className="text-slate-400">({item.pct.toFixed(0)}%)</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Holdings Table */}
      {investments.length > 0 ? (
        <div className="rounded-2xl border border-slate-200/80 bg-white shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-100 bg-slate-50/60 font-semibold">
                <tr>
                  <th className="py-3 px-4">Asset Name</th>
                  <th className="py-3 px-4">Asset Type</th>
                  <th className="py-3 px-4">Units / Quantity</th>
                  <th className="py-3 px-4 text-right">Current Value</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {investments.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-4 font-semibold text-slate-900">{inv.asset_name}</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2.5 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                        {inv.investment_type}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-600">{inv.quantity}</td>
                    <td className="py-3.5 px-4 text-right font-mono font-bold text-slate-900 text-sm">
                      {formatINR(inv.current_value)}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => setDeletingId(inv.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition"
                        title="Delete Asset"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : !loading ? (
        <EmptyState
          icon={Briefcase}
          title="No investments yet"
          description="Add your mutual funds, ETFs, fixed deposits, or other assets to keep an overview of your net worth."
          actionLabel="+ Add Asset"
          onAction={() => {
            setFormData({
              asset_name: '',
              investment_type: 'Mutual Fund',
              quantity: '1',
              current_value: '',
            });
            setFormError(null);
            setIsModalOpen(true);
          }}
        />
      ) : null}

      {/* Add Asset Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/35 backdrop-blur-xs animate-fadeIn">
          <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl shadow-xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-semibold text-slate-900">Add Investment Holding</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {formError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">Asset Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Nifty 50 Index Fund, Sovereign Gold Bond"
                  value={formData.asset_name}
                  onChange={(e) => setFormData({ ...formData, asset_name: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Asset Type</label>
                  <select
                    value={formData.investment_type}
                    onChange={(e) =>
                      setFormData({ ...formData, investment_type: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  >
                    <option value="Mutual Fund">Mutual Fund</option>
                    <option value="ETF">ETF</option>
                    <option value="Stocks">Stocks</option>
                    <option value="Fixed Deposit">Fixed Deposit</option>
                    <option value="Gold">Gold</option>
                    <option value="Bond">Bond</option>
                    <option value="Crypto">Crypto</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Quantity *</label>
                  <input
                    type="number"
                    step="0.0001"
                    min="0.0001"
                    required
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-mono focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">
                  Current Estimated Value (₹) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  placeholder="25000"
                  value={formData.current_value}
                  onChange={(e) => setFormData({ ...formData, current_value: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-mono focus:outline-none focus:border-teal-500 focus:bg-white transition"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-slate-700 hover:bg-slate-100 border border-slate-200 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs disabled:opacity-50 transition"
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
