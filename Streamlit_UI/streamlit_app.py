import json
import os

import requests
import streamlit as st

API_URL = os.environ.get("SME_API_URL", "").strip()


def summarize_logs(prompt):
    """Call the configured API and decode its non-proxy Lambda response."""
    response = requests.post(API_URL, json={"prompt": prompt}, timeout=(5, 35))
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        if payload.get("statusCode", 200) != 200:
            raise ValueError("The analysis service could not process these logs.")
        result = payload.get("body")
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                pass
    else:
        result = payload
    if not isinstance(result, str) or not result.strip():
        raise ValueError("The analysis service returned an unexpected response.")
    return result.strip()


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Wind Turbine SME Assistant | Enterprise",
    page_icon="⚡",
    layout="wide"
)

# ---------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {
            font-family: 'Inter', sans-serif;
        }

        .main {
            background-color: #f8fafc;
        }

        .stTextArea textarea {
            font-size: 15px;
            border-radius: 8px;
            border: 2px solid #e2e8f0;
            padding: 12px;
        }

        .stTextArea textarea:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .stButton button {
            background-color: #3b82f6;
            color: white;
            border-radius: 8px;
            padding: 10px 32px;
            font-weight: 600;
            border: none;
            transition: all 0.2s;
            font-size: 15px;
        }

        .stButton button:hover {
            background-color: #2563eb;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }

        .header-container {
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        }

        .header-title {
            color: white;
            font-size: 2.5em;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.5px;
        }

        .header-subtitle {
            color: #dbeafe;
            font-size: 1.1em;
            margin-top: 8px;
            font-weight: 500;
        }

        .metric-card {
            background: white;
            padding: 24px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border-left: 4px solid;
            transition: all 0.2s;
        }

        .metric-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
        }

        .metric-icon {
            font-size: 2.5em;
            margin-bottom: 8px;
        }

        .metric-title {
            color: #1e293b;
            font-size: 1em;
            font-weight: 600;
            margin: 0;
        }

        .metric-desc {
            color: #64748b;
            font-size: 0.85em;
            margin-top: 4px;
        }

        .card1 {
            border-left-color: #3b82f6;
        }

        .card2 {
            border-left-color: #10b981;
        }

        .card3 {
            border-left-color: #8b5cf6;
        }

        .query-section {
            background: white;
            padding: 32px;
            border-radius: 10px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            margin: 20px 0;
        }

        .section-label {
            color: #1e293b;
            font-size: 0.95em;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .analysis-title {
            color: #1e293b;
            font-size: 1em;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# Header
# ---------------------------------------------------------
st.markdown(
    """
    <div class='header-container'>
        <div class='header-title'>
            ⚡ Wind Turbine Equipment SME Assistant
        </div>
        <div class='header-subtitle'>
            Enterprise AI-Powered Expert System for Predictive Maintenance & Downtime Reduction
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# Metric cards
# ---------------------------------------------------------
metric_col1, metric_col2, metric_col3 = st.columns(3)

with metric_col1:
    st.markdown(
        """
        <div class='metric-card card1'>
            <div class='metric-icon'>🔧</div>
            <div class='metric-title'>Equipment Diagnostics</div>
            <div class='metric-desc'>Real-time fault detection</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with metric_col2:
    st.markdown(
        """
        <div class='metric-card card2'>
            <div class='metric-icon'>⏱️</div>
            <div class='metric-title'>Reduce Downtime</div>
            <div class='metric-desc'>Minimize operational losses</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with metric_col3:
    st.markdown(
        """
        <div class='metric-card card3'>
            <div class='metric-icon'>🤖</div>
            <div class='metric-title'>AI-Powered Insights</div>
            <div class='metric-desc'>Predictive maintenance</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---------------------------------------------------------
# Query section
# ---------------------------------------------------------
st.markdown(
    "<div class='query-section'>",
    unsafe_allow_html=True
)

st.markdown(
    "<div class='section-label'>Equipment Query</div>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    prompt = st.text_area(
        "Equipment logs",
        height=120,
        placeholder="Paste the Equipment Logs...",
        label_visibility="collapsed"
    )

    if not API_URL:
        st.info("The analysis service has not been configured yet.")

    if st.button("Summarize", disabled=not API_URL):
        if not prompt.strip():
            st.warning("Please enter equipment logs to proceed.")
        else:
            with st.spinner("Analyzing equipment data..."):
                try:
                    result = summarize_logs(prompt.strip())
                    st.markdown("### Expert Analysis")
                    st.markdown(result)
                except requests.exceptions.Timeout:
                    st.error("The analysis timed out. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Unable to reach the analysis service. Check your connection.")
                except requests.exceptions.HTTPError as error:
                    if error.response.status_code == 504:
                        st.error("The analysis service timed out. Please try again.")
                    else:
                        st.error("The analysis service could not process the request.")
                except requests.exceptions.RequestException:
                    st.error("Unable to complete the analysis request.")
                except ValueError as error:
                    st.error(str(error))

st.markdown("</div>", unsafe_allow_html=True)
