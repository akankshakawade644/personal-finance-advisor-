import os
import json
import re
import datetime
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-2.5-flash"

def get_gemini_client():
    if not GEMINI_API_KEY:
        return None
    try:
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Error initializing Gemini Client: {e}")
        return None

def analyze_spending_and_health(snapshot):
    """
    Evaluates spending against income, computes 50/30/20 compliance,
    detects overspending, and calculates a financial health score.
    """
    total_income = snapshot.get("total_income", 0.0)
    total_expenses = snapshot.get("total_expenses", 0.0)
    net_cash_flow = total_income - total_expenses
    savings_rate = (net_cash_flow / total_income * 100) if total_income > 0 else 0.0
    overspent_cats = snapshot.get("overspent_categories", [])

    client = get_gemini_client()
    if client:
        try:
            prompt = f"""You are a certified Financial Analyst. Analyze this personal financial snapshot:
Income: ${total_income:.2f}
Total Expenses: ${total_expenses:.2f}
Net Cash Flow: ${net_cash_flow:.2f}
Savings Rate: {savings_rate:.1f}%
Categories with Overspending: {json.dumps(overspent_cats)}
Category Breakdown: {json.dumps(snapshot.get('category_totals', {}))}

Return strictly valid JSON with this exact schema:
{{
  "health_score": <number 0-100>,
  "status": "<Excellent|Good|Fair|Needs Attention>",
  "summary": "<2-3 sentence overview>",
  "actionable_tips": ["<tip1>", "<tip2>", "<tip3>"],
  "budget_comparison": {{
    "needs_percent": <number>,
    "wants_percent": <number>,
    "savings_percent": <number>
  }}
}}"""
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Gemini API rate-limited or error, using algorithmic analyzer: {e}")

    # Deterministic fallback evaluation
    score = 75
    if savings_rate >= 20:
        score += 15
    elif savings_rate >= 10:
        score += 5
    else:
        score -= 15

    score -= min(30, len(overspent_cats) * 8)
    score = max(20, min(98, round(score)))

    if score >= 85:
        status = "Excellent"
    elif score >= 70:
        status = "Good"
    elif score >= 50:
        status = "Fair"
    else:
        status = "Needs Attention"

    return {
        "health_score": score,
        "status": status,
        "summary": f"Your current net cash flow is {'+$' if net_cash_flow >= 0 else '-$'}{abs(net_cash_flow):.2f} with a {savings_rate:.1f}% savings rate. {'Discretionary spending in ' + ', '.join([c['name'] for c in overspent_cats]) + ' requires moderation.' if overspent_cats else 'All tracked envelopes remain comfortably within limits.'}",
        "actionable_tips": [
            f"Cap overspending in {overspent_cats[0]['name']} to recover surplus" if overspent_cats else "Set up automated transfer of 15% income to savings on payday",
            "Audit recurring subscriptions and cancel unused digital services",
            "Prepare weekday lunches at home to reduce dining creep"
        ],
        "budget_comparison": {
            "needs_percent": 55,
            "wants_percent": 30,
            "savings_percent": max(0, round(savings_rate))
        }
    }


def chat_with_advisor(messages, snapshot):
    """
    Interactive contextual financial advisor bot conversation.
    """
    total_income = snapshot.get("total_income", 0.0)
    total_expenses = snapshot.get("total_expenses", 0.0)
    net_flow = total_income - total_expenses
    savings_rate = (net_flow / total_income * 100) if total_income > 0 else 0.0
    overspent = snapshot.get("overspent_categories", [])

    client = get_gemini_client()
    if client:
        try:
            formatted_history = "\n".join([f"{'User' if m['role'] == 'user' else 'Advisor'}: {m['text']}" for m in messages])
            prompt = f"""You are the Personal Finance Advisor Bot, an empathetic, mathematically disciplined financial planner.
User Financial Snapshot:
- Monthly Income: ${total_income:.2f}
- Expenses: ${total_expenses:.2f}
- Net Surplus/Deficit: ${net_flow:.2f}
- Savings Rate: {savings_rate:.1f}%
- Overspent Categories: {json.dumps(overspent)}

Conversation:
{formatted_history}

Advisor:"""
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Advisor Chat fallback: {e}")

    # Fallback contextual response
    last_user_msg = messages[-1]["text"].lower() if messages else ""
    if "audit" in last_user_msg or "overspend" in last_user_msg:
        if overspent:
            items = "\n".join([f"• **{c['name']}**: Spent ${c['spent']:.2f} vs Limit ${c['budget']:.2f} (Over by +${c['variance']:.2f})" for c in overspent])
            return f"Here is your current overspending audit:\n\n{items}\n\n**Recommendation:** Reducing dining out and shopping over the next 2 weeks will recover these funds into your monthly savings."
        return f"Great news! You have no budget categories in excess right now. Your net cash surplus is **+${net_flow:.2f}** with a **{savings_rate:.1f}%** savings rate."
    
    if "save" in last_user_msg or "goal" in last_user_msg:
        return f"Based on your **${total_income:.2f}** monthly income, your 50/30/20 target savings should be **${total_income * 0.2:.2f}/month**. Locking this into an automated transfer immediately on payday prevents lifestyle inflation."

    return f"I have reviewed your financial dashboard (**${total_income:.2f}** income, **${total_expenses:.2f}** expenses, **{'+$' if net_flow >= 0 else '-$'}{abs(net_flow):.2f}** net flow). You can ask me to audit specific envelopes, evaluate future purchases, or optimize your savings rate!"


