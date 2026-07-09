---
title: FinGuard-AI
emoji: 🛡️
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# FinGuard-AI

**Loan risk assessment and AML compliance auditor** — a full-stack fintech app that scores credit risk, runs compliance checks, screens application notes for AML red flags, and generates detailed audit reports.

**Live demo:** [huggingface.co/spaces/niraikula-krishnan/FinGuard-AI](https://huggingface.co/spaces/niraikula-krishnan/FinGuard-AI)  
**GitHub:** [github.com/niraikula-krishnan/FinGuard-AI](https://github.com/niraikula-krishnan/FinGuard-AI)

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange)

---

## Features

- **Credit risk scoring** — Multi-factor model (credit score, DTI, LTI, employment) with grades A–D
- **Auto-calculated DTI** — Computed from income, existing monthly debt, and new loan EMI
- **Compliance checks** — Rule-based audits for DTI limits, LTI thresholds, and credit score floors
- **AML note screening** — Flags suspicious keywords in self-reported application notes
- **Audit reports** — AI-generated via Gemini when configured, with a **rule-based fallback** when not
- **Application ledger** — Search, filter, inspect, and delete loan records
- **Interactive dashboard** — Risk gauge, compliance checklist, and formatted audit reports

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI, Uvicorn |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript |
| AI (optional) | Google Gemini 1.5 Flash |
| Icons | Lucide |

---

## Workflow

### User workflow (dashboard)

1. **Open the dashboard** at `http://localhost:8080`
2. **Fill in the loan application form**
   - Applicant name, annual income, loan amount, tenure
   - Existing monthly debt (EMI and DTI are calculated automatically)
   - Credit score and employment status
   - Optional application notes (screened for AML keywords)
3. **Click "Calculate & Audit Risk"**
4. **Review results** in the application ledger
   - Risk score, DTI, and compliance status (PASSED / FLAGGED)
5. **Inspect an applicant** (eye icon) to open the audit dossier
   - Risk gauge and grade (A–D)
   - Compliance checklist
   - Full audit report (AI or rule-based)
6. **Search or filter** applicants by name or compliance status
7. **Delete** records when no longer needed

---

### Application processing pipeline

When a loan application is submitted, the backend runs this sequence:

```
┌─────────────────┐
│  User submits   │
│  form (UI)      │
└────────┬────────┘
         │  POST /api/applicants
         ▼
┌─────────────────┐
│  1. Calculate   │  EMI from loan amount + tenure (10.5% rate)
│     DTI         │  DTI = (existing debt + EMI) / monthly income
└────────┬────────┘
         ▼
┌─────────────────┐
│  2. Credit risk │  Weighted score from credit score, DTI, LTI,
│     scoring     │  and employment status → grade A–D
└────────┬────────┘
         ▼
┌─────────────────┐
│  3. Compliance  │  DTI ≤ 45%, LTI ≤ 8× income, credit ≥ 550
│     checks      │
└────────┬────────┘
         ▼
┌─────────────────┐
│  4. Audit       │  Gemini AI (if API key set)
│     report      │  ──or── rule-based engine (fallback)
└────────┬────────┘
         ▼
┌─────────────────┐
│  5. Save to     │  Single row in MySQL `loananalysis` table
│     MySQL       │  (scores, logs, report, audit mode)
└────────┬────────┘
         ▼
┌─────────────────┐
│  6. Return      │  Risk score, grade, DTI, compliance status
│     response    │  UI refreshes ledger and opens audit view
└─────────────────┘
```

| Step | Module | Output |
|------|--------|--------|
| DTI calculation | `risk_service.py` | Debt-to-income ratio (%) |
| Risk scoring | `risk_service.py` | Risk score 0–100, grade A–D |
| Compliance checks | `risk_service.py` | Checklist with PASSED / FLAGGED per rule |
| Audit report | `risk_service.py` | Markdown report + `ai` or `rule_based` mode |
| Persistence | `database.py` | Record saved to `loananalysis` table |
| API | `main.py` | JSON response to frontend |

---

### Audit report modes

| Mode | When | Label in UI |
|------|------|-------------|
| **AI report** | `GEMINI_API_KEY` is set and the API call succeeds | AI Report |
| **Rule-based report** | No API key, or AI call fails | Rule-based Report |

Risk scoring and compliance checks **always** run locally. Only the written audit report uses AI when available.

**DTI formula:** `(existing monthly debt + new loan EMI) ÷ monthly income × 100`

---

## Project Structure

```
FinGuard-AI/
├── main.py              # FastAPI server and API routes
├── database.py          # MySQL connection and CRUD operations
├── risk_service.py      # Risk model, compliance checks, audit report engine
├── run.py               # One-click setup and server launcher
├── test_app.py          # API integration tests
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template (safe to commit)
├── .env                 # Your local secrets (never commit)
└── static/
    ├── index.html       # Dashboard UI
    ├── style.css        # Styling
    └── app.js           # Frontend logic
```

---

## Prerequisites

- **Python 3.10+**
- **MySQL 8.0+** running locally (or remote)
- **(Optional)** Gemini API key for AI audit reports

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/niraikula-krishnan/FinGuard-AI.git
cd FinGuard-AI
```

### 2. Configure environment variables

**Windows:**
```bash
copy .env.example .env
```

**macOS / Linux:**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
GEMINI_API_KEY=your_gemini_api_key_here
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password_here
MYSQL_DATABASE=loan
```

> The app works **without** a Gemini API key. It will use the built-in rule-based report generator instead.

> **Local dev:** set `MYSQL_HOST` in `.env` for MySQL. **Hugging Face demo:** leave `MYSQL_HOST` unset — data is stored in memory for the session (same pattern as SkinGPT).

### 3. Start the server

```bash
python run.py
```

This will create a virtual environment, install dependencies, and start the server on port **8080**.

### 4. Open the dashboard

Visit **[http://localhost:8080](http://localhost:8080)**

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/applicants` | List all applications |
| `GET` | `/api/applicants/{id}` | Get full details and audit report |
| `POST` | `/api/applicants` | Submit a new application |
| `DELETE` | `/api/applicants/{id}` | Delete an application |
| `GET` | `/docs` | Interactive API documentation (Swagger) |

### Example POST body

```json
{
  "name": "Jane Doe",
  "income": 800000,
  "loan_amount": 200000,
  "credit_score": 720,
  "existing_monthly_debt": 5000,
  "employment_status": "Employed",
  "notes": "Home renovation loan. No offshore assets.",
  "tenure": 5
}
```

---

## Running Tests

Start the server first, then in a separate terminal:

```bash
python test_app.py
```

---

## Resume Bullet Points

- Designed and built **FinGuard-AI**, a full-stack loan risk and AML compliance system evaluating applicant default probability
- Formulated a multi-factor risk model integrating credit score, debt-to-income (DTI), and loan-to-income (LTI) ratios with graded risk output (A–D)
- Developed a compliance auditor with Gemini AI integration and rule-based fallback for unstructured note analysis and AML flagging
- Configured a MySQL database with JSON-serialized compliance logs and markdown audit report storage
- Built a responsive dashboard with real-time DTI calculation, SVG risk gauges, and dynamic audit report rendering

---

## Deploy live (free)

### Option A: Render — **recommended** (full FastAPI app)

Best for the **complete app** (form, API, risk engine, audit reports).

1. Push code to GitHub: `github.com/niraikula-krishnan/FinGuard-AI`
2. Go to [render.com](https://render.com) → **New → Blueprint** (or Web Service)
3. Connect your **FinGuard-AI** repo — Render reads `render.yaml` automatically
4. **Environment variables** (Render dashboard → Environment):
   - `GEMINI_API_KEY` — optional, for AI audit reports
   - **Do not** set `MYSQL_HOST` on free tier — app uses in-memory storage (demo mode)
5. Click **Deploy** — live URL in ~5 minutes: `https://finguard-ai.onrender.com` (name may vary)

| Render free tier | Note |
|----------------|------|
| Cost | $0 |
| Sleep | App sleeps after ~15 min idle; first load may take 30–60 sec |
| Database | In-memory demo (MySQL code still on GitHub for reviewers) |

---

### Option B: Netlify (static demo only)

Netlify hosts **static sites only** — not FastAPI. Use the `hf_deploy/` browser demo.

1. Go to [netlify.com](https://netlify.com) → **Add new site → Import from Git**
2. Select **FinGuard-AI** repo
3. Build settings (auto-read from `netlify.toml`):
   - **Publish directory:** `hf_deploy`
   - **Build command:** (leave empty)
4. Deploy → live URL like `https://finguard-ai.netlify.app`

| Netlify | What you get |
|---------|----------------|
| Full FastAPI backend | No |
| Working UI demo in browser | Yes |
| Free forever | Yes |

---

### Option C: Hugging Face (optional)

See `hf_deploy/` + `deploy_hf.ps1` for a free static Space. Docker Spaces on HF require Pro.

---

## Deploy comparison

| Platform | Full app | Free | Best for |
|----------|----------|------|----------|
| **Render** | Yes | Yes (sleeps) | Resume live link with real API |
| **Netlify** | Demo only | Yes | Quick static UI demo |
| **HF Static** | Demo only | Yes | If you already use HF |
| **Local + MySQL** | Yes | Yes | Development & showing DB skills |

---

## Security Notes

- Never commit `.env` — it contains database passwords and API keys
- Only commit `.env.example` with placeholder values
- Rotate any credentials that were ever exposed in documentation or chat

---

## License

MIT License — free to use for learning and portfolio purposes.
