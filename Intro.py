# Intro.py

import streamlit as st

st.set_page_config(
    page_title="ScheduleMe App",
    page_icon="🗓️",
    layout="wide",
)

st.title("👷 ScheduleMe")
st.markdown("---")

# Create tabbed sections
tab1, tab2, tab3 = st.tabs(["About", "Future Updates", "Developer Notes"])

with tab1:
    st.markdown("""#### Click the dropdown menus to learn more""")
    with st.expander("What is **ScheduleMe**", expanded=False):
        st.markdown("""
        **ScheduleMe** is a scheduling system built for operations teams managing people across multiple territories.
        """)
    with st.expander("How does **ScheduleMe** help you", expanded=False):
        st.markdown("""
        It's designed to save time and prevent overstaffing, ScheduleMe ensures every employee is scheduled fairly and efficiently.
        """)
    st.markdown("---")
    st.info("📱 **Mobile Users:** Click the arrow in the upper left corner to navigate between pages.")
    st.info("🖥️ **Desktop Users:** Click the sidebar to the left to navigate between pages.")  
    st.markdown("""
    ***⚠️ This software is proprietary. Unauthorized copying, modification, or distribution is strictly prohibited. All rights reserved © 2025 Cody Gardi***
    """)

with tab2:
    st.subheader("Future Updates")
    st.markdown("""
    - Adding a page dedicated to user experience
    
    """)

with tab3:
    st.subheader("Developer Notes")
    st.markdown("""
    - N/A
    
    """)
