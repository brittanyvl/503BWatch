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

I track inspections, recalls, and facility activity over time using the publicly available FDA 503B Outsourcing Facility List.

Built by [**Brittany Campos**](https://www.linkedin.com/in/brittanycampos/)
""")

# ─────────────── TABS
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📰 This Week", "📅 Changes Over Time", "🔍 Inspections", "🧑‍⚖️ Post Inspection Actions", "🚨 Recalls", "ℹ️ About 503B Watch"])

# ═══════════════════════════════════════════════════
#  HELPER: Sparkline Renderer
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
# 🏠 HOME TAB (UPDATED)
# ═══════════════════════════════════════════════════
with tab1:
    # ── KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        kpi_card("Open 503Bs", "Facility", pct=False, key_prefix="open", disable_spark=True)

    with col2:
        kpi_card("% Sterile w/ Bulk API", "intends_to_compound_sterile", pct=True, key_prefix="sterile", disable_spark=True)

    with col3:
        kpi_card("% Uninspected", "no_fda_inspections", pct=True, key_prefix="uninspected", disable_spark=True)

    with col4:
        kpi_card("% w/ Recalls", "fda_recall_conducted", pct=True, key_prefix="recalls", disable_spark=True)

    with col5:
        kpi_card("% w/ 483s", "form_483_issued", pct=True, key_prefix="483", disable_spark=True)

    # ── Facility Changes This Week
    st.markdown("#### Facility Status Changes This Week")

    new_facs = latest_snapshot[~latest_snapshot["Facility"].isin(previous_snapshot["Facility"])]
    missing_facs = previous_snapshot[~previous_snapshot["Facility"].isin(latest_snapshot["Facility"])]

    df_sorted = df.sort_values("scanned_date")

    first_inspections = df_sorted[df_sorted["no_fda_inspections"].astype(str).str.lower() != "true"]
    first_inspections = first_inspections.groupby("Facility").first().reset_index()
    first_inspected_this_week = first_inspections[first_inspections["scanned_date"] == latest_date]

    recalls_true = df_sorted[df_sorted["fda_recall_conducted"].astype(str).str.lower() == "true"]
    first_recalls = recalls_true.groupby("Facility").first().reset_index()
    first_recalled_this_week = first_recalls[first_recalls["scanned_date"] == latest_date]

    s1, s2 = st.columns(2)
    with s1:
        st.metric("🆕 New Facilities", value=f"{len(new_facs)} Added")
    with s2:
        st.metric("⚠️ Missing Facilities", value=f"{len(missing_facs)} Removed")

    s3, s4 = st.columns(2)
    with s3:
        st.metric("🔍 First-Time Inspections", value=f"{len(first_inspected_this_week)} Facilities")
    with s4:
        st.metric("🚨 First-Time Recalls", value=f"{len(first_recalled_this_week)} Facilities")

    with st.expander("🆕 View New Facilities"):
        st.dataframe(new_facs[["pharmacy_name", "license_state", "initial_registration_date", "Facility"]])

    with st.expander("⚠️ View Missing Facilities"):
        st.dataframe(missing_facs[["pharmacy_name", "license_state", "initial_registration_date", "Facility"]])

    with st.expander("🔍 View First-Time Inspections"):
        st.dataframe(first_inspected_this_week[["pharmacy_name", "license_state", "last_fda_inspection_date", "Facility"]])

    with st.expander("📋 View First-Time Recalls"):
        st.dataframe(first_recalled_this_week[["pharmacy_name", "license_state", "Facility"]])

    # ── Download Button
    st.markdown("#### 📥 Download Most Recent Weekly File")
    st.download_button(
        "Download CSV of Latest Facilities",
        data=latest_snapshot.to_csv(index=False).encode("utf-8"),
        file_name=f"503BWatch_{latest_date.date()}.csv",
        mime="text/csv"
    )



# ═══════════════════════════════════════════════════
# 🔍 INSPECTIONS TAB
# ═══════════════════════════════════════════════════
with tab2:
    # ── Historical KPI Trends Section
    st.markdown("---")
    st.markdown("### 📈 Historical KPI Trends")
    st.caption("Click each metric below to explore its trend over time in more detail.")


    def plot_kpi_history(column, pct=False, condition=None, scope=None, chart_type="line", label="Value", height=300):
        chart = sparkline_data(column, pct=pct, condition=condition, scope=scope)

        if chart_type == "bar":
            fig = px.bar(
                chart, x="scanned_date", y="value", text=chart["value"].round(1),
                labels={"scanned_date": "Date", "value": label}
            )
            fig.update_traces(textposition="outside")
        else:
            fig = px.line(
                chart, x="scanned_date", y="value", markers=True,
                labels={"scanned_date": "Date", "value": label}
            )

        y_max = chart["value"].max()
        y_range = [0, y_max * 1.15 if y_max else 1]  # some padding above max

        fig.update_layout(
            height=height,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis_title="Week",
            yaxis_title=label,
            yaxis=dict(range=y_range)
        )
        st.plotly_chart(fig, use_container_width=True)


    with st.expander("📊 Open 503Bs"):
        plot_kpi_history("Facility", pct=False, chart_type="bar", label="Facility Count", height=400)

    with st.expander("🧪 % Sterile w/ Bulk API"):
        plot_kpi_history("intends_to_compound_sterile", pct=True, label="Percent")

    with st.expander("🔍 % Uninspected"):
        plot_kpi_history("no_fda_inspections", pct=True, label="Percent")

    with st.expander("🚨 % w/ Recalls"):
        plot_kpi_history("fda_recall_conducted", pct=True, label="Percent")

    with st.expander("📄 % w/ 483s"):
        plot_kpi_history("form_483_issued", pct=True, label="Percent")



# ═══════════════════════════════════════════════════
# 🚨 RECALLS TAB
# ═══════════════════════════════════════════════════
with tab3:
    st.markdown("## 📊 Inspection KPIs")

    # Prepare datasets
    inspections_df = latest_snapshot[
        ["Facility", "initial_registration_date", "last_fda_inspection_date", "no_fda_inspections"]].copy()
    inspections_df["initial_registration_date"] = pd.to_datetime(inspections_df["initial_registration_date"],
                                                                 errors="coerce")
    inspections_df["last_fda_inspection_date"] = pd.to_datetime(inspections_df["last_fda_inspection_date"],
                                                                errors="coerce")
    inspections_df = inspections_df.dropna(subset=["initial_registration_date"])

    # % never inspected (latest file only)
    percent_uninspected = round(
        inspections_df["no_fda_inspections"].astype(str).str.lower().eq("true").mean() * 100, 2
    )

    # Deduplicated inspections
    deduped_inspections = inspections_df.dropna(subset=["last_fda_inspection_date"]).drop_duplicates(
        subset=["Facility", "last_fda_inspection_date"])
    deduped_inspections["months_to_inspection"] = (deduped_inspections["last_fda_inspection_date"] -
                                                   deduped_inspections["initial_registration_date"]).dt.days / 30.44
    avg_months_to_inspection = round(deduped_inspections["months_to_inspection"].mean(), 1)

    # YTD inspections
    ytd_inspections = deduped_inspections[deduped_inspections["last_fda_inspection_date"].dt.year == latest_date.year]
    num_ytd_inspections = ytd_inspections.shape[0]

    # Avg inspections per year
    if not deduped_inspections.empty:
        deduped_inspections["year"] = deduped_inspections["last_fda_inspection_date"].dt.year
        avg_inspections_per_year = round(deduped_inspections.groupby("year").size().mean(), 1)
    else:
        avg_inspections_per_year = 0.0

    # ── Render KPI Row (4-wide) with short, wrapped labels
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("📌\nNever Inspected", f"{percent_uninspected} %")
    with k2:
        st.metric("📆\nAvg Time to 1st Inspection", f"{avg_months_to_inspection} mo")
    with k3:
        st.metric("📅\nYTD Inspections", f"{num_ytd_inspections}")
    with k4:
        st.metric("📈\nAvg Inspections per Year", f"{avg_inspections_per_year}")

    # ── Facility Expanders
    st.markdown("### 🗂️ Facility Lists")

    with st.expander("🚫 Facilities w/o FDA Inspection"):
        st.dataframe(
            inspections_df[inspections_df["no_fda_inspections"].astype(str).str.lower() == "true"][
                ["Facility", "initial_registration_date"]
            ],
            use_container_width=True
        )

    with st.expander("✅ FDA Inspected Facilities"):
        inspected_latest = latest_snapshot[
            latest_snapshot["no_fda_inspections"].astype(str).str.lower() != "true"
            ].copy()
        inspected_latest["last_fda_inspection_date"] = pd.to_datetime(inspected_latest["last_fda_inspection_date"],
                                                                      errors="coerce")
        inspected_latest = inspected_latest.sort_values(by="last_fda_inspection_date", ascending=False)

        st.dataframe(
            inspected_latest[[
                "Facility", "pharmacy_name", "license_state",
                "last_fda_inspection_date", "post_inspection_action", "post_inspection_action_date"
            ]],
            use_container_width=True
        )

    with st.expander("📄 Facilities with Warning Letters"):
        warning_df = latest_snapshot[
            (latest_snapshot["post_inspection_action"].astype(str).str.upper() == "WARNING LETTER ISSUED")
        ].copy()

        warning_df["last_fda_inspection_date"] = pd.to_datetime(warning_df["last_fda_inspection_date"], errors="coerce")
        warning_df = warning_df.sort_values(by="post_inspection_action_date", ascending=False)

        st.dataframe(warning_df[[
            "pharmacy_name", "license_state", "initial_registration_date",
            "last_fda_inspection_date", "post_inspection_action", "post_inspection_action_date", "Facility"
        ]], use_container_width=True)

    st.markdown("### 🕒 Inspection Timeline")

    timeline_df = latest_snapshot.copy()
    timeline_df["last_fda_inspection_date"] = pd.to_datetime(
        timeline_df["last_fda_inspection_date"], errors="coerce"
    )
    timeline_df = timeline_df.dropna(subset=["last_fda_inspection_date"])

    # 💡 Normalize post-inspection action labels
    import re


    def normalize_action(val):
        if not isinstance(val, str):
            return "NO ACTION"
        val_clean = val.strip().upper()
        # Catch all FMD-145 variations
        if re.search(r"FMD\s*-?\s*145\s*LETTER\s*ISSUED", val_clean):
            return "NO ACTION"
        if val_clean in ["N/A", "NA", ""]:
            return "NO ACTION"
        return val_clean


    timeline_df["action_clean"] = timeline_df["post_inspection_action"].apply(normalize_action)

    # Optional: debug unique actions after normalization
    # st.write(timeline_df["action_clean"].value_counts())

    # Sort by inspection date and facility
    timeline_df = timeline_df.sort_values(["last_fda_inspection_date", "Facility"])

    # Color map
    action_colors = {
        "WARNING LETTER ISSUED": "#E53935",  # red
        "OPEN": "#888888",  # dark gray
        "REGULATORY MEETING HELD": "#AAAAAA",  # medium gray
        "UNTITLED LETTER ISSUED": "#BBBBBB",  # light gray
        "NO ACTION": "#DDDDDD"  # lightest gray
    }

    timeline_df["color"] = timeline_df["action_clean"].map(action_colors).fillna("#CCCCCC")

    fig = go.Figure()

    for action in timeline_df["action_clean"].unique():
        group = timeline_df[timeline_df["action_clean"] == action]
        fig.add_trace(go.Scatter(
            x=group["last_fda_inspection_date"],
            y=group["Facility"],
            mode="markers",
            marker=dict(size=10, color=action_colors.get(action, "#CCCCCC")),
            name=action.title(),
            hovertemplate="<b>Facility:</b> %{y}<br><b>Inspected:</b> %{x|%b %d, %Y}<br><b>Action:</b> " + action.title() + "<extra></extra>"
        ))

    fig.update_layout(
        height=600,
        title="Timeline of FDA Inspections by Facility",
        xaxis_title="Inspection Date",
        yaxis_title="Facility",
        yaxis=dict(showticklabels=False),
        margin=dict(l=20, r=20, t=50, b=20),
        legend_title="Post-Inspection Action"
    )

    st.plotly_chart(fig, use_container_width=True, key="inspection_timeline")

with tab4:
    # ── Post-Inspection KPIs
    st.markdown("## 📑 Post-Inspection Actions")
    st.caption("Metrics below are based on **facilities that have been inspected.**")

    inspected_scope = lambda df: df["no_fda_inspections"].astype(str).str.lower() != "true"
    kpi_cols = st.columns(6)

    with kpi_cols[0]:
        kpi_card("Open Action", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() == "OPEN",
                 key_prefix="insp_open", scope=inspected_scope, disable_spark=True)

    with kpi_cols[1]:
        kpi_card("483 Issued", "form_483_issued", pct=True,
                 condition=lambda row: str(row["form_483_issued"]).lower() == "true",
                 key_prefix="insp_483", scope=inspected_scope, disable_spark=True)

    with kpi_cols[2]:
        kpi_card("Warning Letter", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() == "WARNING LETTER ISSUED",
                 key_prefix="insp_warn", scope=inspected_scope, disable_spark=True)

    with kpi_cols[3]:
        kpi_card("Reg Mtg Held", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() == "REGULATORY MEETING HELD",
                 key_prefix="insp_reg", scope=inspected_scope, disable_spark=True)

    with kpi_cols[4]:
        kpi_card("Untitled Letter", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() == "UNTITLED LETTER ISSUED",
                 key_prefix="insp_untitled", scope=inspected_scope, disable_spark=True)

    with kpi_cols[5]:
        kpi_card("No Action", "post_inspection_action", pct=True,
                 condition=lambda row: (row["post_inspection_action"] or "").upper() in ["NO ACTION",
                                                                                         "FMD-145 LETTER ISSUED"],
                 key_prefix="insp_noaction", scope=inspected_scope, disable_spark=True)

    # ── Line Chart: Post-Inspection Outcomes Over Time
    st.markdown("### 📈 Post-Inspection Outcomes Over Time")
    st.caption(
        "This line chart shows the percentage of inspected facilities that received each post-inspection outcome by week.")

    # Prepare data
    action_df = df.copy()
    action_df["scanned_date"] = pd.to_datetime(action_df["scanned_date"])
    action_df["post_inspection_action"] = (
        action_df["post_inspection_action"]
        .replace(["N/A", "n/a"], None)
        .fillna("Not Inspected")
        .str.strip()
    )

    # Only inspected
    inspected_df = action_df[
        action_df["no_fda_inspections"].astype(str).str.lower() != "true"
        ].copy()

    inspected_df["week"] = inspected_df["scanned_date"].dt.to_period("W").dt.to_timestamp()

    weekly_counts = inspected_df.groupby(["week", "post_inspection_action"]).size().reset_index(name="count")

    pivot_counts = weekly_counts.pivot(index="week", columns="post_inspection_action", values="count").fillna(0)

    percent_df = pivot_counts.div(pivot_counts.sum(axis=1), axis=0) * 100

    plot_df = percent_df.reset_index().melt(id_vars="week", var_name="Post-Inspection Action", value_name="Percent")

    # Better color scheme
    color_map = {
        "WARNING LETTER ISSUED": "#d62728",  # red
        "OPEN": "#9467bd",  # purple
        "UNTITLED LETTER ISSUED": "#ff7f0e",  # orange
        "REGULATORY MEETING HELD": "#2ca02c",  # green
        "FMD-145 LETTER ISSUED": "#1f77b4",  # blue
        "NO ACTION": "#7f7f7f",  # dark grey
        "Not Inspected": "#cccccc",  # light grey
    }

    fig = px.line(
        plot_df,
        x="week",
        y="Percent",
        color="Post-Inspection Action",
        markers=True,
        color_discrete_map=color_map,
        labels={
            "week": "Week",
            "Percent": "Percentage",
            "Post-Inspection Action": "Action Type"
        }
    )

    # 🧠 Custom tooltip for readability
    fig.update_traces(
        hovertemplate=(
            "<b>Week:</b> %{x|%b %d, %Y}<br>"
            "<b>Percent:</b> %{y:.1f}%<extra></extra>"
        )
    )

    fig.update_layout(
        height=500,
        xaxis_title="Week",
        yaxis_title="Percent of Inspected Facilities",
        legend_title="Post-Inspection Action",
        margin=dict(l=20, r=20, t=30, b=20),
        hovermode="x unified",
        yaxis=dict(range=[0, 100])
    )

    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.markdown("## 🚨 Recalls")

    # Calculate % of facilities with recalls
    recall_flag = latest_snapshot["fda_recall_conducted"].astype(str).str.lower()
    recall_pct = recall_flag.eq("true").mean() * 100
    recall_pct = round(recall_pct, 2)

    st.info(
        f"**{recall_pct}% of currently registered 503B facilities have conducted at least one recall.**\n\n"
        "This is based on FDA's published **Outsourcing Facility Registration** data."
    )

    # Clean recall flags to labels
    recall_labels = recall_flag.replace({
        "true": "Recall Conducted",
        "false": "No Recall"
    })

    # Count and compute percent
    recall_counts = recall_labels.value_counts().reset_index()
    recall_counts.columns = ["Status", "Count"]
    recall_counts["Percent"] = recall_counts["Count"] / recall_counts["Count"].sum() * 100

    import plotly.express as px
    fig = px.bar(
        recall_counts,
        x="Percent",
        y="Status",
        orientation="h",
        color="Status",
        text=recall_counts["Percent"].round(1).astype(str) + "%",
        color_discrete_map={
            "Recall Conducted": "#1f77b4",
            "No Recall": "#cccccc"
        }
    )
    fig.update_traces(textposition="inside")
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=10, b=10),
        showlegend=False,
        xaxis=dict(range=[0, 100], title=""),
        yaxis=dict(title=""),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Facilities with recall
    st.markdown("### 🏥 Facilities with Recalls")

    recalled_facs = latest_snapshot[recall_flag == "true"]
    if recalled_facs.empty:
        st.success("✅ No recalls recorded for facilities in the current dataset.")
    else:
        st.dataframe(
            recalled_facs[["pharmacy_name", "license_state", "initial_registration_date", "Facility"]],
            use_container_width=True
        )
