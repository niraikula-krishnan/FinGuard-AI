# FinGuard-AI

**Loan risk assessment and AML compliance auditor** — a full-stack fintech app that scores credit risk, runs compliance checks, screens application notes for AML red flags, and generates detailed audit reports.

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
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| AI (optional) | Google Gemini 1.5 Flash |
| Icons | Lucide |

---

## How It Works

```
Applicant Form → FastAPI → Risk Model + Compliance Checks → Audit Report → MySQL
                                    ↓
                          Gemini API (if key set)
                                    ↓
                          Rule-based engine (fallback)
```

**DTI formula:** `(existing monthly debt + new loan EMI) ÷ monthly income × 100`

**Audit reports:**
- **AI report** — when `GEMINI_API_KEY` is set and the API call succeeds
- **Rule-based report** — when no API key is configured or the AI call fails

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
git clone https://github.com/YOUR_USERNAME/FinGuard-AI.git
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

## Security Notes

- Never commit `.env` — it contains database passwords and API keys
- Only commit `.env.example` with placeholder values
- Rotate any credentials that were ever exposed in documentation or chat

---

## License

MIT License — free to use for learning and portfolio purposes.
