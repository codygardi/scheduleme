import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from modules.db_manager import init_db, load_schedule
from modules.scheduler_engine import RULES as SCHEDULER_RULES

init_db()

st.title("Schedule Statistics")
schedule_df = load_schedule()

if schedule_df.empty:
    st.warning("No schedule data available. Please run the scheduler first.")
    st.stop()

schedule_df["Locked"] = schedule_df.get("Locked", False)

# ----------------------------
# Shift Coverage Summary
# ----------------------------

st.header("Shift Coverage Summary")

shift_counts = (
    schedule_df.groupby(['Date', 'Location', 'Shift'])['EmployeeID']
    .count()
    .reset_index(name='Count')
)

st.dataframe(shift_counts.sort_values(by=["Date", "Location", "Shift"]), use_container_width=True)

# ----------------------------
# Individual Employee Schedule Viewer
# ----------------------------

st.header("Individual Schedule Viewer")

employees = schedule_df["EmployeeID"].unique()
selected_employee = st.selectbox("Select an employee to view their schedule", sorted(employees))

emp_schedule = (
    schedule_df[schedule_df["EmployeeID"] == selected_employee]
    .sort_values(by="Date")[["Date", "Location", "Shift"]]
    .reset_index(drop=True)
)

if emp_schedule.empty:
    st.info("No schedule available for this employee.")
else:
    st.dataframe(emp_schedule, use_container_width=True)


# Under-scheduled
min_req = SCHEDULER_RULES.get('min_staff_threshold', 3)
under_scheduled = shift_counts[shift_counts['Count'] < min_req]

st.subheader(f"Under-Scheduled Shifts (below {min_req})")
if under_scheduled.empty:
    st.success("All shifts meet minimum coverage.")
else:
    st.dataframe(under_scheduled, use_container_width=True)
    
# ----------------------------
# Shift Coverage Chart
# ----------------------------

st.subheader("Shift Coverage Chart")

fig, ax = plt.subplots(figsize=(10, 5))
pivot = shift_counts.pivot_table(index='Date', columns=['Location', 'Shift'], values='Count', fill_value=0)
pivot.plot(kind='bar', ax=ax)
ax.set_ylabel("Employees Assigned")
ax.set_title("Shift Coverage by Date / Location / Shift")
plt.xticks(rotation=45)
st.pyplot(fig)

# ----------------------------
# Employee Shift Assignment Summary
# ----------------------------

st.header("Employee Shift Summary")

assigned_counts = (
    schedule_df.groupby('EmployeeID')['Date']
    .count()
    .reset_index(name='AssignedShifts')
)

max_shifts = SCHEDULER_RULES.get('max_shifts_per_employee', 5)

# Under-assigned employees
under_assigned = assigned_counts[assigned_counts['AssignedShifts'] < max_shifts]
if not under_assigned.empty:
    st.subheader(f"Employees With Fewer Than {max_shifts} Shifts")
    st.warning(f"{len(under_assigned)} employees received fewer than {max_shifts} shifts this week.")
    st.dataframe(under_assigned.sort_values(by='AssignedShifts'))
else:
    st.success("All employees meet the minimum shift expectation.")

# Over-assigned employees
over_assigned = assigned_counts[assigned_counts['AssignedShifts'] > max_shifts]
if not over_assigned.empty:
    st.subheader(f"Employees With MORE Than {max_shifts} Shifts (Violation)")
    st.warning(f"{len(over_assigned)} employees were over-scheduled. This violates the max weekly shift rule.")
    st.dataframe(over_assigned.sort_values(by='AssignedShifts', ascending=False))
else:
    st.success("No employee exceeds the weekly shift cap.")

# ----------------------------
# Locked Assignments
# ----------------------------

st.header("Locked Assignments")

locked_view = st.checkbox("Show locked schedule entries", value=False)
locked_df = schedule_df[schedule_df["Locked"] == True]

if locked_view:
    if not locked_df.empty:
        st.info(f"{len(locked_df)} entries are locked from reassignment.")
        st.dataframe(locked_df.sort_values(by=["Date", "Location", "EmployeeID"]), use_container_width=True)
    else:
        st.success("There are currently no locked entries.")
