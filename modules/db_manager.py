import pandas as pd
import os
import json
import streamlit as st

DB_DIR = "data"

# ----------------------------
# Utility
# ----------------------------

def get_session_id():
    if 'session_id' not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def get_employee_csv():
    return os.path.join(DB_DIR, f"{get_session_id()}_employees.csv")

def get_schedule_csv():
    return os.path.join(DB_DIR, f"{get_session_id()}_schedule.csv")

def safe_json(val):
    try:
        return json.loads(val) if isinstance(val, str) else val
    except Exception:
        return []

# ----------------------------
# Employee I/O
# ----------------------------

def load_employees():
    path = get_employee_csv()
    if not os.path.exists(path):
        return pd.DataFrame(columns=[
            "EmployeeID", "DateHired", "WorkPattern",
            "PreferredLocations", "PreferredShifts",
            "UnavailableDates", "PhoneNumber", "SkillLevel"
        ])
    
    df = pd.read_csv(path)
    df['DateHired'] = pd.to_datetime(df['DateHired'], errors='coerce')
    df['WorkPattern'] = df['WorkPattern'].apply(safe_json)
    df['PreferredLocations'] = df['PreferredLocations'].apply(safe_json)
    df['PreferredShifts'] = df.get('PreferredShifts', pd.Series([[]]*len(df))).apply(safe_json)
    df['UnavailableDates'] = df.get('UnavailableDates', pd.Series([[]]*len(df))).apply(safe_json)
    return df

def save_employees(df):
    os.makedirs(DB_DIR, exist_ok=True)
    df.to_csv(get_employee_csv(), index=False)

# ----------------------------
# Schedule I/O
# ----------------------------

def load_schedule():
    path = get_schedule_csv()
    if not os.path.exists(path):
        return pd.DataFrame(columns=[
            "EmployeeID", "Date", "Shift", "Location", "Locked"
        ])
    
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    if 'Locked' not in df.columns:
        df['Locked'] = False
    return df

def save_schedule(df):
    os.makedirs(DB_DIR, exist_ok=True)
    df.to_csv(get_schedule_csv(), index=False)

# ----------------------------
# Initialization
# ----------------------------

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)

    emp_path = get_employee_csv()
    sched_path = get_schedule_csv()

    if not os.path.exists(emp_path):
        pd.DataFrame(columns=[
            "EmployeeID", "DateHired", "WorkPattern",
            "PreferredLocations", "PreferredShifts",
            "UnavailableDates", "PhoneNumber", "SkillLevel"
        ]).to_csv(emp_path, index=False)

    if not os.path.exists(sched_path):
        pd.DataFrame(columns=[
            "EmployeeID", "Date", "Shift", "Location", "Locked"
        ]).to_csv(sched_path, index=False)
