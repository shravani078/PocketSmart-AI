# 💸 PocketSmart AI
### Your Smart Budget & Recommendation Assistant
*Powered by Google Gemini | Built with Flask*

---

## 📁 Project Structure

```
pocketsmart/
├── app.py                  ← Flask backend (routes + Gemini API)
├── requirements.txt        ← Python dependencies
├── .env                    ← API key (never commit this!)
├── templates/
│   └── index.html          ← Full app UI (login + dashboard)
└── static/
    └── styles.css          ← All styles
```

---

## ⚡ Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Your Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click **"Create API Key"**
3. Copy the key

### 3. Configure `.env`
Open `.env` and replace the placeholder:
```
GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Run the App
```bash
python app.py
```

### 5. Open in Browser
```
http://localhost:5000
```

---

## 🎮 Demo Login
- **Username:** `demo`
- **Password:** `demo123`

This loads sample expense data so you can explore all features immediately.

---

## 🤖 Features

| Feature | Description |
|---------|-------------|
| 🔐 Creative Login | Animated dark-theme auth with glassmorphism card |
| 📊 Dashboard | Live stats, category breakdown, recent expenses |
| 🤖 AI Analyze | Gemini analyzes your income + expenses |
| ➕ Add Expense | Log by category with quick-select pills |
| 🎯 Budget | Per-category limits + savings goal tracker |
| 💬 AI Chatbot | Floating chatbot on every page (Gemini-powered) |

---

## 🔌 API Endpoints

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Serves the main app |
| `/analyze` | POST | Analyzes budget with Gemini AI |
| `/chat` | POST | Powers the floating chatbot |

### `/analyze` Request Body
```json
{
  "income": "3000",
  "expenses": [
    {"category": "Food", "amount": 400, "description": "Groceries"},
    {"category": "Transport", "amount": 150, "description": "Gas"}
  ],
  "savings_goal": "500",
  "currency": "$"
}
```

---

## 🔒 Security Notes
- The `.env` file stores your API key securely
- **Never** commit `.env` to version control
- Add `.env` to your `.gitignore`

---

## 📦 Dependencies
- `flask` — Web framework
- `google-generativeai` — Gemini AI SDK
- `python-dotenv` — Secure env variable loading
