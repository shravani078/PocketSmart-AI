import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        income = data.get("income", "").strip()
        expenses = data.get("expenses", [])
        savings_goal = data.get("savings_goal", "").strip()
        currency = data.get("currency", "$")

        if not income:
            return jsonify({"error": "Monthly income is required"}), 400
        if not expenses:
            return jsonify({"error": "At least one expense is required"}), 400

        # Build expense summary for the prompt
        expense_lines = []
        total_spent = 0
        for exp in expenses:
            cat = exp.get("category", "Other")
            desc = exp.get("description", "")
            amt = float(exp.get("amount", 0))
            total_spent += amt
            expense_lines.append(f"  - {cat}: {currency}{amt:.2f} ({desc})")

        expense_summary = "\n".join(expense_lines)
        remaining = float(income) - total_spent
        spent_pct = (total_spent / float(income) * 100) if float(income) > 0 else 0

        prompt = f"""You are PocketSmart AI, a friendly and insightful personal finance assistant.

Analyze the following financial data and provide actionable, personalized advice:

FINANCIAL SUMMARY:
- Monthly Income: {currency}{income}
- Total Spent: {currency}{total_spent:.2f} ({spent_pct:.1f}% of income)
- Remaining Balance: {currency}{remaining:.2f}
{f'- Savings Goal: {currency}{savings_goal}' if savings_goal else ''}

EXPENSE BREAKDOWN:
{expense_summary}

Please provide a comprehensive analysis with the following sections (use these exact headers):

## 💡 Overall Assessment
A brief 2-3 sentence overview of their financial health.

## ⚠️ Areas of Concern
List specific spending categories that need attention (if any). Be specific with numbers.

## 🎯 Smart Budget Suggestions
3-5 concrete, actionable budget adjustments with specific amounts.

## 💰 Saving Tips
3-4 practical saving strategies tailored to their actual expense categories.

## 📈 Better Spending Strategies
2-3 strategic recommendations for improving long-term financial health.

## 🏆 Financial Health Score
Rate their financial health from 1-100 with a brief explanation.

Keep the tone friendly, motivating, and specific to their actual data. Use emojis sparingly for readability."""

        response = model.generate_content(prompt)
        ai_text = response.text

        return jsonify({
            "success": True,
            "analysis": ai_text,
            "summary": {
                "income": float(income),
                "total_spent": total_spent,
                "remaining": remaining,
                "spent_pct": round(spent_pct, 1),
                "currency": currency
            }
        })

    except ValueError as e:
        return jsonify({"error": f"Invalid number format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route("/chat", methods=["POST"])
def chat():
    """Floating chatbot endpoint."""
    try:
        data = request.get_json()
        message = data.get("message", "").strip()
        context = data.get("context", {})

        if not message:
            return jsonify({"error": "Message is required"}), 400

        income = context.get("income", 0)
        total_spent = context.get("total_spent", 0)
        currency = context.get("currency", "$")
        expenses = context.get("expenses", [])

        expense_info = ""
        if expenses:
            cats = {}
            for e in expenses:
                cats[e.get("category", "Other")] = cats.get(e.get("category", "Other"), 0) + float(e.get("amount", 0))
            expense_info = ", ".join([f"{k}: {currency}{v:.0f}" for k, v in cats.items()])

        system_context = f"""You are PocketSmart AI, a friendly personal finance assistant.
User's financial data: Income={currency}{income}/mo, Spent={currency}{total_spent:.0f}, 
Remaining={currency}{income - total_spent:.0f}, Categories: {expense_info or 'No expenses logged yet'}.
Be concise (2-4 sentences), helpful, and specific to their data. Use 1-2 emojis max."""

        response = model.generate_content(f"{system_context}\n\nUser: {message}")
        return jsonify({"success": True, "reply": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
