import React, { useState, useEffect } from 'react';
import {
  Compass,
  ArrowRight,
  Target,
  ShieldCheck,
  AlertTriangle,
  Layers,
  History,
  Trash2,
  Bookmark,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  Minus,
  Sliders,
  Sparkles,
} from 'lucide-react';
import { api } from '../services/api';
import {
  DecisionSimulateRequest,
  DecisionSimulationResponse,
  DecisionListItem,
  Goal,
  ScenarioCompareResponse,
  DecisionType,
} from '../types';
import { formatINR, formatDate } from '../utils/formatters';
import { EmptyState } from '../components/common/EmptyState';

interface DecisionsPageProps {
  onNavigateTab?: (tab: any) => void;
  initialQuery?: string;
  initialAmount?: string;
  initialType?: DecisionType;
}

const PRESET_DECISIONS: Array<{
  type: DecisionType;
  title: string;
  amount: number;
  category: string;
  description: string;
}> = [
  {
    type: 'purchase',
    title: 'Laptop Purchase',
    amount: 20000,
    category: 'Education',
    description: 'Evaluate paying immediately vs. waiting to save from surplus.',
  },
  {
    type: 'purchase',
    title: 'Smartphone Upgrade',
    amount: 15000,
    category: 'Electronics',
    description: 'Check how buying an upgraded device impacts your savings coverage and goals.',
  },
  {
    type: 'saving',
    title: 'Increase Monthly Savings',
    amount: 5000,
    category: 'Savings',
    description: 'Model adding ₹5,000 more each month to accelerate your goal milestones.',
  },
  {
    type: 'expense_change',
    title: 'Rent Increase',
    amount: 3000,
    category: 'Rent & Housing',
    description: 'See the impact of a ₹3,000/month housing cost increase on your net cash flow.',
  },
  {
    type: 'goal_contribution',
    title: 'Education Goal Allocation',
    amount: 50000,
    category: 'Education',
    description: 'Model a ₹50,000 lump sum contribution toward your primary milestone.',
  },
  {
    type: 'debt_payment',
    title: 'Credit Card Repayment',
    amount: 30000,
    category: 'Debt',
    description: 'Evaluate paying full balance from liquid savings vs. gradual repayment.',
  },
  {
    type: 'subscription',
    title: 'Software & Gym Subscription',
    amount: 1500,
    category: 'Subscriptions',
    description: 'Model adding ₹1,500/month recurring cost vs. offsetting with budget cuts.',
  },
];

