# app.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from Scripts.db_utils import initialize_db, ingest_new_data, get_all_data

# ─────────────── INIT
st.set_page_config(page_title="503B Watch", layout="wide")
initialize_db()
ingest_new_data()

# ─────────────── LOAD DATA
df = get_all_data()
if df.empty:
    st.error("Error loading data.")
    st.stop()

df["scanned_date"] = pd.to_datetime(df["scanned_date"], errors="coerce")
df = df.dropna(subset=["scanned_date"])
latest_date = df["scanned_date"].max()
latest_snapshot = df[df["scanned_date"] == latest_date]

# ─────────────── HEADER
st.title("🔍 503B Watch Dashboard")
st.markdown("""
Welcome to **503B Watch**, a community-maintained dashboard for monitoring FDA-registered **503B outsourcing facilities**.

We track inspections, recalls, and facility activity over time using publicly available FDA data.

Built with ❤️ by [**Brittany Campos**](https://www.linkedin.com/in/brittanycampos/)
""")

# ─────────────── TABS
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "🧪 Inspections", "🚨 Recalls", "📄 483s"])


# ═══════════════════════════════════════════════════
# 💡 HELPER: Sparkline Renderer
# ═══════════════════════════════════════════════════
def render_sparkline(chart_df, force_pct=False):
    values = chart_df["value"].values
    x_vals = chart_df["scanned_date"]

    if force_pct:
        yaxis_range = [0, 100]
        hovertemplate = "<b>Week:</b> %{x|%b %d}<br><b>Value:</b> %{y:.1f}%<extra></extra>"
    else:
        yaxis_range = None
        hovertemplate = "<b>Week:</b> %{x|%b %d}<br><b>Count:</b> %{y:.0f}<extra></extra>"

    norm = (values - values.min()) / (values.max() - values.min() + 1e-9)
    def blue_shade(n): return f"rgba({int(50 + 100 * n)}, {int(130 + 100 * n)}, 255, 1)"
    colors = [blue_shade(x) for x in norm]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=values,
        mode="lines+markers",
        line=dict(color="#1f77b4", width=1),
        marker=dict(size=4, color=colors),
        hovertemplate=hovertemplate
    ))
    fig.update_layout(
        height=45,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, fixedrange=True, range=yaxis_range),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════
