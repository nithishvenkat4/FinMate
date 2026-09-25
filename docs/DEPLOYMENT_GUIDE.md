# FinMate — Web Application Deployment & Pitch Presentation Guide

This guide provides instructions for deploying the FinMate unified web application to the cloud and running a live pitch demonstration.

---

## 1. Cloud Deployment Options

FinMate is configured as a single unified service: FastAPI serves the compiled React 19 single-page application, handles REST API endpoints, and provisions the pre-seeded SQLite financial dataset on container startup.

---

### Option A: Render (Recommended — 100% Free, Permanent HTTPS URL)

Render provides free hosting for containerized web applications.

#### Steps:
1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Configure unified production deployment"
   git push origin main
   ```
2. **Open Render Dashboard**:
   - Go to [render.com](https://dashboard.render.com/) and sign in with GitHub.
3. **Create Web Service**:
   - Click **New +** -> **Web Service**.
   - Select your `FinMate` repository.
4. **Configuration Settings**:
   - **Name**: `finmate-web` (or any custom name)
   - **Region**: Oregon (US West) or Singapore / Frankfurt
   - **Language / Runtime**: **Docker**
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Context**: `.`
   - **Instance Type**: **Free**
5. **Environment Variables**:
   Under the "Environment Variables" section, add:
   - `APP_ENV` = `production`
   - `LOG_LEVEL` = `INFO`
   - `PORT` = `8000` *(Render sets $PORT dynamically; our Dockerfile binds automatically)*
6. **Click "Deploy Web Service"**:
   - Render will build the React frontend and Python backend in ~3 minutes.
   - Once complete, you will receive a public HTTPS URL (e.g., `https://finmate-web.onrender.com`).

---

### Option B: Railway (Fastest Cloud Setup — ~2 Minutes)

#### Steps:
1. Go to [railway.app](https://railway.app/) and sign in with GitHub.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select `FinMate`. Railway automatically detects `railway.json` and `Dockerfile`.
4. Click on the deployed service card -> **Settings** -> **Networking** -> **Generate Domain**.
5. Your service will be accessible immediately via `https://finmate-production.up.railway.app`.

---

### Option C: Instant Live Tunnel (Zero Signup — Live in 30 Seconds)

If your pitch is starting immediately and you want to share a live public link without waiting for cloud builds:

1. **Start the unified FinMate server locally**:
   ```powershell
   cd d:\FinMate\backend
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. **Expose via Cloudflare Tunnel or Localtunnel**:
   - In a second terminal, run:
     ```powershell
     npx localtunnel --port 8000
     ```
     *or with Cloudflare Tunnel (if installed):*
     ```powershell
     cloudflared tunnel --url http://localhost:8000
     ```
3. Copy the generated `https://...` URL and send it to your pitch evaluators.

---

## 2. Pre-Seeded Pitch Demo Data

The application automatically seeds canonical demonstration data upon startup:
- **Demo User**: `demo@finmate.local`
- **Monthly Income**: INR 60,000.00
- **Fixed Monthly Expenses**: INR 15,000.00
- **Liquid Savings / Contingency**: INR 1,20,000.00
- **Pre-loaded Transactions**: Swiggy (Food), Amazon (Shopping), Uber (Transportation), Netflix (Entertainment), Electricity Bill (Utilities).
- **Active Goal**: Higher Education Fund (Target: INR 3,00,000.00 | Saved: INR 1,20,000.00 | Target Date: 12 months).
- **Active Investment**: Tata Silver ETF (Holdings: 150 units).

---

## 3. High-Impact Pitch Demonstration Flow (2-Minute Script)

When demonstrating the prototype during your pitch, follow this structured walkthrough:

### Step 1: Real-Time Financial Ledger & Dashboard
- Navigate to the **Dashboard** view (`/`).
- Show the visual metrics: net monthly surplus (INR 25,000), savings rate (41.67%), categorized expense donut chart, and investment allocation.
- Point out the **Data Quality indicators** and deterministic decimal precision (zero floating-point errors).

### Step 2: Multi-Agent AI Advisor & Complex Decision Synthesis
- Navigate to the **AI Advisor** view (`/ai-advisor`).
- Under Demo Scenarios, select or type:
  > *"Can I afford a INR 20,000 laptop next month without hurting my education goal?"*
- Click **Analyze Scenario**.

### Step 3: Show the Authentic Live Execution Trace
- Expand the **Execution Trace Stepper** card:
  - Show how the **AI Orchestrator** triages the intent.
  - Show the **Budget Agent** fetching real surplus from the ledger.
  - Show the **Goal Agent** calculating the exact INR 16,363.64/month run-rate for the education goal.
  - Show the **Regulatory RAG** retrieving RBI emergency reserve directives.
  - Highlight the sub-second execution latency and zero-hallucinated execution guarantee.

### Step 4: Explainable Decision Options
- Show the synthesized response:
  - **Option A**: Outright purchase next month (utilizes 80% of surplus for 1 month, keeps contingency fund intact).
  - **Option B**: Split outlay across 2 months at INR 10,000/month.
  - **Option C**: Sinking fund deferral for 60 days.

### Step 5: Human-in-the-Loop (HITL) Governance Demonstration
- In the AI Advisor input box, type:
  > *"Change the Amazon transaction category to Shopping"*
- Highlight that the system **does not silently overwrite financial records**.
- Point out the **Interactive Approval Card** displaying:
  - Proposed state mutation diff (Current Category vs Proposed Category).
  - 15-minute expiration countdown timer.
  - **Approve** and **Reject** buttons.
- Click **Approve** and navigate to the Transactions page to show the verified update in the database.

### Step 6: What-If Counterfactual Sandbox
- In the What-If Sandbox panel, model reducing discretionary spending by INR 2,000.
- Show the projected bump in savings rate from 41.67% to 45.00% without modifying any persistent records.
