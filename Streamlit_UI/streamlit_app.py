import json
import os
import re

import requests
import streamlit as st

API_URL = os.environ.get("SME_API_URL", "").strip()


def summarize_logs(prompt):
    """Call the configured API and decode its non-proxy Lambda response."""
    words = re.findall(r"[^\W\d_]+", prompt) if isinstance(prompt, str) else []
    if len(words) < 2 or sum(len(word) for word in words) < 6:
        raise ValueError("Please provide valid equipment logs describing an equipment condition or incident.")
    response = requests.post(API_URL, json={"prompt": prompt}, timeout=(5, 35))
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        result = payload.get("body")
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                pass
        if payload.get("statusCode", 200) != 200:
            if payload.get("statusCode") == 400 and isinstance(result, dict):
                raise ValueError(result.get("error", "Please provide valid equipment logs."))
            raise ValueError("The analysis service could not process these logs.")
    else:
        result = payload
    if not isinstance(result, str) or not result.strip():
        raise ValueError("The analysis service returned an unexpected response.")
    return result.strip()


EXAMPLE_LOG = """Equipment: Turbine WT-101
Date: 2026-10-21, 10:00
Issue: Gearbox temperature reached 105 C and the turbine stopped.
Observation: The oil filter was clogged.
Action: Replaced the filter; the turbine restarted at 10:20.
Downtime: 20 minutes.
Production loss: Not measured."""


def load_example():
    st.session_state.equipment_logs = EXAMPLE_LOG
    st.session_state.pop("analysis", None)
    st.session_state.pop("analyzed_prompt", None)


def clear_workspace():
    st.session_state.equipment_logs = ""
    st.session_state.pop("analysis", None)
    st.session_state.pop("analyzed_prompt", None)


st.set_page_config(page_title="Equipment SME", page_icon="🌬", layout="centered")
st.markdown(
    """
    <style>
    .block-container { max-width: 850px; padding-top: 2.5rem; }
    h1 { letter-spacing: -1px; }
    [data-testid="stTextArea"] textarea { border-radius: 10px; font-size: 15px; line-height: 1.6; }
    [data-testid="stButton"] button { border-radius: 8px; }
    [data-testid="stButton"] button[kind="primary"] { background: #087f75; border-color: #087f75; color: white; }
    [data-testid="stButton"] button[kind="primary"]:hover { background: #06675f; border-color: #06675f; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Equipment Log Assistant")
st.write("Enter your wind turbine logs to get a simple summary.")

example_col, clear_col, _ = st.columns([1, 1, 2])
example_col.button("Load example", on_click=load_example, use_container_width=True)
clear_col.button("Clear", on_click=clear_workspace, use_container_width=True)

prompt = st.text_area(
    "Equipment logs",
    key="equipment_logs",
    height=240,
    placeholder="Describe the equipment, what happened, and any action taken.",
)
st.caption("Describe the issue and any action taken. Select Load example if you need help getting started.")

if not API_URL:
    st.info("The analysis service has not been configured yet.")

if st.button("Analyze", type="primary", disabled=not API_URL, use_container_width=True):
    st.session_state.pop("analysis", None)
    st.session_state.pop("analyzed_prompt", None)
    if not prompt.strip():
        st.warning("Enter equipment logs or select Load example to get started.")
    else:
        with st.spinner("Analyzing your logs..."):
            try:
                result = summarize_logs(prompt.strip())
                if result.startswith("Please provide valid equipment logs"):
                    st.warning(result)
                    st.caption("Select Load example to see the expected format.")
                else:
                    st.session_state.analysis = result
                    st.session_state.analyzed_prompt = prompt.strip()
            except requests.exceptions.Timeout:
                st.error("The analysis timed out. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("Unable to reach the analysis service. Check your connection.")
            except requests.exceptions.HTTPError as error:
                if error.response is not None and error.response.status_code == 504:
                    st.error("The analysis service timed out. Please try again.")
                else:
                    st.error("The analysis service could not process the request.")
            except requests.exceptions.RequestException:
                st.error("Unable to complete the analysis request.")
            except ValueError as error:
                st.error(str(error))
                st.caption("Select Load example to see the expected format.")

if "analysis" in st.session_state:
    st.divider()
    st.subheader("Summary")
    if prompt.strip() != st.session_state.get("analyzed_prompt"):
        st.warning("Your logs have changed. Select Analyze to update the summary.")
    st.markdown(st.session_state.analysis)
    st.caption("AI-generated summary. Verify the findings against your original records.")