# 🏠 HOME TAB
# ═══════════════════════════════════════════════════
with tab1:
    st.markdown("## 📊 This Week in 503B")

    # Time setup
    prior_dates = sorted([d for d in df["scanned_date"].unique() if d < latest_date])
    prior_date = prior_dates[-1] if prior_dates else latest_date
    previous_snapshot = df[df["scanned_date"] == prior_date]
    ytd_df = df[df["scanned_date"].dt.year == latest_date.year]

    def sparkline_data(column, pct=False):
        grouped = ytd_df.copy()
        grouped["value"] = grouped[column].astype(str).str.lower().eq("true") if pct else grouped[column]
        chart_data = grouped.groupby("scanned_date")["value"].agg("mean" if pct else "nunique").reset_index()
        if pct:
            chart_data["value"] *= 100
        return chart_data

    def kpi_card(label, column, pct=False):
        curr = latest_snapshot[column].astype(str).str.lower().eq("true").mean() if pct else latest_snapshot[column].nunique()
        prev = previous_snapshot[column].astype(str).str.lower().eq("true").mean() if pct else previous_snapshot[column].nunique()
        delta = curr - prev
        curr_display = round(curr * 100 if pct else curr, 2)
        delta_display = round(abs(delta * 100 if pct else delta), 2)
        suffix = "%" if pct else ""
        delta_txt = (
            f"⬆️ {delta_display}{suffix} vs last week" if delta > 0
            else f"⬇️ {delta_display}{suffix} vs last week" if delta < 0
            else f"no change vs last week"
        )
        delta_color = "normal" if delta != 0 else "off"
        return curr_display, delta_txt, delta_color, sparkline_data(column, pct)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        val, delta, color, chart = kpi_card("Facility", "Facility", pct=False)
        st.metric("Open 503Bs", int(val), delta=delta, delta_color=color)
        render_sparkline(chart, force_pct=False)

    with col2:
        val, delta, color, chart = kpi_card("Sterile", "intends_to_compound_sterile", pct=True)
        st.metric("% Sterile w/ Bulk API", f"{val:.2f}%", delta=delta, delta_color=color)
        render_sparkline(chart, force_pct=True)

    with col3:
        val, delta, color, chart = kpi_card("Uninspected", "no_fda_inspections", pct=True)
        st.metric("% Uninspected", f"{val:.2f}%", delta=delta, delta_color=color)
        render_sparkline(chart, force_pct=True)

    with col4:
        val, delta, color, chart = kpi_card("Recall", "fda_recall_conducted", pct=True)
        st.metric("% w/ Recalls", f"{val:.2f}%", delta=delta, delta_color=color)
        render_sparkline(chart, force_pct=True)

    with col5:
        val, delta, color, chart = kpi_card("483", "form_483_issued", pct=True)
        st.metric("% w/ 483s", f"{val:.2f}%", delta=delta, delta_color=color)
        render_sparkline(chart, force_pct=True)

    # ░░ New vs Removed Facilities
    st.markdown("### 🆕 New & ⚠️ Missing Facilities")

    new_facs = latest_snapshot[~latest_snapshot["Facility"].isin(previous_snapshot["Facility"])]
    missing_facs = previous_snapshot[~previous_snapshot["Facility"].isin(latest_snapshot["Facility"])]

    with st.expander(f"🆕 {len(new_facs)} New Facilities This Week"):
        if new_facs.empty:
            st.write("No new facilities this week.")
        else:
            st.dataframe(new_facs[["pharmacy_name", "license_state", "initial_registration_date", "Facility"]])
            st.download_button("Download New Facilities", new_facs.to_csv(index=False).encode("utf-8"),
                               file_name=f"new_facilities_{latest_date.date()}.csv", mime="text/csv")

    with st.expander(f"⚠️ {len(missing_facs)} Missing Facilities This Week"):
        if missing_facs.empty:
            st.write("No facilities were removed.")
        else:
            st.dataframe(missing_facs[["pharmacy_name", "license_state", "initial_registration_date", "Facility"]])
            st.download_button("Download Missing Facilities", missing_facs.to_csv(index=False).encode("utf-8"),
                               file_name=f"missing_facilities_{latest_date.date()}.csv", mime="text/csv")

    # ░░ Download Section
    st.markdown("### 📥 Download Most Recent Weekly File")
    st.dataframe(latest_snapshot, use_container_width=True)
    st.download_button(
        label="Download CSV of Latest Facilities",
        data=latest_snapshot.to_csv(index=False).encode("utf-8"),
        file_name=f"503BWatch_{latest_date.date()}.csv",
        mime="text/csv"
    )


# ═══════════════════════════════════════════════════
# 🧪 INSPECTIONS TAB
# ═══════════════════════════════════════════════════
with tab2:
    st.markdown("### 📋 Post-Inspection Actions")

    chart_df = (
        latest_snapshot["post_inspection_action"]
        .fillna("No Action")
        .value_counts()
        .reset_index()
    )
    chart_df.columns = ["Post Inspection Action", "Count"]
    chart_df = chart_df.sort_values(by="Count", ascending=True)

    fig = px.bar(
        chart_df,
        x="Count",
        y="Post Inspection Action",
        orientation="h",
        text="Count",
        color_discrete_sequence=["#3366CC"]
    )
    fig.update_traces(textposition="outside", textfont=dict(size=12))
    fig.update_layout(showlegend=False, height=450, margin=dict(l=40, r=20, t=30, b=30))
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════
# 🚨 RECALLS TAB
# ═══════════════════════════════════════════════════
with tab3:
    st.markdown("## 🚧 Recalls")
    st.info("Recall analysis coming soon!")

# ═══════════════════════════════════════════════════
# 📄 483s TAB
# ═══════════════════════════════════════════════════
with tab4:
    st.markdown("## 🚧 Form 483 Reports")
    st.info("483 insights coming soon!")
