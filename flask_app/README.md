# Personal Finance Advisor Bot (Flask + SQLAlchemy + Jinja2 + Gemini AI)

An AI-powered personal financial planning platform built with **Flask**, **SQLAlchemy**, **SQLite/PostgreSQL**, **Jinja2**, and **Gemini AI**, deployed with **Ngrok** for public accessibility.

---

## 🏛️ Architecture Overview

```
flask_app/
├── app.py                 # Main Flask application, routes, authentication, ledger & API handlers
├── models.py              # SQLAlchemy database models (User, Income, Expense, Category, Goal, Report)
├── ai_advisor.py          # Gemini AI integration, spending diagnostics, chat bot & simulator
├── run_ngrok.py           # Deployment script launching Flask + PyNgrok public tunnel
├── requirements.txt       # Python package dependencies
├── .env.example           # Environment variables configuration template
└── templates/             # Jinja2 responsive templates with Tailwind CSS & FontAwesome
    ├── base.html          # Base layout, navbar, session badges, flash messages & footer
    ├── index.html         # Landing page and feature overview
    ├── login.html         # User sign-in interface
    ├── register.html      # User profile registration & envelope initialization
    ├── dashboard.html     # Executive financial command center (KPIs, health score, 50/30/20)
    ├── expenses.html      # Income & expense ledger with AI natural language quick-log
    ├── budget.html        # 50/30/20 category envelope management
    ├── advisor.html       # Context-aware AI Advisor chatbot interface
    ├── simulator.html     # "Can I Afford This?" purchase simulator
    └── report.html        # Printable monthly statement & CSV export
```

---

## 📋 Features Aligned with Specification

### 1. Environment Setup & AI Configuration
- Modular Flask architecture with `.env` secret management.
- Configurable database connection (SQLite by default, easily swapped to PostgreSQL).
- Gemini 2.5 Flash SDK integration with robust fallback analytics.

### 2. User Authentication & Profile Management
- Secure password hashing via `werkzeug.security` (PBKDF2/SHA256).
- Protected routes using `flask_login.login_required`.
- User profiles with currency preferences ($, €, £, ₹, C$) and financial personas (*Salaried Pro*, *College Student*, *Freelancer*).
- Auto-initialization of starter envelopes and categories upon registration.

### 3. Financial Tracking & Budget Management
- **Inflow Management**: Recurring salary, freelance, investments with frequency tracking.
- **Outflow Tracking**: Date, merchant, category, notes, and instant delete capability.
- **Natural Language Expense Parser**: Type *"Dinner at Chipotle $32.50"* — AI extracts the title, category, and amount into the form.

### 4. AI-Powered Budget & Advisory Engine
- **Health Score (0–100)**: Assesses savings rate, discretionary discipline, and budget adherence.
- **Overspending Detection**: Highlights categories exceeding limits and suggests mitigation.
- **Interactive Advisor Chatbot**: Chat grounded in live income and balances.
- **"Can I Afford This?" Purchase Simulator**: Stress-tests potential purchases against monthly surplus.

### 5. Dashboard & Financial Reporting
- Real-time KPI cards: Gross Inflow, Total Outflow, Net Cash Flow, Savings Rate.
- Visual 50/30/20 allocation bars (Needs, Wants, Savings).
- Goal progress meters with inline deposit forms.
- Printable monthly financial summary statement and CSV export.

---

## 🚀 Step-by-Step Setup & Execution

### 1. Create and Activate Virtual Environment
```bash
cd flask_app
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the template and supply your keys:
```bash
cp .env.example .env
```
Inside `.env`:
```env
SECRET_KEY="your-random-secret-key"
FLASK_PORT=5000
DATABASE_URL="sqlite:///finance_advisor.db"
GEMINI_API_KEY="your-gemini-api-key"
NGROK_AUTHTOKEN="your-ngrok-token-optional"
```

### 4. Run Locally
```bash
python app.py
```
Open **http://localhost:5000** in your browser.

---

## 🌐 Public Deployment with Ngrok (Section 8)

To generate a secure public HTTPS URL for external demonstrations:

1. Obtain a free auth token from [ngrok.com](https://ngrok.com).
2. Set `NGROK_AUTHTOKEN="your_token"` in `.env`.
3. Launch via the ngrok runner:
```bash
python run_ngrok.py
```
The script outputs:
```
============================================================
🚀 Personal Finance Advisor Bot is publicly accessible at:
   👉 https://xxxx-xx-xx-xx.ngrok-free.app
============================================================
```
You can share this URL with anyone to test the application live.

---

## 🧪 Testing & Validation Guide (Section 9)

1. **Authentication Testing**: Register a new user, log out, log in with bad password (check error flash), log in with valid credentials.
2. **Transaction Logging**: Use the AI natural language bar in `/expenses` to auto-fill an expense like *"Trader Joe's groceries $65.40"*, submit it, and verify the ledger.
3. **Budget Envelope Testing**: In `/budget`, adjust limits and verify that the dashboard calculates overspending variances accurately.
4. **AI Advisor Validation**: Open `/advisor`, ask *"Audit my spending leaks"*, and verify the bot returns personalized advice referencing your actual numbers.
5. **Simulator Validation**: In `/simulator`, test a $500 item when your surplus is $200 — verify it returns **NOT RECOMMENDED** with cash flow impact.
6. **Reporting**: Navigate to `/report`, click **Print Statement**, and verify the clean printable layout.
