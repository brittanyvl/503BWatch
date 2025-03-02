import streamlit as st

def display_header():
    """Displays the application header."""
    st.title("🔍 503B Watch")

def display_sidebar():
    """Creates a sidebar dropdown for navigation."""
    menu = st.sidebar.selectbox("📌 Navigation", ["Home", "About"])
    return menu
