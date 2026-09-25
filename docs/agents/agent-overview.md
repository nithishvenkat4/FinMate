# FinMate Phase 4: Agentic Intelligence Overview

## 1. System Identity & Mission
FinMate is an **AI-powered Personal Financial Decision-Support System** designed for CIT Course 19MAM54: AI Systems Engineering. It provides personalized, explainable, and grounded financial reasoning while keeping the user in absolute control.

FinMate is **NOT** an autonomous trading bot, banking application, or money transfer system. It never executes financial transfers or trades, and never mutates user data without explicit human-in-the-loop approval.

---

## 2. Core Agentic Architecture
Phase 4 transforms Phase 3 capabilities (deterministic financial analytics, ML classifiers, time-series forecasters, anomaly detectors, and RAG retrieval) into a governed multi-agent intelligence layer.

```
USER
  ↓
FINMATE INTERACTION LAYER (Frontend Multi-Agent Hub)
  ↓
AI ORCHESTRATOR (Intent Triage, Guardrails, Route Selection)
  ↓
+------------------+------------------+------------------+------------------+
|                  |                  |                  |                  |
v                  v                  v                  v                  v
Transaction        Budget             Goal               Investment         What-If Sandbox
Agent              Agent              Agent              Agent              Simulation
|                  |                  |                  |                  |
+------------------+------------------+------------------+------------------+
                   |
                   v
          Financial Decision Agent (Cross-Domain Synthesis)
                   |
                   v
          Human-in-the-Loop Approval (If Mutating Action Proposed)
                   |
                   v
                 USER
```

---

## 3. Specialized Agents
FinMate implements 6 specialized agents:
1. **AI Orchestrator**: Central supervisor, intent classification, task routing, execution step limits, loop detection, and audit tracing.
2. **Transaction Agent**: Transaction understanding, spending categorization, anomaly detection, and reclassification proposals.
3. **Budget Agent**: Income, expenses, monthly surplus, savings rate, and statistical cashflow forecasting.
4. **Goal Agent**: Milestone tracking, percentage progress, required monthly savings run-rate, and feasibility checks.
5. **Investment Agent**: Informational portfolio valuation, asset allocation breakdown, and regulatory concept explanation via RAG.
6. **Financial Decision Agent**: Cross-domain synthesis, trade-off analysis, structured options (Options A, B, C), and numerical consistency enforcement.

---

## 4. Key Agentic Design Principles
- **Separation of Concerns**: Reasoning, tool selection, and explanation belong to agents; authoritative financial arithmetic, database queries, and ML model execution belong to deterministic backend services.
- **Least-Privilege Tool Permissions**: Agents only receive access to the specific tools required for their responsibilities.
- **Human-in-the-Loop Gating**: Mutating actions (updating transaction category, changing goal targets) are intercepted and held in a 15-minute pending approval state until explicit user confirmation.
- **Zero Fake Agent Activity**: Every displayed UI step corresponds to an authentic, persisted step in `agent_tasks.execution_trace`.
