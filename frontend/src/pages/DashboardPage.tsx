import React, { useEffect, useState } from 'react';
import {
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  Percent,
  Plus,
  Target,
  Sparkles,
  TrendingUp,
  Receipt,
  AlertCircle,
  ArrowRight,
  Compass,
  Wallet,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { StatCard } from '../components/common/StatCard';
import { EmptyState } from '../components/common/EmptyState';
import { StatCardSkeleton, TableSkeleton } from '../components/common/LoadingSkeleton';
import { api } from '../services/api';
import { AnalyticsSummary, Goal, Transaction } from '../types';
import { formatINR, formatDate, formatPercent } from '../utils/formatters';

interface DashboardPageProps {
  onNavigateTab: (tab: any) => void;
  refreshKey: number;
}

const CATEGORY_COLORS = [
  '#0d9488', // teal
  '#3b82f6', // blue
  '#8b5cf6', // purple
  '#f59e0b', // amber
  '#f43f5e', // rose
  '#10b981', // emerald
  '#6366f1', // indigo
  '#64748b', // slate
];

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigateTab, refreshKey }) => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [recentTxns, setRecentTxns] = useState<Transaction[]>([]);
  const [allTxns, setAllTxns] = useState<Transaction[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [sumRes, txRecentRes, txAllRes, goalRes, profRes] = await Promise.all([
          api.getAnalyticsSummary().catch(() => null),
          api.getTransactions({ page: 1, page_size: 5 }).catch(() => ({ items: [] })),
          api.getTransactions({ page: 1, page_size: 100 }).catch(() => ({ items: [] })),
          api.getGoals().catch(() => []),
          api.getProfile().catch(() => null),
        ]);
        setSummary(sumRes);
        setRecentTxns(txRecentRes.items || []);
        setAllTxns(txAllRes.items || []);
        setGoals(goalRes || []);
        setProfile(profRes);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [refreshKey]);

  // Aggregate monthly trend from real transactions
  const monthlyTrendData = React.useMemo(() => {
    if (!allTxns || allTxns.length === 0) return [];
    const monthlyMap: Record<string, { month: string; income: number; expense: number }> = {};

    allTxns.forEach((tx) => {
      if (!tx.transaction_date) return;
      const date = new Date(tx.transaction_date);
      if (isNaN(date.getTime())) return;
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const label = date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });

      if (!monthlyMap[key]) {
        monthlyMap[key] = { month: label, income: 0, expense: 0 };
      }
      const amt = typeof tx.amount === 'string' ? parseFloat(tx.amount) : tx.amount;
      if (tx.transaction_type === 'income') {
        monthlyMap[key].income += amt || 0;
      } else {
        monthlyMap[key].expense += amt || 0;
      }
    });

    return Object.keys(monthlyMap)
      .sort()
      .map((k) => monthlyMap[k]);
  }, [allTxns]);

  // Derive honest, real insights from backend data
  const insights = React.useMemo(() => {
    if (!summary) return [];
    const list: Array<{ title: string; desc: string; icon: any; color: string }> = [];

    if (summary.category_breakdown && summary.category_breakdown.length > 0) {
      const topCat = summary.category_breakdown[0];
      const pct = typeof topCat.percentage === 'string' ? parseFloat(topCat.percentage) : topCat.percentage;
      list.push({
        title: 'Top Spending Category',
        desc: `${topCat.category} is your largest expense at ${formatINR(topCat.total_amount)} (${formatPercent(pct)} of total spending).`,
        icon: TrendingUp,
        color: 'text-teal-600 bg-teal-50 border-teal-100',
      });
    }

    const savingsRate = typeof summary.savings_rate === 'string' ? parseFloat(summary.savings_rate) : summary.savings_rate;
    const totalIncome = typeof summary.total_income === 'string' ? parseFloat(summary.total_income) : summary.total_income;
    if (savingsRate > 20) {
      list.push({
        title: 'Healthy Savings Rate',
        desc: `You are saving ${formatPercent(savingsRate)} of your income this month, exceeding the 20% standard benchmark.`,
        icon: CheckCircle2,
        color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
      });
    } else if (savingsRate < 10 && (totalIncome || 0) > 0) {
      list.push({
        title: 'Savings Opportunity',
        desc: `Your savings rate is currently ${formatPercent(savingsRate)}. Consider reviewing discretionary expenses to boost your buffer.`,
        icon: AlertCircle,
        color: 'text-amber-600 bg-amber-50 border-amber-100',
      });
    }

    if (goals.length > 0) {
      const highestGoal = [...goals].sort((a, b) => {
        const pa = typeof a.progress_percentage === 'string' ? parseFloat(a.progress_percentage) : a.progress_percentage;
        const pb = typeof b.progress_percentage === 'string' ? parseFloat(b.progress_percentage) : b.progress_percentage;
        return pb - pa;
      })[0];
      const prog = typeof highestGoal.progress_percentage === 'string' ? parseFloat(highestGoal.progress_percentage) : highestGoal.progress_percentage;
      list.push({
        title: 'Active Goal Progress',
        desc: `Your "${highestGoal.name}" goal has reached ${formatPercent(prog)} completion (${formatINR(highestGoal.current_amount)} saved).`,
        icon: Target,
        color: 'text-blue-600 bg-blue-50 border-blue-100',
      });
    }

    return list;
  }, [summary, goals]);

  const hasProfileData = Boolean(
    profile && (Number(profile.monthly_income) > 0 || Number(profile.current_savings) > 0)
  );
  const hasData = Boolean(summary && (summary.transaction_count > 0 || goals.length > 0 || hasProfileData));

  const profileSurplus = Math.max(
    0,
    (Number(profile?.monthly_income) || 0) - (Number(profile?.monthly_fixed_expenses) || 0)
  );
  const coverageMonths =
    profile && Number(profile.monthly_fixed_expenses) > 0
      ? (Number(profile.current_savings || 0) / Number(profile.monthly_fixed_expenses)).toFixed(1)
      : null;

  if (loading) {
    return (
      <div className="space-y-6 animate-fadeIn">
        <div className="flex justify-between items-center py-2">
          <div className="space-y-2">
            <div className="h-6 w-48 bg-slate-200 rounded-md animate-pulse" />
            <div className="h-4 w-72 bg-slate-100 rounded-md animate-pulse" />
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </div>
        <TableSkeleton rows={4} />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. Greeting & Quick Actions Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Good morning</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Keep track of your spending, savings, and financial goals in one place.
          </p>
        </div>

        {/* Quick Actions Bar */}
        <div className="flex items-center flex-wrap gap-2.5">
          <button
            onClick={() => onNavigateTab('decisions')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Decision Studio</span>
          </button>
          <button
            onClick={() => onNavigateTab('transactions')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 shadow-xs transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Transaction</span>
          </button>
          <button
            onClick={() => onNavigateTab('goals')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium bg-white text-slate-700 border border-slate-200 hover:bg-slate-50 hover:border-slate-300 shadow-xs transition"
          >
            <Target className="w-3.5 h-3.5 text-slate-500" />
            <span>Create Goal</span>
          </button>
          <button
            onClick={() => onNavigateTab('ai-advisor')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-medium bg-teal-50 text-teal-800 border border-teal-100 hover:bg-teal-100 transition"
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            <span>Ask Advisor</span>
          </button>
        </div>
      </div>

      {/* Financial Profile Baseline Snapshot */}
      {profile && (
        <div className="p-4 sm:p-5 rounded-2xl border border-teal-100 bg-linear-to-r from-teal-50/60 via-white to-slate-50 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Wallet className="w-4 h-4 text-teal-600" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Active Financial Profile Baselines
              </h2>
            </div>
            <button
              onClick={() => onNavigateTab('profile')}
              className="text-xs font-semibold text-teal-700 hover:text-teal-800 hover:underline transition flex items-center gap-1"
            >
              <span>Edit Profile</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-1">
              <span className="text-[11px] text-slate-400 block font-medium">Monthly Income</span>
              <span className="text-sm font-bold text-slate-900 font-mono block">
                {formatINR(profile.monthly_income)}
              </span>
              <span className="text-[10px] text-emerald-600 block">Baseline inflow</span>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-1">
              <span className="text-[11px] text-slate-400 block font-medium">Fixed Expenses</span>
              <span className="text-sm font-bold text-slate-900 font-mono block">
                {formatINR(profile.monthly_fixed_expenses)}
              </span>
              <span className="text-[10px] text-slate-500 block">Monthly commitments</span>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-1">
              <span className="text-[11px] text-slate-400 block font-medium">Planned Monthly Surplus</span>
              <span className="text-sm font-bold text-teal-700 font-mono block">
                {formatINR(profileSurplus)}
              </span>
              <span className="text-[10px] text-teal-600 block">Discretionary margin</span>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-1">
              <span className="text-[11px] text-slate-400 block font-medium">Liquid Savings</span>
              <span className="text-sm font-bold text-slate-900 font-mono block">
                {formatINR(profile.current_savings)}
              </span>
              <span className="text-[10px] text-blue-600 block">
                {coverageMonths ? `${coverageMonths} mo emergency buffer` : 'Available reserve'}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-1">
              <span className="text-[11px] text-slate-400 block font-medium">Risk Stance</span>
              <span className="text-sm font-bold text-slate-800 capitalize block">
                {profile.risk_preference || 'Moderate'}
              </span>
              <span className="text-[10px] text-slate-500 block">Scenario strategy</span>
            </div>
          </div>
        </div>
      )}

      {/* When no transactions or goals exist at all and no profile, present polished onboarding empty state */}
      {!hasData && (
        <EmptyState
          icon={Receipt}
          title="Welcome to FinMate"
          description="Start by configuring your financial profile, adding your first transaction, or importing your bank statement to see your cash flow, category breakdowns, and goal tracking come alive."
          actionLabel="+ Set Financial Profile"
          onAction={() => onNavigateTab('profile')}
          secondaryActionLabel="Import CSV Statement"
          onSecondaryAction={() => onNavigateTab('import')}
        />
      )}

      {/* 2. Key Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title="Monthly Income"
          value={formatINR(
            summary && summary.transaction_count > 0 && Number(summary.total_income) > 0
              ? summary.total_income
              : profile?.monthly_income
          )}
          subtitle={
            summary && summary.transaction_count > 0 && Number(summary.total_income) > 0
              ? (profile?.monthly_income ? `Profile: ${formatINR(profile.monthly_income)}/mo` : 'Recorded incoming funds')
              : 'Profile baseline income'
          }
          icon={ArrowUpRight}
          color="emerald"
        />
        <StatCard
          title="Total Expenses"
          value={formatINR(
            summary && summary.transaction_count > 0 && Number(summary.total_expenses) > 0
              ? summary.total_expenses
              : profile?.monthly_fixed_expenses
          )}
          subtitle={
            summary && summary.transaction_count > 0 && Number(summary.total_expenses) > 0
              ? (profile?.monthly_fixed_expenses ? `Fixed: ${formatINR(profile.monthly_fixed_expenses)}/mo` : 'Recorded outgoing funds')
              : 'Fixed commitments'
          }
          icon={ArrowDownRight}
          color="rose"
        />
        <StatCard
          title="Net Cash Flow"
          value={formatINR(
            summary && summary.transaction_count > 0
              ? summary.net_savings
              : profileSurplus
          )}
          subtitle={summary && summary.transaction_count > 0 ? 'Income minus expenses' : 'Planned monthly surplus'}
          icon={CheckCircle2}
          color="teal"
        />
        <StatCard
          title="Liquid Savings"
          value={formatINR(profile?.current_savings !== undefined && profile?.current_savings !== null ? profile.current_savings : summary?.net_savings)}
          subtitle={coverageMonths ? `${coverageMonths} mo buffer coverage` : 'Available liquid cushion'}
          icon={Wallet}
          color="cyan"
        />
        <StatCard
          title="Savings Rate"
          value={formatPercent(
            summary && summary.transaction_count > 0
              ? summary.savings_rate
              : (Number(profile?.monthly_income) > 0
                  ? (profileSurplus / Number(profile.monthly_income)) * 100
                  : 0)
          )}
          subtitle={summary && summary.transaction_count > 0 ? 'Percentage of income retained' : 'Planned savings margin'}
          icon={Percent}
          color="purple"
        />
      </div>

      {/* 2.5. HERO DECISION ENTRY POINT: "What are you planning?" */}
      <div className="p-6 rounded-2xl border border-teal-200/90 bg-linear-to-r from-teal-50/70 via-white to-slate-50 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shrink-0 shadow-xs">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900">What are you planning?</h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-teal-100 text-teal-800">
                  Decision Intelligence
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-0.5">
                See the financial consequences before you make a decision. FinMate models the impact on your liquid reserves, monthly cashflow, and goal milestones.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigateTab('decisions')}
            className="self-start md:self-auto flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition shrink-0"
          >
            <span>Open Decision Studio</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Quick launch interactive chips */}
        <div className="pt-2 border-t border-teal-100/80">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
            Explore Decision Scenarios
          </span>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => onNavigateTab('decisions')}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-teal-500 hover:bg-teal-50/50 text-xs font-medium text-slate-700 transition flex items-center gap-1.5 shadow-2xs"
            >
              <span className="text-teal-600 font-semibold">₹20,000</span>
              <span>Can I afford a laptop?</span>
            </button>
            <button
              onClick={() => onNavigateTab('decisions')}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-teal-500 hover:bg-teal-50/50 text-xs font-medium text-slate-700 transition flex items-center gap-1.5 shadow-2xs"
            >
              <span className="text-emerald-600 font-semibold">+₹5,000</span>
              <span>What if I save more every month?</span>
            </button>
            <button
              onClick={() => onNavigateTab('decisions')}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-teal-500 hover:bg-teal-50/50 text-xs font-medium text-slate-700 transition flex items-center gap-1.5 shadow-2xs"
            >
              <span className="text-blue-600 font-semibold">Target Milestone</span>
              <span>Can I reach my education goal sooner?</span>
            </button>
            <button
              onClick={() => onNavigateTab('decisions')}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-teal-500 hover:bg-teal-50/50 text-xs font-medium text-slate-700 transition flex items-center gap-1.5 shadow-2xs"
            >
              <span className="text-rose-600 font-semibold">+₹3,000</span>
              <span>What if my rent increases?</span>
            </button>
          </div>
        </div>
      </div>

      {/* 3. Middle Section: Expense Breakdown & Monthly Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Expense Breakdown (5 Cols) */}
        <div className="lg:col-span-5 p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Expense Breakdown</h2>
              <p className="text-[11px] text-slate-500">Distribution across categories</p>
            </div>
            {summary?.total_expenses ? (
              <span className="text-xs font-semibold text-slate-700 font-mono">
                {formatINR(summary.total_expenses)}
              </span>
            ) : null}
          </div>

          {summary?.category_breakdown && summary.category_breakdown.length > 0 ? (
            <div className="space-y-4">
              <div className="h-48 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={summary.category_breakdown.map((item) => ({
                        name: item.category,
                        value:
                          typeof item.total_amount === 'string'
                            ? parseFloat(item.total_amount)
                            : item.total_amount,
                      }))}
                      cx="50%"
                      cy="50%"
                      innerRadius={48}
                      outerRadius={75}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {summary.category_breakdown.map((_, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <RechartsTooltip
                      formatter={(val: any) => [formatINR(val), 'Amount']}
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        borderRadius: '12px',
                        border: '1px solid #E2E8F0',
                        fontSize: '12px',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Clean Legend List */}
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {summary.category_breakdown.map((item, idx) => {
                  const pct =
                    typeof item.percentage === 'string'
                      ? parseFloat(item.percentage)
                      : item.percentage;
                  return (
                    <div
                      key={item.category}
                      className="flex items-center justify-between text-xs py-1 px-1.5 rounded-lg hover:bg-slate-50"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full shrink-0"
                          style={{
                            backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length],
                          }}
                        />
                        <span className="font-medium text-slate-700">{item.category}</span>
                      </div>
                      <div className="flex items-center gap-2 font-mono">
                        <span className="text-slate-900 font-semibold">
                          {formatINR(item.total_amount)}
                        </span>
                        <span className="text-slate-400 text-[11px]">({formatPercent(pct)})</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-400 text-xs">
              No expense categories recorded yet. Add transactions to see breakdown.
            </div>
          )}
        </div>

        {/* Monthly Trend (7 Cols) */}
        <div className="lg:col-span-7 p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Monthly Trend</h2>
              <p className="text-[11px] text-slate-500">Income vs. expenses comparison</p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-teal-500" />
                <span className="text-slate-600 text-[11px]">Income</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-400" />
                <span className="text-slate-600 text-[11px]">Expenses</span>
              </div>
            </div>
          </div>

          {monthlyTrendData.length > 0 ? (
            <div className="h-64 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    axisLine={{ stroke: '#e2e8f0' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `₹${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`}
                  />
                  <RechartsTooltip
                    formatter={(val: any) => [formatINR(val)]}
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderRadius: '12px',
                      border: '1px solid #E2E8F0',
                      fontSize: '12px',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                    }}
                  />
                  <Bar dataKey="income" name="Income" fill="#0d9488" radius={[4, 4, 0, 0]} maxBarSize={32} />
                  <Bar dataKey="expense" name="Expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} maxBarSize={32} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="py-20 text-center text-slate-400 text-xs">
              No historical trend data recorded yet.
            </div>
          )}
        </div>
      </div>

      {/* 4. Active Goals & Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Active Goals (5 Cols) */}
        <div className="lg:col-span-5 p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-teal-600" />
              <h2 className="text-sm font-semibold text-slate-900">Active Goals</h2>
            </div>
            <button
              onClick={() => onNavigateTab('goals')}
              className="text-xs text-teal-600 hover:text-teal-700 font-medium flex items-center gap-1"
            >
              <span>View All</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3.5 pt-1">
            {goals.length > 0 ? (
              goals.slice(0, 3).map((g) => {
                const prog =
                  typeof g.progress_percentage === 'string'
                    ? parseFloat(g.progress_percentage)
                    : g.progress_percentage;
                return (
                  <div
                    key={g.id}
                    className="p-3.5 rounded-xl border border-slate-100 bg-slate-50/60 space-y-2 hover:bg-slate-50 transition"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="text-xs font-semibold text-slate-800">{g.name}</p>
                        <p className="text-[11px] text-slate-500">Target: {formatDate(g.target_date)}</p>
                      </div>
                      <span className="text-xs font-bold text-teal-700 font-mono">
                        {formatPercent(prog)}
                      </span>
                    </div>

                    <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-teal-600 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(prog, 100)}%` }}
                      />
                    </div>

                    <div className="flex justify-between text-[11px] text-slate-500 font-mono">
                      <span>Saved: {formatINR(g.current_amount)}</span>
                      <span>Target: {formatINR(g.target_amount)}</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="py-8 text-center text-slate-400 text-xs">
                No goals created yet. Click "Create Goal" to start planning savings targets.
              </div>
            )}
          </div>
        </div>

        {/* Recent Transactions (7 Cols) */}
        <div className="lg:col-span-7 p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Recent Transactions</h2>
              <p className="text-[11px] text-slate-500">Latest entries from your ledger</p>
            </div>
            <button
              onClick={() => onNavigateTab('transactions')}
              className="text-xs text-teal-600 hover:text-teal-700 font-medium flex items-center gap-1"
            >
              <span>All Transactions</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                <tr>
                  <th className="py-2.5 px-3 font-medium">Date</th>
                  <th className="py-2.5 px-3 font-medium">Description</th>
                  <th className="py-2.5 px-3 font-medium">Category</th>
                  <th className="py-2.5 px-3 text-right font-medium">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentTxns.length > 0 ? (
                  recentTxns.map((tx) => (
                    <tr key={tx.id} className="hover:bg-slate-50/80 transition">
                      <td className="py-3 px-3 text-slate-500 whitespace-nowrap">
                        {formatDate(tx.transaction_date)}
                      </td>
                      <td className="py-3 px-3">
                        <span className="font-semibold text-slate-800">{tx.description}</span>
                        {tx.notes && <span className="block text-[10px] text-slate-400 line-clamp-1">{tx.notes}</span>}
                      </td>
                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                          {tx.category}
                        </span>
                      </td>
                      <td
                        className={`py-3 px-3 text-right font-mono font-semibold ${
                          tx.transaction_type === 'income' ? 'text-emerald-600' : 'text-slate-800'
                        }`}
                      >
                        {tx.transaction_type === 'income' ? '+' : '-'}
                        {formatINR(tx.amount)}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-400">
                      No recent transactions recorded.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 5. FinMate Financial Insights Card */}
      {insights.length > 0 && (
        <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-teal-600" />
            <h2 className="text-sm font-semibold text-slate-900">Financial Insights</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {insights.map((ins, i) => {
              const Icon = ins.icon;
              return (
                <div key={i} className="p-4 rounded-xl border border-slate-100 bg-slate-50/60 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-lg border ${ins.color}`}>
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-semibold text-slate-800">{ins.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed pl-1">{ins.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
