import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Search,
  CheckCircle2,
  AlertTriangle,
  Send,
  TrendingUp,
  Tag,
  ShieldCheck,
  BookOpen,
  BarChart3,
  Layers,
  RefreshCw,
  Clock,
  Check,
  X,
  Sliders,
  UserCheck,
} from 'lucide-react';
import { api } from '../services/api';
import {
  AgentTaskResult,
  TransactionClassificationResult,
  ExpenseForecastResult,
  AnomalyCheckResult,
  ModelMetadataItem,
} from '../types';

export const AIAdvisorPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<
    'agents' | 'classifier' | 'forecasting' | 'benchmarks' | 'architecture'
  >('agents');

  // --- Tab 1: Financial Assistant State ---
  const [agentQuery, setAgentQuery] = useState(
    'Can I afford a ₹20,000 purchase next month without hurting my education goal?'
  );
  const [isAgentRunning, setIsAgentRunning] = useState(false);
  const [agentTask, setAgentTask] = useState<AgentTaskResult | null>(null);
  const [agentError, setAgentError] = useState<string | null>(null);
  const [approvalFeedback, setApprovalFeedback] = useState<string | null>(null);
  const [isProcessingApproval, setIsProcessingApproval] = useState(false);

  // --- What-If Quick Sandbox in Multi-Agent Tab ---
  const [simExpense, setSimExpense] = useState('20000');
  const [simSaving, setSimSaving] = useState('2000');
  const [isSimulating, setIsSimulating] = useState(false);

  // --- Tab 2: Transaction Classification & Anomaly State ---
  const [txDesc, setTxDesc] = useState('Swiggy dinner order ₹450');
  const [txAmount, setTxAmount] = useState('450.00');
  const [txType] = useState('expense');
  const [isClassifying, setIsClassifying] = useState(false);
  const [classificationResult, setClassificationResult] =
    useState<TransactionClassificationResult | null>(null);
  const [anomalyResult, setAnomalyResult] = useState<AnomalyCheckResult | null>(null);

  // --- Tab 3: Forecasting Studio State ---
  const [lag1, setLag1] = useState('36000');
  const [lag2, setLag2] = useState('34500');
  const [lag3, setLag3] = useState('33000');
  const [forecastMonth, setForecastMonth] = useState('10');
  const [isForecasting, setIsForecasting] = useState(false);
  const [forecastResult, setForecastResult] = useState<ExpenseForecastResult | null>(null);

  // --- Tab 4: Benchmarks State ---
  const [models, setModels] = useState<ModelMetadataItem[]>([]);

  const loadModelRegistry = async () => {
    try {
      const data = await api.getModelRegistry();
      setModels(data.models || []);
    } catch (err) {
      console.error('Failed to load model registry:', err);
    }
  };

  useEffect(() => {
    if (activeTab === 'benchmarks' && models.length === 0) {
      loadModelRegistry();
    }
  }, [activeTab, models.length]);

  // --- Financial Assistant Handlers ---
  const handleRunAgentTask = async (customQuery?: string) => {
    const q = customQuery || agentQuery;
    if (!q.trim()) return;

    setIsAgentRunning(true);
    setAgentError(null);
    setApprovalFeedback(null);
    try {
      const taskRes = await api.createAgentTask(q);
      setAgentTask(taskRes);
    } catch (err: any) {
      setAgentError(err.message || 'Failed to complete advisory evaluation.');
    } finally {
      setIsAgentRunning(false);
    }
  };

  const handleApproveAction = async () => {
    if (!agentTask || !agentTask.pending_approval) return;
    setIsProcessingApproval(true);
    try {
      const res = await api.approveAgentAction(
        agentTask.task_id,
        agentTask.pending_approval.approval_id
      );
      setApprovalFeedback(`✓ Approved: ${res.message}`);
      setAgentTask({
        ...agentTask,
        status: 'completed',
        pending_approval: null,
      });
    } catch (err: any) {
      setApprovalFeedback(`✕ Error approving action: ${err.message}`);
    } finally {
      setIsProcessingApproval(false);
    }
  };

  const handleRejectAction = async () => {
    if (!agentTask || !agentTask.pending_approval) return;
    setIsProcessingApproval(true);
    try {
      const res = await api.rejectAgentAction(
        agentTask.task_id,
        agentTask.pending_approval.approval_id
      );
      setApprovalFeedback(`✕ Rejected: ${res.message}`);
      setAgentTask({
        ...agentTask,
        status: 'completed',
        pending_approval: null,
      });
    } catch (err: any) {
      setApprovalFeedback(`Error rejecting action: ${err.message}`);
    } finally {
      setIsProcessingApproval(false);
    }
  };

  const handleSimulateWhatIf = async () => {
    setIsSimulating(true);
    try {
      const q = `What if I spend ₹${simExpense} more and reduce monthly spending by ₹${simSaving}?`;
      await handleRunAgentTask(q);
    } finally {
      setIsSimulating(false);
    }
  };

  // --- Tab 2: Classification Handler ---
  const handleClassifyTransaction = async () => {
    if (!txDesc.trim()) return;
    setIsClassifying(true);
    try {
      const clf = await api.classifyTransaction({
        description: txDesc,
        amount: parseFloat(txAmount) || undefined,
        transaction_type: txType,
      });
      setClassificationResult(clf);

      if (parseFloat(txAmount) > 0) {
        const anom = await api.checkAnomaly({
          amount: txAmount,
          category: clf.predicted_category,
        });
        setAnomalyResult(anom);
      }
    } catch (err) {
      console.error('Classification error:', err);
    } finally {
      setIsClassifying(false);
    }
  };

  // --- Tab 3: Forecasting Handler ---
  const handleRunForecast = async () => {
    setIsForecasting(true);
    try {
      const lags = [
        parseFloat(lag1) || 35000,
        parseFloat(lag2) || 34000,
        parseFloat(lag3) || 33000,
      ];
      const res = await api.forecastExpenses({
        recent_lags: lags,
        forecast_month: parseInt(forecastMonth) || 10,
      });
      setForecastResult(res);
    } catch (err) {
      console.error('Forecasting error:', err);
    } finally {
      setIsForecasting(false);
    }
  };

  const suggestedQuestions = [
    {
      label: 'Where did I spend the most this month?',
      query: 'Where did I spend the most this month?',
    },
    {
      label: 'Can I reach my education goal?',
      query: 'Can I reach my education goal?',
    },
    {
      label: 'How can I improve my savings?',
      query: 'How can I improve my savings rate?',
    },
    {
      label: 'Can I afford a ₹20,000 purchase next month?',
      query: 'Can I afford a ₹20,000 purchase next month without hurting my goals?',
    },
    {
      label: 'What if I trim entertainment by ₹2,000?',
      query: 'What if I reduce my monthly entertainment spending by ₹2,000?',
    },
    {
      label: 'Reclassify Amazon transaction',
      query: 'Change the Amazon transaction category to Shopping.',
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Financial Assistant</h1>
            <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-100">
              Decision Support
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Ask questions, run what-if simulations, and inspect smart financial projections.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-teal-100 bg-teal-50/70 text-teal-800 text-xs font-medium">
          <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0" />
          <span>Verifiable ledger facts & human approval guardrails</span>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        {[
          { id: 'agents', label: 'Financial Assistant', icon: Sparkles },
          { id: 'classifier', label: 'Smart Categorization', icon: Tag },
          { id: 'forecasting', label: 'Spending Forecast', icon: TrendingUp },
          { id: 'benchmarks', label: 'Model Benchmarks', icon: BarChart3 },
          { id: 'architecture', label: 'System Overview', icon: Layers },
        ].map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
                isActive
                  ? 'bg-teal-600 text-white font-semibold shadow-xs'
                  : 'bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50 border border-slate-200/80'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: FINANCIAL ASSISTANT WORKSPACE */}
      {/* ========================================================================= */}
      {activeTab === 'agents' && (
        <div className="space-y-6">
          {/* Query Bar Card */}
          <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
                <Sparkles className="w-4 h-4 text-teal-600" />
                <span>What would you like to understand about your finances?</span>
              </div>
              <span className="text-[11px] text-slate-400 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200 hidden sm:inline-block">
                Evaluates ledger & active goals
              </span>
            </div>

            <div className="flex flex-col sm:flex-row gap-2.5">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={agentQuery}
                  onChange={(e) => setAgentQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleRunAgentTask()}
                  placeholder="Ask e.g. 'Can I afford a ₹20,000 purchase next month without hurting my education goal?'"
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-xs focus:outline-none focus:border-teal-500 focus:bg-white transition"
                />
              </div>
              <button
                onClick={() => handleRunAgentTask()}
                disabled={isAgentRunning}
                className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition shadow-xs disabled:opacity-50"
              >
                {isAgentRunning ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5" />
                )}
                <span>{isAgentRunning ? 'Analyzing...' : 'Ask FinMate'}</span>
              </button>
            </div>

            {/* Suggested Question Chips */}
            <div className="space-y-2 pt-1">
              <span className="text-[11px] text-slate-400 font-medium">Suggested questions:</span>
              <div className="flex flex-wrap gap-2">
                {suggestedQuestions.map((sc, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setAgentQuery(sc.query);
                      handleRunAgentTask(sc.query);
                    }}
                    className="text-[11px] px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-600 hover:text-teal-800 hover:border-teal-200 hover:bg-teal-50/50 transition text-left"
                  >
                    {sc.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Error Banner */}
          {agentError && (
            <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{agentError}</span>
            </div>
          )}

          {/* Feedback Banner */}
          {approvalFeedback && (
            <div className="p-4 rounded-xl border border-teal-200 bg-teal-50 text-teal-800 text-xs flex items-center gap-2 animate-fadeIn">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-teal-600" />
              <span>{approvalFeedback}</span>
            </div>
          )}

          {/* Results Container */}
          {agentTask && (
            <div className="space-y-6 animate-fadeIn">
              {/* HUMAN-IN-THE-LOOP APPROVAL CARD (Rendered when approval is pending) */}
              {agentTask.pending_approval && (
                <div className="p-6 rounded-2xl border border-amber-200 bg-amber-50/70 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-amber-900 font-semibold text-sm">
                      <UserCheck className="w-4 h-4 text-amber-700" />
                      <span>Review Proposed Change</span>
                    </div>
                    <span className="text-[10px] font-medium px-2.5 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                      Confirmation Required
                    </span>
                  </div>

                  <p className="text-xs text-amber-800 leading-relaxed">
                    {agentTask.pending_approval.message ||
                      'The assistant proposed a record modification. Under FinMate safety guardrails, no database record is changed without your explicit approval.'}
                  </p>

                  {/* Proposed Change Comparison */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-3.5 rounded-xl bg-white border border-amber-200">
                      <span className="text-slate-400 block mb-1 text-[11px]">Current Value</span>
                      <pre className="font-mono text-slate-800 text-xs whitespace-pre-wrap">
                        {JSON.stringify(agentTask.pending_approval.current_value, null, 2)}
                      </pre>
                    </div>

                    <div className="p-3.5 rounded-xl bg-white border border-emerald-300">
                      <span className="text-emerald-700 block mb-1 text-[11px] font-semibold">
                        Proposed Value
                      </span>
                      <pre className="font-mono text-emerald-800 text-xs font-medium whitespace-pre-wrap">
                        {JSON.stringify(agentTask.pending_approval.proposed_value, null, 2)}
                      </pre>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-amber-100/60 text-[11px] text-amber-900 flex items-center justify-between">
                    <span>
                      <strong>Reason:</strong> {agentTask.pending_approval.reason}
                    </span>
                  </div>

                  {/* Approve / Reject Action Buttons */}
                  <div className="flex items-center gap-3 pt-2">
                    <button
                      onClick={handleApproveAction}
                      disabled={isProcessingApproval}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs transition shadow-xs disabled:opacity-50"
                    >
                      <Check className="w-4 h-4" />
                      <span>{isProcessingApproval ? 'Applying...' : 'Approve & Update'}</span>
                    </button>

                    <button
                      onClick={handleRejectAction}
                      disabled={isProcessingApproval}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs border border-slate-200 transition disabled:opacity-50"
                    >
                      <X className="w-4 h-4" />
                      <span>Reject Change</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Master Decision-Support Synthesis Card */}
              <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                  <div className="flex items-center gap-2 text-slate-900 font-bold text-sm">
                    <Sparkles className="w-4 h-4 text-teal-600" />
                    <span>Decision-Support Evaluation</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] px-2 py-0.5 rounded-md bg-teal-50 text-teal-700 border border-teal-100 font-medium">
                      Evidence: {agentTask.evidence_quality}
                    </span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200/80">
                  <p className="text-xs text-slate-800 leading-relaxed font-normal">
                    {agentTask.summary}
                  </p>
                </div>

                {/* 4 Partitioned Information Panels */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Panel 1: Authoritative Financial Facts */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2.5">
                    <div className="flex items-center gap-2 text-emerald-700 text-xs font-semibold uppercase tracking-wider">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Verified Ledger Facts</span>
                    </div>
                    {agentTask.facts.length > 0 ? (
                      <div className="space-y-1.5 text-xs">
                        {agentTask.facts.map((f, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex justify-between items-center"
                          >
                            <span className="text-slate-600 font-medium">
                              {f.metric ||
                                f.category ||
                                f.goal_name ||
                                f.asset_class ||
                                f.entity ||
                                'Metric'}
                            </span>
                            <span className="font-bold text-slate-900">
                              {f.value ||
                                f.total_amount ||
                                f.current_amount ||
                                f.valuation ||
                                f.amount ||
                                '—'}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">General conceptual inquiry mode.</p>
                    )}
                  </div>

                  {/* Panel 2: Model Predictions & Projections */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2.5">
                    <div className="flex items-center gap-2 text-sky-700 text-xs font-semibold uppercase tracking-wider">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>Projections & Estimates</span>
                    </div>
                    {agentTask.predictions.length > 0 ? (
                      <div className="space-y-1.5 text-xs">
                        {agentTask.predictions.map((p, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 space-y-1"
                          >
                            <div className="flex justify-between items-center">
                              <span className="text-slate-600">{p.metric || 'Forecast'}</span>
                              <span className="font-bold text-slate-900 font-mono">
                                {p.point_estimate || '—'}
                              </span>
                            </div>
                            {p.confidence_interval_95 && (
                              <div className="text-[11px] text-slate-500 flex justify-between">
                                <span>Confidence Band:</span>
                                <span className="font-mono text-slate-700">
                                  {p.confidence_interval_95}
                                </span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">
                        Based entirely on verified user ledger calculations.
                      </p>
                    )}
                  </div>

                  {/* Panel 3: Trade-Offs & Action Options */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2.5">
                    <div className="flex items-center gap-2 text-amber-700 text-xs font-semibold uppercase tracking-wider">
                      <Sliders className="w-3.5 h-3.5" />
                      <span>Action Options & Trade-Offs</span>
                    </div>
                    {agentTask.tradeoffs.length > 0 ? (
                      <div className="space-y-2 text-xs">
                        {agentTask.tradeoffs.map((t, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 space-y-1 text-[11px]"
                          >
                            <span className="font-bold text-slate-900 block">
                              {t.option ||
                                t.action ||
                                t.dimension ||
                                t.focus_area ||
                                `Option ${idx + 1}`}
                            </span>
                            {t.cashflow_impact && (
                              <p className="text-slate-700">
                                <strong className="text-slate-500">Cashflow:</strong>{' '}
                                {t.cashflow_impact}
                              </p>
                            )}
                            {t.goal_impact && (
                              <p className="text-slate-700">
                                <strong className="text-slate-500">Goal Impact:</strong>{' '}
                                {t.goal_impact}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="space-y-1 text-xs">
                        {agentTask.recommendations.map((rec, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-2 text-slate-700 text-[11px]"
                          >
                            <span className="text-teal-600 font-bold">•</span>
                            <span>{rec}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Panel 4: Verified Knowledge Citations */}
                  <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-2.5">
                    <div className="flex items-center gap-2 text-teal-700 text-xs font-semibold uppercase tracking-wider">
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>Guidance & Reference Citations</span>
                    </div>
                    {agentTask.sources.length > 0 ? (
                      <div className="space-y-2 text-xs">
                        {agentTask.sources.map((s, idx) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-[11px]"
                          >
                            <div className="flex justify-between items-center">
                              <span className="font-semibold text-slate-900">
                                {s.title || 'Guideline'}
                              </span>
                              <span className="text-[10px] text-slate-500 font-medium">
                                {s.organization || 'Standard'}
                              </span>
                            </div>
                            <p className="text-slate-600 text-[11px] mt-1 italic">
                              "{s.key_takeaway || s.content_snippet}"
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">
                        Based entirely on verified user financial ledger and deterministic rules.
                      </p>
                    )}
                  </div>
                </div>

                {/* Assumptions & Uncertainties Footer */}
                <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row justify-between gap-3 text-[11px] text-slate-500">
                  <div>
                    <span className="font-semibold text-slate-700">Assumptions: </span>
                    <span>
                      {agentTask.assumptions.length > 0
                        ? agentTask.assumptions.join('; ')
                        : 'Income remains consistent with recent pay cycle.'}
                    </span>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-700">Uncertainties: </span>
                    <span className="text-slate-600">
                      {agentTask.uncertainties.length > 0
                        ? agentTask.uncertainties.join('; ')
                        : 'Seasonal outlays may vary.'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Execution Trace Stepper */}
              <div className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                  <div className="flex items-center gap-2 text-slate-700 font-semibold text-xs uppercase tracking-wider">
                    <Clock className="w-3.5 h-3.5 text-teal-600" />
                    <span>Evaluation Steps ({agentTask.execution_trace.length})</span>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                    Status: {agentTask.status}
                  </span>
                </div>

                <div className="space-y-2">
                  {agentTask.execution_trace.map((step, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                    >
                      <div className="flex items-start gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-mono font-bold text-[10px] shrink-0 mt-0.5 sm:mt-0">
                          {step.step_number}
                        </span>
                        <div>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="font-semibold text-slate-800">{step.agent}</span>
                            <span className="text-slate-300">•</span>
                            <span className="text-teal-700 font-medium">{step.action}</span>
                            {step.tool && (
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white text-slate-600 border border-slate-200">
                                {step.tool}
                              </span>
                            )}
                          </div>
                          <p className="text-slate-500 mt-0.5 text-[11px] leading-relaxed">
                            {step.detail}
                          </p>
                        </div>
                      </div>

                      <div className="shrink-0 self-end sm:self-center font-mono text-[10px] text-slate-400">
                        {step.duration_ms} ms
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* What-If Simulation Sandbox Panel */}
              <div className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-slate-800 font-semibold text-xs uppercase tracking-wider">
                    <Sliders className="w-3.5 h-3.5 text-teal-600" />
                    <span>Interactive What-If Simulation Sandbox</span>
                  </div>
                  <span className="text-[10px] text-slate-400">In-memory isolation</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="text-[11px] text-slate-600 block mb-1">
                      Simulated Outlay (₹)
                    </label>
                    <input
                      type="number"
                      value={simExpense}
                      onChange={(e) => setSimExpense(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] text-slate-600 block mb-1">
                      Monthly Expense Cut (₹)
                    </label>
                    <input
                      type="number"
                      value={simSaving}
                      onChange={(e) => setSimSaving(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white"
                    />
                  </div>

                  <div className="flex items-end">
                    <button
                      onClick={handleSimulateWhatIf}
                      disabled={isSimulating}
                      className="w-full py-2 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs transition shadow-xs disabled:opacity-50"
                    >
                      {isSimulating ? 'Simulating...' : 'Run Scenario Simulation'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: TRANSACTION CLASSIFIER STUDIO */}
      {/* ========================================================================= */}
      {activeTab === 'classifier' && (
        <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-5">
          <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
            <Tag className="w-4 h-4 text-teal-600" />
            <span>Smart Category & Anomaly Classifier</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-slate-600 block mb-1">Raw Description</label>
              <input
                type="text"
                value={txDesc}
                onChange={(e) => setTxDesc(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-xs focus:outline-none focus:border-teal-500 focus:bg-white"
              />
            </div>
            <div>
              <label className="text-xs text-slate-600 block mb-1">Amount (₹)</label>
              <input
                type="number"
                value={txAmount}
                onChange={(e) => setTxAmount(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl border border-slate-200 bg-slate-50 text-slate-900 text-xs focus:outline-none focus:border-teal-500 focus:bg-white"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={handleClassifyTransaction}
                disabled={isClassifying}
                className="w-full py-2.5 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition shadow-xs disabled:opacity-50"
              >
                {isClassifying ? 'Predicting...' : 'Classify & Inspect'}
              </button>
            </div>
          </div>

          {classificationResult && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-600">Predicted Category:</span>
                <span className="text-sm font-bold text-teal-700">
                  {classificationResult.predicted_category} (
                  {(classificationResult.confidence * 100).toFixed(1)}%)
                </span>
              </div>
              {anomalyResult && (
                <div className="p-3 rounded-lg bg-white border border-slate-200 text-xs flex justify-between items-center">
                  <span className="text-slate-600">Anomaly Check:</span>
                  <span
                    className={
                      anomalyResult.is_unusual
                        ? 'text-amber-700 font-bold'
                        : 'text-emerald-700 font-bold'
                    }
                  >
                    {anomalyResult.is_unusual
                      ? '⚠️ Flagged as Unusual Amount'
                      : '✓ Normal Spending Pattern'}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: EXPENSE FORECASTING */}
      {/* ========================================================================= */}
      {activeTab === 'forecasting' && (
        <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-5">
          <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
            <TrendingUp className="w-4 h-4 text-teal-600" />
            <span>Time-Series Expense Forecasting</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
            <div>
              <label className="text-xs text-slate-600 block mb-1">Lag 1 (Most Recent)</label>
              <input
                type="number"
                value={lag1}
                onChange={(e) => setLag1(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white"
              />
            </div>
            <div>
              <label className="text-xs text-slate-600 block mb-1">Lag 2</label>
              <input
                type="number"
                value={lag2}
                onChange={(e) => setLag2(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white"
              />
            </div>
            <div>
              <label className="text-xs text-slate-600 block mb-1">Lag 3</label>
              <input
                type="number"
                value={lag3}
                onChange={(e) => setLag3(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white"
              />
            </div>
            <div>
              <label className="text-xs text-slate-600 block mb-1">Target Month</label>
              <input
                type="number"
                min="1"
                max="12"
                value={forecastMonth}
                onChange={(e) => setForecastMonth(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={handleRunForecast}
                disabled={isForecasting}
                className="w-full py-2 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition shadow-xs disabled:opacity-50"
              >
                {isForecasting ? 'Forecasting...' : 'Run Forecast'}
              </button>
            </div>
          </div>

          {forecastResult && (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Projected Monthly Outlay:</span>
                <span className="font-bold text-teal-700 text-sm font-mono">
                  ₹{forecastResult.predicted_expense?.toLocaleString()}
                </span>
              </div>
              {forecastResult.uncertainty_range && (
                <div className="flex justify-between text-slate-500">
                  <span>Uncertainty Range:</span>
                  <span className="font-mono text-slate-800">
                    ₹{forecastResult.uncertainty_range.lower_bound.toLocaleString()} – ₹
                    {forecastResult.uncertainty_range.upper_bound.toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: BENCHMARKS */}
      {/* ========================================================================= */}
      {activeTab === 'benchmarks' && (
        <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm">
              <BarChart3 className="w-4 h-4 text-teal-600" />
              <span>Model Registry & Evaluated Benchmarks</span>
            </div>
            <button
              onClick={loadModelRegistry}
              className="text-xs text-teal-600 hover:text-teal-700 flex items-center gap-1 font-medium"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-500 font-medium uppercase text-[10px] border-b border-slate-200">
                <tr>
                  <th className="p-3">Task</th>
                  <th className="p-3">Model</th>
                  <th className="p-3">Algorithm</th>
                  <th className="p-3">Primary Metric</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {models.map((m, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80">
                    <td className="p-3 font-semibold text-slate-900">{m.task}</td>
                    <td className="p-3 font-mono text-teal-700">{m.model_name}</td>
                    <td className="p-3 text-slate-600">{m.algorithm}</td>
                    <td className="p-3 font-mono text-slate-900">
                      {m.metrics.accuracy
                        ? `Acc: ${(m.metrics.accuracy * 100).toFixed(1)}%`
                        : `MAE: ₹${m.metrics.mae || '—'}`}
                    </td>
                    <td className="p-3">
                      {m.is_selected ? (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-semibold">
                          Active Champion
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px]">
                          Baseline
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: SYSTEM OVERVIEW */}
      {/* ========================================================================= */}
      {activeTab === 'architecture' && (
        <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-5">
          <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm border-b border-slate-100 pb-3">
            <Layers className="w-4 h-4 text-teal-600" />
            <span>Assistant Architecture & Guardrails Matrix</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <span className="font-bold text-slate-900 block text-sm">Specialist Modules</span>
              <ul className="space-y-1.5 text-slate-600">
                <li>
                  <strong className="text-slate-800">Transaction Specialist:</strong> Automatically
                  suggests categories and flags unusual amounts.
                </li>
                <li>
                  <strong className="text-slate-800">Cash Flow Specialist:</strong> Evaluates net
                  savings, run rate, and executes isolated what-if scenarios.
                </li>
                <li>
                  <strong className="text-slate-800">Goal Specialist:</strong> Tracks savings
                  progress and evaluates milestone timelines.
                </li>
                <li>
                  <strong className="text-slate-800">Portfolio Specialist:</strong> Informational
                  asset allocation and guidance citations.
                </li>
                <li>
                  <strong className="text-slate-800">Coordinator:</strong> Synthesizes verified
                  ledger records into clear financial summaries.
                </li>
              </ul>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <span className="font-bold text-slate-900 block text-sm">Safety Guardrails</span>
              <ul className="space-y-1.5 text-slate-600">
                <li>
                  <strong className="text-emerald-700">Read-Only Safety:</strong> Queries and
                  summaries run without altering your financial database.
                </li>
                <li>
                  <strong className="text-amber-700">Human Approval:</strong> Any database mutation
                  proposal must be explicitly confirmed by you.
                </li>
                <li>
                  <strong className="text-teal-700">In-Memory Sandboxing:</strong> What-If scenarios
                  are simulated strictly in memory.
                </li>
                <li>
                  <strong className="text-slate-700">Exact Decimal Math:</strong> Financial metrics
                  use deterministic accounting logic, not estimated hallucinated math.
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
