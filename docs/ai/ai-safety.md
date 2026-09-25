# FinMate Phase 3 — AI Safety, Guardrails & Decision-Support Policies

---

## 1. Core Principle: Decision-Support Only

FinMate is an **AI-powered Personal Financial Decision-Support System**.

### 1.1 Non-Autonomous Boundary
FinMate is explicitly **NOT**:
- An autonomous stock trading bot
- A banking or automated payment platform
- A credit card charge authorization tool
- A financial advisor legally replacing certified human professionals
- An autonomous system that transfers money, liquidates assets, or modifies accounts

The user **always** remains the final decision-maker.

---

## 2. Human-in-the-Loop Safeguards

1. **Transaction Categorization**:
   - The ML classifier provides category suggestions with confidence scores.
   - Low-confidence predictions ($< 60\%$) explicitly display a warning.
   - The user has interactive `Confirm` and `Override` buttons to enforce their preferred category.
2. **Actionable Options in AI Answers**:
   - The LLM synthesizes choices as distinct, mutually exclusive options (e.g., *"Option 1: Purchase from surplus"*, *"Option 2: Apply 30-Day Waiting Rule"*, *"Option 3: Save over 2 months"*).
   - Responses always set `user_decision_required = true`.

---

## 3. Ban on False Precision

AI models must never project certainty where stochastic variance exists:
- **BAD**: *"Your monthly expense next month will be exactly ₹34,521.13 with 95% guarantee."*
- **GOOD**: *"Estimated monthly expense: ₹34,500 (90% confidence range: ₹31,450 to ₹37,550). Subject to unexpected seasonal outlays."*

Rupee projections are cleanly rounded to the nearest ₹50 or ₹100 to communicate that they are probabilistic estimates.

---

## 4. Privacy & Context Minimization

To safeguard sensitive financial information:
- Passwords, credit card CVV numbers, UPI PINs, bank credentials, and national identification numbers (Aadhaar, PAN) are never forwarded to AI models or LLMs.
- Only aggregated figures necessary for decision analysis (monthly income, total expenses, net savings rate, active goal targets) are included in the synthesized context.

---

## 5. Defense Against Prompt Injection & Jailbreaks

- Input text is sanitized and scanned against known injection patterns.
- External documents retrieved via RAG are treated strictly as untrusted reference data enclosed in `<untrusted_retrieved_evidence>` delimiters.
- Immutable System Rules override any attempted user or document instruction overrides.
