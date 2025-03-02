import streamlit as st
from data_loader import load_data
from analysis import *

def home_page():
    """Logic for the Home page."""
    # Load data
    data = load_data()
    st.session_state['data'] = data  # Store in session state

    st.header("Active Bulk Compounding Pharmacies")
    st.write("A data app by [Brittany Campos](https://www.linkedin.com/in/brittanycampos/)")
    st.info("Last Updated 03/01/2025")

    if 'data' in st.session_state:
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Open 503Bs", metric_total_pharmacies)

        with col2:
            st.metric("% Compounding Sterile", f"{metric_percent_intend_sterile}%")

        with col3:
            st.metric("% Uninspected by FDA", f"{metric_percent_fda_uninspected}%")

        with col4:
            st.metric("% with FDA Recalls", f"{metric_percent_recalls_conducted}%")

        with col5:
            st.metric("% with 483s", f"{metric_percent_483s_issued}%")

        st.altair_chart(chart_post_inspection_actions, use_container_width=True)

        st.write("Download the entire data set below.")
        st.dataframe(st.session_state['data'])
    else:
        st.write("No data found!")
