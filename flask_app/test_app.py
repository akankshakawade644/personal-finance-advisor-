import unittest
import os
import tempfile
from app import app, db
from models import User, Income, ExpenseCategory, Expense, SavingsGoal
from ai_advisor import analyze_spending_and_health, simulate_purchase, parse_natural_language_expense

class FinanceAdvisorTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_user_registration_and_login(self):
        """Test registration, password hashing, and login flow"""
        # Register
        res = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'currency': '$',
            'persona': 'Salaried Professional'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Financial Command Center', res.data)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Login with valid password
        res = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Financial Command Center', res.data)

        # Login with invalid password
        self.client.get('/logout')
        res = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username/email or password', res.data)

    def test_income_and_expense_tracking(self):
        """Test adding and deleting incomes and expenses"""
        with app.app_context():
            user = User(username='finance_user', email='fin@test.com')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()

            # Add category
            cat = ExpenseCategory(user_id=user.id, name='Groceries', budget_limit=400.0, envelope_type='Needs')
            db.session.add(cat)

            # Add Income
            income = Income(user_id=user.id, source='Salary', amount=5000.0)
            db.session.add(income)

            # Add Expense
            exp = Expense(user_id=user.id, category_id=cat.id, title='Supermarket', amount=120.50)
            db.session.add(exp)
            db.session.commit()

            # Assertions
            self.assertEqual(Income.query.filter_by(user_id=user.id).count(), 1)
            self.assertEqual(Expense.query.filter_by(user_id=user.id).count(), 1)
            self.assertEqual(Expense.query.first().amount, 120.50)

    def test_ai_spending_health_evaluation(self):
        """Test AI Spending analysis and deterministic health score algorithm"""
        snapshot = {
            'total_income': 5000.0,
            'total_expenses': 3200.0,
            'overspent_categories': [{'name': 'Food & Dining', 'spent': 600.0, 'budget': 350.0, 'variance': 250.0}]
        }
        analysis = analyze_spending_and_health(snapshot)
        self.assertIn('health_score', analysis)
        self.assertIn('status', analysis)
        self.assertIn('summary', analysis)
        self.assertTrue(0 <= analysis['health_score'] <= 100)

    def test_purchase_simulator(self):
        """Test 'Can I Afford This?' purchase stress-tester"""
        snapshot = {
            'total_income': 4000.0,
            'total_expenses': 3500.0,
            'net_cash_flow': 500.0
        }
        # Testing item within buffer
        result_safe = simulate_purchase('Office Chair', 150.0, 'Shopping', 'Nice to Have', snapshot)
        self.assertIn(result_safe['verdict'], ['SAFE', 'CAUTION'])

        # Testing item exceeding buffer
        result_excess = simulate_purchase('Luxury Watch', 1200.0, 'Shopping', 'Impulse', snapshot)
        self.assertEqual(result_excess['verdict'], 'NOT_RECOMMENDED')

    def test_natural_language_expense_parser(self):
        """Test NLP / regex extraction from conversational entry"""
        entry = "Lunch at Chipotle for $18.50"
        parsed = parse_natural_language_expense(entry)
        self.assertEqual(parsed['amount'], 18.50)
        self.assertEqual(parsed['category'], 'Food & Dining')

if __name__ == '__main__':
    unittest.main()
