"""
PocketSmart AI v2 — Smart Budget & Recommendation Assistant
Flask Backend with Google Gemini API
"""

import os
import json
import uuid
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "pocketsmart-secret-2024")
CORS(app, supports_credentials=True)

# ── Gemini Setup ───────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
API_KEY_VALID  = bool(GEMINI_API_KEY and GEMINI_API_KEY not in ("YOUR_GEMINI_API_KEY_HERE", ""))

# Try models in order — gemini-1.5-flash has highest free-tier quota
MODEL_PRIORITY = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.0-pro",
]

model             = None
active_model_name = ""

if API_KEY_VALID:
    genai.configure(api_key=GEMINI_API_KEY)
    for m_name in MODEL_PRIORITY:
        try:
            model             = genai.GenerativeModel(m_name)
            active_model_name = m_name
            print(f"✅  Model loaded: {m_name}")
            break
        except Exception as ex:
            print(f"   ↳ {m_name} unavailable: {ex}")
    if model is None:
        print("❌  No Gemini model could be loaded. Check your API key.")
else:
    print("⚠️   GEMINI_API_KEY not set — add it to .env and restart.")
    print("    Free key → https://aistudio.google.com/app/apikey")

# ── Rate Limiter ── stay under 14 req/min on free tier ─────────────────────
_rate_lock = threading.Lock()
_req_times = []
MAX_RPM    = 14

def _throttle():
    global _req_times
    with _rate_lock:
        now        = time.time()
        _req_times = [t for t in _req_times if now - t < 60]
        if len(_req_times) >= MAX_RPM:
            sleep_for = 62 - (now - _req_times[0])
            if sleep_for > 0:
                print(f"⏳  Rate-limit pause: {sleep_for:.1f}s")
                time.sleep(sleep_for)
            _req_times = []
        _req_times.append(time.time())

def ai_generate(prompt: str) -> str:
    """Generate content with throttling and 3-attempt retry on quota errors."""
    for attempt in range(3):
        _throttle()
        try:
            return model.generate_content(prompt).text
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                wait = (attempt + 1) * 25
                print(f"⏳  Quota hit (attempt {attempt+1}/3) — waiting {wait}s")
                time.sleep(wait)
                continue
            raise e
    raise Exception("QUOTA_EXCEEDED")

def ai_chat(session, message: str):
    """Send chat message with throttling and retry."""
    for attempt in range(3):
        _throttle()
        try:
            return session.send_message(message)
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                wait = (attempt + 1) * 25
                print(f"⏳  Quota hit on chat (attempt {attempt+1}/3) — waiting {wait}s")
                time.sleep(wait)
                continue
            raise e
    raise Exception("QUOTA_EXCEEDED")

def friendly_ai_error(e: Exception) -> str:
    err = str(e)
    if "QUOTA_EXCEEDED" in err or "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
        return ("quota_exceeded: Free-tier rate limit reached (15 req/min). "
                "Please wait ~60 seconds and try again.")
    if "API_KEY_INVALID" in err or "API key not valid" in err:
        return "API key is invalid. Check your .env file — no spaces, no quotes around the key."
    return f"AI error: {err}"

def check_api_key():
    if not API_KEY_VALID or model is None:
        return {"error": (
            "Gemini API key not configured.\n\n"
            "1. Go to https://aistudio.google.com/app/apikey\n"
            "2. Create a free API key\n"
            "3. Open .env and set GEMINI_API_KEY=your_key\n"
            "4. Restart: python app.py"
        )}
    return None

# ── In-Memory Storage ──────────────────────────────────────────────────────
users_db = {}

def get_or_create_user(uid: str) -> dict:
    if uid not in users_db:
        users_db[uid] = {
            "user_id": uid, "name": "User",
            "created_at": datetime.now().isoformat(),
            "monthly_income": 0, "currency": "USD",
            "expenses": [], "savings_goal": 0, "savings_saved": 0,
            "budget_limits": {}, "chat_history": [],
        }
    return users_db[uid]