def simulate_purchase(item_name, cost, category, urgency, snapshot):
    """
    Evaluates whether a purchase is safe based on monthly surplus and goals.
    """
    total_income = snapshot.get("total_income", 0.0)
    total_expenses = snapshot.get("total_expenses", 0.0)
    net_surplus = total_income - total_expenses

    client = get_gemini_client()
    if client:
        try:
            prompt = f"""Assess this purchase for a user:
Item: {item_name}, Cost: ${cost:.2f}, Category: {category}, Urgency: {urgency}
User Income: ${total_income:.2f}, Expenses: ${total_expenses:.2f}, Current Monthly Surplus: ${net_surplus:.2f}

Output JSON with schema:
{{
  "verdict": "SAFE" | "CAUTION" | "NOT_RECOMMENDED",
  "verdict_title": "<short title>",
  "rationale": "<explanation>",
  "impact_on_cash_flow": "<cash flow impact>",
  "recommended_action": "<recommendation>"
}}"""
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Simulator fallback: {e}")

    # Fallback simulation logic
    if cost > net_surplus:
        return {
            "verdict": "NOT_RECOMMENDED",
            "verdict_title": "Exceeds Monthly Cash Buffer",
            "rationale": f"This purchase of ${cost:.2f} exceeds your remaining monthly surplus of ${net_surplus:.2f}. Proceeding will create a deficit or require dipping into emergency savings.",
            "impact_on_cash_flow": f"Turns your monthly flow from +${net_surplus:.2f} to -${cost - net_surplus:.2f}.",
            "recommended_action": "Postpone this purchase to next month and establish a dedicated savings sinking fund."
        }
    elif cost > (net_surplus * 0.4):
        return {
            "verdict": "CAUTION",
            "verdict_title": "Proceed With Caution",
            "rationale": f"At ${cost:.2f}, this purchase consumes over 40% of your remaining cash buffer (${net_surplus:.2f}).",
            "impact_on_cash_flow": f"Leaves you with an estimated ${net_surplus - cost:.2f} remaining surplus for unexpected costs.",
            "recommended_action": "Wait 48 hours to avoid impulse bias, or reduce discretionary dining this week."
        }
    else:
        return {
            "verdict": "SAFE",
            "verdict_title": "Safe to Proceed",
            "rationale": f"Your current cash buffer of ${net_surplus:.2f} comfortably absorbs this ${cost:.2f} expense without compromising emergency reserves.",
            "impact_on_cash_flow": f"Retains a healthy ${net_surplus - cost:.2f} positive surplus.",
            "recommended_action": "Log this transaction under {category} upon completion."
        }


def parse_natural_language_expense(text, current_date=None):
    """
    Extracts amount, category, and title from natural language text.
    """
    if not current_date:
        current_date = datetime.date.today().isoformat()

    client = get_gemini_client()
    if client:
        try:
            prompt = f"""Extract expense details from: "{text}". Today's date is {current_date}.
Categories: Housing, Food & Dining, Groceries, Transportation, Utilities, Entertainment, Healthcare, Shopping, Education, Subscriptions, Miscellaneous.
Return JSON:
{{"amount": float, "category": string, "title": string, "date": "YYYY-MM-DD"}}"""
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Parse expense fallback: {e}")

    # Fallback regex parser
    match = re.search(r'\$?(\d+(?:\.\d{1,2})?)', text)
    amount = float(match.group(1)) if match else 20.0
    lower = text.lower()

    category = "Food & Dining"
    if any(k in lower for k in ["rent", "lease", "apartment"]): category = "Housing"
    elif any(k in lower for k in ["grocery", "trader", "walmart", "supermarket"]): category = "Groceries"
    elif any(k in lower for k in ["uber", "lyft", "gas", "transit", "metro"]): category = "Transportation"
    elif any(k in lower for k in ["power", "electric", "wifi", "water", "utility"]): category = "Utilities"
    elif any(k in lower for k in ["movie", "concert", "game", "club"]): category = "Entertainment"
    elif any(k in lower for k in ["netflix", "spotify", "subscription", "gym"]): category = "Subscriptions"
    elif any(k in lower for k in ["clothes", "shoes", "amazon", "mall"]): category = "Shopping"

    title = re.sub(r'\$?(\d+(?:\.\d{1,2})?)', '', text).strip()
    if not title:
        title = f"{category} expense"

    return {
        "amount": amount,
        "category": category,
        "title": title.capitalize(),
        "date": current_date
    }
