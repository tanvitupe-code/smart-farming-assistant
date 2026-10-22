import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="Smart Farming AI Decision Assistant", page_icon="🌱", layout="wide")

# ---------- Helpers ----------
@st.cache_data(ttl=1800, show_spinner=False)
def get_weather(city):
    """Fetch current conditions and a three-day forecast from Open-Meteo."""
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=12,
        )
        geo.raise_for_status()
        places = geo.json().get("results", [])
        if not places:
            return None, f"No location found for '{city}'. Try a nearby larger town."
        place = places[0]
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
                "timezone": "auto",
                "forecast_days": 3,
            },
            timeout=12,
        )
        resp.raise_for_status()
        return {"place": place, "data": resp.json()}, None
    except requests.RequestException:
        return None, "Weather service could not be reached. Check the location and internet connection."


def get_api_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        try:
            key = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
        except Exception:
            key = ""
    return key


def build_prompt(profile, weather_summary, prices, question):
    return f"""
You are the AI decision-support component of a student Smart Farming Decision Assistant.
Use only the supplied information and general cautious reasoning. Do not pretend to be a local agronomist.
Do not invent live prices, rainfall, soil test results, crop yield, disease diagnoses, or guaranteed profit.
Do not prescribe pesticide/fertilizer dosages. State uncertainty and advise checking local KVK/agriculture officers
and a soil-test report before making real farming decisions.

Return your answer using these headings:
1. Farm situation summary
2. Weather-related considerations (refer only to supplied weather)
3. Crop-planning considerations (general, not a guarantee)
4. Water and soil checks
5. Budget planning (show only transparent arithmetic based on the supplied budget; label any split as illustrative)
6. Market-price interpretation (only the entered values; note they are user supplied)
7. Three practical next steps
8. What must be verified locally

Farm profile:
{profile}

Weather data:
{weather_summary}

User-entered market-price rows (not independently verified):
{prices}

Farmer's question:
{question or "No extra question supplied."}

Be clear, concise, and specific to these inputs. If information is missing, say what is missing.
"""


# ---------- Sidebar inputs ----------
st.title("🌱 Smart Farming Decision Assistant")
st.caption("AI-assisted farm planning using user inputs, weather context, and market-price comparison.")
with st.sidebar:
    st.header("Farm profile")
    location = st.text_input("Town / city", "Baramati")
    crop = st.selectbox("Crop", ["Sugarcane", "Cotton", "Soybean", "Tomato", "Onion", "Potato", "Wheat", "Maize", "Other"])
    area = st.number_input("Farm area (acres)", min_value=0.1, max_value=10000.0, value=2.0, step=0.5)
    soil = st.selectbox("Soil type", ["Black soil", "Loamy", "Sandy", "Clayey", "Unknown"])
    ph = st.number_input("Soil pH (if known)", min_value=0.0, max_value=14.0, value=7.0, step=0.1)
    water = st.selectbox("Water availability", ["Reliable irrigation", "Limited irrigation", "Rain-fed"])
    season = st.selectbox("Season / planning period", ["Kharif", "Rabi", "Summer", "Year-round / perennial"])
    budget = st.number_input("Approximate input budget (₹)", min_value=0, max_value=100000000, value=15000, step=1000)

st.info("This is a student decision-support prototype. AI suggestions are not guaranteed farming advice.")

# ---------- Weather ----------
st.subheader("1. Weather snapshot")
weather, weather_error = get_weather(location.strip()) if location.strip() else (None, "Enter a town or city.")
weather_summary = "Weather unavailable."
if weather:
    current = weather["data"].get("current", {})
    daily = weather["data"].get("daily", {})
    weather_summary = (
        f"Location matched: {weather['place'].get('name')}, {weather['place'].get('country')}. "
        f"Temperature {current.get('temperature_2m')} °C; humidity {current.get('relative_humidity_2m')}%; "
        f"precipitation now {current.get('precipitation')} mm; wind {current.get('wind_speed_10m')} km/h. "
        f"Forecast dates: {daily.get('time')}; max temperatures: {daily.get('temperature_2m_max')}; "
        f"min temperatures: {daily.get('temperature_2m_min')}; rain probabilities: "
        f"{daily.get('precipitation_probability_max')}; forecast precipitation sums: {daily.get('precipitation_sum')}."
    )
    cols = st.columns(4)
    cols[0].metric("Temperature", f"{current.get('temperature_2m', '—')} °C")
    cols[1].metric("Humidity", f"{current.get('relative_humidity_2m', '—')}%")
    cols[2].metric("Precipitation now", f"{current.get('precipitation', '—')} mm")
    cols[3].metric("Wind speed", f"{current.get('wind_speed_10m', '—')} km/h")
    if daily.get("time"):
        forecast = pd.DataFrame({
            "Date": daily.get("time", []),
            "Max temp (°C)": daily.get("temperature_2m_max", []),
            "Min temp (°C)": daily.get("temperature_2m_min", []),
            "Rain probability (%)": daily.get("precipitation_probability_max", []),
            "Forecast rain (mm)": daily.get("precipitation_sum", []),
        })
        st.dataframe(forecast, use_container_width=True, hide_index=True)
