import pandas as pd
import random
import json
from datetime import datetime, timedelta
from modules.db_manager import save_employees
from modules.scheduler_engine import RULES

LOCATIONS = RULES['active_locations']
SHIFT_TYPES = RULES['shift_types']
WORK_PATTERNS = [
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    ["Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"],
    ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
]
SKILL_LEVELS = ["Tech1", "Tech2", "Tech3"]

def generate_employees(n=30, seed=42):
    random.seed(seed)
    employees = []
    today = datetime.today()

    for i in range(n):
        emp_id = f"E{i:03}"
        hire_date = today - timedelta(days=random.randint(30, 1000))
        work_pattern = random.choice(WORK_PATTERNS)
        preferred_locations = random.sample(LOCATIONS, k=random.choice([1, 2]))
        preferred_shifts = random.sample(SHIFT_TYPES, k=random.choice([1, len(SHIFT_TYPES)]))
        skill_level = random.choice(SKILL_LEVELS)

        # Generate 1–3 unavailable days in the next 2 weeks
        unavailable_days = sorted(list({
            (today + timedelta(days=random.randint(0, 13))).strftime('%Y-%m-%d')
            for _ in range(random.randint(1, 3))
        }))

        employees.append({
            "EmployeeID": emp_id,
            "DateHired": hire_date.strftime('%Y-%m-%d'),
            "WorkPattern": json.dumps(work_pattern),
            "PreferredLocations": json.dumps(preferred_locations),
            "PreferredShifts": json.dumps(preferred_shifts),
            "SkillLevel": skill_level,
            "UnavailableDates": json.dumps(unavailable_days)
        })

    df = pd.DataFrame(employees)
    save_employees(df)
    return df
