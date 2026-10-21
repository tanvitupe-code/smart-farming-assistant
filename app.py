import os
import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Smart Farming Decision Assistant", page_icon="🌱", layout="wide")

st.title("🌱 Smart Farming Decision Assistant")
st.caption("A decision-support prototype for crop planning, weather awareness, and farm-market context.")

with st.sidebar:
    st.header("Farm profile")
    location = st.text_input("Town / city", value="Baramati")
    crop = st.selectbox("Crop", ["Sugarcane", "Cotton", "Soybean", "Tomato", "Onion", "Potato", "Wheat", "Other"])
    area_acres = st.number_input("Farm area (acres)", min_value=0.1, max_value=10000.0, value=2.0, step=0.5)
    soil_type = st.selectbox("Soil type", ["Black soil", "Loamy", "Sandy", "Clayey", "Unknown"])
    soil_ph = st.number_input("Soil pH (if known)", min_value=0.0, max_value=14.0, value=7.0, step=0.1)
    water_source = st.selectbox("Water availability", ["Reliable irrigation", "Limited irrigation", "Rain-fed"])
    season = st.selectbox("Season / planning period", ["Kharif", "Rabi", "Summer", "Year-round / perennial"])
    budget_inr = st.number_input("Approximate input budget (₹)", min_value=0, max_value=100000000, value=15000, step=1000)

st.subheader("1. Weather snapshot")
def get_weather(city):
    """Fetch current weather from Open-Meteo geocoding + forecast APIs (no API key required)."""
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=12
        )
        geo.raise_for_status()
        results = geo.json().get("results", [])
        if not results:
            return None, f"No location found for '{city}'. Check spelling or use a nearby larger town."
        place = results[0]
        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": 3
            },
            timeout=12
        )
        wx.raise_for_status()
        return {"place": place, "data": wx.json()}, None
    except requests.RequestException as exc:
        return None, f"Weather service is temporarily unavailable: {exc}"

weather, weather_error = get_weather(location)
if weather:
    current = weather["data"].get("current", {})
    daily = weather["data"].get("daily", {})
    cols = st.columns(4)
    cols[0].metric("Temperature", f'{current.get("temperature_2m", "—")} °C')
    cols[1].metric("Relative humidity", f'{current.get("relative_humidity_2m", "—")} %')
    cols[2].metric("Precipitation", f'{current.get("precipitation", "—")} mm')
    cols[3].metric("Wind speed", f'{current.get("wind_speed_10m", "—")} km/h')
    if daily.get("time"):
        forecast_df = pd.DataFrame({
            "Date": daily.get("time", []),
            "Max temperature (°C)": daily.get("temperature_2m_max", []),
            "Min temperature (°C)": daily.get("temperature_2m_min", []),
            "Rain probability (%)": daily.get("precipitation_probability_max", [])
        })
        st.dataframe(forecast_df, use_container_width=True, hide_index=True)
else:
    st.warning(weather_error or "Weather data not available.")
    st.info("You can still use the planning features below. Weather data requires an internet connection.")

st.subheader("2. Planning indicators")
left, right = st.columns(2)
with left:
    st.markdown("**Farm profile summary**")
    st.write({
        "Location": location,
        "Crop selected": crop,
        "Farm area (acres)": area_acres,
        "Soil type": soil_type,
        "Soil pH": soil_ph,
        "Water availability": water_source,
        "Season": season,
        "Budget (₹)": budget_inr
    })
with right:
    st.markdown("**Input budget overview**")
    estimated_reserve = budget_inr * 0.10
    operating_budget = budget_inr - estimated_reserve
    budget_df = pd.DataFrame({"Category": ["Planning reserve (10%)", "Remaining budget"], "Amount (₹)": [estimated_reserve, operating_budget]})
    fig = px.pie(budget_df, names="Category", values="Amount (₹)", title="Illustrative budget split")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("The 10% reserve is a planning assumption, not a crop-specific recommendation.")

st.subheader("3. Market price comparison")
st.write("Enter verified local mandi prices. The demo does not claim that these figures are live market data.")
market_rows = st.session_state.get("market_rows", [
    {"Market": "Example Market A", "Price (₹/quintal)": 2500},
    {"Market": "Example Market B", "Price (₹/quintal)": 2700},
    {"Market": "Example Market C", "Price (₹/quintal)": 2400},
])
edited_market = st.data_editor(pd.DataFrame(market_rows), num_rows="dynamic", use_container_width=True, key="market_editor")
if not edited_market.empty and "Price (₹/quintal)" in edited_market.columns:
    clean_prices = pd.to_numeric(edited_market["Price (₹/quintal)"], errors="coerce").dropna()
    if not clean_prices.empty:
        st.metric("Highest entered price", f"₹{clean_prices.max():,.0f}/quintal")
        st.metric("Average entered price", f"₹{clean_prices.mean():,.0f}/quintal")
        st.caption("Market data is user-entered demonstration data until connected to a verified official feed.")

st.subheader("4. AI-generated farming advisory")
st.write("The AI feature is optional. Without an API key, the app still demonstrates weather retrieval, farm profile capture, and market-price analysis.")
if st.button("Generate advisory", type="primary"):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        st.warning("Add GEMINI_API_KEY to your .env file to enable generative AI. No key is needed for the other features.")
    else:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            weather_summary = "Weather unavailable."
            if weather:
                c = weather["data"].get("current", {})
                weather_summary = (
                    f"Temperature: {c.get('temperature_2m')} C; humidity: "
                    f"{c.get('relative_humidity_2m')}%; precipitation: {c.get('precipitation')} mm; "
                    f"wind: {c.get('wind_speed_10m')} km/h."
                )
            prompt = f"""
You are an agricultural information assistant. Provide cautious, practical, non-prescriptive planning guidance.
Farm profile:
Location: {location}
Crop: {crop}
Area: {area_acres} acres
Soil: {soil_type}; pH: {soil_ph}
Water: {water_source}
Season: {season}
Budget: INR {budget_inr}
Weather snapshot: {weather_summary}
Market price entries supplied by user: {edited_market.to_dict(orient='records')}
Give: (1) summary of the supplied inputs, (2) weather considerations, (3) questions the farmer should verify locally,
(4) budget-planning cautions, (5) market-price interpretation only for user-entered data.
Do not invent live prices, yields, pesticide/fertilizer dosages, or guaranteed profit. Explain that advice must be verified
with local agricultural officers/KVK and soil-test results. If information is insufficient, say so clearly.
"""
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=prompt
            )
            st.markdown(response.text or "The model returned an empty response.")
        except Exception as exc:
            st.error(f"Could not generate the AI advisory: {exc}")
            st.caption("Check the API key, model availability, internet connection, and package versions.")

st.divider()
st.caption("Educational prototype only. Verify weather, prices, crop suitability, and all agronomic actions with official local sources or a qualified agricultural expert.")
