import streamlit as st
import pandas as pd
from modules.employee_generator import generate_employees
import os
from modules.scheduler_engine import run_scheduler

st.title("📁 Quick Demonstration")
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

# Create tabbed sections
tab1, tab2, tab3 = st.tabs(["Generate Sample Data", "Generate Schedule", "Statistics & Overview"])

with tab1:
    st.subheader("Generate Sample Data")
    with st.expander("📘 Features", expanded=False):
        st.markdown("""
            ### ✨ Features Explained

            **0. EmployeeID & Name**  
            - A unique ID like `E001`, `E002`, etc.  
            - Full name generated using Faker.
            
            **1. EmployeeName**  
            - Full `fake` name generated
                    
            **2. Phone Number**  
            - Realistic `fake` phone numbers for contacting employees

            **3. Preferred Locations**  
            - Each employee selects **1 or 2** regions from:  
            `South Bay, East Bay, North Bay`.

            **4. Available Days**  
            - Assigned one of two 5-day schedules:  
            - `Tuesday, Wednesday, Thursday, Friday, Saturday`  
            - `Sunday, Monday, Tuesday, Wednesday, Thursday`

            **5. Shift Preference**  
            - Randomly selected as either `Morning` or `Afternoon`.

            **6. Date Hired**  
            - Random hiring date from the **past 3 years** input as `YYYY-MM-DD` (helps rank seniority).

            **7. Export**  
            - All data is saved as `data/employees.csv`.  
            - If the folder doesn't exist, it will be created automatically.
        """)
    st.markdown("---")
    # 🔢 Employee slider
    num_employees = st.slider("Select number of employees to generate", min_value=10, max_value=30, value=20)

    # 📦 Generate button
    if st.button("Generate Sample Data"):
        df = generate_employees(num_employees)
        st.success(f"{num_employees} sample employees generated.")
    else:
        if os.path.exists("data/employees.csv"):
            df = pd.read_csv("data/employees.csv")
        else:
            df = None

    # 📊 Collapsible preview
    if df is not None:
        with st.expander("📊 Preview Data", expanded=False):
            pretty_df = df.copy()
            for col in ['PreferredLocations', 'AvailableDays']:
                pretty_df[col] = pretty_df[col].apply(lambda x: ', '.join(eval(x)) if isinstance(x, str) else x)
            st.dataframe(pretty_df)

with tab2:
    
    st.subheader("Generate Schedule")
    import streamlit as st

    with st.expander("⚙️ Scheduling Algorithm", expanded=False):
        st.markdown("""
           - `Prioritizes Seniority`
           - `Checks Preferred Regions`
           - `Checks Preferred Day & Shift`
           - `Matches Employees to Criteria`
           - `Enforces Rules like each employee needs 5 shifts (aka 40hrs)`
           - `Handles Fallbacks if preferrences are not available`
           - `Outputs Final Schedule that is searcheable by the Employee's Name`
            """)


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
        with st.expander("🧑 View Individual Employee Schedules", expanded=True):

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
