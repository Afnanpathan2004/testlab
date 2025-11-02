"""Reusable Plotly chart components for Streamlit UI."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_score_distribution(df: pd.DataFrame, title: str = "Score Distribution") -> None:
    if df is None or df.empty:
        st.info("No data to display")
        return
    fig = px.histogram(df, x="score", nbins=20, title=title, color_discrete_sequence=["#2E86AB"])
    fig.update_layout(bargap=0.05, xaxis_title="Score (%)", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)


def render_pre_post_comparison(pre_scores: pd.Series, post_scores: pd.Series) -> None:
    fig = go.Figure()
    fig.add_trace(go.Box(y=pre_scores, name="Pre-Test", marker_color="#AB342E"))
    fig.add_trace(go.Box(y=post_scores, name="Post-Test", marker_color="#2E8B57"))
    fig.update_layout(title="Pre vs Post Score Comparison", yaxis_title="Score (%)")
    st.plotly_chart(fig, use_container_width=True)


def render_top_performers(df: pd.DataFrame, limit: int = 5) -> None:
    if df is None or df.empty:
        st.info("No data to display")
        return
    agg = df.groupby("student_id")["score"].mean().sort_values(ascending=False).head(limit).reset_index()
    fig = px.bar(
        agg,
        x="student_id",
        y="score",
        color="score",
        color_continuous_scale="Blues",
        title=f"Top {min(limit, len(agg))} Performers",
    )
    fig.update_layout(xaxis_title="Student ID", yaxis_title="Average Score (%)")
    st.plotly_chart(fig, use_container_width=True)


def render_student_performance_table(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        st.info("No data to display")
        return
    agg = (
        df.groupby("student_id")["score"]
        .agg(["mean", "count", "max", "min"])  # type: ignore[attr-defined]
        .reset_index()
        .rename(columns={"student_id": "Student", "mean": "Avg Score", "count": "Tests Taken", "max": "Highest", "min": "Lowest"})
    )
    agg["Avg Score"] = agg["Avg Score"].round(1)
    st.dataframe(agg, use_container_width=True)
