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
tab1, tab2, tab3 = st.tabs(["About", "Instructions", "Future Updates"])

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
    with st.expander("How do I work this thing?", expanded=False):
        st.markdown("""
        #### 1️⃣ Generate Employee Information
        - Generate randomized pre-set employee info  
        - Preview the generated data
        
        #### 2️⃣ Generate a Schedule
        - Use the employee info to generate a schedule  
        - View the full schedule  
        - View by individual employee

        #### 3️⃣ View Statistics & Oversight
        - Show how many employees were staffed  
        - See where minimum coverage isn’t met  
        - Get insights to adjustments
        """)

with tab3:
    st.subheader("Future Updates")
    st.markdown("""
    - Adding a page dedicated to user experience
    
    """)