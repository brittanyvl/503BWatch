import streamlit as st
from pathlib import Path
import layout
import about  # Import the about page
import home  # Import the home page

#st.set_page_config(page_title="503B WATCH", layout="wide", initial_sidebar_state="collapsed")

def load_css():
    """Load external CSS file."""
    css_path = Path(__file__).parent / "style.css"
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    # Set page title and layout

    # Load styles
    load_css()

    # Display header
    layout.display_header()

    # Sidebar navigation (Remove extra menu duplication)
    menu = st.sidebar.radio("📌 Navigation", ["Home", "About"], index=0)

    # Show the selected page
    if menu == "Home":
        home.home_page()  # Call the Home page function
    elif menu == "About":
        about.about_page()  # Call the About page function

if __name__ == "__main__":
    main()
