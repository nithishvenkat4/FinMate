import React, { useEffect, useState } from 'react';
import {
  Edit2,
  Plus,
  Receipt,
  Search,
  Trash2,
  UploadCloud,
  X,
} from 'lucide-react';
import { ConfirmModal } from '../components/common/ConfirmModal';
import { EmptyState } from '../components/common/EmptyState';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { api } from '../services/api';
import { Transaction, TransactionCategory } from '../types';
import { formatINR, formatDate } from '../utils/formatters';

interface TransactionsPageProps {
  refreshKey: number;
  onRefresh: () => void;
  onNavigateTab?: (tab: any) => void;
}

export const TransactionsPage: React.FC<TransactionsPageProps> = ({
  refreshKey,
  onRefresh,
  onNavigateTab,
}) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<TransactionCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'income' | 'expense'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  // Add / Edit Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTx, setEditingTx] = useState<Transaction | null>(null);
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    transaction_type: 'expense',
    category: 'Food',
    transaction_date: new Date().toISOString().split('T')[0],
    notes: '',
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Delete modal state
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const [txRes, catRes] = await Promise.all([
        api.getTransactions({
          transaction_type: typeFilter === 'all' ? undefined : typeFilter,
          category: categoryFilter === 'all' ? undefined : categoryFilter,
          page: 1,
          page_size: 100,
        }),
        api.getCategories(),
      ]);
      setTransactions(txRes.items || []);
      setCategories(catRes || []);
    } catch (err) {
      console.error('Failed to load transactions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [typeFilter, categoryFilter, refreshKey]);

  const handleOpenAdd = () => {
    setEditingTx(null);
    setFormData({
      description: '',
      amount: '',
      transaction_type: 'expense',
      category: categories.length > 0 ? categories[0].name : 'Food',
      transaction_date: new Date().toISOString().split('T')[0],
      notes: '',
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (tx: Transaction) => {
    setEditingTx(tx);
    setFormData({
      description: tx.description,
      amount: tx.amount.toString(),
      transaction_type: tx.transaction_type,
      category: tx.category,
      transaction_date: tx.transaction_date,
      notes: tx.notes || '',
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.description.trim()) {
      setFormError('Please enter a description.');
      return;
    }
    const amtNum = parseFloat(formData.amount);
    if (isNaN(amtNum) || amtNum <= 0) {
      setFormError('Amount must be a valid number greater than zero.');
      return;
    }

    setSubmitting(true);
    setFormError(null);
    try {
      if (editingTx) {
        await api.updateTransaction(editingTx.id, {
          description: formData.description.trim(),
          amount: amtNum,
          transaction_type: formData.transaction_type as 'income' | 'expense',
          category: formData.category,
          transaction_date: formData.transaction_date,
          notes: formData.notes.trim() || undefined,
        });
      } else {
        await api.createTransaction({
          description: formData.description.trim(),
          amount: amtNum,
          transaction_type: formData.transaction_type as 'income' | 'expense',
          category: formData.category,
          transaction_date: formData.transaction_date,
          notes: formData.notes.trim() || undefined,
        });
      }
      setIsModalOpen(false);
      onRefresh();
      fetchTransactions();
    } catch (err: any) {
      setFormError(err.message || 'Failed to save transaction.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await api.deleteTransaction(deletingId);
      setDeletingId(null);
      onRefresh();
      fetchTransactions();
    } catch (err) {
      console.error('Failed to delete transaction:', err);
    }
  };

  const filtered = transactions.filter(
    (tx) =>
      tx.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tx.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (tx.notes && tx.notes.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Transactions</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            View and manage your recorded income and expenses.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          {onNavigateTab && (
            <button
              onClick={() => onNavigateTab('import')}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 shadow-xs transition"
            >
              <UploadCloud className="w-3.5 h-3.5 text-slate-500" />
              <span>Import CSV</span>
            </button>
          )}
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Transaction</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl border border-slate-200/80 bg-white shadow-xs flex flex-col md:flex-row gap-3.5 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-2.5" />
          <input
            type="text"
            placeholder="Search description, category, notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:bg-white transition"
          />
        </div>

        <div className="flex items-center flex-wrap gap-3 w-full md:w-auto justify-end">
          {/* Category Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Category:</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-700 focus:outline-none focus:border-teal-500 focus:bg-white transition"
            >
              <option value="all">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Type Segmented Control */}
          <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200 text-xs">
            <button
              onClick={() => setTypeFilter('all')}
              className={`px-3 py-1 rounded-lg font-medium transition ${
                typeFilter === 'all'
                  ? 'bg-white text-slate-900 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setTypeFilter('income')}
              className={`px-3 py-1 rounded-lg font-medium transition ${
                typeFilter === 'income'
                  ? 'bg-white text-emerald-700 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Income
            </button>
            <button
              onClick={() => setTypeFilter('expense')}
              className={`px-3 py-1 rounded-lg font-medium transition ${
                typeFilter === 'expense'
                  ? 'bg-white text-rose-700 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Expense
            </button>
          </div>
        </div>
      </div>

      {/* Transactions Table Card */}
      {loading ? (
        <TableSkeleton rows={8} />
      ) : transactions.length === 0 ? (
        <EmptyState
          icon={Receipt}
          title="No transactions yet"
          description="Start tracking your cash flow by recording your first transaction or importing a CSV bank statement."
          actionLabel="+ Add Transaction"
          onAction={handleOpenAdd}
          secondaryActionLabel="Import CSV"
          onSecondaryAction={() => onNavigateTab && onNavigateTab('import')}
        />
      ) : (
        <div className="rounded-2xl border border-slate-200/80 bg-white shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-100 bg-slate-50/60 font-semibold">
                <tr>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Description & Notes</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.length > 0 ? (
                  filtered.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-50/80 transition">
                      <td className="py-3.5 px-4 text-slate-500 whitespace-nowrap">
                        {formatDate(tx.transaction_date)}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900">{tx.description}</div>
                        {tx.notes && (
                          <div className="text-[11px] text-slate-500 line-clamp-1">{tx.notes}</div>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                          {tx.category}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`capitalize font-semibold text-[11px] px-2 py-0.5 rounded-full ${
                            tx.transaction_type === 'income'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
                              : 'bg-rose-50 text-rose-700 border border-rose-100'
                          }`}
                        >
                          {tx.transaction_type}
                        </span>
                      </td>
                      <td
                        className={`py-3.5 px-4 text-right font-mono font-bold text-sm ${
                          tx.transaction_type === 'income' ? 'text-emerald-600' : 'text-slate-900'
                        }`}
                      >
                        {tx.transaction_type === 'income' ? '+' : '-'}
                        {formatINR(tx.amount)}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handleOpenEdit(tx)}
                            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition"
                            title="Edit"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => setDeletingId(tx.id)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 transition"
                            title="Delete"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      No matching transactions found for this search or filter.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add / Edit Transaction Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/35 backdrop-blur-xs animate-fadeIn">
          <div className="w-full max-w-lg bg-white border border-slate-200 rounded-2xl shadow-xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-semibold text-slate-900">
                {editingTx ? 'Edit Transaction' : 'Record Transaction'}
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
                <label className="block text-slate-700 font-medium mb-1">
                  Description / Payee *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Swiggy, Amazon, Monthly Salary"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:bg-white transition"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Amount (₹) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    placeholder="0.00"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 font-mono focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">
                    Transaction Type *
                  </label>
                  <select
                    value={formData.transaction_type}
                    onChange={(e) =>
                      setFormData({ ...formData, transaction_type: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  >
                    <option value="expense">Expense</option>
                    <option value="income">Income</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Category *</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.name}>
                        {c.name}
                      </option>
                    ))}
                    {categories.length === 0 && <option value="Other">Other</option>}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Date *</label>
                  <input
                    type="date"
                    required
                    value={formData.transaction_date}
                    onChange={(e) =>
                      setFormData({ ...formData, transaction_date: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-medium mb-1">
                  Notes / Remarks (Optional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Additional context or invoice memo..."
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:bg-white transition"
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
                  {submitting
                    ? 'Saving...'
                    : editingTx
                    ? 'Save Changes'
                    : 'Record Transaction'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={Boolean(deletingId)}
        title="Delete Transaction"
        message="Are you sure you want to permanently delete this transaction? This action will remove it from your financial totals and category breakdowns."
        confirmLabel="Delete"
        isDangerous={true}
        onConfirm={handleDelete}
        onCancel={() => setDeletingId(null)}
      />
    </div>
  );
};