def build_budget_summary(user: dict) -> dict:
    exps        = user.get("expenses", [])
    total_spent = sum(e["amount"] for e in exps)
    income      = user.get("monthly_income", 0)
    by_cat      = {}
    for e in exps:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
    violations = []
    for cat, lim in user.get("budget_limits", {}).items():
        sp = by_cat.get(cat, 0)
        if sp > lim:
            violations.append({"category": cat, "limit": lim, "spent": sp, "over_by": round(sp - lim, 2)})
    sg = user.get("savings_goal", 0)
    ss = user.get("savings_saved", 0)
    return {
        "monthly_income": income,
        "total_spent": round(total_spent, 2),
        "remaining_balance": round(income - total_spent, 2),
        "spending_by_category": by_cat,
        "budget_violations": violations,
        "savings_goal": sg, "savings_saved": ss,
        "savings_progress_pct": round(ss / sg * 100, 1) if sg > 0 else 0,
        "currency": user.get("currency", "USD"),
    }

def sys_prompt(user: dict) -> str:
    s = build_budget_summary(user)
    return f"""You are PocketSmart AI — a warm, smart personal finance assistant.

USER: {user.get('name','User')} | Income: {s['currency']} {s['monthly_income']}/mo
Spent: {s['currency']} {s['total_spent']} | Remaining: {s['currency']} {s['remaining_balance']}
Categories: {json.dumps(s['spending_by_category'])}
Violations: {json.dumps(s['budget_violations'])}
Savings: {s['currency']} {s['savings_saved']} / {s['currency']} {s['savings_goal']} ({s['savings_progress_pct']}%)

Be concise, warm, use emojis, specific with numbers. Use {s['currency']} currency symbol.
"""

# ── Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "model": active_model_name, "timestamp": datetime.now().isoformat()})

@app.route("/api/check-key")
def check_key_endpoint():
    if API_KEY_VALID and model is not None:
        return jsonify({"valid": True, "model": active_model_name})
    return jsonify({"valid": False, "message": "Add GEMINI_API_KEY to .env and restart."}), 200

# User
@app.route("/api/user/setup", methods=["POST"])
def user_setup():
    d = request.get_json()
    uid  = d.get("user_id", str(uuid.uuid4()))
    user = get_or_create_user(uid)
    user["monthly_income"] = float(d.get("monthly_income", user["monthly_income"]))
    user["currency"]       = d.get("currency", user["currency"])
    user["savings_goal"]   = float(d.get("savings_goal", user["savings_goal"]))
    user["name"]           = d.get("name", user.get("name", "User"))
    return jsonify({"message": "Saved.", "user_id": uid, "profile": user}), 200

@app.route("/api/user/<uid>/profile")
def get_profile(uid):
    return jsonify({"profile": get_or_create_user(uid)}), 200

@app.route("/api/user/<uid>/reset", methods=["DELETE"])
def reset_user(uid):
    users_db.pop(uid, None)
    return jsonify({"message": "Reset."}), 200

# Expenses
@app.route("/api/expense/add", methods=["POST"])
def add_expense():
    d = request.get_json()
    uid = d.get("user_id")
    if not uid: return jsonify({"error": "user_id required"}), 400
    user = get_or_create_user(uid)
    exp  = {
        "expense_id":  str(uuid.uuid4()),
        "category":    d.get("category", "Other"),
        "amount":      float(d.get("amount", 0)),
        "description": d.get("description", ""),
        "date":        d.get("date", datetime.now().strftime("%Y-%m-%d")),
        "added_at":    datetime.now().isoformat(),
    }
    if exp["amount"] <= 0: return jsonify({"error": "Amount must be > 0"}), 400
    user["expenses"].append(exp)
    summary  = build_budget_summary(user)
    alert    = None
    cat_spent = summary["spending_by_category"].get(exp["category"], 0)
    cat_lim   = user["budget_limits"].get(exp["category"])
    if cat_lim and cat_spent > cat_lim:
        alert = f"⚠️ Over budget '{exp['category']}': {user['currency']} {cat_spent:.2f} / {cat_lim:.2f}"
    return jsonify({"message": "Added.", "expense": exp, "alert": alert, "summary": summary}), 201

