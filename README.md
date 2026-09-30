# Personal Finance Advisor Bot 💰🤖

An AI-powered personal financial planning assistant designed to help individuals take control of their finances with clarity and confidence. The platform integrates real-time income and expense tracking, category envelope budgeting (50/30/20 rule), goal-based savings, natural language transaction logging, a "Can I Afford This?" purchase simulator, and deep spending diagnostics powered by Gemini 3.8 Flash.

---

## 🌟 Key Features

- **Executive Financial Dashboard**: Real-time tracking of monthly income inflow, expense outflow, net cash flow surplus/deficit, and savings rate.
- **Financial Health Score (0–100)**: Autonomous diagnostic rating assessing savings rate, emergency reserve adequacy, budget variance, and discretionary discipline.
- **Dynamic 50/30/20 Budget Envelopes**: Automated comparison between actual spending in Needs (Essentials), Wants (Lifestyle), and Savings vs. persona benchmarks, with an AI auto-balancer.
- **AI Natural Language Quick-Log**: Type entries like *"Dinner with team at Chipotle $32.50 yesterday"* or *"Bought textbooks $79.99"* — the AI automatically extracts the description, amount, category, and date.
- **Overspending Alert System**: Highlights categories exceeding limits with actionable reduction advice.
- **Goal-Based Savings Tracker**: Visual milestone meters, target completion dates, and monthly required pace calculators for emergency funds, vacations, tech upgrades, and debt payoffs.
- **Interactive AI Advisor Bot**: Chat directly with a context-aware financial advisor grounded in your exact live balances and category budgets.
- **"Can I Afford This?" Purchase Simulator**: Stress-tests potential purchases before you buy, returning a verdict (**SAFE**, **CAUTION**, or **NOT RECOMMENDED**) with cash flow impact.
- **Exportable & Printable Monthly Statement**: One-click printable financial summary and CSV export.
- **Pre-configured Scenario Switcher**:
  1. **Salaried Professional (Alex Bennett, $5,400/mo)**: Corporate salary, rent, dining creep, and emergency buffer.
  2. **College Student (Maya Patel, $1,250/mo)**: Strict family allowance & work-study job, textbooks, and low-cost emergency reserve.
  3. **Freelancer / Consultant (Sam Chen, $4,300/mo)**: Variable client retainers, quarterly tax withholding, and equipment upgrades.

---

## 🛠️ Project Editions & Tech Stacks

This repository contains two complete implementations of the Personal Finance Advisor Bot:

### 1. Interactive React + TypeScript + Express (Root)
- **Frontend**: React 19, TypeScript, Tailwind CSS, Lucide React, Motion
- **Server**: Express, Node.js, TSX, Vite
- **AI Integration**: `@google/genai` (Gemini Flash) with client/server fallbacks

### 2. Full-Stack Python Flask + SQLAlchemy + Jinja2 (`/flask_app`)
- **Backend & Web Framework**: Python 3, Flask, Jinja2 Templates
- **ORM & Database**: SQLAlchemy, SQLite (or PostgreSQL)
- **Authentication**: Flask-Login, Werkzeug password hashing
- **Deployment**: Ngrok for public tunneling, Gunicorn

---

## 🚀 Getting Started

### Option A: Running the React + Express Application
```bash
# Install dependencies
npm install

# Setup environment variables
cp .env.example .env

# Run development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000)

### Option B: Running the Python Flask + SQLAlchemy Application
```bash
cd flask_app

# Create virtual environment & install requirements
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run the Flask app
python app.py
```
Open [http://localhost:5000](http://localhost:5000)

### Deploying Publicly with Ngrok
```bash
cd flask_app
python run_ngrok.py
```
This generates a secure public HTTPS URL to test and demonstrate the app externally.

### 6. Build for Production
```bash
npm run build
npm start
```

---

## 📄 License
Apache-2.0
