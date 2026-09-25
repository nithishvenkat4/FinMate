# AI Orchestration & Multi-Agent Workflows

## 1. Orchestration Architecture Diagram

```mermaid
flowchart TD
    User([User Prompt]) --> Interaction[FinMate Frontend Hub]
    Interaction --> Orchestrator[AI Orchestrator / Triage Agent]
    
    subgraph Guardrails [Input & Security Guardrails]
        Orchestrator --> InjCheck{Prompt Injection?}
        InjCheck -- Yes --> Refusal[Block & Return Security Refusal]
        InjCheck -- No --> IntentClass[Classify Intent]
    end
    
    subgraph Specialists [Specialized Agents Layer]
        IntentClass -->|TRANSACTION_QUERY| TxAgent[Transaction Agent]
        IntentClass -->|BUDGET_QUERY| BudgetAgent[Budget Agent]
        IntentClass -->|GOAL_QUERY| GoalAgent[Goal Agent]
        IntentClass -->|INVESTMENT_QUERY| InvAgent[Investment Agent]
        IntentClass -->|WHAT_IF_SCENARIO| SimSandbox[What-If Simulation Sandbox]
        IntentClass -->|MUTATION_PROPOSAL| MutProp[Approval Proposal Generator]
        IntentClass -->|COMPLEX_FINANCIAL_DECISION| PrimaryCollab[Multi-Agent Collaboration]
    end

    subgraph PrimaryCollabChain [Primary Multi-Agent Collaboration Flow]
        PrimaryCollab --> Step1[Step 1: Budget Agent Evaluates Surplus & Forecast]
        Step1 --> Step2[Step 2: Goal Agent Calculates Milestone Run-Rate]
        Step2 --> Step3[Step 3: RAG Retrieves Regulatory Guidelines]
        Step3 --> Step4[Step 4: Financial Decision Agent Synthesizes Options A/B/C]
    end

    subgraph ApprovalEngine [Human-in-the-Loop Engine]
        MutProp --> PendingApp[Pending Approval Object Created]
        PendingApp --> UserDecision{User Approves?}
        UserDecision -- Approved --> ExecuteMutation[Apply Mutation to Database]
        UserDecision -- Rejected --> KeepDB[Database Remains Unchanged]
    end

    Step4 --> FinalResp[Decision-Support Response with Tradeoffs]
    ExecuteMutation --> FinalResp
    KeepDB --> FinalResp
    TxAgent --> FinalResp
    InvAgent --> FinalResp
    SimSandbox --> FinalResp
    FinalResp --> User
```

---

## 2. Intent Routing Rules
1. **Simple Queries** route directly to the single specialist:
   - *"How much did I spend on food?"* → `TransactionAgent`
   - *"Can I save ₹10,000 this month?"* → `BudgetAgent`
   - *"Can I reach my education goal?"* → `GoalAgent`
   - *"What does an ETF mean?"* → `InvestmentAgent`
   *(Prevents multi-agent latency, cost, and complexity overhead when unnecessary.)*
2. **Multi-Domain Complex Queries** trigger sequential multi-agent collaboration:
   - *"Can I afford a ₹20,000 laptop next month without hurting my education goal?"*
     → `AIOrchestrator` → `BudgetAgent` → `GoalAgent` → `FinancialDecisionAgent`
   - *"I am spending more than usual. What should I look at first?"*
     → `AIOrchestrator` → `TransactionAgent` → `BudgetAgent` → `FinancialDecisionAgent`

---

## 3. Execution Bounds & Loop Detection
To protect system resources and prevent infinite loops:
- `MAX_AGENT_STEPS = 8`
- `MAX_TOOL_CALLS = 12`
- `MAX_AGENT_HANDOFFS = 3`
- **Cycle Detection**: The orchestrator records a set of `(agent, action)` signatures. If a cycle is detected (e.g. Agent A → Agent B → Agent A), execution immediately breaks and returns the accumulated partial results safely.