@app.route("/api/expense/<uid>/list")
def list_expenses(uid):
    user = get_or_create_user(uid)
    cat  = request.args.get("category")
    exps = user["expenses"]
    if cat: exps = [e for e in exps if e["category"].lower() == cat.lower()]
    return jsonify({"expenses": exps, "count": len(exps)}), 200

@app.route("/api/expense/<uid>/<eid>", methods=["DELETE"])
def delete_expense(uid, eid):
    user   = get_or_create_user(uid)
    before = len(user["expenses"])
    user["expenses"] = [e for e in user["expenses"] if e["expense_id"] != eid]
    if len(user["expenses"]) == before: return jsonify({"error": "Not found"}), 404
    return jsonify({"message": "Deleted.", "summary": build_budget_summary(user)}), 200

# Budget / Savings
@app.route("/api/budget/set-limits", methods=["POST"])
def set_budget_limits():
    d   = request.get_json()
    uid = d.get("user_id")
    if not uid: return jsonify({"error": "user_id required"}), 400
    user = get_or_create_user(uid)
    for cat, lim in d.get("limits", {}).items():
        user["budget_limits"][cat] = float(lim)
    return jsonify({"message": "Updated.", "limits": user["budget_limits"]}), 200

@app.route("/api/savings/update", methods=["POST"])
def update_savings():
    d    = request.get_json()
    user = get_or_create_user(d.get("user_id", ""))
    if "savings_saved" in d: user["savings_saved"] = float(d["savings_saved"])
    if "savings_goal"  in d: user["savings_goal"]  = float(d["savings_goal"])
    return jsonify({"message": "Updated.", "summary": build_budget_summary(user)}), 200

# Dashboard
@app.route("/api/dashboard/<uid>")
def dashboard(uid):
    user    = get_or_create_user(uid)
    summary = build_budget_summary(user)
    top     = sorted(summary["spending_by_category"].items(), key=lambda x: x[1], reverse=True)[:5]
    income  = summary["monthly_income"]
    spent   = summary["total_spent"]
    score   = 100
    if income > 0:
        r = spent / income
        score = 10 if r > 1.0 else 30 if r > 0.9 else 55 if r > 0.7 else 75 if r > 0.5 else 95
        if summary["budget_violations"]:
            score = max(10, score - 15 * len(summary["budget_violations"]))
    label = "Excellent" if score >= 90 else "Good" if score >= 70 else "Fair" if score >= 50 else "Poor"
    return jsonify({
        "summary": summary,
        "top_categories": [{"category": k, "amount": v} for k, v in top],
        "financial_health_score": score, "health_label": label,
        "total_expenses_count": len(user["expenses"]),
    }), 200

# AI Chat
@app.route("/api/chat", methods=["POST"])
def chat():
    err = check_api_key()
    if err: return jsonify(err), 503
    d       = request.get_json()
    uid     = d.get("user_id")
    message = d.get("message", "").strip()
    if not uid or not message: return jsonify({"error": "user_id and message required"}), 400
    user    = get_or_create_user(uid)
    history = user["chat_history"][-20:]
    full_msg = message if history else f"{sys_prompt(user)}\n\nUser: {message}"
    try:
        if history:
            session  = model.start_chat(history=history)
            response = ai_chat(session, full_msg)
        else:
            session  = model.start_chat()
            response = ai_chat(session, full_msg)
        reply = response.text
        user["chat_history"].append({"role": "user",  "parts": [full_msg]})
        user["chat_history"].append({"role": "model", "parts": [reply]})
        return jsonify({"reply": reply, "user_id": uid, "timestamp": datetime.now().isoformat()}), 200
    except Exception as e:
        return jsonify({"error": friendly_ai_error(e)}), 500

# AI Analysis
@app.route("/api/analyze/<uid>", methods=["POST"])
def analyze_spending(uid):
    err = check_api_key()
    if err: return jsonify(err), 503
    user    = get_or_create_user(uid)
    summary = build_budget_summary(user)
    focus   = request.get_json().get("focus", "general")
    prompt  = f"""{sys_prompt(user)}

Perform a detailed {focus} spending analysis:
1. 📊 Key observations
2. ⚠️ Top 3 concerns with numbers
3. 💡 3 actionable recommendations with specific amounts
4. 🏆 Health score explanation
5. 🌟 Motivational closing

Keep under 300 words, use emojis per section."""
    try:
        text = ai_generate(prompt)
        return jsonify({"analysis": text, "summary": summary, "focus": focus}), 200
    except Exception as e:
        return jsonify({"error": friendly_ai_error(e)}), 500

