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
st.title("🔍 503B Watch")
st.markdown("""
Welcome to **503B Watch**, a free dashboard for monitoring FDA-registered **503B outsourcing pharmacy facilities**.

I track inspections, recalls, and facility activity over time using publicly available FDA data.

Built by [**Brittany Campos**](https://www.linkedin.com/in/brittanycampos/)
""")

# ─────────────── TABS
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "🧪 Inspections", "🚨 Recalls", "📄 483s"])

# ═══════════════════════════════════════════════════
# 💡 HELPER: Sparkline Renderer
# ═══════════════════════════════════════════════════
def render_sparkline(chart_df, force_pct=False, key=None):
    values = chart_df["value"].values
    x_vals = chart_df["scanned_date"]

    yaxis_range = [0, 100] if force_pct else None
    hovertemplate = "<b>Week:</b> %{x|%b %d}<br><b>Value:</b> %{y:.1f}%<extra></extra>" if force_pct else \
                    "<b>Week:</b> %{x|%b %d}<br><b>Count:</b> %{y:.0f}<extra></extra>"

    norm = (values - values.min()) / (values.max() - values.min() + 1e-9)
    colors = [f"rgba({int(50 + 100 * n)}, {int(130 + 100 * n)}, 255, 1)" for n in norm]

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
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)

# ═══════════════════════════════════════════════════
# SHARED KPI LOGIC
# ═══════════════════════════════════════════════════
prior_dates = sorted([d for d in df["scanned_date"].unique() if d < latest_date])
prior_date = prior_dates[-1] if prior_dates else latest_date
previous_snapshot = df[df["scanned_date"] == prior_date]
ytd_df = df[df["scanned_date"].dt.year == latest_date.year]

def sparkline_data(column, pct=False, condition=None, scope=None):
    grouped = ytd_df.copy()
    if scope is not None:
        grouped = grouped[scope(grouped)]
    if condition:
        grouped["value"] = grouped.apply(condition, axis=1)
    else:
        grouped["value"] = grouped[column].astype(str).str.lower().eq("true") if pct else grouped[column]
    chart_data = grouped.groupby("scanned_date")["value"].agg("mean" if pct else "nunique").reset_index()
    if pct:
        chart_data["value"] *= 100
    return chart_data

def kpi_card(label, column, pct=False, condition=None, key_prefix="kpi", scope=None, disable_spark=False):
    snap_scope = latest_snapshot if scope is None else latest_snapshot[scope(latest_snapshot)]
    prev_scope = previous_snapshot if scope is None else previous_snapshot[scope(previous_snapshot)]

    if condition:
        curr = snap_scope.apply(condition, axis=1).mean()
        prev = prev_scope.apply(condition, axis=1).mean()
    else:
        curr = snap_scope[column].astype(str).str.lower().eq("true").mean() if pct else snap_scope[column].nunique()
        prev = prev_scope[column].astype(str).str.lower().eq("true").mean() if pct else prev_scope[column].nunique()

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
    st.metric(label, f"{curr_display}{suffix}", delta=delta_txt, delta_color=delta_color)

    if not disable_spark:
        chart = sparkline_data(column, pct=pct, condition=condition, scope=scope)
        render_sparkline(chart, force_pct=pct, key=key_prefix)

