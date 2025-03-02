import streamlit as st

def display_header():
    """Displays the application header."""
    st.title("🔍 503B Watch")

def display_sidebar():
    """Creates a sidebar dropdown for navigation."""
    # Placeholder to simulate the menu being closed or not selected
    menu = st.sidebar.selectbox("📌 Navigation", ["Select an option", "Home", "About"])
    return menu
