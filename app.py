# Intro.py

import streamlit as st
import pandas as pd
import os
from modules.scheduler_engine import run_scheduler

st.set_page_config(
    page_title="ScheduleMe (Alpha)",
    page_icon="🗓️",
    layout="wide",
)

st.title("Welcome to ScheduleMe (`Alpha`)")
st.markdown("---")

# Create tabbed sections
tab1, tab2, tab3, tab4 = st.tabs(["ScheduleMe", "More Info", "Future Updates", "Developer Notes"])
with tab1:
    st.subheader("Getting Started")
    with st.expander("How do I work this thing?", expanded=False):
            st.markdown("""
            #### 1️⃣ Generate Sample Data
            - Generate randomized pre-set employee info  
            - Preview the generated data
            
            #### 2️⃣ Generate Schedule
            - Use the employee info to generate a schedule  
            - View the full schedule  
            - View by individual employee

            #### 3️⃣ View Statistics & Oversight
            - Show how many employees were staffed  
            - See where minimum coverage isn’t met  
            - Get insights to adjustments
            """)
    st.markdown("---")

    # Management Inputs
    num_employees = st.number_input("`Number of employees in your business:`", min_value=1, max_value=200, value=20)
    num_zones = st.number_input("`Number of locations your business operates in:`", min_value=2, max_value=10, value=3)

    customize_shifts = st.checkbox("Customize working shifts?")
    shift_patterns = []

    if customize_shifts:
        num_shift_patterns = st.number_input(
            "`How many working shift patterns do you support?` (e.g. Tues-Sat, Sun-Thu)",
            min_value=1,
            max_value=3,
            value=2
        )

        for i in range(num_shift_patterns):
            pattern_days = st.multiselect(
                f"Shift Pattern {i+1}:",
                options=["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                default=["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                key=f"shift_pattern_{i}"
            )
            shift_patterns.append(pattern_days)

    shift_types = st.multiselect(
        "`Select your business's shift types:`",
        options=["Morning", "Swing", "Night"],
        default=["Morning", "Swing"]
    )

    
    
    generate_button = st.button("Generate Employees")
    df = None

    if generate_button:
        from modules.employee_generator import generate_employees
        generate_employees(
            num_employees=num_employees,
            output_path="data/employees.csv",
            num_zones=num_zones,
            shift_patterns=shift_patterns,
            shift_types=shift_types
        )
        st.success("✅ Sample employee data generated!")
        df = pd.read_csv("data/employees.csv")

    if df is not None:
        with st.expander("Preview Data", expanded=False):
            pretty_df = df.copy()
            for col in ['PreferredLocations', 'AvailableDays']:
                pretty_df[col] = pretty_df[col].apply(lambda x: ', '.join(eval(x)) if isinstance(x, str) else x)
            st.dataframe(pretty_df)
    st.markdown("---")
    if st.button("Generate Schedule"):
        schedule_df = run_scheduler()
        st.success("Schedule generated.")
    else:
        if os.path.exists("data/weekly_schedule.csv"):
            schedule_df = pd.read_csv("data/weekly_schedule.csv")
        else:
            st.warning("Please generate a schedule first.")
            schedule_df = None
    if schedule_df is not None:
        with st.expander("View Individual Employee Schedules", expanded=True):

            employee_options = schedule_df['Name'].unique()
            selected_employee = st.selectbox("Select an Employee", employee_options)

            # Filter schedule by selected employee
            emp_schedule = schedule_df[schedule_df['Name'] == selected_employee]

            if not emp_schedule.empty:
                # Reorder and clean the display
                display_df = emp_schedule[['Date', 'Location', 'Shift']].sort_values(by='Date')
                display_df.columns = ['📅 Date', '📍 Location', '⏰ Shift']

                st.table(display_df.reset_index(drop=True))
            else:
                st.info("No shifts assigned to this employee.")
with tab2:
    st.markdown("""#### Click the dropdown menus to learn more""")
    with st.expander("What is **ScheduleMe**", expanded=False):
        st.markdown("""
        **ScheduleMe** is a scheduling system built for operations teams managing people across multiple territories.
        """)
    with st.expander("How does **ScheduleMe** help you", expanded=False):
        st.markdown("""
        It's designed to save time, prevent overstaffing, amd give employees options. ScheduleMe ensures every employee is scheduled fairly and efficiently while taking their preferences into consideration.
        """)
    st.markdown("---")
    # st.info("📱 **Mobile Users:** Click the arrow in the upper left corner to navigate between pages.")
    # st.info("🖥️ **Desktop Users:** Click the sidebar to the left to navigate between pages.")  
    st.markdown("""
    ***⚠️ This software is proprietary. Unauthorized copying, modification, or distribution is strictly prohibited. All rights reserved © 2025 Cody Gardi***
    """)

with tab3:
    st.subheader("Future Updates")
    st.markdown("""
    - Adding a page dedicated to user experience
    
    """)

with tab4:
    st.subheader("Developer Notes")
    st.markdown("""
    - N/A
    
    """)