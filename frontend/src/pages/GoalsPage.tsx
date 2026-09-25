import React, { useEffect, useState } from 'react';
import {
  Calendar,
  CheckCircle2,
  Edit2,
  Plus,
  Target,
  Trash2,
  X,
} from 'lucide-react';
import { ConfirmModal } from '../components/common/ConfirmModal';
import { EmptyState } from '../components/common/EmptyState';
import { api } from '../services/api';
import { Goal } from '../types';
import { formatINR, formatDate, formatPercent } from '../utils/formatters';

interface GoalsPageProps {
  refreshKey: number;
  onRefresh: () => void;
}

export const GoalsPage: React.FC<GoalsPageProps> = ({ refreshKey, onRefresh }) => {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    target_amount: '',
    current_amount: '',
    target_date: '',
    priority: 'medium',
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchGoals = async () => {
    setLoading(true);
    try {
      const res = await api.getGoals();
      setGoals(res || []);
    } catch (err) {
      console.error('Failed to load goals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGoals();
  }, [refreshKey]);

  const handleOpenAdd = () => {
    setEditingGoal(null);
    setFormData({
      name: '',
      target_amount: '',
      current_amount: '0',
      target_date: new Date(new Date().setFullYear(new Date().getFullYear() + 1))
        .toISOString()
        .split('T')[0],
      priority: 'medium',
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (goal: Goal) => {
    setEditingGoal(goal);
    setFormData({
      name: goal.name,
      target_amount: goal.target_amount.toString(),
      current_amount: goal.current_amount.toString(),
      target_date: goal.target_date,
      priority: goal.priority,
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setFormError('Goal title is required.');
      return;
    }
    const target = parseFloat(formData.target_amount);
    const current = parseFloat(formData.current_amount);
    if (isNaN(target) || target <= 0) {
      setFormError('Target amount must be greater than zero.');
      return;
    }
    if (isNaN(current) || current < 0) {
      setFormError('Current amount saved cannot be negative.');
      return;
    }

    setSubmitting(true);
    setFormError(null);
    try {
      if (editingGoal) {
        await api.updateGoal(editingGoal.id, {
          name: formData.name.trim(),
          target_amount: target,
          current_amount: current,
          target_date: formData.target_date,
          priority: formData.priority as 'low' | 'medium' | 'high',
        });
      } else {
        await api.createGoal({
          name: formData.name.trim(),
          target_amount: target,
          current_amount: current,
          target_date: formData.target_date,
          priority: formData.priority as 'low' | 'medium' | 'high',
        });
      }
      setIsModalOpen(false);
      onRefresh();
      fetchGoals();
    } catch (err: any) {
      setFormError(err.message || 'Failed to save goal.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await api.deleteGoal(deletingId);
      setDeletingId(null);
      onRefresh();
      fetchGoals();
    } catch (err) {
      console.error('Failed to delete goal:', err);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Financial Goals</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Set savings targets and monitor your progress over time.
          </p>
        </div>
        <button
          onClick={handleOpenAdd}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Create Goal</span>
        </button>
      </div>

      {/* Goal Cards Grid */}
      {goals.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {goals.map((g) => {
            const prog =
              typeof g.progress_percentage === 'string'
                ? parseFloat(g.progress_percentage)
                : g.progress_percentage;
            const isCompleted = prog >= 100;

            return (
              <div
                key={g.id}
                className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4 hover-lift transition"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-900 text-base">{g.name}</h3>
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-0.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>Target: {formatDate(g.target_date)}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded-md border ${
                        g.priority === 'high'
                          ? 'bg-rose-50 text-rose-700 border-rose-100'
                          : g.priority === 'medium'
                          ? 'bg-amber-50 text-amber-700 border-amber-100'
                          : 'bg-slate-100 text-slate-600 border-slate-200'
                      }`}
                    >
                      {g.priority}
                    </span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="space-y-2 pt-1">
                  <div className="flex justify-between items-baseline text-xs">
                    <span className="text-slate-500 font-medium">Progress</span>
                    <span className="font-bold font-mono text-teal-700 text-sm">
                      {formatPercent(prog)}
                    </span>
                  </div>
                  <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isCompleted ? 'bg-emerald-600' : 'bg-teal-600'
                      }`}
                      style={{ width: `${Math.min(prog, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-500 font-mono pt-1">
                    <span>Saved: {formatINR(g.current_amount)}</span>
                    <span>Target: {formatINR(g.target_amount)}</span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                  <div className="flex items-center gap-1 text-xs">
                    {isCompleted ? (
                      <span className="flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Target Achieved
                      </span>
                    ) : (
                      <span className="text-slate-400 text-[11px]">
                        {formatINR(
                          Math.max(
                            0,
                            (typeof g.target_amount === 'string'
                              ? parseFloat(g.target_amount)
                              : g.target_amount) -
                              (typeof g.current_amount === 'string'
                                ? parseFloat(g.current_amount)
                                : g.current_amount)
                          )
                        )}{' '}
                        remaining
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleOpenEdit(g)}
                      className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition"
                      title="Edit Goal"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setDeletingId(g.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition"
                      title="Delete Goal"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : !loading ? (
        <EmptyState
          icon={Target}
          title="No goals yet"
          description="Create your first financial goal to track savings milestones for education, emergency funds, or large purchases."
          actionLabel="+ Create Goal"
          onAction={handleOpenAdd}
        />
      ) : null}

      {/* Add / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/35 backdrop-blur-xs animate-fadeIn">
          <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl shadow-xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-semibold text-slate-900">
                {editingGoal ? 'Edit Goal' : 'Create Financial Goal'}
              </h3>
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
                <label className="block text-slate-700 font-medium mb-1">Goal Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Higher Education, Emergency Fund"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">
                    Target Amount (₹) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    placeholder="100000"
                    value={formData.target_amount}
                    onChange={(e) =>
                      setFormData({ ...formData, target_amount: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-mono focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">
                    Currently Saved (₹)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    placeholder="0"
                    value={formData.current_amount}
                    onChange={(e) =>
                      setFormData({ ...formData, current_amount: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-mono focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Target Date *</label>
                  <input
                    type="date"
                    required
                    value={formData.target_date}
                    onChange={(e) =>
                      setFormData({ ...formData, target_date: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Priority</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
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
                  {submitting ? 'Saving...' : editingGoal ? 'Save Changes' : 'Create Goal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      <ConfirmModal
        isOpen={Boolean(deletingId)}
        title="Delete Goal"
        message="Are you sure you want to remove this financial goal? Your transactions and ledger history will remain unaffected."
        confirmLabel="Delete"
        isDangerous={true}
        onConfirm={handleDelete}
        onCancel={() => setDeletingId(null)}
      />
    </div>
  );
};
