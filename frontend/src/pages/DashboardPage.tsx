import React, { useEffect, useState } from 'react';
import {
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  AlertTriangle,
  UploadCloud,
  Percent,
  Plus,
  Target,
  FileSpreadsheet,
} from 'lucide-react';
import { StatCard } from '../components/common/StatCard';
import { api } from '../services/api';
import { AnalyticsSummary, DataQualitySummary, Goal, Transaction } from '../types';
import { formatINR, formatDate, formatPercent } from '../utils/formatters';

interface DashboardPageProps {
  onNavigateTab: (tab: any) => void;
  refreshKey: number;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigateTab, refreshKey }) => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [quality, setQuality] = useState<DataQualitySummary | null>(null);
  const [recentTxns, setRecentTxns] = useState<Transaction[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [sumRes, qualRes, txRes, goalRes] = await Promise.all([
          api.getAnalyticsSummary(),
          api.getDataQualitySummary(),
          api.getTransactions({ page: 1, page_size: 5 }),
          api.getGoals(),
        ]);
        setSummary(sumRes);
        setQuality(qualRes);
        setRecentTxns(txRes.items || []);
        setGoals(goalRes || []);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [refreshKey]);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">Financial Overview</h2>
          <p className="text-sm text-slate-400">
            Deterministic cash flow analysis, verified data quality metrics, and goal tracking.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigateTab('import')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 hover:bg-cyan-500/20 transition"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Import CSV</span>
          </button>
          <button
            onClick={() => onNavigateTab('transactions')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-600/20 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Add Transaction</span>
          </button>
        </div>
      </div>

      {/* Phase 2: Data Quality & Lineage Health Banner */}
      {quality && (
        <div className="p-4 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900/90 to-slate-900/50 backdrop-blur-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-slate-100">Data Engineering & Quality Status</h3>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  Phase 2 Verified
                </span>
              </div>
              <p className="text-xs text-slate-400">
                {quality.total_transactions} total records • {quality.valid_transactions} fully verified •{' '}
                {quality.warning_transactions} flagged with review warnings
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <CheckCircle2 className="w-4 h-4" />
              <span>{quality.valid_transactions} Clean</span>
            </div>
            {quality.possible_duplicates > 0 && (
              <div className="flex items-center gap-1.5 text-amber-400 font-medium">
                <AlertTriangle className="w-4 h-4" />
                <span>{quality.possible_duplicates} Duplicate Warnings</span>
              </div>
            )}
            <button
              onClick={() => onNavigateTab('import')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold underline underline-offset-4"
            >
              Batch Ingestion →
            </button>
          </div>
        </div>
      )}

      {/* Financial Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Income"
          value={formatINR(summary?.total_income)}
          subtitle="Recorded incoming funds"
          icon={ArrowUpRight}
          color="emerald"
        />
        <StatCard
          title="Total Expenses"
          value={formatINR(summary?.total_expenses)}
          subtitle="Recorded outgoing funds"
          icon={ArrowDownRight}
          color="rose"
        />
        <StatCard
          title="Net Cash Flow"
          value={formatINR(summary?.net_savings)}
          subtitle="Deterministic income - expenses"
          icon={CheckCircle2}
          color="cyan"
        />
        <StatCard
          title="Savings Rate"
          value={formatPercent(summary?.savings_rate)}
          subtitle="Percentage of income retained"
          icon={Percent}
          color="purple"
        />
      </div>

      {/* Two Column Grid: Goals & Category Spending */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Breakdown (2 Cols) */}
        <div className="lg:col-span-2 p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-100">Category Spending Distribution</h3>
            <span className="text-xs text-slate-400">Expense Breakdown</span>
          </div>

          {summary?.category_breakdown && summary.category_breakdown.length > 0 ? (
            <div className="space-y-3.5 pt-2">
              {summary.category_breakdown.map((item) => {
                const pct = typeof item.percentage === 'string' ? parseFloat(item.percentage) : item.percentage;
                return (
                  <div key={item.category} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-slate-300">{item.category}</span>
                      <span className="text-slate-400 font-mono">
                        {formatINR(item.total_amount)} ({formatPercent(pct)})
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-emerald-500 to-cyan-400 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500 text-sm">
              No expense categories recorded yet. Import transactions to populate category analytics.
            </div>
          )}
        </div>

        {/* Goals Summary (1 Col) */}
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-emerald-400" />
              <h3 className="text-base font-semibold text-slate-100">Active Goals</h3>
            </div>
            <button
              onClick={() => onNavigateTab('goals')}
              className="text-xs text-emerald-400 hover:text-emerald-300 font-medium"
            >
              View All
            </button>
          </div>

          <div className="space-y-4 pt-1">
            {goals.length > 0 ? (
              goals.slice(0, 3).map((g) => {
                const prog = typeof g.progress_percentage === 'string' ? parseFloat(g.progress_percentage) : g.progress_percentage;
                return (
                  <div key={g.id} className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 space-y-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-xs font-semibold text-slate-200">{g.name}</p>
                        <p className="text-[10px] text-slate-500">Target: {formatDate(g.target_date)}</p>
                      </div>
                      <span className="text-xs font-bold text-emerald-400 font-mono">{formatPercent(prog)}</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${Math.min(prog, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                      <span>Saved: {formatINR(g.current_amount)}</span>
                      <span>Target: {formatINR(g.target_amount)}</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-8 text-center text-slate-500 text-xs">
                No active goals created yet.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Transactions Table */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-slate-100">Recent Transactions</h3>
            <p className="text-xs text-slate-400">Latest financial records retrieved from backend persistence</p>
          </div>
          <button
            onClick={() => onNavigateTab('transactions')}
            className="text-xs font-medium text-cyan-400 hover:text-cyan-300"
          >
            Open Transactions Page →
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-800">
              <tr>
                <th className="py-3 px-3">Date</th>
                <th className="py-3 px-3">Description</th>
                <th className="py-3 px-3">Category</th>
                <th className="py-3 px-3">Type</th>
                <th className="py-3 px-3">Lineage</th>
                <th className="py-3 px-3 text-right">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {recentTxns.length > 0 ? (
                recentTxns.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3 px-3 text-slate-400 font-mono">{formatDate(tx.transaction_date)}</td>
                    <td className="py-3 px-3 font-medium text-slate-200">{tx.description}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                        {tx.category}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`capitalize font-semibold text-[10px] ${
                          tx.transaction_type === 'income' ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        {tx.transaction_type}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                        {tx.source_type}
                      </span>
                    </td>
                    <td
                      className={`py-3 px-3 text-right font-mono font-bold ${
                        tx.transaction_type === 'income' ? 'text-emerald-400' : 'text-slate-200'
                      }`}
                    >
                      {tx.transaction_type === 'income' ? '+' : '-'}
                      {formatINR(tx.amount)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No transactions recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