else:
    st.warning(weather_error)

# ---------- Planning dashboard ----------
st.subheader("2. Farm planning dashboard")
left, right = st.columns(2)
with left:
    st.markdown("**Farm profile summary**")
    st.json({
        "Location": location, "Crop": crop, "Area (acres)": area, "Soil": soil,
        "Soil pH": ph, "Water availability": water, "Season": season, "Budget (₹)": budget
    })
with right:
    reserve = budget * 0.10
    budget_df = pd.DataFrame({
        "Category": ["Illustrative planning reserve (10%)", "Remaining budget"],
        "Amount (₹)": [reserve, budget - reserve],
    })
    st.plotly_chart(px.pie(budget_df, names="Category", values="Amount (₹)", title="Illustrative budget overview"),
                    use_container_width=True)
    st.caption("The 10% reserve is only an example, not a crop-specific recommendation.")

# ---------- Market price comparison ----------
st.subheader("3. Market price comparison")
st.caption("Enter prices from a verified local source. These values are not automatically fetched or verified.")
default_rows = [
    {"Market": "Enter local market name", "Price (₹/quintal)": 0},
    {"Market": "Second market (optional)", "Price (₹/quintal)": 0},
]
market_df = pd.DataFrame(st.session_state.get("market_rows", default_rows))
edited = st.data_editor(market_df, num_rows="dynamic", use_container_width=True, key="market_table")
prices_clean = pd.DataFrame()
if not edited.empty and "Price (₹/quintal)" in edited.columns:
    prices_clean = edited.copy()
    prices_clean["Price (₹/quintal)"] = pd.to_numeric(prices_clean["Price (₹/quintal)"], errors="coerce")
    prices_clean = prices_clean[prices_clean["Price (₹/quintal)"] > 0]
    if not prices_clean.empty:
        c1, c2 = st.columns(2)
        c1.metric("Highest entered price", f"₹{prices_clean['Price (₹/quintal)'].max():,.0f}/quintal")
        c2.metric("Average entered price", f"₹{prices_clean['Price (₹/quintal)'].mean():,.0f}/quintal")
        st.session_state["market_rows"] = edited.to_dict(orient="records")
    else:
        st.caption("Add one or more positive price values to calculate a comparison.")

# ---------- Main AI feature ----------
st.subheader("4. AI Farming Decision Engine")
st.write(
    "This is the main AI feature. It reviews the farm profile, available weather data and entered prices, "
    "then produces a structured explanation with practical checks and next steps."
)
question = st.text_area(
    "Ask a farming-planning question (optional)",
    placeholder="Example: What should I check before planning irrigation for this field?",
    height=90,
)
if st.button("🧠 Generate AI farming decision", type="primary", use_container_width=True):
    api_key = get_api_key()
    if not api_key:
        st.error("AI is not configured yet. Add GEMINI_API_KEY in Streamlit app settings → Secrets.")
    else:
        profile = {
            "location": location, "crop": crop, "area_acres": area, "soil_type": soil,
            "soil_pH": ph, "water_availability": water, "season": season, "budget_INR": budget,
        }
        market_records = prices_clean.to_dict(orient="records") if not prices_clean.empty else []
        prompt = build_prompt(profile, weather_summary, market_records, question.strip())
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            with st.spinner("AI is reviewing your farm details..."):
                response = client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                    contents=prompt,
                )
            answer = (getattr(response, "text", None) or "").strip()
            if answer:
                st.success("AI decision support generated")
                st.markdown(answer)
                st.download_button(
                    "Download AI advisory as text",
                    data=answer,
                    file_name="smart_farming_ai_advisory.txt",
                    mime="text/plain",
                )
            else:
                st.warning("The AI model returned an empty response. Please try again.")
        except Exception as exc:
            st.error("The AI request failed. Check the API key, model availability, and app logs.")
            st.caption(f"Technical detail: {type(exc).__name__}")
st.divider()
st.caption("AI output can be inaccurate. Verify crop, soil, irrigation and market decisions with local agricultural experts and official sources.")
