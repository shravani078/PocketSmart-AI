# PocketSmart AI v2 — Smart Budget & Recommendation Assistant

## 🚀 Quick Start (3 Steps)

### Step 1 — Install Dependencies
```bash
cd pocketsmart-v2
python -m venv venv

# Activate venv:
# Windows:  venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

### Step 2 — Add Your Gemini API Key
Open `.env` and replace `YOUR_GEMINI_API_KEY_HERE` with your actual key.

Get a FREE key at: https://aistudio.google.com/app/apikey

```
GEMINI_API_KEY=AIza...your_key_here
```

### Step 3 — Run
```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## ✅ What's Fixed
- **Model Error Fixed**: Now uses `gemini-2.0-flash` (latest, always available) with fallback to `gemini-1.5-flash-latest`
- The old error `404 models/gemini-1.5-flash is not found for API version v1beta` is resolved

## 🌟 Features

### AI Chatbot
- Real-time chat with Gemini AI, personalized with your budget data
- **Voice Input**: Click mic button to speak your question
- **Voice Output**: Click "Play Audio" on any AI response to hear it read aloud
- Quick prompt buttons for common questions

### Budget Dashboard
- Income, spending, remaining balance stats
- Category spending charts
- Financial health score (0-100)
- Budget violation alerts

### Expense Tracking
- Add/delete expenses by category
- Date tracking

### Budget Limits & Savings
- Set per-category spending limits
- Savings goal tracker with progress bar

### AI Analysis
- Deep spending analysis by focus area (general, savings, food, etc.)

### 3 Smart Recommendation Planners
1. **🏠 Home Budget Planner** — Furniture & decor recs with Amazon/IKEA/Wayfair suggestions
2. **🎉 Party Budget Planner** — Event budget allocation by type (birthday, wedding, corporate, etc.)
3. **💎 Jewelry Budget Planner** — Occasion-based jewelry with outfit pairing tips

---

## 📁 File Structure
```
pocketsmart-v2/
├── app.py              ← Flask backend (main server)
├── requirements.txt    ← Python dependencies
├── .env                ← API keys (edit this!)
└── static/
    └── index.html      ← Complete frontend
```

## 🔧 Troubleshooting
- **Port 5000 in use (Mac)**: Change `PORT=5001` in `.env`
- **API errors**: Make sure your Gemini API key is valid and has quota
- **Module not found**: Make sure venv is activated before `pip install`
