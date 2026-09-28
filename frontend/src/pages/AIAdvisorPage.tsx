import React, { useState } from 'react';
import {
  Sparkles,
  Search,
  CheckCircle2,
  AlertTriangle,
  Send,
  ShieldCheck,
  Check,
  X,
  Info,
  Clock,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import { AgentTaskResult } from '../types';

const SUGGESTED_PROMPTS = [
  'Can I afford a ₹20,000 purchase next month without hurting my education goal?',
  'What happens if my monthly expenses increase by ₹5,000?',
  'Can I reach my education goal this year with my current surplus?',
  'What if I save ₹5,000 more every month?',
];

export const AIAdvisorPage: React.FC = () => {
  const [query, setQuery] = useState(SUGGESTED_PROMPTS[0]);
  const [isRunning, setIsRunning] = useState(false);
  const [taskResult, setTaskResult] = useState<AgentTaskResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approvalFeedback, setApprovalFeedback] = useState<string | null>(null);
  const [isProcessingApproval, setIsProcessingApproval] = useState(false);

  const handleRunTask = async (customQuery?: string) => {
    const q = (customQuery || query).trim();
    if (!q) return;

    if (customQuery) {
      setQuery(customQuery);
    }

    setIsRunning(true);
    setError(null);
    setApprovalFeedback(null);

    try {
      const res = await api.createAgentTask(q);
      setTaskResult(res);
    } catch (err: any) {
      setError(err.message || 'We could not complete the advisory analysis right now. Please try again.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleApproveAction = async () => {
    if (!taskResult || !taskResult.pending_approval) return;
    setIsProcessingApproval(true);
    try {
      const res = await api.approveAgentAction(
        taskResult.task_id,
        taskResult.pending_approval.approval_id
      );
      setApprovalFeedback(`✓ Confirmed: ${res.message}`);
      setTaskResult({
        ...taskResult,
        status: 'completed',
        pending_approval: null,
      });
    } catch (err: any) {
      setApprovalFeedback(`✕ Error confirming action: ${err.message}`);
    } finally {
      setIsProcessingApproval(false);
    }
  };

  const handleRejectAction = async () => {
    if (!taskResult || !taskResult.pending_approval) return;
    setIsProcessingApproval(true);
    try {
      const res = await api.rejectAgentAction(
        taskResult.task_id,
        taskResult.pending_approval.approval_id
      );
      setApprovalFeedback(`✓ Declined: ${res.message}`);
      setTaskResult({
        ...taskResult,
        status: 'completed',
        pending_approval: null,
      });
    } catch (err: any) {
      setApprovalFeedback(`Error declining action: ${err.message}`);
    } finally {
      setIsProcessingApproval(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-teal-600" />
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Financial Advisor</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-2xl">
            Understand the financial consequences of decisions before you make them. Every analysis is
            grounded in your verified ledger facts and respects strict decision-support boundaries.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-teal-100 bg-teal-50/70 text-teal-800 text-xs font-medium self-start md:self-auto">
          <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0" />
          <span>Verifiable ledger facts • Decision support only</span>
        </div>
      </div>

      {/* Suggested Prompts Chips */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          Suggested Decision Questions
        </span>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_PROMPTS.map((promptText, idx) => (
            <button
              key={idx}
              onClick={() => handleRunTask(promptText)}
              className="text-left px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:border-teal-500 hover:bg-teal-50/50 text-xs font-medium text-slate-700 transition shadow-2xs"
            >
              {promptText}
            </button>
          ))}
        </div>
      </div>

      {/* Query Bar */}
      <div className="p-4 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-3">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRunTask()}
              placeholder="Ask a decision question, e.g. 'Can I afford a ₹20,000 laptop?'"
              className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 transition"
            />
          </div>
          <button
            onClick={() => handleRunTask()}
            disabled={isRunning || !query.trim()}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white shadow-xs transition shrink-0"
          >
            {isRunning ? (
              <span>Analyzing...</span>
            ) : (
              <>
                <span>Analyze Impact</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Loading Skeleton */}
      {isRunning && (
        <div className="p-6 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-4 animate-pulse">
          <div className="h-5 w-48 bg-slate-200 rounded" />
          <div className="h-4 w-full bg-slate-100 rounded" />
          <div className="h-4 w-3/4 bg-slate-100 rounded" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div className="h-24 bg-slate-100 rounded-xl" />
            <div className="h-24 bg-slate-100 rounded-xl" />
            <div className="h-24 bg-slate-100 rounded-xl" />
          </div>
        </div>
      )}

      {/* ANALYSIS RESULT */}
      {taskResult && !isRunning && (
        <div className="space-y-6 animate-fadeIn">
          {/* 1. Decision Summary & Primary Synthesis */}
          <div className="p-6 rounded-2xl border border-teal-200/90 bg-white shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-teal-600" />
                <h2 className="text-base font-bold text-slate-900">Analysis Summary</h2>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-teal-50 text-teal-800 border border-teal-100">
                Verified Decision Support
              </span>
            </div>

            <p className="text-sm text-slate-700 leading-relaxed font-medium">
              {taskResult.summary}
            </p>

            {/* Verified Ledger Facts */}
            {taskResult.facts && taskResult.facts.length > 0 && (
              <div className="pt-3 border-t border-slate-100 space-y-2">
                <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                  Verified Ledger Facts
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {taskResult.facts.map((fact, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1"
                    >
                      <span className="text-[10px] text-slate-400 font-medium block">
                        {fact.metric || 'Metric'}
                      </span>
                      <span className="text-xs font-bold text-slate-900 font-mono block">
                        {fact.value || 'N/A'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 2. Structured Options & Scenario Comparison */}
          {taskResult.tradeoffs && taskResult.tradeoffs.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-teal-600" />
                <h3 className="text-sm font-bold text-slate-900">Modeled Options & Trade-Offs</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {taskResult.tradeoffs.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-3.5 hover:border-teal-300 transition"
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700">
                        {item.option ? item.option.split(':')[0] : `Option ${String.fromCharCode(65 + idx)}`}
                      </span>
                      {item.risk_level && (
                        <span className="text-[10px] font-medium text-slate-500">
                          {item.risk_level}
                        </span>
                      )}
                    </div>

                    <h4 className="text-xs font-bold text-slate-900">
                      {item.option ? item.option.split(':')[1] || item.option : item.focus_area || 'Scenario'}
                    </h4>

                    <div className="space-y-2 text-xs">
                      {item.cashflow_impact && (
                        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                          <span className="text-[10px] font-semibold text-slate-400 block">
                            Cashflow Impact
                          </span>
                          <span className="text-slate-800 font-medium">{item.cashflow_impact}</span>
                        </div>
                      )}
                      {item.savings_impact && (
                        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                          <span className="text-[10px] font-semibold text-slate-400 block">
                            Savings Impact
                          </span>
                          <span className="text-slate-800 font-medium">{item.savings_impact}</span>
                        </div>
                      )}
                      {item.goal_impact && (
                        <div className="p-2.5 rounded-xl bg-teal-50/50 border border-teal-100">
                          <span className="text-[10px] font-semibold text-teal-800 block">
                            Goal Timeline
                          </span>
                          <span className="text-teal-900 font-medium">{item.goal_impact}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Action Proposal Guardrail (if human approval is requested) */}
          {taskResult.pending_approval && (
            <div className="p-5 rounded-2xl border-2 border-teal-500 bg-teal-50/40 shadow-xs space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-teal-600 text-white">
                    Action Proposal Pending Your Decision
                  </span>
                  <h3 className="text-sm font-bold text-slate-900 mt-2">
                    Action Proposal: {taskResult.pending_approval.action_type.replace('_', ' ')}
                  </h3>
                  <p className="text-xs text-slate-600 mt-1">
                    {taskResult.pending_approval.reason}
                  </p>
                </div>
                <Clock className="w-5 h-5 text-teal-600 shrink-0" />
              </div>

              <div className="p-3.5 rounded-xl bg-white border border-teal-100 grid grid-cols-2 gap-4 text-xs font-mono">
                <div>
                  <span className="text-[10px] font-medium text-slate-400 block">Current State</span>
                  <pre className="text-slate-800 text-[11px] whitespace-pre-wrap mt-0.5">
                    {JSON.stringify(taskResult.pending_approval.current_value, null, 2)}
                  </pre>
                </div>
                <div>
                  <span className="text-[10px] font-medium text-teal-700 block">Proposed Change</span>
                  <pre className="text-teal-900 text-[11px] whitespace-pre-wrap mt-0.5">
                    {JSON.stringify(taskResult.pending_approval.proposed_value, null, 2)}
                  </pre>
                </div>
              </div>

              <div className="flex items-center gap-3 pt-1">
                <button
                  onClick={handleApproveAction}
                  disabled={isProcessingApproval}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-teal-600 hover:bg-teal-700 text-white shadow-xs transition"
                >
                  <Check className="w-4 h-4" />
                  <span>Confirm Change</span>
                </button>
                <button
                  onClick={handleRejectAction}
                  disabled={isProcessingApproval}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition shadow-2xs"
                >
                  <X className="w-4 h-4" />
                  <span>Decline</span>
                </button>
              </div>

              {approvalFeedback && (
                <p className="text-xs font-medium text-teal-800 pt-1">{approvalFeedback}</p>
              )}
            </div>
          )}

          {/* 4. Considerations & Next Steps */}
          {taskResult.recommendations && taskResult.recommendations.length > 0 && (
            <div className="p-5 rounded-2xl border border-slate-200/80 bg-white shadow-xs space-y-3">
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4 text-teal-600" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                  Considerations for Your Plan
                </h3>
              </div>
              <ul className="text-xs text-slate-600 space-y-1.5 pl-1">
                {taskResult.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-teal-600 font-bold">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 5. Model Assumptions & Safety Notice */}
          <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/70 text-xs text-slate-500 space-y-1.5">
            <div className="flex items-center gap-1.5 font-semibold text-slate-700 text-[11px]">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
              <span>Safety & Governance Note</span>
            </div>
            <p className="text-[11px] leading-relaxed">
              FinMate operates with strict read-only financial modeling. No autonomous transfers,
              trades, or payments are ever executed. You remain in complete control of your finances.
            </p>
            {taskResult.assumptions && taskResult.assumptions.length > 0 && (
              <div className="pt-2 border-t border-slate-200/80 space-y-1 text-[10px] text-slate-400">
                {taskResult.assumptions.map((a, i) => (
                  <p key={i}>• {a}</p>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
