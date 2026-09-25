# Agent Responsibilities & Permission Matrix

## 1. Agent Responsibility Matrix

| Agent | Identity & Purpose | Allowed Inputs | Structured Outputs | Permitted Tools | Permission Level | Escalation Conditions | Failure Handling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Transaction Agent** | Transaction history analysis, NLP categorization, spending aggregation, anomaly identification | Natural language transaction queries, description text, filter dates | Categorized spending breakdown, anomalies, reclassification proposals | `get_transactions`, `get_category_spending`, `classify_transaction`, `check_transaction_anomaly`, `propose_transaction_update` | Read-only analytics + Approval-gated mutation | If transaction description indicates large transfer or trade | Returns 0.00 fallback with note if zero ledger records found |
| **Budget Agent** | Income, expense, surplus, savings rate, and cashflow modeling | Financial profile, spending queries, What-If parameter deltas | Deterministic surplus, savings rate %, ML forecast outlays | `get_financial_summary`, `get_category_spending`, `forecast_monthly_expenses`, `simulate_financial_scenario` | Read-only + In-memory simulation | If query impacts goal feasibility (signals `GoalAgent` handoff) | Falls back to baseline 3-month rolling average if ML forecaster unavailable |
| **Goal Agent** | Target milestone feasibility, percentage progress, required monthly savings run-rate | Target amounts, deadlines, goal queries, surplus context | Progress %, remaining amount, required run-rate, delay projections | `get_goals`, `calculate_goal_progress`, `calculate_required_monthly_saving`, `simulate_financial_scenario`, `propose_goal_update` | Read-only + Approval-gated mutation | If surplus is insufficient to meet required monthly run-rate | Informs user if zero registered goals are present in ledger |
| **Investment Agent** | Informational portfolio valuations, asset allocation %, educational concept guide | Educational queries (ETF, index fund, risk), portfolio review | Asset class allocation %, diversification status, RAG citations | `get_investments`, `calculate_investment_allocation`, `retrieve_financial_knowledge` | Read-only informational | If user requests trade execution or stock advice (firm refusal) | Returns educational concept summary if investment holdings are empty |
| **Financial Decision Agent** | Multi-agent synthesis, trade-off modeling, Option A/B/C structuring | Specialist results from Budget, Goal, Transaction, Investment agents | Balanced options, trade-offs, numerical consistency, uncertainties | `get_financial_summary`, `simulate_financial_scenario`, `retrieve_financial_knowledge` | Read-only synthesis | If agent perspectives conflict (preserves both without artificial consensus) | Produces partial fallback report if individual specialist agents fail |
| **AI Orchestrator** | Task triage, intent classification, route selection, loop prevention, trace recording | Raw user prompt, authenticated security context | Universal `AgentTaskResult`, execution trace, pending approvals | Central supervisor over all agent workflows | Read-only orchestration | If prompt injection, SQL injection, or autonomous trade detected | Safely terminates, halts runaway loops, records trace to database |

---

## 2. Principle of Least Privilege
No agent is granted global or arbitrary tool access:
- **Transaction Agent** cannot read investment data or modify goals.
- **Budget Agent** cannot modify transaction records or execute orders.
- **Investment Agent** has ZERO write access and CANNOT execute trades.
- **AI Orchestrator** enforces strict parameter schema validation and injects the authenticated `user_id` from security context, completely preventing cross-tenant data leakage.
