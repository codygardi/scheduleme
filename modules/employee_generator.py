import pandas as pd
from faker import Faker
import random
from datetime import datetime
import os

fake = Faker()

def generate_employees(num_employees=30, output_path="data/employees.csv"):
    locations = ["South Bay", "East Bay", "North Bay"]

    # Only allow these two weekly scheduling patterns
    weekday_options = [
        ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    ]

    employees = []
    for i in range(num_employees):
        name = fake.name()
        employee_id = f"E{i+1:03d}"
        phone = fake.phone_number()
        preferred_locations = random.sample(locations, k=random.randint(1, 2))
        available_days = random.choice(weekday_options)
        shift_preference = random.choice(["Morning", "Afternoon"])
        date_hired = fake.date_between(start_date='-3y', end_date='today').strftime("%Y-%m-%d")

        employees.append({
            "EmployeeID": employee_id,
            "Name": name,
            "Phone": phone,
            "PreferredLocations": preferred_locations,
            "AvailableDays": available_days,
            "ShiftPreference": shift_preference,
            "DateHired": date_hired
        })

    df = pd.DataFrame(employees)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Sample employee data saved to '{output_path}'")

    return df
