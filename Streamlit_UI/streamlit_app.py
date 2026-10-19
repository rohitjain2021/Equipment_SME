import streamlit as st
import requests
import json

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
        "",
        height=120,
        placeholder="Paste the Equipment Logs...",
        label_visibility="collapsed"
    )

    if st.button("Summarize"):

        if prompt.strip():

            with st.spinner("Analyzing equipment data..."):

                try:
                    # -----------------------------------------
                    # Call API Gateway / Lambda
                    # -----------------------------------------
                    response = requests.post(
                        "https://ozpc8pljx5.execute-api.us-east-1.amazonaws.com/Prod/",
                        json={
                            "prompt": prompt
                        },
                        timeout=60
                    )

                    # -----------------------------------------
                    # Successful API response
                    # -----------------------------------------
                    if response.status_code == 200:

                        response_data = response.json()

                        # Handle Lambda/API Gateway response
                        if (
                            isinstance(response_data, dict)
                            and "body" in response_data
                        ):
                            try:
                                result = json.loads(
                                    response_data["body"]
                                )
                            except (json.JSONDecodeError, TypeError):
                                result = response_data["body"]

                        else:
                            result = response_data

                        # Ensure output is a string
                        result = str(result).strip()

                        # -----------------------------------------
                        # Fix bullet formatting
                        # -----------------------------------------
                        # Handles output like:
                        # - point 1 - point 2 - point 3
                        result = result.replace(
                            " - ",
                            "\n- "
                        )

                        # Remove accidental escaped bullet characters
                        result = result.replace(
                            "\\- ",
                            "- "
                        )

                        # -----------------------------------------
                        # Display response
                        # -----------------------------------------
                        st.markdown(
                            """
                            <div class='analysis-title'>
                                Expert Analysis:
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Important:
                        # Render model output as Markdown,
                        # not inside a raw HTML div.
                        st.markdown(result)

                    # -----------------------------------------
                    # API error
                    # -----------------------------------------
                    else:
                        st.error(
                            f"System Error: Unable to process request "
                            f"(Status: {response.status_code})"
                        )

                        # Useful during development
                        if response.text:
                            st.caption(response.text)

                except requests.exceptions.Timeout:
                    st.error(
                        "The request timed out while waiting for the AI service."
                    )

                except requests.exceptions.ConnectionError:
                    st.error(
                        "Unable to connect to the API. "
                        "Check the API Gateway endpoint and network connection."
                    )

                except Exception as e:
                    st.error(
                        f"Error: {str(e)}"
                    )

        else:
            st.warning(
                "Please enter equipment logs to proceed."
            )

st.markdown(
    "</div>",
    unsafe_allow_html=True
)