# AI Recommendations
@app.route("/api/recommendations/<uid>")
def recommendations(uid):
    err = check_api_key()
    if err: return jsonify(err), 503
    user  = get_or_create_user(uid)
    ptype = request.args.get("type", "general")
    bal   = build_budget_summary(user)["remaining_balance"]
    cur   = user["currency"]

    prompts = {
        "home":    f"""{sys_prompt(user)}
Home upgrade budget = {cur} {bal}. Recommend 5 furniture/decor items.
Return ONLY valid JSON array:
[{{"title":"name","category":"Furniture/Decor/Lighting","estimated_price":100,"platform":"Amazon/IKEA/Wayfair","description":"2 sentences.","priority":"high","tip":"saving tip"}}]""",

        "party":   f"""{sys_prompt(user)}
Party budget = {cur} {bal}. Smart allocation plan for 5 tips.
Return ONLY valid JSON array:
[{{"title":"tip","category":"venue/food/decor/entertainment","estimated_cost":100,"description":"2 sentences.","priority":"high"}}]""",

        "jewelry": f"""{sys_prompt(user)}
Jewelry budget = {cur} {bal}. Recommend 5 occasion-based pieces.
Return ONLY valid JSON array:
[{{"title":"item","occasion":"wedding/casual/formal/festive","estimated_price":100,"style_tip":"outfit advice","where_to_buy":"platform","description":"2 sentences.","priority":"high"}}]""",

        "general": f"""{sys_prompt(user)}
Give 5 personalized money-saving recommendations.
Return ONLY valid JSON array:
[{{"title":"title","category":"category","potential_savings":50,"description":"2-3 sentences.","priority":"high"}}]""",
    }

    try:
        text  = ai_generate(prompts.get(ptype, prompts["general"]))
        clean = text.strip()
        if "```" in clean:
            parts = clean.split("```")
            clean = parts[1] if len(parts) > 1 else clean
            if clean.startswith("json"): clean = clean[4:]
        recs = json.loads(clean.strip())
        return jsonify({"recommendations": recs, "type": ptype}), 200
    except json.JSONDecodeError:
        return jsonify({"recommendations_text": text, "type": ptype}), 200
    except Exception as e:
        return jsonify({"error": friendly_ai_error(e)}), 500

# Forecast
@app.route("/api/forecast/<uid>", methods=["POST"])
def forecast(uid):
    err = check_api_key()
    if err: return jsonify(err), 503
    user         = get_or_create_user(uid)
    d            = request.get_json()
    days_elapsed = int(d.get("days_elapsed", 15))
    total_days   = int(d.get("total_days", 30))
    summary      = build_budget_summary(user)
    spent        = summary["total_spent"]
    income       = summary["monthly_income"]
    daily_avg    = spent / days_elapsed if days_elapsed > 0 else 0
    proj_spend   = daily_avg * total_days
    prompt       = f"""{sys_prompt(user)}
Spent {user['currency']} {spent:.2f} in {days_elapsed} days. Projected: {user['currency']} {proj_spend:.2f}/month.
Write 2 paragraphs: forecast + one improvement tip. Under 150 words."""
    try:
        text = ai_generate(prompt)
        return jsonify({
            "days_elapsed": days_elapsed, "spent_so_far": round(spent, 2),
            "daily_avg_spend": round(daily_avg, 2),
            "projected_monthly_spend": round(proj_spend, 2),
            "projected_monthly_savings": round(income - proj_spend, 2),
            "ai_assessment": text,
        }), 200
    except Exception as e:
        return jsonify({"error": friendly_ai_error(e)}), 500

@app.errorhandler(404)
def not_found(e): return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e): return jsonify({"error": "Server error"}), 500

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    print(f"\n🚀  PocketSmart AI v2 → http://localhost:{port}")
    print(f"🤖  Active model: {active_model_name or 'None (set GEMINI_API_KEY in .env)'}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
