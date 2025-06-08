import streamlit as st

st.set_page_config(page_title="503B WATCH", layout="wide", initial_sidebar_state="collapsed")


# Inject custom CSS to make the sidebar smaller
st.markdown("""
    <style>
        .css-1d391kg {  /* This is the class for the sidebar */
            width: 150px; /* Set the width to a smaller value */
        }
    </style>
""", unsafe_allow_html=True)

def display_header():
    """Displays the application header."""
    st.title("🔍 503B Watch")

def display_sidebar():
    """Creates a sidebar dropdown for navigation."""
    menu = st.sidebar.selectbox("📌 Navigation", ["Home", "About"])
    return menu
