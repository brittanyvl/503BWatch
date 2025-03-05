import streamlit as st


def about_page():
    """Display the About page for 503B Watch."""

    st.title("ℹ️ About 503B Watch")

    st.markdown("""
    **503B Watch** is a data application developed by [Brittany Campos](https://www.linkedin.com/in/brittanycampos/) for professionals and stakeholders in the compounding pharmacy industry. This tool transforms the raw FDA dataset—often delivered as a poorly formatted spreadsheet—into a clean, insightful dashboard designed to support informed decision-making.

    **What is a 503B Compounding Pharmacy?**  
    503B compounding pharmacies, also known as outsourcing facilities, are specialized establishments that compound sterile and non-sterile drugs in bulk for hospitals and healthcare providers. These facilities operate under stringent FDA regulations to ensure quality and safety, making them a critical part of the healthcare supply chain.

    **Regulatory Oversight & Key Metrics**  
    To maintain high standards, the FDA inspects these facilities regularly. During inspections, the FDA may issue a Form 483—a list of observations if any discrepancies are found—or mandate a recall if safety concerns arise.  
    **503B Watch** focuses on key operational metrics, including:

    - **Open 503Bs:** Total count of currently operating compounding facilities.
    - **% Compounding Sterile Drugs from Bulk API:** All 503B Pharmacies are required to prepare at least (1) sterile human compound; this metric measures how many facilities intend to compound sterile using bulk drug API.
    - **% Uninspected by FDA:** Proportion of facilities that have not yet been inspected.
    - **% with FDA Recalls:** Percentage of facilities that have experienced product recalls.
    - **% with 483s Issued:** Fraction of facilities that have received FDA Form 483 observations.

    **Our Process & Future Enhancements**  
    Every Friday, the FDA updates its registry. On Saturdays, 503B Watch uses Selenium with the Chrome browser to programmatically download the latest XLSX file, which is then parsed and cleaned using Python and pandas. This refined data is analyzed to highlight trends and present a clear snapshot of the current industry landscape.  
    Looking ahead, future releases will incorporate week-to-week change tracking and additional data insights to further empower industry professionals with actionable information.

    **Contact Me**  
    For inquiries or further discussion, please feel free to reach out via [LinkedIn](https://www.linkedin.com/in/brittanycampos/). Your feedback is invaluable as we continuously work to enhance this tool for the compounding pharmacy community.
    """, unsafe_allow_html=True)
