# PocketSmart-AI

📌About the Project
PocketSmart AI is a full-stack web application built as part of a Google Cloud Generative AI course project. It combines a clean, modern UI with the power of the Google Gemini 1.5 Flash model to help users understand their spending habits, set smarter budgets, and receive personalized financial recommendations in real time.
The core idea is simple: instead of just showing you numbers, PocketSmart AI talks to you about your money — explaining where you're overspending, how to save more, and what strategies can improve your overall financial health.

🎯 What Problem Does It Solve?
Most budgeting apps show charts and graphs but leave the interpretation to the user. PocketSmart AI bridges that gap by using a large language model to:

Explain your spending in plain English
Point out specific categories that need attention
Suggest concrete, actionable steps to save money
Give you a personalized financial health score
Answer your finance questions conversationally via a built-in chatbot

✨ Features

🔐 Animated login page with glassmorphism design
📊 Live dashboard — income, spending, category breakdown
🤖 AI budget analysis powered by Gemini 1.5 Flash
➕ Expense tracker with category tags
🎯 Budget limits & savings goal tracker
💬 Floating AI chatbot available on every page

🛠️ Tech Stack

Backend — Python, Flask
AI — Google Gemini 1.5 Flash (google-generativeai)
Frontend — HTML, CSS, Vanilla JS
Config — python-dotenv for secure API key storage

AI Model
gemini-1.5-flash — Fast, efficient, and cost-effective for financial analysis tasks

📁 Project Structure
pocketsmart/
├── app.py               ← Flask routes + Gemini API
├── .env                 ← Your API key (never commit this)
├── requirements.txt
├── templates/
│   └── index.html       ← Full app UI
└── static/
    └── styles.css

🚀 Quick Start

# 1. Clone the repo
git clone https://github.com/your-username/pocketsmart-ai.git
cd pocketsmart-ai
# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
# 3. Install dependencies
pip install -r requirements.txt
# 4. Add your Gemini API key to .env
GEMINI_API_KEY=AIzaSyBmL1TM3O3Lcvf44NyJ1Y6JWcbhA8SlPyc
# 5. Run
python app.py
Open → http://localhost:5000
Demo login → username: demo | password: demo123
