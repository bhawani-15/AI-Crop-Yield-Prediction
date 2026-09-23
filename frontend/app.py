import os
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# Configure page layout and meta
st.set_page_config(
    page_title="AI Crop Yield Forecasting | KrishiDrishti",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich, state-of-the-art agricultural theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Main Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #134e4a 0%, #064e3b 50%, #042f2e 100%);
        border-radius: 16px;
        padding: 24px 32px;
        color: #f0fdf4;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(6, 78, 59, 0.25);
        border: 1px solid rgba(52, 211, 153, 0.2);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #a7f3d0;
        margin-bottom: 0px;
    }
    
    /* Metric Cards - Sleek Glassmorphism */
    .metric-card {
        background: rgba(30, 41, 59, 0.75);
        border-radius: 14px;
        padding: 20px;
        border: 1px solid rgba(148, 163, 184, 0.25);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        backdrop-filter: blur(8px);
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        border-color: rgba(52, 211, 153, 0.4);
    }
    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #f8fafc;
        white-space: nowrap;
    }
    .metric-subtext {
        font-size: 0.85rem;
        color: #34d399;
        font-weight: 500;
        margin-top: 4px;
    }
    
    /* Weather Box */
    .weather-container {
        background: rgba(30, 41, 59, 0.75);
        border-radius: 14px;
        padding: 20px;
        border: 1px solid rgba(148, 163, 184, 0.25);
        margin-bottom: 16px;
        color: #f8fafc;
        backdrop-filter: blur(8px);
    }
    .advisory-badge {
        background-color: rgba(6, 78, 59, 0.8);
        color: #6ee7b7;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.92rem;
        border: 1px solid rgba(52, 211, 153, 0.3);
        display: inline-block;
        margin-top: 8px;
    }
    
    /* Clean button styling */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
        font-weight: 600;
        font-size: 1.05rem;
        border-radius: 10px;
        padding: 12px 24px;
        border: none;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.35);
        transition: all 0.2s ease;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #047857 0%, #065f46 100%);
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.45);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# Backend API Configuration
DEFAULT_API_URL = "http://127.0.0.1:8000"

# Sidebar Configuration
st.sidebar.markdown("### ⚙️ System Configuration")
api_base_url = st.sidebar.text_input("FastAPI Base URL", value=DEFAULT_API_URL).rstrip("/")

# Check API health
api_online = False
try:
    health_resp = requests.get(f"{api_base_url}/health", timeout=2)
    if health_resp.status_code == 200:
        api_online = True
        st.sidebar.success("🟢 FastAPI Backend Connected")
    else:
        st.sidebar.warning("🟡 Backend returned non-200 status")
except Exception:
    st.sidebar.error("🔴 FastAPI Backend Offline (Start `uvicorn backend.main:app`)")

