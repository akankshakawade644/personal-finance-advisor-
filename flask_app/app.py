import os
import datetime
import csv
from io import StringIO
from flask import (
    Flask, render_template, redirect, url_for, request,
    flash, jsonify, session, Response
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from dotenv import load_dotenv

from models import db, User, Income, ExpenseCategory, Expense, SavingsGoal, MonthlyReport
from ai_advisor import (
    analyze_spending_and_health, chat_with_advisor,
    simulate_purchase, parse_natural_language_expense
)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-finance-advisor-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///finance_advisor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Default category template for new users
DEFAULT_CATEGORIES = [
    {"name": "Housing & Rent", "budget": 1600.0, "type": "Needs", "color": "#2563eb", "icon": "home"},
    {"name": "Groceries", "budget": 450.0, "type": "Needs", "color": "#059669", "icon": "shopping-cart"},
    {"name": "Utilities & Wifi", "budget": 220.0, "type": "Needs", "color": "#0284c7", "icon": "zap"},
    {"name": "Transportation", "budget": 300.0, "type": "Needs", "color": "#d97706", "icon": "car"},
    {"name": "Food & Dining Out", "budget": 350.0, "type": "Wants", "color": "#ea580c", "icon": "coffee"},
    {"name": "Entertainment", "budget": 180.0, "type": "Wants", "color": "#8b5cf6", "icon": "film"},
    {"name": "Shopping & Lifestyle", "budget": 200.0, "type": "Wants", "color": "#ec4899", "icon": "gift"},
    {"name": "Subscriptions", "budget": 60.0, "type": "Wants", "color": "#6366f1", "icon": "repeat"},
    {"name": "Emergency Savings", "budget": 500.0, "type": "Savings", "color": "#10b981", "icon": "shield"},
]

def seed_default_user_data(user):
    for cat_data in DEFAULT_CATEGORIES:
        category = ExpenseCategory(
            user_id=user.id,
            name=cat_data["name"],
            budget_limit=cat_data["budget"],
            envelope_type=cat_data["type"],
            color=cat_data["color"],
            icon=cat_data["icon"]
        )
        db.session.add(category)
    
    # Add initial income
    primary_income = Income(
        user_id=user.id,
        source="Primary Monthly Salary",
        amount=5200.0,
        date=datetime.date.today(),
        frequency="Monthly"
    )
    db.session.add(primary_income)

    # Add default emergency goal
    emergency_goal = SavingsGoal(
        user_id=user.id,
        title="3-Month Emergency Reserve",
        target_amount=10000.0,
        current_amount=3500.0,
        target_date=datetime.date.today() + datetime.timedelta(days=180),
        category="Emergency Fund"
    )
    db.session.add(emergency_goal)
    db.session.commit()

def get_user_snapshot(user):
    """Calculates all key metrics for the current user."""
    incomes = Income.query.filter_by(user_id=user.id).all()
    expenses = Expense.query.filter_by(user_id=user.id).all()
    categories = ExpenseCategory.query.filter_by(user_id=user.id).all()
    goals = SavingsGoal.query.filter_by(user_id=user.id).all()

    total_income = sum(i.amount for i in incomes)
    total_expenses = sum(e.amount for e in expenses)
    net_cash_flow = total_income - total_expenses
    savings_rate = (net_cash_flow / total_income * 100) if total_income > 0 else 0.0

    category_totals = {}
    for exp in expenses:
        cat_name = exp.category.name if exp.category else "Uncategorized"
        category_totals[cat_name] = category_totals.get(cat_name, 0.0) + exp.amount

    overspent_categories = []
    for cat in categories:
        spent = category_totals.get(cat.name, 0.0)
        if cat.budget_limit > 0 and spent > cat.budget_limit:
            overspent_categories.append({
                "name": cat.name,
                "spent": spent,
                "budget": cat.budget_limit,
                "variance": spent - cat.budget_limit
            })

    return {
        "persona": user.persona,
        "currency": user.currency,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "savings_rate": savings_rate,
        "category_totals": category_totals,
        "overspent_categories": overspent_categories,
        "categories": categories,
        "incomes": incomes,
        "expenses": expenses,
        "goals": goals
    }

# ----------------- Authentication Routes -----------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        currency = request.form.get('currency', '$')
        persona = request.form.get('persona', 'Salaried Professional')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'warning')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email is already registered.', 'warning')
            return render_template('register.html')

        user = User(username=username, email=email, currency=currency, persona=persona)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Seed categories and starter numbers
        seed_default_user_data(user)
        login_user(user)
        flash('Registration successful! Welcome to your Financial Advisor.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter((User.username == username) | (User.email == username.lower())).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# ----------------- Dashboard & Analytics -----------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    snapshot = get_user_snapshot(current_user)
    ai_analysis = analyze_spending_and_health(snapshot)
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc(), Expense.id.desc()).limit(8).all()
    
    return render_template(
        'dashboard.html',
        snapshot=snapshot,
        analysis=ai_analysis,
        recent_expenses=recent_expenses
    )

# ----------------- Income & Expense Management -----------------

@app.route('/expenses', methods=['GET'])
@login_required
def expenses_view():
    snapshot = get_user_snapshot(current_user)
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    categories = ExpenseCategory.query.filter_by(user_id=current_user.id).all()
    
    return render_template(
        'expenses.html',
        snapshot=snapshot,
        expenses=expenses,
        incomes=incomes,
        categories=categories
    )

