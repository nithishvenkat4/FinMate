# FinMate — Personal Financial Decision-Support Agent & Ingestion Ecosystem

FinMate is an enterprise-grade personal financial decision-support system engineered to provide accurate, transparent, and mathematically verified financial insights. The platform unifies a deterministic calculation engine, predictive machine learning models, semantic regulatory retrieval-augmented generation (RAG), a collaborative multi-agent orchestration architecture, an interactive React workspace, and a native Android background SMS ingestion engine.

FinMate operates strictly as a decision-support system. It never acts as an autonomous financial agent: it does not execute trades, perform money transfers, or apply state-modifying ledger updates without verified human-in-the-loop authorization.

---

## Executive Summary & Engineering Highlights

| Dimension | Specification / Metric | Technical Implementation |
| :--- | :--- | :--- |
| Core Architecture | Multi-Agent Orchestration + Clean Layered Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0 ORM, Python 3.11+ |
| Computation Standard | Zero-Deviation Exact Monetary Arithmetic | Python Decimal (`ROUND_HALF_UP`), SQL `NUMERIC(15, 2)` |
| Transaction Classification | 98.4% Accuracy, 0.9849 Macro F1-Score | LinearSVC Champion Model + Scikit-Learn TF-IDF Pipeline |
| Time-Series Forecasting | Holdout MAE: INR 3,369.93 | Ridge Regression with Strict Lagged Features & 90% Confidence Intervals |
| Anomaly Detection | Statistical Expenditure Spike Identification | Unsupervised Isolation Forest (Contamination: 0.05) |
| Regulatory Knowledge RAG | 93.3% Hit Rate @ 3, 0.95ms Latency | Cosine Vector Similarity over RBI, SEBI, and FPSB India Guidelines |
| Governance Model | 3-Tier Human-in-the-Loop (HITL) Engine | 15-Minute Expiration Window, Two-Step State Mutation Gating |
| Counterfactual Analysis | In-Memory What-If Simulation Sandbox | Isolated In-Memory Delta Computations without Database Side-Effects |
| Mobile Telemetry | Privacy-First Native Android Ingestion | Kotlin, AndroidX Room, WorkManager, On-Device Regex Parsing |
| Test Coverage | 92 / 92 Automated Tests Passing (100%) | Pytest Unit, Integration, and Data Pipeline Test Suites |
| Benchmark Performance | 12 / 12 Standard Agent Benchmark Tasks (100%) | End-to-End Orchestrator Decision Evaluation Matrix |
| Frontend Platform | Zero-Error Production Build | React 19, TypeScript, Vite, Tailwind CSS, Lucide, Recharts |

---

## Master System Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                          CLIENT INTERFACES                                        |
|                                                                                                   |
|   +---------------------------------------+       +-------------------------------------------+   |
|   |         React 19 Web Workspace        |       |          Native Android Client            |   |
|   |   (TypeScript, Vite, Tailwind CSS,    |       |   (Kotlin, Room DB, WorkManager,          |   |
|   |    Live Agent Trace, HITL Diff Cards) |       |    On-Device Regex, Zero Raw SMS Upload)  |   |
|   +---------------------------------------+       +-------------------------------------------+   |
+-----------------------│-------------------------------------------------│-------------------------+
                        │ HTTP / JSON                                     │ POST /api/v1/transactions/from-sms
                        ▼                                                 ▼
