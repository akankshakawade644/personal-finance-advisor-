import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    currency = db.Column(db.String(10), default='$')
    persona = db.Column(db.String(50), default='Salaried Professional')
    monthly_income_target = db.Column(db.Float, default=5000.0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    incomes = db.relationship('Income', backref='user', lazy=True, cascade="all, delete-orphan")
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade="all, delete-orphan")
    categories = db.relationship('ExpenseCategory', backref='user', lazy=True, cascade="all, delete-orphan")
    savings_goals = db.relationship('SavingsGoal', backref='user', lazy=True, cascade="all, delete-orphan")
    reports = db.relationship('MonthlyReport', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Income(db.Model):
    __tablename__ = 'incomes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.date.today)
    frequency = db.Column(db.String(50), default='Monthly') # Monthly, Bi-weekly, One-time
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    budget_limit = db.Column(db.Float, default=0.0)
    envelope_type = db.Column(db.String(20), default='Needs') # Needs (50%), Wants (30%), Savings (20%)
    color = db.Column(db.String(30), default='#3b82f6')
    icon = db.Column(db.String(50), default='tag')
    
    expenses = db.relationship('Expense', backref='category', lazy=True)


class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.date.today)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class SavingsGoal(db.Model):
    __tablename__ = 'savings_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    target_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(50), default='Emergency Fund')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    @property
    def percentage(self):
        if self.target_amount <= 0:
            return 0
        return min(100.0, round((self.current_amount / self.target_amount) * 100, 1))


class MonthlyReport(db.Model):
    __tablename__ = 'monthly_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False) # 1-12
    year = db.Column(db.Integer, nullable=False)
    total_income = db.Column(db.Float, default=0.0)
    total_expense = db.Column(db.Float, default=0.0)
    net_savings = db.Column(db.Float, default=0.0)
    savings_rate = db.Column(db.Float, default=0.0)
    health_score = db.Column(db.Integer, default=70)
    ai_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