# ═══════════════════════════════════════════════════
# 🏠 HOME TAB
# ═══════════════════════════════════════════════════
with tab1:
    st.markdown("## 📊 This Week in 503B")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        kpi_card("Open 503Bs", "Facility", pct=False, key_prefix="open")

    with col2:
        kpi_card("% Sterile w/ Bulk API", "intends_to_compound_sterile", pct=True, key_prefix="sterile")

    with col3:
        kpi_card("% Uninspected", "no_fda_inspections", pct=True, key_prefix="uninspected")

    with col4:
        kpi_card("% w/ Recalls", "fda_recall_conducted", pct=True, key_prefix="recalls")

    with col5:
        kpi_card("% w/ 483s", "form_483_issued", pct=True, key_prefix="483")

    st.markdown("### 🆕 New & ⚠️ Missing Facilities")
    new_facs = latest_snapshot[~latest_snapshot["Facility"].isin(previous_snapshot["Facility"])]
    missing_facs = previous_snapshot[~previous_snapshot["Facility"].isin(latest_snapshot["Facility"])]

    with st.expander(f"🆕 {len(new_facs)} New Facilities This Week"):
        st.dataframe(new_facs)

    with st.expander(f"⚠️ {len(missing_facs)} Missing Facilities This Week"):
        st.dataframe(missing_facs)

    st.markdown("### 📥 Download Most Recent Weekly File")
    st.download_button(
        "Download CSV of Latest Facilities",
        data=latest_snapshot.to_csv(index=False).encode("utf-8"),
        file_name=f"503BWatch_{latest_date.date()}.csv",
        mime="text/csv"
    )