export const DecisionsPage: React.FC<DecisionsPageProps> = ({
  initialQuery,
  initialAmount,
  initialType,
}) => {
  const [activeView, setActiveView] = useState<'simulator' | 'history'>('simulator');

  // Simulator Form State
  const [decisionType, setDecisionType] = useState<DecisionType>(initialType || 'purchase');
  const [title, setTitle] = useState(initialQuery || 'Laptop Purchase');
  const [amount, setAmount] = useState(initialAmount || '20000');
  const [category, setCategory] = useState('Education');
  const [selectedGoalId, setSelectedGoalId] = useState<string>('');
  const [saveToHistory, setSaveToHistory] = useState(false);

  // User-Controllable Scenario Assumption State
  const [discretionaryReduction, setDiscretionaryReduction] = useState<string>('2000');
  const [showAssumptionControl, setShowAssumptionControl] = useState(false);

  // Data & Execution State
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulation, setSimulation] = useState<DecisionSimulationResponse | null>(null);
  const [comparison, setComparison] = useState<ScenarioCompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // History State
  const [historyItems, setHistoryItems] = useState<DecisionListItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    // Load active goals for selector
    api.getGoals()
      .then((res) => {
        setGoals(res || []);
        if (res && res.length > 0) {
          setSelectedGoalId(res[0].id);
        }
      })
      .catch((err) => console.error('Could not load goals:', err));
  }, []);

  useEffect(() => {
    if (activeView === 'history') {
      let isMounted = true;
      setLoadingHistory(true);
      api.getDecisions(1, 50)
        .then((res) => {
          if (isMounted) setHistoryItems(res.items || []);
        })
        .catch((err) => console.error('Failed to load decision history:', err))
        .finally(() => {
          if (isMounted) setLoadingHistory(false);
        });
      return () => {
        isMounted = false;
      };
    }
  }, [activeView]);

  const handleSimulate = async (customRequest?: DecisionSimulateRequest) => {
    setError(null);
    setSaveSuccessMsg(null);
    setIsSimulating(true);

    const numAmount = parseFloat(customRequest ? String(customRequest.amount) : amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      setError('Please specify a positive decision amount greater than ₹0.');
      setIsSimulating(false);
      return;
    }

    const customParams: Record<string, any> = {};
    const numDiscCut = parseFloat(discretionaryReduction);
    if (!isNaN(numDiscCut) && numDiscCut > 0) {
      customParams.discretionary_reduction_amount = numDiscCut;
    }

    const payload: DecisionSimulateRequest = customRequest || {
      decision_type: decisionType,
      title: title.trim() || 'Financial Decision',
      amount: numAmount,
      category: category || 'General',
      affected_goal_id: selectedGoalId || null,
      custom_parameters: customParams,
      save_to_history: saveToHistory,
    };

    try {
      const simRes = await api.simulateDecision(payload);
      setSimulation(simRes);

      // Automatically generate side-by-side comparison matrix
      const compRes = await api.compareScenarios(simRes);
      setComparison(compRes);

      if (payload.save_to_history && simRes.decision_id) {
        setSaveSuccessMsg('✓ Decision simulation saved to your history.');
      }
    } catch (err: any) {
      setError(err.message || 'We could not complete the decision simulation right now.');
    } finally {
      setIsSimulating(false);
    }
  };

  const handleApplyPreset = (preset: (typeof PRESET_DECISIONS)[0]) => {
    setDecisionType(preset.type);
    setTitle(preset.title);
    setAmount(String(preset.amount));
    setCategory(preset.category);
    handleSimulate({
      decision_type: preset.type,
      title: preset.title,
      amount: preset.amount,
      category: preset.category,
      affected_goal_id: selectedGoalId || null,
      save_to_history: false,
    });
  };

  const handleSaveCurrentSimulation = async () => {
    if (!simulation) return;
    try {
      const payload: DecisionSimulateRequest = {
        decision_type: simulation.decision.decision_type as DecisionType,
        title: simulation.decision.title,
        amount: simulation.decision.amount,
        category: simulation.decision.category,
        affected_goal_id: selectedGoalId || null,
        save_to_history: true,
      };
      await api.simulateDecision(payload);
      setSaveSuccessMsg('✓ Successfully saved this simulation to your decision history.');
    } catch (err: any) {
      setError(err.message || 'Failed to save simulation to history.');
    }
  };

  const handleDeleteHistoryItem = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteDecision(id);
      setHistoryItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      console.error('Failed to delete history item:', err);
    }
  };

  const handleSelectHistoryItem = async (id: string) => {
    try {
      setIsSimulating(true);
      const detail = await api.getDecision(id);
      setTitle(detail.title);
      setAmount(String(detail.amount));
      setDecisionType(detail.decision_type as DecisionType);
      if (detail.category) setCategory(detail.category);

      // Re-simulate to get current matrix against fresh ledger baseline
      handleSimulate({
        decision_type: detail.decision_type as DecisionType,
        title: detail.title,
        amount: detail.amount,
        category: detail.category,
        save_to_history: false,
      });
      setActiveView('simulator');
    } catch (err) {
      console.error('Failed to load decision detail:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Derive quantitative changes for the flagship "What changes?" section
  const primaryScenario = simulation?.scenarios[0];
  const primarySavingsCoverage =
    primaryScenario?.financial_impact.savings_coverage_months ||
    primaryScenario?.financial_impact.projected_emergency_buffer_months;
  const baselineSavingsCoverage =
    simulation?.baseline.savings_coverage_months ||
    simulation?.baseline.emergency_buffer_months;

  const savingsChange = primaryScenario
    ? Number(primaryScenario.financial_impact.new_savings) - Number(simulation?.baseline.current_savings || 0)
    : 0;
  const cashFlowChange = primaryScenario
    ? Number(primaryScenario.financial_impact.surplus_change)
    : 0;

  return (
    <div className="space-y-6 animate-fadeIn pb-12 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-teal-600" />
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Decision Studio
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Understand the financial impact of your decision before you make it. FinMate calculates the
            consequences for your savings, cash flow, savings coverage, and goal timelines — and leaves the choice in your hands.
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl border border-slate-200 self-start md:self-auto">
          <button
            onClick={() => setActiveView('simulator')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeView === 'simulator'
                ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Compass className="w-3.5 h-3.5 text-teal-600" />
            <span>Studio</span>
          </button>
          <button
            onClick={() => setActiveView('history')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeView === 'history'
                ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <History className="w-3.5 h-3.5 text-slate-500" />
            <span>Saved History</span>
          </button>
        </div>
      </div>

      {activeView === 'history' ? (
        /* ================= HISTORY VIEW ================= */
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">Saved Decision History</h2>
            <span className="text-xs text-slate-400 font-mono">{historyItems.length} records</span>
          </div>

          {loadingHistory ? (
            <div className="py-16 text-center text-xs text-slate-400">
              Loading simulation history...
            </div>
          ) : historyItems.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {historyItems.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSelectHistoryItem(item.id)}
                  className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-xs hover:border-teal-300 hover:shadow-sm cursor-pointer transition space-y-3.5"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="inline-block px-2 py-0.5 rounded-md text-[10px] font-semibold uppercase tracking-wider bg-teal-50 text-teal-700 border border-teal-100">
                        {item.decision_type.replace('_', ' ')}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 mt-1.5">{item.title}</h3>
                    </div>
                    <button
                      onClick={(e) => handleDeleteHistoryItem(item.id, e)}
                      className="p-1 rounded-lg text-slate-300 hover:text-rose-500 hover:bg-rose-50 transition"
                      title="Remove from history"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="flex items-baseline justify-between pt-1 border-t border-slate-100">
                    <span className="text-lg font-bold text-slate-900 font-mono">
                      {formatINR(item.amount)}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      {formatDate(item.created_at)}
                    </span>
                  </div>

                  {item.goal_impact_summary && (
                    <div className="text-xs text-slate-600 bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-100 flex items-center justify-between">
                      <span className="text-[11px] text-slate-500 font-medium">Estimated goal impact:</span>
                      <span className="font-semibold text-slate-800">{item.goal_impact_summary}</span>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-xs text-teal-600 font-medium pt-1">
                    <span>{item.scenario_count} options modeled</span>
                    <span className="flex items-center gap-1 group font-semibold">
                      View analysis <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={History}
              title="No Saved Decisions Yet"
              description="When you evaluate purchases, savings plans, or expense changes, you can save them here to review your options and trade-offs anytime."
              actionLabel="Start a New Simulation"
              onAction={() => setActiveView('simulator')}
            />
          )}
        </div>
      ) : (
        /* ================= SIMULATOR VIEW ================= */
        <div className="space-y-8">
          {/* Quick Decision Templates */}
          <div className="space-y-2">
            <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
              Quick Decision Templates
            </span>
            <div className="flex flex-wrap gap-2">
              {PRESET_DECISIONS.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleApplyPreset(p)}
                  className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-teal-500 hover:bg-teal-50/40 text-xs font-medium text-slate-700 transition flex items-center gap-1.5 shadow-2xs"
                >
                  <span className="text-teal-600 font-semibold">{formatINR(p.amount)}</span>
                  <span>{p.title}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Decision Planning Input Card */}
          <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">What are you planning?</h2>
                <p className="text-xs text-slate-500">
                  Enter the details of your planned purchase, savings target, or recurring expense change.
                </p>
              </div>
              <span className="px-2.5 py-1 rounded-lg bg-teal-50 text-teal-800 text-xs font-medium border border-teal-100 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                Read-only evaluation
              </span>
            </div>

            {error && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {saveSuccessMsg && (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-700 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>{saveSuccessMsg}</span>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
              {/* Decision Type */}
              <div className="md:col-span-3 space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Decision Type</label>
                <select
                  value={decisionType}
                  onChange={(e) => setDecisionType(e.target.value as DecisionType)}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                >
                  <option value="purchase">Purchase / Outlay</option>
                  <option value="saving">Increase Monthly Savings</option>
                  <option value="expense_change">Recurring Expense Change</option>
                  <option value="goal_contribution">Goal Capital Contribution</option>
                  <option value="debt_payment">Debt Repayment</option>
                  <option value="investment">Investment Allocation (Informational)</option>
                  <option value="subscription">Subscription</option>
                  <option value="income_change">Income Change</option>
                  <option value="custom">Custom Financial Scenario</option>
                </select>
              </div>

              {/* Title */}
              <div className="md:col-span-5 space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Description / Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Can I buy a ₹20,000 laptop?"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              {/* Amount */}
              <div className="md:col-span-4 space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Amount (INR)</label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 font-bold text-xs">
                    ₹
                  </span>
                  <input
                    type="number"
                    min="1"
                    step="100"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="20,000"
                    className="w-full pl-8 pr-3.5 py-2.5 rounded-xl border border-slate-200 text-xs font-mono font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              {/* Category */}
              <div className="md:col-span-4 space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                >
                  <option value="Education">Education</option>
                  <option value="Electronics">Electronics & Tech</option>
                  <option value="Shopping">Shopping & Lifestyle</option>
                  <option value="Rent & Housing">Rent & Housing</option>
                  <option value="Savings">Savings & Investments</option>
                  <option value="Debt">Debt Repayment</option>
                  <option value="Subscriptions">Subscriptions</option>
                  <option value="Travel">Travel & Vacations</option>
                  <option value="Vehicle">Vehicle & Transport</option>
                  <option value="Health">Health & Wellness</option>
                  <option value="General">Other / General</option>
                </select>
              </div>

              {/* Target Goal Linked */}
              <div className="md:col-span-5 space-y-1.5">
                <label className="text-xs font-semibold text-slate-700">
                  Target Goal to Evaluate (Optional)
                </label>
                <select
                  value={selectedGoalId}
                  onChange={(e) => setSelectedGoalId(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                >
                  <option value="">Evaluate all active goals</option>
                  {goals.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.name} (Target: {formatINR(g.target_amount)})
                    </option>
                  ))}
                </select>
              </div>

              {/* Save Option & CTA Button */}
              <div className="md:col-span-3 flex flex-col justify-end gap-2">
                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-600 select-none pb-1">
                  <input
                    type="checkbox"
                    checked={saveToHistory}
                    onChange={(e) => setSaveToHistory(e.target.checked)}
                    className="w-3.5 h-3.5 text-teal-600 rounded border-slate-300 focus:ring-teal-500"
                  />
                  <span>Save to history</span>
                </label>

                <button
                  onClick={() => handleSimulate()}
                  disabled={isSimulating}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white shadow-xs transition"
                >
                  {isSimulating ? (
                    <span>Evaluating scenarios...</span>
                  ) : (
                    <>
                      <span>Simulate Impact</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Optional Scenario Assumptions Control (e.g. Discretionary spending reduction) */}
            <div className="pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowAssumptionControl(!showAssumptionControl)}
                className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-teal-700 transition font-medium"
              >
                <Sliders className="w-3.5 h-3.5 text-teal-600" />
                <span>
                  {showAssumptionControl ? 'Hide custom assumptions' : 'Adjust scenario assumptions (e.g. discretionary spending cut)'}
                </span>
              </button>

              {showAssumptionControl && (
                <div className="mt-3 p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <span className="text-xs font-bold text-slate-800">
                        Monthly Discretionary Spending Reduction
                      </span>
                      <p className="text-[11px] text-slate-500">
                        Choose how much flexible spending you are willing to trim each month to offset this decision.
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-slate-900">
                        ₹{parseFloat(discretionaryReduction || '0').toLocaleString('en-IN')}
                      </span>
                      <span className="text-[10px] text-slate-400">/ month</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <input
                      type="range"
                      min="500"
                      max="10000"
                      step="500"
                      value={discretionaryReduction}
                      onChange={(e) => setDiscretionaryReduction(e.target.value)}
                      className="flex-1 accent-teal-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
                    />
                    <button
                      type="button"
                      onClick={() => handleSimulate()}
                      className="px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:border-teal-500 text-xs font-medium text-slate-700 shadow-2xs transition"
                    >
                      Update Model
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ================= SIMULATION RESULTS ================= */}
          {simulation && (
            <div className="space-y-6 animate-fadeIn">
              {/* 1. FLAGSHIP RESULT: "What changes?" */}
              <div className="p-6 rounded-2xl border-2 border-teal-500/90 bg-white shadow-xs space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                      <span>What changes?</span>
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Immediate financial delta comparing your current verified position with the decision outcome.
                    </p>
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-teal-50 text-teal-800 border border-teal-100 self-start sm:self-auto">
                    Primary: {primaryScenario?.name || 'Immediate Action'}
                  </span>
                </div>

                {/* 4 Quantitative Result Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Savings Card */}
                  <div className="p-4 rounded-xl border border-slate-200/90 bg-slate-50/70 space-y-1">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                      Liquid Savings
                    </span>
                    <div className="text-base font-bold text-slate-900 font-mono flex items-baseline gap-1.5">
                      <span>{formatINR(simulation.baseline.current_savings)}</span>
                      <span className="text-slate-400 font-normal">→</span>
                      <span>{formatINR(primaryScenario?.financial_impact.new_savings)}</span>
                    </div>
                    <div className="text-xs pt-1 flex items-center gap-1 font-semibold">
                      {savingsChange < 0 ? (
                        <span className="text-rose-600 flex items-center gap-0.5 font-mono">
                          <TrendingDown className="w-3.5 h-3.5" />
                          {formatINR(Math.abs(savingsChange))}
                        </span>
                      ) : savingsChange > 0 ? (
                        <span className="text-emerald-600 flex items-center gap-0.5 font-mono">
                          <TrendingUp className="w-3.5 h-3.5" />
                          +{formatINR(savingsChange)}
                        </span>
                      ) : (
                        <span className="text-slate-500 flex items-center gap-0.5 font-normal">
                          <Minus className="w-3 h-3 text-slate-400" /> No change
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Cash Flow Card */}
                  <div className="p-4 rounded-xl border border-slate-200/90 bg-slate-50/70 space-y-1">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                      Monthly Cash Flow
                    </span>
                    <div className="text-base font-bold text-slate-900 font-mono flex items-baseline gap-1.5">
                      <span>{formatINR(simulation.baseline.monthly_surplus)}</span>
                      <span className="text-slate-400 font-normal">→</span>
                      <span>{formatINR(primaryScenario?.financial_impact.new_monthly_surplus)}</span>
                    </div>
                    <div className="text-xs pt-1 flex items-center gap-1 font-semibold">
                      {cashFlowChange !== 0 ? (
                        <span className={cashFlowChange > 0 ? 'text-emerald-600 font-mono' : 'text-rose-600 font-mono'}>
                          {cashFlowChange > 0 ? `+${formatINR(cashFlowChange)}/mo` : `-${formatINR(Math.abs(cashFlowChange))}/mo`}
                        </span>
                      ) : (
                        <span className="text-slate-500 flex items-center gap-0.5 font-normal">
                          <Minus className="w-3 h-3 text-slate-400" /> No change
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Goal Timeline Card */}
                  <div className="p-4 rounded-xl border border-slate-200/90 bg-slate-50/70 space-y-1">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                      Goal Timeline
                    </span>
                    <div className="text-sm font-bold text-slate-900 flex items-baseline gap-1 truncate">
                      {primaryScenario?.goal_impact && primaryScenario.goal_impact.length > 0 ? (
                        <span>{primaryScenario.goal_impact[0].goal_name}</span>
                      ) : (
                        <span>All Active Goals</span>
                      )}
                    </div>
                    <div className="text-xs pt-1 font-semibold">
                      {primaryScenario?.goal_impact && primaryScenario.goal_impact.length > 0 ? (
                        primaryScenario.goal_impact[0].timeline_difference_months && primaryScenario.goal_impact[0].timeline_difference_months > 0 ? (
                          <span className="text-amber-700 flex items-center gap-1 font-mono">
                            <TrendingDown className="w-3.5 h-3.5" />
                            Estimated +{primaryScenario.goal_impact[0].timeline_difference_months} month delay
                          </span>
                        ) : primaryScenario.goal_impact[0].timeline_difference_months && primaryScenario.goal_impact[0].timeline_difference_months < 0 ? (
                          <span className="text-emerald-600 flex items-center gap-1 font-mono">
                            <TrendingUp className="w-3.5 h-3.5" />
                            Estimated {Math.abs(primaryScenario.goal_impact[0].timeline_difference_months)} mo earlier
                          </span>
                        ) : (
                          <span className="text-slate-600 flex items-center gap-1 font-normal">
                            <Minus className="w-3 h-3 text-slate-400" /> On schedule
                          </span>
                        )
                      ) : (
                        <span className="text-slate-500 font-normal">No active goals linked</span>
                      )}
                    </div>
                  </div>

                  {/* Savings Coverage Card */}
                  <div className="p-4 rounded-xl border border-slate-200/90 bg-slate-50/70 space-y-1">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                      Savings Coverage
                    </span>
                    <div className="text-base font-bold text-slate-900 font-mono flex items-baseline gap-1.5">
                      <span>{baselineSavingsCoverage ? `${baselineSavingsCoverage} mo` : 'N/A'}</span>
                      <span className="text-slate-400 font-normal">→</span>
                      <span>{primarySavingsCoverage ? `${primarySavingsCoverage} mo` : 'N/A'}</span>
                    </div>
                    <p className="text-[10px] text-slate-500 pt-0.5 leading-tight">
                      Based on current savings and average monthly expenses.
                    </p>
                  </div>
                </div>

                {/* Separation: Changes vs. No Major Change */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
                    <div className="flex items-center gap-1.5 font-bold text-slate-800 text-xs uppercase tracking-wide">
                      <TrendingDown className="w-3.5 h-3.5 text-rose-500" />
                      <span>Changes</span>
                    </div>
                    <ul className="text-xs text-slate-700 space-y-1.5">
                      {simulation.explanation.what_changes.length > 0 ? (
                        simulation.explanation.what_changes.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-1.5 font-medium">
                            <span className="text-teal-600 font-bold">•</span>
                            <span>{item}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-slate-500">No significant changes to current baseline.</li>
                      )}
                    </ul>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
                    <div className="flex items-center gap-1.5 font-bold text-slate-800 text-xs uppercase tracking-wide">
                      <Minus className="w-3.5 h-3.5 text-slate-400" />
                      <span>No Major Change</span>
                    </div>
                    <ul className="text-xs text-slate-600 space-y-1.5">
                      {simulation.explanation.what_stays_unchanged.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-slate-400 font-bold">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* 2. Current Verified Baseline Ribbon */}
              <div className="p-4 rounded-2xl border border-slate-200/80 bg-slate-50/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                    Your Current Verified Baseline
                  </span>
                  <span className="text-[11px] text-slate-500">
                    Source: Profile & Verified Ledger
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-1">
                  <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-0.5">
                    <span className="text-[10px] text-slate-400 font-medium">Monthly Income</span>
                    <p className="text-sm font-bold text-slate-900 font-mono">
                      {formatINR(simulation.baseline.monthly_income)}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-0.5">
                    <span className="text-[10px] text-slate-400 font-medium">Monthly Expenses</span>
                    <p className="text-sm font-bold text-slate-900 font-mono">
                      {formatINR(simulation.baseline.monthly_expenses)}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-0.5">
                    <span className="text-[10px] text-slate-400 font-medium">Monthly Surplus</span>
                    <p className="text-sm font-bold text-teal-700 font-mono">
                      {formatINR(simulation.baseline.monthly_surplus)}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-0.5">
                    <span className="text-[10px] text-slate-400 font-medium">Liquid Savings</span>
                    <p className="text-sm font-bold text-slate-900 font-mono">
                      {formatINR(simulation.baseline.current_savings)}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-white border border-slate-200/80 space-y-0.5">
                    <span className="text-[10px] text-slate-400 font-medium">Savings Coverage</span>
                    <p className="text-sm font-bold text-slate-900 font-mono">
                      {baselineSavingsCoverage ? `${baselineSavingsCoverage} months` : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* 3. Structured Scenarios Grid (Options A, B, C) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900">Modeled Options</h3>
                  <button
                    onClick={handleSaveCurrentSimulation}
                    className="flex items-center gap-1.5 text-xs text-teal-600 hover:text-teal-700 font-medium"
                  >
                    <Bookmark className="w-3.5 h-3.5" />
                    <span>Save This Analysis</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  {simulation.scenarios.map((sc, i) => {
                    const cov =
                      sc.financial_impact.savings_coverage_months ||
                      sc.financial_impact.projected_emergency_buffer_months;
                    return (
                      <div
                        key={i}
                        className="p-5 rounded-2xl border border-slate-200/90 bg-white shadow-xs hover:border-teal-300 transition-all flex flex-col justify-between"
                      >
                        <div className="space-y-4">
                          {/* Scenario Header */}
                          <div>
                            <div className="flex items-center justify-between">
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wider uppercase bg-slate-100 text-slate-600">
                                Option {String.fromCharCode(65 + i)}
                              </span>
                              {sc.warnings && sc.warnings.length > 0 && (
                                <span className="flex items-center gap-1 text-[10px] font-semibold text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
                                  <AlertTriangle className="w-3 h-3" /> Caution
                                </span>
                              )}
                            </div>
                            <h4 className="text-sm font-bold text-slate-900 mt-2">{sc.name}</h4>
                            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                              {sc.description}
                            </p>
                          </div>

                          {/* Key Numbers */}
                          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 space-y-2.5">
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-slate-500">Projected Savings</span>
                              <span className="font-mono font-bold text-slate-900">
                                {formatINR(sc.financial_impact.new_savings)}
                              </span>
                            </div>
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-slate-500">Immediate Outlay</span>
                              <span
                                className={`font-mono font-semibold ${
                                  Number(sc.financial_impact.cash_position_change) < 0
                                    ? 'text-rose-600'
                                    : 'text-slate-700'
                                }`}
                              >
                                {Number(sc.financial_impact.cash_position_change) < 0
                                  ? `-${formatINR(Math.abs(Number(sc.financial_impact.cash_position_change)))}`
                                  : '₹0'}
                              </span>
                            </div>
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-slate-500">Monthly Cash Flow</span>
                              <span className="font-mono font-semibold text-teal-700">
                                {formatINR(sc.financial_impact.new_monthly_surplus)}
                              </span>
                            </div>
                            {cov && (
                              <div className="flex justify-between items-center text-xs">
                                <span className="text-slate-500">Savings Coverage</span>
                                <span className="font-mono font-medium text-slate-700">
                                  {cov} months
                                </span>
                              </div>
                            )}
                          </div>

                          {/* Goal Timeline Impact */}
                          {sc.goal_impact && sc.goal_impact.length > 0 && (
                            <div className="p-3 rounded-xl border border-slate-100 bg-teal-50/40 text-xs space-y-1">
                              <div className="flex items-center gap-1.5 font-semibold text-teal-900 text-[11px]">
                                <Target className="w-3.5 h-3.5 text-teal-600" />
                                <span>Goal Timeline Impact</span>
                              </div>
                              <p className="text-[11px] text-teal-800 leading-relaxed">
                                {sc.goal_impact[0].impact_summary}
                              </p>
                            </div>
                          )}

                          {/* Warnings if any */}
                          {sc.warnings && sc.warnings.length > 0 && (
                            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200/80 text-[11px] text-amber-800 space-y-1">
                              {sc.warnings.map((w, wIdx) => (
                                <p key={wIdx}>• {w}</p>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Assumptions Footnote */}
                        <div className="pt-4 border-t border-slate-100 mt-4 text-[10px] text-slate-400 space-y-1">
                          {sc.assumptions.slice(0, 3).map((a, aIdx) => (
                            <p key={aIdx}>• {a}</p>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* 4. Side-by-Side Comparison Matrix ("What do I gain or give up?") */}
              {comparison && comparison.comparison_matrix.length > 0 && (
                <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2">
                      <Layers className="w-4 h-4 text-teal-600" />
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">
                          Option Comparison Matrix
                        </h3>
                        <p className="text-[11px] text-slate-500">
                          What do you gain or give up with each option? Side-by-side trade-offs computed directly from your financial baseline.
                        </p>
                      </div>
                    </div>
                    <span className="text-[11px] text-slate-400">Objective Trade-Offs</span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100">
                        <tr>
                          <th className="py-2.5 px-3 font-medium">Impact Area</th>
                          <th className="py-2.5 px-3 font-medium text-slate-600">Current Baseline</th>
                          {Object.keys(comparison.comparison_matrix[0].scenarios).map((scName) => (
                            <th key={scName} className="py-2.5 px-3 font-semibold text-teal-900">
                              {scName}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {comparison.comparison_matrix.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-slate-50/70 transition">
                            <td className="py-3 px-3 font-semibold text-slate-800">{row.metric}</td>
                            <td className="py-3 px-3 font-mono text-slate-600">{row.baseline}</td>
                            {Object.entries(row.scenarios).map(([scName, val]) => (
                              <td key={scName} className="py-3 px-3 font-mono font-semibold text-slate-900">
                                {val}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 5. Trade-Off Analysis & User Decides */}
              <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
                <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
                  <Sparkles className="w-4 h-4 text-teal-600" />
                  <h3 className="text-sm font-bold text-slate-900">Trade-Off Analysis</h3>
                </div>

                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  {simulation.explanation.trade_off_analysis}
                </p>

                {/* Considerations before you decide */}
                <div className="p-4 rounded-xl bg-teal-50/50 border border-teal-100 space-y-1.5">
                  <span className="text-[11px] font-bold text-teal-900 uppercase tracking-wide">
                    Considerations before you decide
                  </span>
                  <ul className="text-xs text-teal-900 space-y-1">
                    {simulation.explanation.key_considerations.map((c, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="text-teal-600 font-bold">•</span>
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* 6. Transparent Methodology & Assumptions Footnote */}
              <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/60 text-xs text-slate-500 space-y-2">
                <div className="flex items-center gap-1.5 font-semibold text-slate-700 text-[11px]">
                  <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                  <span>Model Assumptions & Methodology</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                  {simulation.assumptions.map((a, i) => (
                    <p key={i}>• {a}</p>
                  ))}
                </div>
                <p className="text-[10px] text-slate-400 pt-1 border-t border-slate-200">
                  Estimated timelines are based on your current monthly surplus and linear contribution without investment return guarantees. FinMate does not make the decision for you — you remain in complete control.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