# Fetch metadata
@st.cache_data(ttl=300)
def fetch_metadata(base_url: str):
    try:
        resp = requests.get(f"{base_url}/api/metadata", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

metadata = fetch_metadata(api_base_url) if api_online else None

# Fallback lists if API is not yet loaded
if not metadata:
    sample_states = ["Punjab", "Haryana", "Andhra Pradesh", "Maharashtra", "Uttar Pradesh", "Madhya Pradesh"]
    sample_districts = {"Punjab": ["Ludhiana", "Amritsar", "Patiala", "Bathinda", "Jalandhar"]}
    sample_crops = ["Wheat", "Rice", "Maize", "Cotton", "Sugarcane", "Bajra", "Gram", "Moong"]
    sample_seasons = ["Kharif", "Rabi", "Summer", "Autumn", "Winter"]
else:
    sample_states = metadata["states"]
    sample_districts = metadata["state_to_districts"]
    sample_crops = metadata["crops"]
    sample_seasons = metadata["seasons"]

# Sidebar Selection Form
st.sidebar.markdown("---")
st.sidebar.markdown("### 🌾 Target Crop & Geography")

selected_state = st.sidebar.selectbox("1. State", sample_states, index=sample_states.index("Punjab") if "Punjab" in sample_states else 0)

available_districts = sample_districts.get(selected_state, ["All Districts"])
default_district_idx = available_districts.index("Ludhiana") if "Ludhiana" in available_districts else 0
selected_district = st.sidebar.selectbox("2. District", available_districts, index=default_district_idx)

default_crop_idx = sample_crops.index("Wheat") if "Wheat" in sample_crops else 0
selected_crop = st.sidebar.selectbox("3. Crop", sample_crops, index=default_crop_idx)

default_season_idx = sample_seasons.index("Rabi") if "Rabi" in sample_seasons else 0
selected_season = st.sidebar.selectbox("4. Season", sample_seasons, index=default_season_idx)

selected_year = st.sidebar.number_input("5. Forecast Target Year", min_value=2024, max_value=2030, value=2025, step=1)

with st.sidebar.expander("🛠️ Advanced Settings (Lag Yield)"):
    custom_lag_toggle = st.checkbox("Manual Prior-Year Yield Override", value=False)
    custom_lag_val = None
    if custom_lag_toggle:
        custom_lag_val = st.number_input("Prior Year Yield (kg/ha)", min_value=10.0, max_value=25000.0, value=4500.0, step=50.0)

predict_clicked = st.sidebar.button("🚀 Forecast Crop Yield")

# Hero Banner
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🌾 KrishiDrishti: AI Agricultural Intelligence</div>
    <div class="hero-subtitle">District-Level Multi-Source Crop Yield Forecasting & Live Agro-Climatic Advisory Engine</div>
</div>
""", unsafe_allow_html=True)

# Main App Logic
if not api_online:
    st.info("💡 **Backend Service Notice**: Please ensure the FastAPI backend is running via `uvicorn backend.main:app --port 8000 --reload` in your terminal.")

# Trigger prediction on initial load or button click
if "prediction_data" not in st.session_state or predict_clicked:
    if api_online:
        with st.spinner("Analyzing historical patterns, district productivity, and agro-climatic trends..."):
            try:
                # 1. Prediction API call
                payload = {
                    "state": selected_state,
                    "district": selected_district,
                    "crop": selected_crop,
                    "season": selected_season,
                    "year": int(selected_year),
                    "custom_lag_yield": custom_lag_val if custom_lag_toggle else None
                }
                pred_res = requests.post(f"{api_base_url}/api/predict", json=payload, timeout=8)
                if pred_res.status_code == 200:
                    st.session_state["prediction_data"] = pred_res.json()
                else:
                    st.error(f"Prediction Error: {pred_res.text}")

                # 2. Weather API call
                weather_res = requests.get(
                    f"{api_base_url}/api/weather",
                    params={"district": selected_district, "state": selected_state},
                    timeout=6
                )
                if weather_res.status_code == 200:
                    st.session_state["weather_data"] = weather_res.json()

                # 3. Historical Trends API call
                trends_res = requests.get(
                    f"{api_base_url}/api/historical-trends",
                    params={"district": selected_district, "state": selected_state, "crop": selected_crop},
                    timeout=6
                )
                if trends_res.status_code == 200:
                    st.session_state["trends_data"] = trends_res.json()

            except Exception as e:
                st.error(f"Error communicating with backend: {e}")

# Display Results if available
pred_data = st.session_state.get("prediction_data")
weather_data = st.session_state.get("weather_data")
trends_data = st.session_state.get("trends_data")

if pred_data:
    # 1. Top KPI Summary Grid
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Forecasted Yield</div>
            <div class="metric-value">{pred_data['predicted_yield_kg_ha']:,} <span style="font-size: 1.1rem; color:#64748b;">kg/ha</span></div>
            <div class="metric-subtext">Confidence: {pred_data['confidence_level']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Indian Farming Unit</div>
            <div class="metric-value">{pred_data['predicted_yield_quintal_acre']} <span style="font-size: 1.1rem; color:#64748b;">Qtl/Acre</span></div>
            <div class="metric-subtext">Standard Farm Benchmark</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        delta_dist = pred_data.get('delta_vs_district_pct')
        dist_avg = pred_data.get('district_avg_yield')
        color = "#10b981" if (delta_dist or 0) >= 0 else "#ef4444"
        symbol = "+" if (delta_dist or 0) >= 0 else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Vs District History</div>
            <div class="metric-value" style="color: {color};">{symbol}{delta_dist if delta_dist is not None else 0.0}%</div>
            <div class="metric-subtext" style="color: #64748b;">Avg: {dist_avg or 'N/A'} kg/ha</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        delta_state = pred_data.get('delta_vs_state_pct')
        state_avg = pred_data.get('state_avg_yield')
        color_st = "#10b981" if (delta_state or 0) >= 0 else "#ef4444"
        symbol_st = "+" if (delta_state or 0) >= 0 else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Vs State Average</div>
            <div class="metric-value" style="color: {color_st};">{symbol_st}{delta_state if delta_state is not None else 0.0}%</div>
            <div class="metric-subtext" style="color: #64748b;">State Avg: {state_avg or 'N/A'} kg/ha</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs for in-depth insights
    tab_weather, tab_shap, tab_history, tab_model = st.tabs([
        "🌦️ Live Agro-Weather & Advisory",
        "🔍 AI Explainability (SHAP)",
        "📈 Historical Yield Trends",
        "🧠 Model Architecture & Metrics"
    ])

    # TAB 1: WEATHER
    with tab_weather:
        if weather_data:
            w_col1, w_col2 = st.columns([1.2, 1.8])

            with w_col1:
                st.markdown(f"""
                <div class="weather-container">
                    <h4 style="margin-top:0; color:#f8fafc;">📍 {weather_data['district']}, {weather_data['state']}</h4>
                    <p style="font-size: 1.1rem; font-weight:600; color:#38bdf8; margin-bottom: 12px;">
                        Condition: {weather_data['weather_condition']}
                    </p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; color:#e2e8f0;">
                        <div>🌡️ <b>Temp:</b> {weather_data['current_temperature']}°C</div>
                        <div>💧 <b>Humidity:</b> {weather_data['current_humidity']}%</div>
                        <div>🌧️ <b>Precipitation:</b> {weather_data['current_precipitation']} mm</div>
                        <div>💨 <b>Wind:</b> {weather_data['current_wind_speed']} km/h</div>
                    </div>
                    <div class="advisory-badge">
                        🌱 <b>Advisory:</b> {weather_data['agricultural_advisory']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with w_col2:
                # 7-day forecast chart
                forecast_list = weather_data.get("daily_forecast", [])
                if forecast_list:
                    df_w = pd.DataFrame(forecast_list)
                    fig_w = go.Figure()
                    fig_w.add_trace(go.Scatter(
                        x=df_w["date"], y=df_w["temp_max"],
                        mode="lines+markers", name="Max Temp (°C)",
                        line=dict(color="#f97316", width=3)
                    ))
                    fig_w.add_trace(go.Scatter(
                        x=df_w["date"], y=df_w["temp_min"],
                        mode="lines+markers", name="Min Temp (°C)",
                        line=dict(color="#0284c7", width=2, dash="dot")
                    ))
                    fig_w.add_trace(go.Bar(
                        x=df_w["date"], y=df_w["precipitation_sum"],
                        name="Rainfall (mm)", marker_color="rgba(14, 165, 233, 0.4)",
                        yaxis="y2"
                    ))
                    fig_w.update_layout(
                        title=f"7-Day Weather Forecast for {selected_district}",
                        xaxis_title="Date",
                        yaxis=dict(title="Temperature (°C)"),
                        yaxis2=dict(title="Precipitation (mm)", overlaying="y", side="right"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=290,
                        margin=dict(l=40, r=40, t=40, b=30),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_w, use_container_width=True)
        else:
            st.warning("Live weather data currently unavailable.")

    # TAB 2: SHAP EXPLAINABILITY
    with tab_shap:
        st.markdown("#### 🔬 Why Did the AI Make This Prediction?")
        st.caption("SHAP (SHapley Additive exPlanations) isolates the exact impact of each feature on the final yield calculation.")

        shap_list = pred_data.get("shap_feature_importance", [])
        if shap_list:
            df_shap = pd.DataFrame(shap_list)
            # Create colorful bar chart
            colors = ["#10b981" if x >= 0 else "#ef4444" for x in df_shap["impact"]]
            fig_shap = go.Figure(go.Bar(
                x=df_shap["impact"],
                y=df_shap["feature_name_clean"],
                orientation='h',
                marker=dict(color=colors),
                text=[f"{'+' if x>0 else ''}{x:.1f} kg/ha" for x in df_shap["impact"]],
                textposition='outside'
            ))
            fig_shap.update_layout(
                title=f"Feature Contributions for {selected_crop} in {selected_district} ({selected_year})",
                xaxis_title="Impact on Yield Prediction (kg/ha)",
                yaxis=dict(autorange="reversed"),
                height=350,
                margin=dict(l=40, r=60, t=50, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_shap, use_container_width=True)

            st.markdown(f"""
            - **Persistence Factor (`lag_yield`)**: The prior recorded yield was **{pred_data['lag_yield_used']} kg/ha**, providing the foundational productivity anchor.
            - **District & State Calibration**: Historical agricultural productivity of **{selected_district}** and **{selected_state}** adjusts the expected output up or down.
            """)
        else:
            st.info("SHAP explainability details will be calculated on subsequent runs.")

    # TAB 3: HISTORICAL TRENDS
    with tab_history:
        if trends_data and trends_data.get("trends"):
            df_trends = pd.DataFrame(trends_data["trends"])
            st.markdown(f"#### 📊 Historical Yield Progression: {selected_crop} in {selected_district}")

            t_col1, t_col2, t_col3 = st.columns(3)
            t_col1.metric("Historical Peak", f"{trends_data.get('max_yield'):,} kg/ha")
            t_col2.metric("Historical Low", f"{trends_data.get('min_yield'):,} kg/ha")
            t_col3.metric("Multi-Year Average", f"{trends_data.get('avg_yield'):,} kg/ha")

            fig_trend = px.area(
                df_trends,
                x="year",
                y="yield_kg_ha",
                markers=True,
                labels={"year": "Crop Year", "yield_kg_ha": "Yield (kg/ha)"},
                title=f"Yield Trend (2016 - 2024)"
            )
            fig_trend.update_traces(
                line_color="#059669",
                fillcolor="rgba(16, 185, 129, 0.15)"
            )
            fig_trend.update_layout(
                height=320,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=40, r=40, t=40, b=30)
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info(f"No previous longitudinal records found for {selected_crop} in {selected_district}.")

    # TAB 4: MODEL ARCHITECTURE
    with tab_model:
        st.markdown("#### 🧠 Model Benchmarking & Architecture")
        st.markdown("""
        The underlying AI engine was trained on **77,000+ government census records (DES)** spanning 2016 to 2024 across 30+ states and union territories.
        """)

        metrics_data = {
            "Model Candidate": [
                "Linear Regression (Baseline)",
                "Random Forest (Unconstrained)",
                "Random Forest (Regularized)",
                "XGBoost Regressor (Selected Best)"
            ],
            "Train R²": [0.789, 0.983, 0.870, 0.879],
            "Holdout Test R²": [0.849, 0.852, 0.858, 0.865],
            "Test RMSE (kg/ha)": [518.9, 514.3, 503.6, 491.4],
            "Status": ["Baseline", "Overfit", "Strong", "🏆 Deployed Model"]
        }
        st.table(pd.DataFrame(metrics_data))
        st.caption("Validation conducted using a chronological holdout (Train: 2016–2022, Test: 2023–2024) to eliminate temporal data leakage.")
