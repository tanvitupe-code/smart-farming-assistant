# Smart Farming Decision Assistant

A Python + Streamlit educational prototype for farm planning, weather awareness, user-entered mandi-price comparison, and optional AI-generated guidance.

## Setup in VS Code
1. Install Python 3.10 or newer and VS Code.
2. Open this folder in VS Code.
3. Create a terminal and run:
   - Windows: `py -m venv .venv`
   - Activate: `.venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install packages: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env`; add your Gemini API key if you want AI text generation.
6. Run: `streamlit run app.py`

Weather data uses the Open-Meteo geocoding and forecast APIs. The AI call is optional. The market table is explicitly user-entered demo data and should be replaced only with verified data from an official source.

## Important
This is an educational decision-support prototype, not a substitute for an agronomist, soil test, local agricultural university/KVK, or official market data. Never treat generated suggestions as guaranteed agronomic advice.
