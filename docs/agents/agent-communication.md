# Agent Communication & Evidence Contracts

## 1. Inter-Agent Communication Protocol
FinMate rejects opaque, unconstrained natural-language babble between agents. All inter-agent data exchange utilizes strictly structured Pydantic messages:

```python
class AgentMessage(BaseModel):
    task_id: str
    from_agent: str
    to_agent: str
    message_type: str  # analysis_result, handoff_request, clarification_needed
    data: Dict[str, Any]
    confidence: float
    assumptions: List[str]
    limitations: List[str]
```

---

## 2. Universal Agent Result Contract
Every specialist agent returns an explicit `AgentResult` object that strictly partitions evidence types:

```python
class AgentResult(BaseModel):
    agent: str
    status: str  # completed, pending_approval, failed, requires_handoff
    summary: str
    facts: List[Dict[str, Any]]          # Derived from stored ledger data
    predictions: List[Dict[str, Any]]    # Produced by supervised/time-series ML models
    recommendations: List[str]          # Actionable decision options
    tradeoffs: List[Dict[str, Any]]      # Concrete comparative trade-offs
    assumptions: List[str]              # Explicit modeling assumptions
    uncertainties: List[str]            # Statistical variance & unknown factors
    tools_used: List[str]               # Audit trail of invoked tools
    sources: List[Dict[str, Any]]        # Regulatory citations retrieved via RAG
    evidence_quality: str               # HIGH_EVIDENCE, MEDIUM_EVIDENCE, LOW_EVIDENCE
    pending_approval: Optional[Dict]    # Mutating proposal payload if human review required
    handoff_target: Optional[str]       # Target agent name if handoff requested
```

---

## 3. Fact vs. Prediction vs. External Knowledge Separation
A core mandate of Course 19MAM54 is preventing hallucinations by enforcing strict evidence boundaries:
- **FACT**: Exact mathematical numbers computed by Python Decimal routines from PostgreSQL/SQLite records (e.g. `Income: ₹60,000`, `Recent Expenses: ₹35,000`, `Surplus: ₹25,000`).
- **PREDICTION**: Probabilistic statistical forecasts with explicit confidence intervals (e.g. `Ridge Regression: ₹36,250 ± ₹3,050 at 90% confidence`).
- **EXTERNAL KNOWLEDGE**: Regulatory rules and personal finance guidelines retrieved from verified markdown documents (RBI, SEBI, FPSB India 50/30/20 guideline).
- **INTERPRETATION / TRADEOFF**: The agent's synthesized trade-offs and options (Option A, Option B, Option C).
- **UNCERTAINTY**: Explicitly acknowledged variance factors (e.g., utility fluctuations, inflation).
