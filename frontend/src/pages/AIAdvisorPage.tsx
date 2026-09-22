import React from 'react';
import { BrainCircuit, ShieldAlert, Cpu, Sparkles, CheckCircle, Lock } from 'lucide-react';

export const AIAdvisorPage: React.FC = () => {
  const agents = [
    {
      name: 'Transaction Agent',
      phase: 'Phase 4',
      role: 'Automated pattern extraction, payee categorization, and anomaly flag triage.',
    },
    {
      name: 'Budget Agent',
      phase: 'Phase 8',
      role: 'Deterministic cash flow forecasting and proactive category threshold alerts.',
    },
    {
      name: 'Goal Agent',
      phase: 'Phase 8',
      role: 'Savings milestone feasibility analysis and adaptive timeline forecasting.',
    },
    {
      name: 'Investment Agent',
      phase: 'Phase 8',
      role: 'Asset allocation monitoring against declared user risk preferences.',
    },
    {
      name: 'Financial Decision Agent',
      phase: 'Phase 9',
      role: 'Synthesizes cross-agent insights for human review with explainable rationale.',
    },
  ];

  return (
    <div className="space-y-8 animate-fadeIn max-w-5xl">
      <div>
        <div className="flex items-center gap-2">
          <h2 className="text-2xl font-bold text-slate-100 tracking-tight">AI Advisor Architecture</h2>
          <span className="text-xs uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
            Future Scope (Phase 8+)
          </span>
        </div>
        <p className="text-sm text-slate-400">
          Conceptual blueprint for multi-agent reasoning, grounded RAG retrieval, and human-in-the-loop decision support.
        </p>
      </div>

      {/* Principle Notice */}
      <div className="p-6 rounded-2xl border border-purple-500/20 bg-purple-500/5 backdrop-blur-sm space-y-3">
        <div className="flex items-center gap-2.5 text-purple-300 font-semibold text-sm">
          <Lock className="w-5 h-5 text-purple-400" />
          <span>Core Engineering Principle: Zero Fake AI</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          FinMate adheres strictly to reliable software systems engineering: AI agents and LLM explanations are deferred until high-integrity data pipelines (Phase 2), analytics engines (Phase 3), and verified RAG knowledge bases (Phase 6) are completely established. In Phase 2, FinMate operates strictly on deterministic mathematical truth.
        </p>
      </div>

      {/* Multi-Agent Architecture Blueprint */}
      <div className="space-y-4">
        <h3 className="text-base font-semibold text-slate-100">Planned Multi-Agent System</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((ag) => (
            <div
              key={ag.name}
              className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm text-slate-200">{ag.name}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {ag.phase}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{ag.role}</p>
              <div className="pt-2 border-t border-slate-800/80 flex items-center gap-1.5 text-[10px] text-emerald-400 font-medium">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Boundary Defined</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Decision-Support Safeguard */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 text-xs text-slate-400 space-y-2">
        <div className="flex items-center gap-2 text-slate-300 font-semibold">
          <ShieldAlert className="w-4 h-4 text-cyan-400" />
          <span>Human-in-the-Loop Guarantee</span>
        </div>
        <p>
          Future AI agent outputs will always present explainable recommendations requiring explicit human confirmation. The system will never execute autonomous monetary transfers, transactions, or account alterations.
        </p>
      </div>
    </div>
  );
};
