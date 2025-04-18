import pandas as pd
from faker import Faker
import random
from datetime import datetime
import os

fake = Faker()

def generate_employees(
    num_employees=30,
    output_path="data/employees.csv",
    num_zones=3,
    shift_patterns=None,
    shift_types=None
):
    # Generate dynamic zone names
    locations = [f"Zone {i+1}" for i in range(num_zones)]

    # Use default patterns if none provided
    if not shift_patterns:
        shift_patterns = [
            ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
        ]

    if not shift_types:
        shift_types = ["Morning", "Afternoon"]

    employees = []
    for i in range(num_employees):
        name = fake.name()
        employee_id = f"E{i+1:03d}"
        phone = fake.phone_number()

        preferred_location = random.choice(locations)
        available_days = random.choice(shift_patterns)
        shift_preference = random.choice(shift_types)
        date_hired = fake.date_between(start_date='-3y', end_date='today').strftime("%Y-%m-%d")

        employees.append({
            "EmployeeID": employee_id,
            "Name": name,
            "Phone": phone,
            "PreferredLocations": [preferred_location],
            "AvailableDays": available_days,
            "ShiftPreference": shift_preference,
            "DateHired": date_hired
        })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pd.DataFrame(employees).to_csv(output_path, index=False)
