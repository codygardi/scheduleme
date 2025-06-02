import pandas as pd
import random
import json
import string
from datetime import datetime, timedelta
from modules.db_manager import save_employees
from modules.scheduler_engine import RULES
from faker import Faker

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
    fake = Faker()
    Faker.seed(seed)

    def generate_id():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    employees = []
    today = datetime.today()
    used_ids = set()

    for _ in range(n):
        emp_id = generate_id()
        while emp_id in used_ids:
            emp_id = generate_id()
        used_ids.add(emp_id)

        hire_date = today - timedelta(days=random.randint(30, 1000))
        work_pattern = random.choice(WORK_PATTERNS)
        preferred_locations = random.sample(LOCATIONS, k=random.choice([1, 2]))
        preferred_shifts = random.sample(SHIFT_TYPES, k=random.choice([1, len(SHIFT_TYPES)]))
        skill_level = random.choice(SKILL_LEVELS)
        full_name = fake.name()
        phone_number= fake.phone_number()
        unavailable_days = sorted(list({
            (today + timedelta(days=random.randint(8, 24))).strftime('%Y-%m-%d')
            for _ in range(random.randint(1, 3))
        }))

        employees.append({
            "EmployeeID": emp_id,
            "Name": full_name,
            "PhoneNumber": phone_number,
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
