# FinMate Agent Tool Registry

## 1. Tool Governance & Architecture
All agent actions in FinMate must be mediated through the central `ToolRegistry` (`app/ai/tools/registry.py`).
Agents are strictly prohibited from executing raw SQL, spawning arbitrary subprocesses, making unconstrained HTTP network calls, or directly modifying database tables.

---

## 2. Complete Registered Tools Catalog (15 Tools)

### A. Read-Only Analytics Tools
1. **`get_financial_summary`**:
   - *Description*: Retrieves authoritative deterministic financial totals (income, expenses, net surplus, savings rate %, active goals count, total investments).
   - *Allowed Agents*: `BudgetAgent`, `FinancialDecisionAgent`, `Orchestrator`
2. **`get_transactions`**:
   - *Description*: Retrieves recent transaction records with category, type, and date filters.
   - *Allowed Agents*: `TransactionAgent`, `Orchestrator`
3. **`get_category_spending`**:
   - *Description*: Computes category-wise expenditure aggregations and percentages.
   - *Allowed Agents*: `TransactionAgent`, `BudgetAgent`, `Orchestrator`
4. **`get_goals`**:
   - *Description*: Fetches all active goals with target amounts, current accumulations, and deadlines.
   - *Allowed Agents*: `GoalAgent`, `Orchestrator`
5. **`calculate_goal_progress`**:
   - *Description*: Computes exact progress percentage and remaining amounts for a goal.
   - *Allowed Agents*: `GoalAgent`, `FinancialDecisionAgent`, `Orchestrator`
6. **`calculate_required_monthly_saving`**:
   - *Description*: Calculates required monthly savings run-rate to reach a target amount by a deadline.
   - *Allowed Agents*: `GoalAgent`, `BudgetAgent`, `Orchestrator`
7. **`get_investments`**:
   - *Description*: Retrieves portfolio investment holdings and current valuations.
   - *Allowed Agents*: `InvestmentAgent`, `Orchestrator`
8. **`calculate_investment_allocation`**:
   - *Description*: Computes asset class allocation breakdown percentages (equity, debt, gold).
   - *Allowed Agents*: `InvestmentAgent`, `FinancialDecisionAgent`, `Orchestrator`

### B. Machine Learning & RAG Intelligence Tools
9. **`classify_transaction`**:
   - *Description*: Categorizes transaction descriptions using supervised LinearSVC classifier (98.4% Accuracy).
   - *Allowed Agents*: `TransactionAgent`, `Orchestrator`
10. **`check_transaction_anomaly`**:
    - *Description*: Evaluates if a transaction amount is an anomaly using an Isolation Forest model.
    - *Allowed Agents*: `TransactionAgent`, `Orchestrator`
11. **`forecast_monthly_expenses`**:
    - *Description*: Projects upcoming monthly expenses with 90% confidence bands using Ridge regression.
    - *Allowed Agents*: `BudgetAgent`, `GoalAgent`, `FinancialDecisionAgent`, `Orchestrator`
12. **`retrieve_financial_knowledge`**:
    - *Description*: Performs semantic search over verified regulatory guidelines (RBI/SEBI).
    - *Allowed Agents*: `InvestmentAgent`, `FinancialDecisionAgent`, `Orchestrator`

### C. Simulation & Mutating Tools
13. **`simulate_financial_scenario`** *(In-Memory Sandbox)*:
    - *Description*: Computes the impact of additional expenses, cuts, or income changes on monthly surplus and goal completion times in an isolated in-memory sandbox without touching the database.
    - *Allowed Agents*: `BudgetAgent`, `GoalAgent`, `FinancialDecisionAgent`, `Orchestrator`
14. **`propose_transaction_update`** *(Mutating — Human Approval Required)*:
    - *Description*: Generates a pending `AgentApproval` object to reclassify a transaction. Never mutates database until user approves.
    - *Allowed Agents*: `TransactionAgent`, `Orchestrator`
15. **`propose_goal_update`** *(Mutating — Human Approval Required)*:
    - *Description*: Generates a pending `AgentApproval` object to update a goal target amount. Never mutates database until user approves.
    - *Allowed Agents*: `GoalAgent`, `Orchestrator`

---

## 3. Tool Execution Audit Trail
Every tool invocation records an entry in the `agent_tool_calls` table:
- `task_id`: UUID
- `agent_name`: Name of calling agent
- `tool_name`: Name of invoked tool
- `parameters`: Sanitized input parameters
- `result`: Structured JSON output
- `is_mutation`: Boolean
- `status`: `success`, `error`, `blocked`, or `pending_approval`
- `execution_ms`: Accurate duration in milliseconds
