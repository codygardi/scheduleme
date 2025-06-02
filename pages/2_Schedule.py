# 2_Schedule.py
import streamlit as st
import pandas as pd
from modules.scheduler_engine import run_scheduler, RULES
from modules.db_manager import load_schedule, load_employees

st.title("Schedule & Logistics")

# ----------------------------
# Scheduler Controls
# ----------------------------
st.markdown("---")
with st.expander("View Active Rules", expanded=False):
    st.json(RULES, expanded=False)

if st.button("Run Scheduler"):
    run_scheduler()
    st.success("Schedule generated")

schedule_df = load_schedule()

if schedule_df.empty:
    st.warning("No schedule found. Please run the scheduler.")
    st.stop()

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["| Schedule |", "| Logistics |", "| Underscheduled |"])

# ----------------------------
# Tab 1 - Schedule Viewer
# ----------------------------
with tab1:
    st.markdown("---")
    st.header("Individual Schedule Viewer")

    employees = schedule_df["Name"].unique()
    selected_employee = st.selectbox("Select an employee to view their schedule", sorted(employees))

    emp_schedule = (
        schedule_df[schedule_df["Name"] == selected_employee]
        .sort_values(by="Date")[["Date", "Location", "Shift"]]
        .reset_index(drop=True)
    )

    if emp_schedule.empty:
        st.info("No schedule available for this employee.")
    else:
        st.dataframe(emp_schedule, use_container_width=True)

# ----------------------------
# Tab 2 - Daily Location Shift Count Breakdown
# ----------------------------
with tab2:
    st.markdown("---")
    st.subheader("Per-Location Daily Shift Coverage")

    min_req = RULES.get('min_staff_threshold', 3)
    shift_types = RULES.get("shift_types", [])

    coverage_grid = (
        schedule_df
        .groupby(['Date', 'Location', 'Shift'])['EmployeeID']
        .count()
        .reset_index()
        .pivot_table(index=['Date', 'Location'], columns='Shift', values='EmployeeID', fill_value=0)
        .reset_index()
    )

    for shift in shift_types:
        if shift not in coverage_grid.columns:
            coverage_grid[shift] = 0
    coverage_grid[shift_types] = coverage_grid[shift_types].astype(int)
    coverage_grid = coverage_grid[['Date', 'Location'] + shift_types]

    def highlight_shift(val):
        try:
            return 'background-color: #99ccff' if val < min_req else 'background-color: #666699'
        except:
            return ''

    styled = (
        coverage_grid.style
        .applymap(highlight_shift, subset=shift_types)
        .format({shift: "{:.0f}" for shift in shift_types})
    )

    st.dataframe(styled, use_container_width=True)

# ----------------------------
# Tab 3 - Underscheduled Employees
# ----------------------------
with tab3:
    st.markdown("---")
    st.subheader("Employees Below Max Weekly Shifts")

    employees_df = load_employees()
    employees_df['ScheduledShifts'] = employees_df['Name'].apply(
        lambda eid: (schedule_df['Name'] == eid).sum()
    )

    max_allowed = RULES.get('max_shifts_per_employee', 5)
    underscheduled = employees_df[employees_df['ScheduledShifts'] < max_allowed].copy()

    if underscheduled.empty:
        st.success("All employees have been fully utilized.")
    else:
        underscheduled = underscheduled[['EmployeeID', 'Name', 'ScheduledShifts']]
        underscheduled = underscheduled.sort_values(by='ScheduledShifts')
        st.dataframe(underscheduled.reset_index(drop=True), use_container_width=True)
