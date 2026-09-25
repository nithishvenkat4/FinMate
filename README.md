# FinMate — Personal Financial Decision Agent

**FinMate** is an AI-powered personal financial decision-support system designed to help users track cash flows, organize transactions, monitor savings goals, and understand their financial profile while keeping the human firmly in control of every financial decision.

> [!IMPORTANT]
> FinMate is a **decision-support system**, never an autonomous financial actor. The system never executes trades, transfers, or unauthorized payments.

---

## Current Scope: Phase 2 Completed

- **Phase 0 (Foundation)**: FastAPI backend, React + Vite frontend, PostgreSQL/SQLite database layer, Docker Compose, testing framework.
- **Phase 1 (Domain Model & Data Layer)**: User, Financial Profile, Category, Transaction, Goal, Investment entities with exact `Decimal` / `NUMERIC(15, 2)` monetary representation and database check constraints.
- **Phase 2 (Data Engineering & Data Quality)**:
  - Multi-stage Ingestion Pipeline: `CSVParser` with encoding and delimiter auto-sensing.
  - Deterministic Normalizer (`DataNormalizer`).
  - 11-Rule Data Quality Engine (`DataQualityEngine`) with `ERROR`, `WARNING`, `INFO` severities.
  - Duplicate Detection Heuristic (`user_id + date + amount + description`) with human-in-the-loop review flags.
  - Data Lineage Tracking (`source_type`, `source_reference`, `import_id`, `data_quality_flags`).
  - Batch Import Audit Log (`import_records`).
  - Full React UI with live Dashboard, CSV Ingestion with row-by-row pre-validation preview, Transactions Ledger, Goals, Investments, Profile, and Settings.

---

## Quick Start & Local Execution

### Prerequisites
- Python 3.11+ (with `uv` recommended)
- Node.js 20+ and npm
- Docker & Docker Compose (optional for containerized deployment)

### 1. Seed Synthetic Financial Demo Data
To provision the canonical demo dataset (Demo User, ₹60,000 salary, Swiggy, Amazon, Uber, Netflix, Electricity, Higher Education goal, Tata Silver ETF):

```powershell
python scripts/seed_demo_data.py
```

### 2. Run Backend API Server
```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 3. Run Frontend Web Application
```powershell
cd frontend
npm run dev
```
- Web Application: `http://localhost:5173`

### 4. Run Automated Test Suite
```powershell
cd backend
uv run pytest -v
```
All 37 unit and integration tests covering financial calculations, CSV parsing, data quality rules, and API endpoints will execute.

### 5. Run via Docker Compose
```powershell
docker compose up -d --build
```

---

## Architecture & Data Flow

```
                      USER
                        │
                        ▼
               ┌────────────────┐
               │    FRONTEND    │
               │ (React + Vite) │
               └────────┬───────┘
                        │ HTTP / JSON
                        ▼
               ┌────────────────┐
               │ FASTAPI ROUTER │
               └────────┬───────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
┌───────────────────┐        ┌───────────────────┐
│  INGESTION PIPELINE│        │  DOMAIN SERVICES  │
│  - CSVParser      │        │  - Calculations   │
│  - DataNormalizer │        │  - Transactions   │
│  - QualityEngine  │        │  - Goals/Profile  │
└────────┬──────────┘        └─────────┬─────────┘
         │                             │
         └──────────────┬──────────────┘
                        ▼
               ┌────────────────┐
               │  REPOSITORIES  │
               └────────┬───────┘
                        ▼
               ┌────────────────┐
               │   POSTGRESQL   │
               └────────────────┘
```

---

## Project Roadmap

- [x] **Phase 0**: Project Foundation & Tooling
- [x] **Phase 1**: Financial Domain Model & Data Layer
- [x] **Phase 2**: Data Engineering & Data Quality
- [x] **Phase 3**: AI Models & Intelligence (ML, NLP, RAG, LLM Abstraction)
- [x] **Phase 4**: Agentic Intelligence & Multi-Agent Collaboration
  - Specialized Financial Agents (Transaction, Budget, Goal, Investment, Decision Agent)
  - AI Orchestrator with Deterministic Intent Triage & Route Selection
  - Formal Tool Registry with Least-Privilege Allowlists & Ownership Enforcement
  - Human-in-the-Loop Approval Engine with 15-minute Expiration & Verified Mutation
  - Isolated In-Memory What-If Simulation Sandbox
  - Real Execution Trace Stepper with Zero-Fake AI Guarantee
  - 88/88 Automated Tests & 12/12 Benchmark Tasks Passing (100%)
- [x] **SMS Transaction Tracking Integration**:
  - Native Android application (`android/FinMateSMS`)
  - Local deterministic SMS parsing (Amount, Date, Credit/Debit)
  - Offline Room database queue & automatic background synchronization via WorkManager
  - FastAPI dedicated ingestion endpoint (`POST /api/v1/transactions/from-sms`)
  - Dual-layer duplicate protection (local DB hash + server hash deduplication)
  - See [SMS Ingestion Guide](docs/SMS_INGESTION.md) for architecture and build details.
- [ ] **Phase 5**: Production Readiness & Deployment Engineering
- [ ] **Phase 6**: Continuous Learning & Decision Feedback
