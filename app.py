import streamlit as st
from modules.db_manager import init_db

# ----------------------------
# App Initialization
# ----------------------------

st.set_page_config(
    page_title="ScheduleMe",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

# ----------------------------
# Header & Intro
# ----------------------------

st.title("ScheduleMe")
st.markdown("""
Welcome to the **ScheduleMe** intelligent shift scheduling system.

This platform supports:
- **Employee generation** with work patterns, preferences, and seniority
- **Customizable scheduling rules** including cooldowns, max shifts, and no-morning-after-night
- **Fair, constraint-aware scheduling** with automated rebalancing
- **Schedule locking**, shift visualization, and real-time edits

Navigate using the **sidebar** to:
1. Configure rule logic and generate employees
2. Build and rebalance weekly schedules
3. Visualize shift coverage by day, location, and type

---

💡 *Tip: Enable rebalancing in Setup to auto-adjust staffing gaps after initial schedule generation.*
""")
