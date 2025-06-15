# plots/chart_utils.py
import streamlit as st
import plotly.express as px

def plot_facility_bar_chart(df):
    count_by_facility = df["facility_name"].value_counts().reset_index()
    count_by_facility.columns = ["facility_name", "count"]

    fig = px.bar(
        count_by_facility,
        y="facility_name",
        x="count",
        orientation="h",
        color_discrete_sequence=["#3366CC"]
    )
    fig.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="",
        margin=dict(l=10, r=10, t=30, b=30),
    )
    fig.update_traces(textposition='outside', texttemplate='%{x}', insidetextanchor="end")

    st.plotly_chart(fig, use_container_width=True)
