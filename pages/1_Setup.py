import streamlit as st
import pandas as pd
from datetime import date
from modules.employee_generator import generate_employees
from modules.db_manager import load_employees
from modules import scheduler_engine
st.markdown("---")
st.title("Setup & Configuration")
st.markdown("---")
# ----------------------------
# Init Session State
# ----------------------------

st.session_state.setdefault("holiday_buffer", [])
st.session_state.setdefault("locked_locations", [])

# ----------------------------
# Employee Generation
# ----------------------------

with st.expander("EMPLOYEE GENERATOR", expanded=True):
    st.markdown("---")
    num_employees = st.slider("Number of employees", 5, 100, value=30)
    if st.button("Generate Employees"):
        df = generate_employees(n=num_employees)
        st.success(f"{num_employees} employees generated.")
    else:
        df = load_employees()

    st.subheader("Employee Preview")
    st.dataframe(df, use_container_width=True)

# ----------------------------
# Global Parameters
# ----------------------------
st.markdown("---")
st.header("Scheduler Rules")
st.markdown("---")
with st.expander("GLOBAL SCHEDULING PARAMETERS", expanded=False):
    st.markdown("---")
    scheduler_engine.RULES['schedule_days'] = st.slider("Schedule length (days)", 1, 30, scheduler_engine.RULES['schedule_days'])

    scheduler_engine.RULES['shift_types'] = st.multiselect(
        "Shift types", ["Morning", "Afternoon", "Night"],
        default=scheduler_engine.RULES['shift_types']
    )

    scheduler_engine.RULES['active_locations'] = st.multiselect(
        "Active locations", ["ZoneA", "ZoneB", "ZoneC"],
        default=scheduler_engine.RULES['active_locations']
    )

    min_staff, max_staff = st.slider(
        "Employees per shift (min/max)", 1, 10,
        value=(scheduler_engine.RULES['min_staff_threshold'], scheduler_engine.RULES['max_staff_per_shift'])
    )
    scheduler_engine.RULES['min_staff_threshold'] = min_staff
    scheduler_engine.RULES['max_staff_per_shift'] = max_staff

    scheduler_engine.RULES['max_shifts_per_employee'] = st.slider(
        "Max shifts per employee (per week)", 1, 7,
        value=scheduler_engine.RULES['max_shifts_per_employee']
    )

# ----------------------------
# Core Assignment Rules
# ----------------------------

with st.expander("CORE ASSIGNMENT RULES", expanded=False):
    st.markdown("---")
    scheduler_engine.RULES['enforce_work_pattern'] = st.checkbox("Respect Work Patterns", scheduler_engine.RULES['enforce_work_pattern'])
    scheduler_engine.RULES['enforce_no_morning_after_night'] = st.checkbox("Avoid Morning After Night", scheduler_engine.RULES['enforce_no_morning_after_night'])

    scheduler_engine.RULES['shift_preference_mode'] = st.radio(
        "Preferred Shift Handling",
        options=["strict", "soft", "ignore"],
        index=["strict", "soft", "ignore"].index(scheduler_engine.RULES['shift_preference_mode']),
        help="Strict = Required, Soft = Prefer, Ignore = No Preference"
    )

    scheduler_engine.RULES['location_preference_mode'] = st.radio(
        "Preferred Location Handling",
        options=["strict", "soft", "ignore"],
        index=["strict", "soft", "ignore"].index(scheduler_engine.RULES.get('location_preference_mode', 'soft')),
        help="Strict = Required, Soft = Prefer, Ignore = No Preference"
    )

# ----------------------------
# Seniority and Preferences
# ----------------------------

with st.expander("SENIORITY & PREFERENCES", expanded=False):
    st.markdown("---")
    scheduler_engine.RULES['use_seniority_weighting'] = st.checkbox("Use Seniority Weighting", scheduler_engine.RULES['use_seniority_weighting'])

# ----------------------------
# Constraints and Cooldowns
# ----------------------------

with st.expander("CONSTRAINTS & COOLDOWNS", expanded=False):
    st.markdown("---")
    scheduler_engine.RULES['enforce_consecutive_day_limit'] = st.checkbox("Limit Consecutive Workdays", scheduler_engine.RULES['enforce_consecutive_day_limit'])
    scheduler_engine.RULES['max_consecutive_days'] = st.slider("Max Consecutive Days", 1, 10, scheduler_engine.RULES['max_consecutive_days'])

    scheduler_engine.RULES['enforce_shift_cooldown'] = st.checkbox("Enforce Shift Cooldown", scheduler_engine.RULES['enforce_shift_cooldown'])
    scheduler_engine.RULES['min_hours_between_shifts'] = st.slider("Cooldown Hours Between Shifts", 1, 24, scheduler_engine.RULES['min_hours_between_shifts'])

# ----------------------------
# Holiday Logic
# ----------------------------

with st.expander("COMPANY-WIDE HOLIDAYS", expanded=False):
    st.markdown("---")
    st.markdown("Add one or more **company-wide holidays**. These will be blocked from scheduling.")

    new_holiday = st.date_input("Pick a holiday to add", min_value=date.today(), key="holiday_calendar")
    if st.button("Add Holiday"):
        str_date = new_holiday.strftime('%Y-%m-%d')
        if str_date not in st.session_state.holiday_buffer:
            st.session_state.holiday_buffer.append(str_date)
            st.success(f"Added: {str_date}")
        else:
            st.warning("Date already added.")

    if st.session_state.holiday_buffer:
        st.markdown("### Selected Holidays")
        holiday_df = pd.DataFrame(sorted(st.session_state.holiday_buffer), columns=["Holiday Date"])
        st.dataframe(holiday_df, use_container_width=True)

        if st.button("Clear All Holidays"):
            st.session_state.holiday_buffer = []

    scheduler_engine.RULES['holiday_dates'] = st.session_state.holiday_buffer

# ----------------------------
# Locked Locations
# ----------------------------

with st.expander("LOCKED LOCATIONS", expanded=False):
    st.markdown("---")
    st.session_state.locked_locations = st.multiselect(
        "Lock specific locations from being scheduled:",
        options=scheduler_engine.RULES['active_locations'],
        default=st.session_state.locked_locations,
    )
    scheduler_engine.RULES['locked_locations'] = st.session_state.locked_locations

# ----------------------------
# Rebalancing Controls
# ----------------------------

with st.expander("REBALANCING RULES", expanded=False):
    st.markdown("---")
    st.markdown("_Note: If enabled, rebalancing will automatically run after scheduling is generated._")
    scheduler_engine.RULES['balance_enabled'] = st.checkbox("Enable Shift Rebalancing", scheduler_engine.RULES['balance_enabled'])
    scheduler_engine.RULES['balance_prefer_seniority'] = st.checkbox("Prefer Seniority in Rebalancing", scheduler_engine.RULES['balance_prefer_seniority'])