# ═══════════════════════════════════════════════════
# 🧪 INSPECTIONS TAB
# ═══════════════════════════════════════════════════
with tab2:
    st.markdown("## 🧪 Inspections Overview")

    # ── Uninspected KPI text
    uninspected_pct = round(
        latest_snapshot["no_fda_inspections"].astype(str).str.lower().eq("true").mean() * 100, 2
    )
    st.info(f"**{uninspected_pct}% of facilities have never been inspected by the FDA.** See the list below.")

    # ── Uninspected Facilities Table
    st.markdown("### 🏥 Uninspected Facilities")
    uninspected = latest_snapshot[
        latest_snapshot["no_fda_inspections"].astype(str).str.lower() == "true"
    ].sort_values(by="initial_registration_date", ascending=False)
    st.dataframe(uninspected[["pharmacy_name", "license_state", "initial_registration_date", "Facility"]])

    # ── Post-Inspection KPIs
    st.markdown("## 📑 Post-Inspection Actions")
    st.caption("Metrics below are based on **facilities that have been inspected.**")

    inspected_scope = lambda df: df["no_fda_inspections"].astype(str).str.lower() != "true"
    kpi_cols = st.columns(6)

    with kpi_cols[0]:
        kpi_card("% w/ Open Action", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() == "OPEN",
                 key_prefix="insp_open", scope=inspected_scope, disable_spark=True)

    with kpi_cols[1]:
        kpi_card("% w/ 483", "form_483_issued", pct=True,
                 condition=lambda row: str(row["form_483_issued"]).lower() == "true",
                 key_prefix="insp_483", scope=inspected_scope, disable_spark=True)

    with kpi_cols[2]:
        kpi_card("% w/ Warning Letter", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() == "WARNING LETTER ISSUED",
                 key_prefix="insp_warn", scope=inspected_scope, disable_spark=True)

    with kpi_cols[3]:
        kpi_card("% w/ Regulatory Mtg", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() == "REGULATORY MEETING HELD",
                 key_prefix="insp_reg", scope=inspected_scope, disable_spark=True)

    with kpi_cols[4]:
        kpi_card("% w/ Untitled Letter", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() == "UNTITLED LETTER ISSUED",
                 key_prefix="insp_untitled", scope=inspected_scope, disable_spark=True)

    with kpi_cols[5]:
        kpi_card("% w/ No Action", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() in ["NO ACTION", "FMD-145 LETTER ISSUED"],
                 key_prefix="insp_noaction", scope=inspected_scope, disable_spark=True)

    # ── Area Chart
    st.markdown("### 📈 Monthly Breakdown of Post-Inspection Outcomes")

    action_df = df.copy()
    action_df["month"] = action_df["scanned_date"].dt.to_period("M").dt.to_timestamp()
    action_df["action_group"] = (
        action_df["post_inspection_action"]
        .replace(["N/A", "n/a"], None)
        .fillna("Not Inspected")
    )

    monthly = action_df.groupby(["month", "action_group"]).size().reset_index(name="count")
    total_per_month = monthly.groupby("month")["count"].transform("sum")
    monthly["pct"] = monthly["count"] / total_per_month * 100

    color_map = {
        "Not Inspected": "#4B4B4B",  # dark gray
        "OPEN": "#90CAF9",
        "UNTITLED LETTER ISSUED": "#FFD54F",
        "REGULATORY MEETING HELD": "#FFB74D",
        "FMD-145 LETTER ISSUED": "#F57C00",
        "WARNING LETTER ISSUED": "#E53935",
        "NO ACTION": "#A5D6A7",
    }

    fig = px.area(
        monthly,
        x="month",
        y="pct",
        color="action_group",
        line_group="action_group",
        groupnorm="percent",
        labels={"pct": "% of Facilities", "month": "Month", "action_group": "Action"},
        color_discrete_map=color_map,
    )
    fig.update_layout(
        yaxis_tickformat=".0f",
        yaxis_title="Percent of Facilities",
        xaxis_title="Month",
        height=420,
        legend_title="Post Inspection Action",
        margin=dict(l=20, r=20, t=20, b=20),
        legend_traceorder="normal"
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Facilities w/ Warning Letters
    st.markdown("### 🧾 Facilities with Warning Letters")
    warning_df = latest_snapshot[
        (latest_snapshot["post_inspection_action"].astype(str).str.upper() == "WARNING LETTER ISSUED")
    ].sort_values(by="post_inspection_action_date", ascending=False)

    if warning_df.empty:
        st.write("No facilities with warning letters this week.")
    else:
        st.dataframe(warning_df[["pharmacy_name", "license_state", "post_inspection_action_date", "Facility"]])

    # ── Timeline: Last Inspection Date
    st.markdown("### 🗓️ Timeline of Last FDA Inspections")

    inspected_only = latest_snapshot[latest_snapshot["no_fda_inspections"].astype(str).str.lower() != "true"].copy()
    inspected_only["last_fda_inspection_date"] = pd.to_datetime(inspected_only["last_fda_inspection_date"], errors="coerce")
    inspected_only["post_inspection_action_date"] = pd.to_datetime(inspected_only["post_inspection_action_date"], errors="coerce")

    inspected_only = inspected_only.dropna(subset=["last_fda_inspection_date"])
    inspected_only["days_since"] = (latest_date - inspected_only["last_fda_inspection_date"]).dt.days
    inspected_only["months_since"] = (inspected_only["days_since"] / 30.44).round(1)
    inspected_only["years_since"] = (inspected_only["days_since"] / 365.25).round(2)

    inspected_only["hover"] = (
        "<b>Pharmacy:</b> " + inspected_only["pharmacy_name"].astype(str) +
        "<br><b>Facility:</b> " + inspected_only["Facility"].astype(str) +
        "<br><b>Last Inspection:</b> " + inspected_only["last_fda_inspection_date"].dt.date.astype(str) +
        "<br><b>Post Action:</b> " + inspected_only["post_inspection_action"].fillna("None") +
        "<br><b>Post Action Date:</b> " + inspected_only["post_inspection_action_date"].dt.date.astype(str) +
        "<br><br><b>Days Since:</b> " + inspected_only["days_since"].astype(str) +
        "<br><b>Months Since:</b> " + inspected_only["months_since"].astype(str) +
        "<br><b>Years Since:</b> " + inspected_only["years_since"].astype(str)
    )

    timeline_fig = go.Figure()
    timeline_fig.add_trace(go.Scatter(
        x=inspected_only["last_fda_inspection_date"],
        y=[1] * len(inspected_only),  # flat line
        mode="markers",
        marker=dict(size=8, color="#1f77b4"),
        hoverinfo="text",
        hovertext=inspected_only["hover"],
    ))
    timeline_fig.update_layout(
        title="Timeline of Last FDA Inspections",
        xaxis_title="Inspection Date",
        yaxis=dict(visible=False),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(timeline_fig, use_container_width=True)


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
