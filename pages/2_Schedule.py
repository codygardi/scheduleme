import streamlit as st
import pandas as pd
from modules.scheduler_engine import run_scheduler, RULES
from modules.db_manager import load_schedule, save_schedule

st.title("Generate Schedule")

# ----------------------------
# Scheduler Controls
# ----------------------------

with st.expander("View Active Rules", expanded=False):
    st.json(RULES, expanded=False)
    
if st.button("Run Scheduler"):
    run_scheduler()
    st.success("Schedule generated" + (" with rebalancing." if RULES['balance_enabled'] else "."))

# ----------------------------
# Schedule Viewer
# ----------------------------

schedule_df = load_schedule()

if schedule_df.empty:
    st.warning("No schedule found. Please run the scheduler.")
    st.stop()

if 'Locked' not in schedule_df.columns:
    schedule_df["Locked"] = False

st.subheader("Shift Schedule")
st.dataframe(schedule_df.sort_values(by=["Date", "Location", "Shift"]), use_container_width=True)

# ----------------------------
# Lock/Unlock Shift Control
# ----------------------------

st.markdown("### Lock or Unlock a Shift Assignment")

unique_rows = schedule_df[["EmployeeID", "Date", "Shift", "Location"]].astype(str)
unique_rows["Label"] = unique_rows.apply(
    lambda row: f"{row['Date']} | {row['EmployeeID']} | {row['Shift']} @ {row['Location']}", axis=1
)

selection = st.selectbox("Select a shift to lock/unlock", unique_rows["Label"].tolist())

if selection:
    sel_row = unique_rows[unique_rows["Label"] == selection].iloc[0]
    condition = (
        (schedule_df["EmployeeID"].astype(str) == sel_row["EmployeeID"]) &
        (schedule_df["Date"].astype(str) == sel_row["Date"]) &
        (schedule_df["Shift"].astype(str) == sel_row["Shift"]) &
        (schedule_df["Location"].astype(str) == sel_row["Location"])
    )
    is_locked = schedule_df.loc[condition, "Locked"].values[0]
    new_lock_state = st.checkbox("Locked?", value=is_locked, key="shift_lock_toggle")

    if st.button("Apply Shift Lock Toggle"):
        schedule_df.loc[condition, "Locked"] = new_lock_state
        save_schedule(schedule_df)
        st.success(f"Shift lock status updated to {'Locked' if new_lock_state else 'Unlocked'}.")
