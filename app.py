"""app.py - Streamlit user interface.

Run:  streamlit run app.py
It calls the FastAPI backend (API_URL). If the API is not running, it falls back to
the same analytics engine locally, and says so on screen.
"""
from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st

from analytics import SUPPORTED_EXAMPLES, answer_question
from db import DatabaseNotReady

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Mini AI BI Assistant", page_icon="📊", layout="centered")
st.title("📊 Mini AI Business Intelligence Assistant")
st.write(
    "Ask a question about the **sales dataset** in plain English. Every answer is "
    "calculated from the SQLite database, not typed in by hand."
)


def set_question(text: str) -> None:
    st.session_state["question"] = text


def ask_backend(question: str) -> tuple[dict, str]:
    """Try the FastAPI backend first, then the local engine."""
    try:
        resp = requests.post(f"{API_URL}/ask", json={"question": question}, timeout=30)
        if resp.status_code == 200:
            return resp.json(), f"FastAPI backend ({API_URL})"
        detail = resp.json().get("detail", resp.text) if resp.content else resp.text
        raise RuntimeError(f"API error {resp.status_code}: {detail}")
    except requests.exceptions.ConnectionError:
        return answer_question(question), "local engine (API not running)"


st.subheader("Try an example")
cols = st.columns(2)
for i, example in enumerate(SUPPORTED_EXAMPLES):
    cols[i % 2].button(example, key=f"ex{i}", on_click=set_question, args=(example,))

with st.form("ask_form"):
    question = st.text_input("Your question", key="question", placeholder="e.g. Which region has the highest sales?")
    submitted = st.form_submit_button("Ask")

if submitted:
    if not question.strip():
        st.warning("Please type a question first.")
    else:
        try:
            with st.spinner("Querying the database..."):
                result, source = ask_backend(question)
        except DatabaseNotReady as exc:
            st.error(f"{exc}")
        except Exception as exc:
            st.error(f"Something went wrong: {exc}")
        else:
            if result["supported"]:
                st.success(result["answer"])
            else:
                st.info(result["answer"])

            if result["rows"]:
                df = pd.DataFrame(result["rows"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                if len(df) > 1 and "total_sales" in df.columns:
                    chart_df = df.set_index(df.columns[0])["total_sales"]
                    if result["intent"] == "monthly_sales":
                        st.line_chart(chart_df)
                    else:
                        st.bar_chart(chart_df)

            with st.expander("How was this calculated?"):
                st.write(result["formula"])
                st.caption(
                    f"Interpreted by: {result['method']} · Answered via: {source}"
                )
                if result["sql"]:
                    st.code(result["sql"], language="sql")

st.caption(
    "Answers are based only on the loaded sales dataset (data/sales_data.csv → data/sales.db)."
)
