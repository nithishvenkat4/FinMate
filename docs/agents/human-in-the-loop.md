# Human-in-the-Loop & Approval System

## 1. Governance Principles
FinMate strictly enforces a 3-tier oversight model:
- **Level 1 (Autonomous Analytics)**: Read-only data queries, statistical forecasting, RAG knowledge retrieval, and What-If simulations. No approval required.
- **Level 2 (Proposed Mutations)**: Reclassifying transactions, updating financial goals, modifying profile settings. Mandatory user confirmation required before any database write occurs.
- **Level 3 (High-Impact Financial Actions)**: Real fund transfers, trade executions, payments. Strictly **BLOCKED** and forbidden in the architecture.

---

## 2. Mutating Action Lifecycle

```
[Agent Proposes Mutation]
        ↓
[Create AgentApproval Record (status='pending', expires_at=now + 15m)]
        ↓
[Pause Workflow (status='waiting_for_user')]
        ↓
[Frontend Displays Proposed vs Current Diff]
        ↓
+------------------------+------------------------+
|                                                 |
v                                                 v
[User Clicks Approve]                    [User Clicks Reject]
        ↓                                         ↓
[Verify Task Ownership & Expiry]         [Mark status='rejected']
        ↓                                         ↓
[Execute Database Mutation]              [Database UNCHANGED]
        ↓
[Mark status='approved']
```

---

## 3. Approval Object Contract
Every approval request contains:
```json
{
  "approval_id": "8f8b030b-9273-4537-a50d-85f839c4f028",
  "task_id": "c0182470-36d7-40d6-848e-282d1c67e810",
  "user_id": "00000000-0000-0000-0000-000000000001",
  "agent_name": "TransactionAgent",
  "action_type": "update_transaction_category",
  "target_id": "e2e92c28-2dfa-45c1-8ce2-4752b04f7f6e",
  "current_value": { "category": "Other" },
  "proposed_value": { "category": "Shopping" },
  "reason": "User requested reclassification based on Amazon purchase description.",
  "status": "pending",
  "expires_at": "2026-09-22T16:30:00Z"
}
```

---

## 4. Expiration & User Cancellation
- **Expiration Mechanism**: Approvals remain valid for 15 minutes. Attempting to approve an expired proposal throws `410 Gone (TimeoutError)` and refuses execution.
- **Cancellation**: Users can cancel an ongoing task or approval at any time via `POST /api/v1/agent/tasks/{id}/cancel`.