@app.route('/expense/add', methods=['POST'])
@login_required
def add_expense():
    title = request.form.get('title', '').strip()
    amount = float(request.form.get('amount', 0))
    category_id = request.form.get('category_id')
    date_str = request.form.get('date', '')
    notes = request.form.get('notes', '')

    try:
        exp_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.date.today()
    except ValueError:
        exp_date = datetime.date.today()

    if title and amount > 0:
        expense = Expense(
            user_id=current_user.id,
            category_id=int(category_id) if category_id else None,
            title=title,
            amount=amount,
            date=exp_date,
            notes=notes
        )
        db.session.add(expense)
        db.session.commit()
        flash(f'Expense "{title}" of {current_user.currency}{amount:.2f} logged.', 'success')
    else:
        flash('Please provide a valid title and amount.', 'danger')

    return redirect(url_for('expenses_view'))

@app.route('/expense/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash('Expense removed.', 'info')
    return redirect(url_for('expenses_view'))

@app.route('/income/add', methods=['POST'])
@login_required
def add_income():
    source = request.form.get('source', '').strip()
    amount = float(request.form.get('amount', 0))
    frequency = request.form.get('frequency', 'Monthly')

    if source and amount > 0:
        income = Income(
            user_id=current_user.id,
            source=source,
            amount=amount,
            frequency=frequency,
            date=datetime.date.today()
        )
        db.session.add(income)
        db.session.commit()
        flash(f'Income source "{source}" added.', 'success')
    else:
        flash('Please provide a valid source name and amount.', 'danger')

    return redirect(url_for('expenses_view'))

@app.route('/income/delete/<int:income_id>', methods=['POST'])
@login_required
def delete_income(income_id):
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    db.session.delete(income)
    db.session.commit()
    flash('Income source deleted.', 'info')
    return redirect(url_for('expenses_view'))

# ----------------- Budget Planning & Envelopes -----------------

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget_view():
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('budget_limit_'):
                cat_id = int(key.replace('budget_limit_', ''))
                cat = ExpenseCategory.query.filter_by(id=cat_id, user_id=current_user.id).first()
                if cat:
                    cat.budget_limit = max(0.0, float(value or 0))
        db.session.commit()
        flash('Budget envelopes updated successfully.', 'success')
        return redirect(url_for('budget_view'))

    snapshot = get_user_snapshot(current_user)
    return render_template('budget.html', snapshot=snapshot)

# ----------------- Savings Goals -----------------

@app.route('/goals/add', methods=['POST'])
@login_required
def add_goal():
    title = request.form.get('title', '').strip()
    target_amount = float(request.form.get('target_amount', 0))
    current_amount = float(request.form.get('current_amount', 0))
    category = request.form.get('category', 'Emergency Fund')

    if title and target_amount > 0:
        goal = SavingsGoal(
            user_id=current_user.id,
            title=title,
            target_amount=target_amount,
            current_amount=current_amount,
            category=category,
            target_date=datetime.date.today() + datetime.timedelta(days=180)
        )
        db.session.add(goal)
        db.session.commit()
        flash(f'Savings goal "{title}" established.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/goals/deposit/<int:goal_id>', methods=['POST'])
@login_required
def deposit_goal(goal_id):
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    deposit = float(request.form.get('deposit_amount', 0))
    if deposit > 0:
        goal.current_amount += deposit
        db.session.commit()
        flash(f'Added {current_user.currency}{deposit:.2f} toward "{goal.title}".', 'success')
    return redirect(url_for('dashboard'))

# ----------------- AI Services & Features -----------------

@app.route('/advisor', methods=['GET', 'POST'])
@login_required
def advisor_chat_view():
    snapshot = get_user_snapshot(current_user)
    return render_template('advisor.html', snapshot=snapshot)

@app.route('/api/ai/chat', methods=['POST'])
@login_required
def api_ai_chat():
    data = request.get_json() or {}
    messages = data.get('messages', [])
    snapshot = get_user_snapshot(current_user)
    reply = chat_with_advisor(messages, snapshot)
    return jsonify({"reply": reply})

@app.route('/api/ai/parse-expense', methods=['POST'])
@login_required
def api_parse_expense():
    data = request.get_json() or {}
    text = data.get('text', '')
    parsed = parse_natural_language_expense(text)
    return jsonify(parsed)

@app.route('/simulator', methods=['GET', 'POST'])
@login_required
def purchase_simulator():
    snapshot = get_user_snapshot(current_user)
    result = None

    if request.method == 'POST':
        item_name = request.form.get('item_name', '').strip()
        cost = float(request.form.get('cost', 0))
        category = request.form.get('category', 'Shopping')
        urgency = request.form.get('urgency', 'Nice to Have')

        if item_name and cost > 0:
            result = simulate_purchase(item_name, cost, category, urgency, snapshot)

    return render_template('simulator.html', snapshot=snapshot, result=result)

@app.route('/report')
@login_required
def monthly_report():
    snapshot = get_user_snapshot(current_user)
    ai_analysis = analyze_spending_and_health(snapshot)
    current_month_name = datetime.date.today().strftime("%B %Y")
    
    return render_template(
        'report.html',
        snapshot=snapshot,
        analysis=ai_analysis,
        month_name=current_month_name
    )

@app.route('/export-csv')
@login_required
def export_csv():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Date', 'Title', 'Category', 'Amount', 'Notes'])

    for e in expenses:
        cw.writerow([
            e.id,
            e.date.strftime('%Y-%m-%d'),
            e.title,
            e.category.name if e.category else 'Uncategorized',
            f"{e.amount:.2f}",
            e.notes or ''
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=expenses_{datetime.date.today().strftime('%Y%m%d')}.csv"}
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
