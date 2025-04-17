import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import itertools
import ast
import os

def run_scheduler(employee_path="data/employees.csv",
                  output_path="data/weekly_schedule.csv",
                  min_shifts_required=5):

    if not os.path.exists(employee_path):
        raise FileNotFoundError("Employee file not found.")

    employee_df = pd.read_csv(employee_path, converters={
        'PreferredLocations': ast.literal_eval,
        'AvailableDays': ast.literal_eval
    })
    employee_df['DateHired'] = pd.to_datetime(employee_df['DateHired'])
    employee_df.sort_values('DateHired', inplace=True)

    shifts = ['Morning', 'Afternoon']
    locations = ['South Bay', 'East Bay', 'North Bay']
    max_per_shift = 5
    weekend_days = ['Saturday', 'Sunday']

    today = datetime.today()
    days_until_sunday = (6 - today.weekday()) % 7 + 1 if today.weekday() != 6 else 0
    start_date = today + timedelta(days=days_until_sunday)
    date_range = pd.date_range(start=start_date, periods=7)

    schedule = []
    employee_shifts = defaultdict(list)
    employee_scheduled_days = defaultdict(set)
    employee_weekend_flag = defaultdict(bool)
    round_robin_office_iter = itertools.cycle(locations)

    def get_balanced_offices(preferred, used_today):
        for _ in range(len(locations)):
            location = next(round_robin_office_iter)
            if location in preferred and location not in used_today:
                yield location
        for location in locations:
            if location not in used_today:
                yield location

    def try_assign(emp, date_str, day_name, shift_list):
        emp_id = emp['EmployeeID']
        used_offices_today = set()

        for shift in shift_list:
            for location in get_balanced_offices(emp['PreferredLocations'], used_offices_today):
                used_offices_today.add(location)

                assigned = [s for s in schedule if s['Date'] == date_str and s['Shift'] == shift and s['Location'] == location]
                if len(assigned) >= max_per_shift:
                    continue

                schedule.append({
                    'EmployeeID': emp_id,
                    'Name': emp['Name'],
                    'Phone': emp['Phone'],
                    'Date': date_str,
                    'Shift': shift,
                    'Location': location
                })
                employee_shifts[emp_id].append((date_str, shift))
                employee_scheduled_days[emp_id].add(date_str)
                if day_name in weekend_days:
                    employee_weekend_flag[emp_id] = True
                return True
        return False

    # Phase 1: Assign by seniority and availability
    for _, emp in employee_df.iterrows():
        emp_id = emp['EmployeeID']
        shifts_assigned = 0

        for date in date_range:
            day_name = date.strftime('%A')
            date_str = date.strftime('%Y-%m-%d')
            if date_str in employee_scheduled_days[emp_id] or day_name not in emp['AvailableDays']:
                continue

            shift_order = [emp['ShiftPreference']] + [s for s in shifts if s != emp['ShiftPreference']]
            if try_assign(emp, date_str, day_name, shift_order):
                shifts_assigned += 1
            if shifts_assigned >= min_shifts_required:
                break

    # Phase 2: Enforce at least one weekend shift if possible
    for _, emp in employee_df.iterrows():
        emp_id = emp['EmployeeID']
        if employee_weekend_flag[emp_id]:
            continue

        for date in date_range:
            day_name = date.strftime('%A')
            date_str = date.strftime('%Y-%m-%d')
            if day_name not in weekend_days or day_name not in emp['AvailableDays']:
                continue
            if date_str in employee_scheduled_days[emp_id]:
                continue
            if try_assign(emp, date_str, day_name, shifts):
                break

    # Phase 3: Retry pass for under-scheduled employees
    retry_list = sorted(
        [(emp['EmployeeID'], len(employee_shifts[emp['EmployeeID']]), emp) for _, emp in employee_df.iterrows()],
        key=lambda x: x[1]
    )

    for emp_id, shift_count, emp in retry_list:
        while len(employee_shifts[emp_id]) < min_shifts_required:
            for date in date_range:
                day_name = date.strftime('%A')
                date_str = date.strftime('%Y-%m-%d')
                if date_str in employee_scheduled_days[emp_id] or day_name not in emp['AvailableDays']:
                    continue
                if try_assign(emp, date_str, day_name, shifts):
                    break
            else:
                break

    # Phase 4: Enforce minimum 2 employees per shift/location per day
    shift_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for s in schedule:
        shift_counts[s['Date']][s['Location']][s['Shift']] += 1

    for date in date_range:
        date_str = date.strftime('%Y-%m-%d')
        day_name = date.strftime('%A')
        for location in locations:
            for shift in shifts:
                current_count = shift_counts[date_str][location][shift]
                while current_count < 2:
                    eligible = employee_df[
                        employee_df['AvailableDays'].apply(lambda x: day_name in x) &
                        ~employee_df['EmployeeID'].isin([
                            s['EmployeeID'] for s in schedule if s['Date'] == date_str
                        ]) &
                        employee_df['PreferredLocations'].apply(lambda x: location in x)
                    ]

                    if eligible.empty:
                        break

                    emp = eligible.iloc[0]
                    schedule.append({
                        'EmployeeID': emp['EmployeeID'],
                        'Name': emp['Name'],
                        'Phone': emp['Phone'],
                        'Date': date_str,
                        'Shift': shift,
                        'Location': location
                    })
                    employee_shifts[emp['EmployeeID']].append((date_str, shift))
                    employee_scheduled_days[emp['EmployeeID']].add(date_str)
                    if day_name in weekend_days:
                        employee_weekend_flag[emp['EmployeeID']] = True
                    shift_counts[date_str][location][shift] += 1
                    current_count += 1

    schedule_df = pd.DataFrame(schedule)
    schedule_df.to_csv(output_path, index=False)
    return schedule_df