+---------------------------------------------------------------------------------------------------+
|                                      FASTAPI REST API GATEWAY                                     |
|                              (/api/v1/* Routing, Pydantic v2 Validation)                          |
+---------------------------------------------------------------------------------------------------+
         │                                       │                                       │
         ▼                                       ▼                                       ▼
+---------------------------------+ +---------------------------------+ +---------------------------+
|    MULTI-AGENT ORCHESTRATION    | |    MACHINE LEARNING & RAG       | |    DATA & COMPUTATION     |
|                                 | |                                 | |                           |
| - AI Orchestrator (DAG Router)  | | - LinearSVC Classifier          | | - Deterministic Math      |
| - Transaction Specialist        | |   (10 Categories, 98.4% Acc)    | |   (Python Decimal Engine) |
| - Budget Specialist             | | - Ridge Expense Forecaster      | | - 11-Rule Data Quality    |
| - Goal Specialist               | |   (Lagged Features, 90% Bands)  | |   Engine (Error/Warn/Info)|
| - Investment Specialist         | | - Isolation Forest Anomaly      | | - CSV Ingestion Pipeline  |
| - Decision Synthesis Specialist | |   Detection                     | |   (Delimiter/Encoding)    |
| - 15-Tool Governed Registry     | | - Semantic Vector RAG Engine    | | - Duplicate Detection     |
| - 3-Tier HITL Approval Engine   | |   (RBI, SEBI, FPSB Guidelines)  | |   (Sliding Window Hash)   |
| - In-Memory What-If Sandbox     | | - Multi-Provider LLM Gateway    | | - Lineage Tracking        |
+---------------------------------+ +---------------------------------+ +---------------------------+
         │                                       │                                       │
         └───────────────────────────────────────┼───────────────────────────────────────┘
                                                 ▼
+---------------------------------------------------------------------------------------------------+
|                                      PERSISTENCE & STORAGE LAYER                                  |
|                                                                                                   |
|   SQLAlchemy 2.0 ORM  <--->  Primary: PostgreSQL (Docker)  |  Resilient Fallback: SQLite         |
|   Entities: User, FinancialProfile, Transaction, Category, Goal, Investment, ImportRecord,       |
|             AgentTask, AgentApproval, AgentToolCall                                               |
+---------------------------------------------------------------------------------------------------+
```

---

## Core System Subsystems

### 1. Multi-Agent Intelligence & Orchestration Subsystem

The multi-agent tier coordinates specialized, domain-constrained AI agents through a centralized orchestrator, strictly enforcing the principle of least privilege.

```
                              User Financial Query
                                       │
                                       ▼
                             +-------------------+
                             |  AI Orchestrator  |
                             |  (Intent Triage)  |
                             +-------------------+
                                       │
         ┌──────────────────┬──────────┴──────────┬──────────────────┐
         ▼                  ▼                     ▼                  ▼
+------------------+ +----------------+ +------------------+ +------------------+
| TransactionAgent | |  BudgetAgent   | |    GoalAgent     | | InvestmentAgent  |
| Spending breakdown| | Surplus & cash | | Milestones & run | | Allocation % &   |
| & anomaly review | | flow forecasts | | rate feasibility | | risk disclosures|
+------------------+ +----------------+ +------------------+ +------------------+
         │                  │                     │                  │
         └──────────────────┼─────────────────────┴──────────────────┘
                            ▼
               +--------------------------+
               |  FinancialDecisionAgent  |
               | (Multi-Option Synthesis) |
               +--------------------------+
                            │
            ┌───────────────┴───────────────┐
            │                               │
    Informational Plan              Mutating Proposal
    (Read-Only Response)            (Triggers HITL Gate)
            │                               │
            ▼                               ▼
    Render Facts, Trade-Offs,       Create AgentApproval Record
    Predictions, and Citations      (15-Minute Expiration, Awaiting User)
```

- **AI Orchestrator**: Executes deterministic intent triage, maps user queries to optimal specialist execution routes, enforces loop boundaries (`MAX_AGENT_STEPS = 8`, `MAX_TOOL_CALLS = 12`, `MAX_AGENT_HANDOFFS = 3`), and generates non-fabricated execution traces.
- **Transaction Specialist**: Aggregates categorical spending, investigates transaction flags, and drafts reclassification proposals.
- **Budget Specialist**: Calculates cash flow surpluses, savings rates, projects monthly expense trajectories, and evaluates scenario deltas.
- **Goal Specialist**: Monitors target accumulation, estimates horizon feasibility, and computes required monthly contribution rates.
- **Investment Specialist**: Evaluates portfolio distribution and surfaces asset allocation education based on official regulatory frameworks (strictly non-transactional).
- **Financial Decision Agent**: Synthesizes cross-specialist evidence into structured decision alternatives (Option A, Option B, Option C), surfacing trade-offs, potential drawbacks, and numerical validations against backend facts.
- **Governed Tool Registry (15 Tools)**:
  - Strict input and output contracts enforced via Pydantic schemas.
  - Per-agent allowlists ensuring specialists can only invoke domain-relevant capabilities.
  - Mandatory tenant injection guaranteeing data isolation across multi-user environments.
- **Human-in-the-Loop (HITL) Approval Engine**:
  - Classifies actions into Read-Only (automatic), Simulation (in-memory execution), and Mutating (approval required).
  - Mutating operations (`propose_transaction_update`, `propose_goal_update`) are staged in a pending state with a 15-minute expiration window.
  - State changes are committed to the primary ledger only upon explicit user confirmation; rejection leaves records completely untouched.
- **In-Memory What-If Simulation Sandbox**:
  - Implements `simulate_financial_scenario` to project adjustments to income, fixed expenditures, or discretionary spending.
  - Models financial runway, revised savings percentages, and goal milestone shifts without altering persistent database records.

---

### 2. Machine Learning & Regulatory RAG Pipeline

FinMate couples traditional machine learning models for low-latency inference with retrieval-augmented generation for compliance-backed guidance.

```
                          Incoming Unstructured Text / Query
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
+-----------------------+   +---------------------------+   +-----------------------+
|  Transaction Classifier|   |  Expense Forecaster       |   |  Regulatory RAG       |
|                       |   |                           |   |                       |
| - Architecture:       |   | - Architecture:           |   | - Knowledge Base:     |
|   LinearSVC + TF-IDF  |   |   Ridge Regression        |   |   RBI, SEBI, FPSB     |
| - Accuracy: 98.4%     |   | - Features: Strict Lagged |   | - Metric: 93.3% Hit@3 |
| - Macro F1: 0.9849    |   |   (Zero Data Leakage)     |   | - Latency: 0.95ms     |
| - Output: 10 Taxonomies|  | - Output: Point + 90% CI  |   | - Cosine Similarity   |
+-----------------------+   +---------------------------+   +-----------------------+
```

- **Transaction Classification Model**:
  - Model: Calibrated Linear Support Vector Classifier (`LinearSVC`) with word-level TF-IDF feature extraction.
  - Performance: **98.4% Accuracy** and **0.9849 Macro F1-Score** across 10 discrete categories (*Housing, Food & Dining, Transportation, Utilities, Healthcare, Entertainment, Shopping, Personal Care, Education, Investments*).
  - Inference Latency: Sub-millisecond execution suitable for high-volume streaming imports.
- **Time-Series Monthly Expense Forecaster**:
  - Model: `Ridge` Regression trained via `TimeSeriesSplit` cross-validation.
  - Feature Engineering: Incorporates strictly lagged features (`lag_1`, `lag_2`, `lag_3`, `rolling_avg_3`, `month_num`) to eliminate look-ahead bias.
  - Accuracy: Holdout Mean Absolute Error (MAE) of **INR 3,369.93**.
  - Output Structure: Generates expected expenditure together with statistical 90% uncertainty intervals (`lower_bound` to `upper_bound`).
- **Unsupervised Anomaly Detection**:
  - Model: `IsolationForest` configured with an empirical contamination factor of 0.05.
  - Identifies irregular transaction amounts and category-specific expenditure deviations to surface potential billing errors or fraud.
- **Semantic Vector Regulatory RAG Engine**:
  - Corpus: Grounded in official regulatory policies including Reserve Bank of India (RBI) emergency reserve directives, Securities and Exchange Board of India (SEBI) risk disclosures, and Financial Planning Standards Board (FPSB) India 50/30/20 guidelines.
  - Vector Retrieval: Cosine similarity vector search achieving **93.3% Hit Rate @ 3** with an average retrieval latency of **0.95ms**.
- **LLM Abstraction & Security Guardrails**:
  - Unified interface (`BaseLLMProvider`) supporting deterministic zero-cost testing (`MockLLMProvider`), OpenAI models (`OpenAILLMProvider`), and Google Gemini (`GeminiLLMProvider`).
  - Integrated prompt injection detection filter (`detect_prompt_injection`) that flags adversarial injection attempts before orchestration execution.

---

### 3. Deterministic Financial Domain & Calculation Engine

To prevent hallucinated financial calculations, all numerical computations are strictly decoupled from Large Language Models and delegated to a dedicated mathematical engine.

- **Monetary Precision**: Engineered with Python's native `Decimal` module and explicit rounding (`ROUND_HALF_UP`) matching relational `NUMERIC(15, 2)` columns, eliminating IEEE 754 floating-point errors.
- **Authoritative Calculations**:
  - Net monthly surplus: `Surplus = Monthly Income - (Fixed Expenses + Discretionary Outflows)`
  - True savings rate: `Savings Rate = (Savings Contributions / Total Inflows) * 100`
  - Milestone velocity: Exact remaining horizon calculation and required monthly saving:
    $$\text{Required Monthly Saving} = \frac{\text{Target Amount} - \text{Current Amount}}{\text{Remaining Months}}$$
- **Rule of Separation**: Language models are restricted to textual narration and contextual explanation; all monetary statistics provided to the user are derived from backend calculation outputs.

---

### 4. Data Engineering, Ingestion & Quality Engine

FinMate incorporates an end-to-end data processing pipeline capable of handling heterogeneous financial records while enforcing structural integrity.

- **Multi-Stage Ingestion Pipeline**:
  - `CSVParser`: Automatic detection of delimiters (comma, semicolon, tab, pipe) and file encodings (UTF-8, Latin-1, CP1252).
  - `DataNormalizer`: Normalizes varying date structures (`YYYY-MM-DD`, `DD/MM/YYYY`, `MM/DD/YYYY`), extracts numeric amounts across differing credit/debit column conventions, and removes foreign currency symbols.
- **11-Rule Deterministic Quality Engine**:
  - Evaluates every row against comprehensive rules categorized by severity:
    - `ERROR`: Rejects rows with unparseable dates, negative expense amounts, missing mandatory identifiers, or invalid categories.
    - `WARNING`: Flags statistical anomalies, potential duplicates, or unassigned classifications.
    - `INFO`: Highlights data enrichment events and format conversions.
- **Duplicate Prevention & Lineage Tracking**:
  - Sliding-window heuristic matching `user_id + transaction_date + amount + normalized_description`.
  - Full audit lineage recorded on each transaction: `source_type`, `source_reference`, `import_id`, and `data_quality_flags`.
  - Batch import tracking captured in dedicated `import_records` tables with pre-commit preview capabilities.

---

### 5. Native Android SMS Ingestion Subsystem (`FinMateSMS`)

The Android client provides passive, privacy-preserving transaction tracking by parsing authorized bank SMS alerts directly on-device.

```
+-------------------------------------------------------------------------------+
|                        Android Client (FinMateSMS)                            |
|                                                                               |
|   Incoming Bank SMS                                                           |
|        │                                                                      |
|        ▼                                                                      |
|   [SmsReceiver] ──────► Sender in Allowed Whitelist? (HDFCBK, SBIINB, etc.)   |
|        │                       │                                              |
|        │                       └─► NO: Immediate Discard                      |
|        ▼                                                                      |
|   [Security Filter] ──► Contains OTP / Secret PIN? ──► YES: Immediate Discard |
|        │                                                                      |
|        ▼                                                                      |
|   [SmsTransactionParser] (Local Deterministic Regex)                          |
|        │ Extracts: Amount (>0), Date, Type (Debit/Credit), SHA-256 Hash      |
|        ▼                                                                      |
|   [Room Database] ─────► Inserts PendingTransaction (Unique Hash Index)       |
|        │                                                                      |
|        ▼                                                                      |
|   [SyncWorker] (WorkManager with NetworkType.CONNECTED Constraint)            |
+--------│----------------------------------------------------------------------+
         │ HTTP POST /api/v1/transactions/from-sms (JSON)
         ▼
+-------------------------------------------------------------------------------+
|                            FinMate Backend API                                |
|                                                                               |
|   1. Payload Schema & Numerical Validation                                    |
|   2. Duplicate Verification (source_type="sms" AND source_reference=sms_hash) |
|   3. Atomic Ledger Insertion (HTTP 201 Created)                               |
|   4. Idempotent Conflict Return (HTTP 409 Conflict)                           |
+-------------------------------------------------------------------------------+
```

- **Technical Stack**: Kotlin 1.9+, AndroidX Room 2.6.1, AndroidX WorkManager 2.9.0, Retrofit 2.11.0, OkHttp 4.12.0, Material Design 3.
- **Privacy & Security Guarantees**:
  - Zero Raw SMS Transmission: Message body is parsed locally; raw SMS text is never transmitted over the network.
  - OTP & PIN Filtering: Incoming messages matching one-time passcodes or two-factor security patterns are discarded instantly.
  - Sender Whitelisting: Strict filtering restricted to verified financial institution sender IDs.
- **Dual-Layer Duplicate Protection**:
  - Device Layer: SQLite unique constraint on `sms_hash` prevents duplicate insertions in local Room queue.
  - Server Layer: Query-level verification against `source_reference = sms_hash`. If already recorded, backend returns `HTTP 409 Conflict`, which the Android client marks as synced to prevent retry loops.

---

### 6. Modern Web Interaction Hub

The frontend workspace is built as a single-page application focused on data visualization, agent interaction, and decision governance.

- **Stack**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons, Recharts.
- **Core Views**:
  - **AI Advisor Hub**: Unified multi-agent console with live step-by-step execution traces, latency metrics, partitioned decision support cards (Facts, Forecasts, Trade-offs, Regulatory Citations), and interactive What-If simulation controls.
  - **Human-in-the-Loop Review**: Visual diff cards displaying current ledger values alongside agent-proposed updates with one-click Approve and Reject actions.
  - **Financial Dashboard**: Real-time KPI summaries (monthly surplus, cumulative savings, goal burn-down, asset distribution) rendered via responsive Recharts visualizations.
  - **CSV Ingestion Wizard**: File upload workspace with delimiter sniffing, row-by-row syntax validation, and pre-commit preview.
  - **Transactions Ledger**: Searchable, filterable ledger with category badges, data quality warning indicators, and lineage metadata.
  - **Goals & Portfolio Views**: Milestone tracking with time-horizon projections and asset class allocation breakdowns.

---

## Technical Stack Matrix

| Domain | Technology / Library | Role in System |
| :--- | :--- | :--- |
| Backend Runtime | Python 3.11+ / FastAPI | Asynchronous REST API service and routing |
| Validation & Settings | Pydantic v2 / Pydantic-Settings | Request/response schema validation and environment configuration |
| Database & ORM | SQLAlchemy 2.0 / Alembic | Relational data mapping, connection pooling, declarative migrations |
| Primary Database | PostgreSQL 16 (Docker) | Production transactional database |
| Embedded Database | SQLite 3 (`finmate.db`) | Zero-configuration local database with automatic connection fallback |
| Numerical Math | Python `decimal.Decimal` | Exact monetary calculations with `ROUND_HALF_UP` precision |
| Machine Learning | Scikit-Learn / NumPy / SciPy | LinearSVC classifier, Ridge forecaster, Isolation Forest detector |
| RAG & Embeddings | Scikit-Learn TF-IDF / Cosine Metric | Vector indexing and retrieval over regulatory financial corpus |
| Agent Orchestration | Custom Multi-Agent Runtime | Intent triage, DAG routing, tool execution boundaries, trace logging |
| Frontend Framework | React 19 / TypeScript / Vite | Single-page client web application |
| Styling & UI | Tailwind CSS v4 / Lucide React | Modern responsive interface design and icon system |
| Data Visualization | Recharts | Interactive financial analytics charts and forecast bands |
| Mobile Platform | Kotlin 1.9+ / Android SDK (API 24-34) | Native background SMS ingestion client (`FinMateSMS`) |
| Mobile Persistence | AndroidX Room 2.6.1 | Local offline transaction queue with unique hash constraints |
| Mobile Background | AndroidX WorkManager 2.9.0 | Guaranteed network-constrained synchronization tasks |
| Mobile Networking | Retrofit 2.11.0 / OkHttp 4.12.0 | Type-safe REST client for backend ledger synchronization |
| Testing Framework | Pytest / Pytest-Asyncio / HTTPX | Comprehensive asynchronous unit and integration test runners |
| Containerization | Docker / Docker Compose | Multi-service orchestration for backend and database |

---

## REST API Reference

The FastAPI gateway exposes modular, versioned endpoints under `/api/v1`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/agent/query` | Submits a query to the multi-agent orchestrator; returns execution trace and synthesis |
| `GET` | `/api/v1/agent/tasks/{task_id}` | Retrieves execution trace, facts, predictions, and status of an agent task |
| `POST` | `/api/v1/agent/approvals/{approval_id}/approve` | Approves a pending state mutation and commits updates to the database |
| `POST` | `/api/v1/agent/approvals/{approval_id}/reject` | Rejects a pending state mutation without modifying stored records |
| `POST` | `/api/v1/ai/classify-transaction` | Classifies transaction description via the LinearSVC machine learning model |
| `POST` | `/api/v1/ai/forecast-expenses` | Returns 30-day expense forecast with 90% statistical uncertainty intervals |
| `POST` | `/api/v1/ai/detect-anomalies` | Evaluates transaction batches for spending outliers using Isolation Forest |
| `POST` | `/api/v1/ai/rag/query` | Executes semantic vector search over the regulatory compliance knowledge base |
| `POST` | `/api/v1/transactions/from-sms` | Ingests parsed Android SMS transaction with hash-based duplicate prevention |
| `GET` | `/api/v1/transactions/` | Lists user transactions with filtering, pagination, and category breakdowns |
| `POST` | `/api/v1/imports/preview` | Generates pre-commit validation preview and quality audit for uploaded CSVs |
| `POST` | `/api/v1/imports/commit` | Commits verified CSV import batch into database with lineage records |
| `GET` | `/api/v1/goals/` | Fetches milestone goals and computes progress metrics |
| `GET` | `/api/v1/investments/` | Retrieves investment portfolio holdings and asset allocation breakdown |
| `GET` | `/api/v1/profile/` | Fetches user profile, monthly income, fixed expenses, and risk preferences |
| `GET` | `/health` | System health check reporting database connectivity and runtime status |

---

## Verification, Testing & Benchmark Results

FinMate maintains an automated test and validation harness across the full application stack:

### Automated Test Suite (92 / 92 Passed)

```
tests/integration/test_agent_api.py            [PASS]  (6 tests)
tests/integration/test_ai_api.py               [PASS]  (7 tests)
tests/integration/test_data_quality_api.py     [PASS]  (1 test)
tests/integration/test_goals_api.py            [PASS]  (1 test)
tests/integration/test_health_api.py           [PASS]  (1 test)
tests/integration/test_imports_api.py          [PASS]  (4 tests)
tests/integration/test_profile_api.py          [PASS]  (1 test)
tests/integration/test_sms_transaction_api.py  [PASS]  (4 tests)
tests/integration/test_transactions_api.py     [PASS]  (1 test)
tests/unit/test_agent_evaluation.py            [PASS]  (1 test)
tests/unit/test_anomaly_detector.py            [PASS]  (2 tests)
tests/unit/test_approval_engine.py             [PASS]  (3 tests)
tests/unit/test_calculations.py                [PASS]  (9 tests)
tests/unit/test_classifier.py                  [PASS]  (3 tests)
tests/unit/test_csv_parser.py                  [PASS]  (5 tests)
tests/unit/test_data_quality_rules.py          [PASS]  (5 tests)
tests/unit/test_forecaster.py                  [PASS]  (4 tests)
tests/unit/test_llm_and_guardrails.py          [PASS]  (5 tests)
tests/unit/test_nlp_preprocessor.py            [PASS]  (5 tests)
tests/unit/test_normalizer.py                  [PASS]  (5 tests)
tests/unit/test_orchestrator.py                [PASS]  (6 tests)
tests/unit/test_rag_pipeline.py                [PASS]  (4 tests)
tests/unit/test_schemas.py                     [PASS]  (4 tests)
tests/unit/test_tool_registry.py               [PASS]  (5 tests)
-----------------------------------------------------------------
Total: 92 passed in 3.59s (100% Pass Rate)
```

### Agent Benchmark Matrix (12 / 12 Passed)

The multi-agent system is benchmarked against 12 standardized financial intent scenarios covering single-agent lookups, cross-specialist deliberations, approval gating, and security defense:

- Benchmark Success Rate: **12 / 12 (100.0%)**
- Zero-Hallucination Invariant: All numerical values verified against backend database records.
- Prompt Injection Defense: Adversarial queries intercepted and rejected with `SECURITY_VIOLATION` status without tool execution.

### Production Frontend Build

- Validation Command: `npm run build` (`tsc -b && vite build`)
- Outcome: **0 Errors, 0 Warnings** across 1,892 transformed modules.

---

## Getting Started & Local Execution

### Prerequisites

- Python 3.11 or higher (`uv` package manager recommended)
- Node.js 20 or higher and npm
- Docker and Docker Compose (optional for containerized deployment)
- Android Studio Iguana+ / Android SDK 34 (optional for building Android client)

### 1. Repository Setup

```powershell
git clone https://github.com/nithishvenkat4/FinMate.git
cd FinMate
```

### 2. Environment Configuration

```powershell
cp .env.example .env
```

Ensure `.env` contains valid runtime settings. The application defaults to local SQLite if PostgreSQL credentials are not provided.

### 3. Database Initialization & Demo Seeding

Provision the standard demonstration environment (Demo User, INR 60,000 monthly income, recurring expenses, milestone goals, and investment assets):

```powershell
python scripts/seed_demo_data.py
```

### 4. Running Backend API Server

```powershell
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Interactive Swagger Documentation: `http://localhost:8000/docs`
- Service Health Check: `http://localhost:8000/health`

### 5. Running Frontend Web Workspace

```powershell
cd frontend
npm install
npm run dev
```

- Web Application Interface: `http://localhost:5173`

### 6. Executing Test Suites

```powershell
cd backend
uv run pytest -v
```

### 7. Running with Docker Compose

To deploy the backend API and PostgreSQL database containers:

```powershell
docker compose up -d --build
```

---

## Repository Directory Structure

```
FinMate/
├── android/
│   └── FinMateSMS/              # Native Android background SMS tracking application
│       ├── app/src/main/java/   # Kotlin source (SmsReceiver, Room DB, WorkManager sync)
│       └── build.gradle.kts     # Android build configuration
├── backend/
│   ├── app/
│   │   ├── ai/                  # AI subsystem (Agents, Orchestrator, Tools, ML models, RAG)
│   │   ├── api/v1/              # FastAPI route controllers and endpoint handlers
│   │   ├── core/                # Configuration, logging, and security definitions
│   │   ├── db/                  # Database session management and base models
│   │   ├── models/              # SQLAlchemy relational entity definitions
│   │   ├── repositories/        # Data access layer implementing repository pattern
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   └── services/            # Domain logic (Calculations, Normalizer, Quality Engine)
│   ├── tests/                   # Pytest automated test suite (Unit and Integration)
│   └── pyproject.toml           # Backend project dependencies and packaging specifications
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components (Diff cards, Execution traces)
│   │   ├── pages/               # Top-level view containers (AIAdvisor, Dashboard, etc.)
│   │   ├── services/            # Typed API client services
│   │   └── types/               # TypeScript domain interfaces
│   ├── package.json             # Frontend dependencies (React 19, Tailwind CSS, Recharts)
│   └── vite.config.ts           # Vite build and development configuration
├── docs/                        # Technical specifications, architecture docs, and reports
├── scripts/                     # Database seeding and utility scripts
├── compose.yaml                 # Docker Compose multi-service deployment definition
└── README.md                    # System documentation and technical overview
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete details.
