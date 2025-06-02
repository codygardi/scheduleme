import pandas as pd
from datetime import datetime, timedelta
import json
from modules.db_manager import load_employees, save_schedule, load_schedule

# ----------------------------
# Configuration
# ----------------------------

RULES = {
    'enforce_work_pattern': True,
    'enforce_max_one_shift_per_day': True,
    'enforce_no_morning_after_night': True,
    'shift_preference_mode': 'soft',
    'location_preference_mode': 'soft',
    'use_seniority_weighting': True,

    'enforce_consecutive_day_limit': True,
    'max_consecutive_days': 5,
    'enforce_shift_cooldown': True,
    'min_hours_between_shifts': 12,

    'min_staff_threshold': 1,
    'max_staff_per_shift': 3,
    'max_shifts_per_employee': 5,
    'shift_types': ['Morning', 'Afternoon', 'Night'],
    'schedule_days': 7,
    'active_locations': ["ZoneA", "ZoneB", "ZoneC"],
    'holiday_dates': []
}

# ----------------------------
# Helpers
# ----------------------------

def is_working_today(employee, date):
    return date.strftime('%A') in employee['WorkPattern'] if RULES['enforce_work_pattern'] else True

def is_unavailable(employee, date):
    try:
        return date.strftime('%Y-%m-%d') in json.loads(employee.get("UnavailableDates", "[]"))
    except Exception:
        return False

def get_assigned_shift(schedule, emp_id, date):
    return schedule.get((emp_id, date), {}).get('Shift')

def is_locked(schedule, emp_id, date):
    return schedule.get((emp_id, date), {}).get('Locked', False)

def get_last_shift_datetime(schedule, emp_id, date):
    prev_day = date - timedelta(days=1)
    prev_shift = get_assigned_shift(schedule, emp_id, prev_day)
    shift_hours = {'Morning': 8, 'Afternoon': 16, 'Night': 22}
    return datetime.combine(prev_day, datetime.min.time()) + timedelta(hours=shift_hours.get(prev_shift, 0)) if prev_shift else None

def is_already_scheduled(schedule, emp_id, date):
    return (emp_id, date) in schedule

def count_weekly_assignments(schedule, emp_id):
    return sum(1 for (e, _), v in schedule.items() if e == emp_id and not v.get('Locked', False))

def count_consecutive_days(schedule, emp_id, current_date):
    count = 0
    for i in range(1, RULES['max_consecutive_days'] + 2):
        if (emp_id, current_date - timedelta(days=i)) in schedule:
            count += 1
        else:
            break
    return count

# ----------------------------
# Main Scheduler
# ----------------------------

def generate_schedule(employees_df, schedule_days, shift_types, locations):
    existing_schedule_df = load_schedule()
    schedule = {
        (row['EmployeeID'], row['Date']): {
            'Shift': row['Shift'],
            'Location': row['Location'],
            'Locked': row.get('Locked', False)
        } for _, row in existing_schedule_df.iterrows()
    }

    for date in schedule_days:
        if date.strftime('%Y-%m-%d') in RULES['holiday_dates']:
            continue

        for location in locations:
            for shift in shift_types:
                current_count = sum(
                    1 for (eid, d), val in schedule.items()
                    if d == date and val['Shift'] == shift and val['Location'] == location
                )
                if current_count >= RULES['min_staff_threshold']:
                    continue

                candidates = []

                for _, emp in employees_df.iterrows():
                    emp_id = emp['EmployeeID']
                    if is_locked(schedule, emp_id, date): continue
                    if not is_working_today(emp, date): continue
                    if is_unavailable(emp, date): continue
                    if RULES['enforce_max_one_shift_per_day'] and is_already_scheduled(schedule, emp_id, date): continue
                    if count_weekly_assignments(schedule, emp_id) >= RULES['max_shifts_per_employee']: continue

                    loc_mode = RULES['location_preference_mode']
                    if loc_mode == 'strict' and location not in emp['PreferredLocations']:
                        continue

                    shift_mode = RULES['shift_preference_mode']
                    if shift_mode == 'strict' and shift not in emp['PreferredShifts']:
                        continue

                    prev_shift = get_assigned_shift(schedule, emp_id, date - timedelta(days=1))
                    if RULES['enforce_no_morning_after_night'] and shift == 'Morning' and prev_shift == 'Night':
                        continue

                    if RULES['enforce_consecutive_day_limit']:
                        if count_consecutive_days(schedule, emp_id, date) >= RULES['max_consecutive_days']:
                            continue

                    if RULES['enforce_shift_cooldown']:
                        last_shift_time = get_last_shift_datetime(schedule, emp_id, date)
                        if last_shift_time:
                            current_time = datetime.combine(date, datetime.min.time()) + timedelta(
                                hours={'Morning': 8, 'Afternoon': 16, 'Night': 22}[shift])
                            if (current_time - last_shift_time).total_seconds() < RULES['min_hours_between_shifts'] * 3600:
                                continue

                    score = 0
                    if location in emp['PreferredLocations']:
                        score += 1
                    elif loc_mode == 'soft':
                        score -= 1

                    if shift in emp['PreferredShifts']:
                        score += 1
                    elif shift_mode == 'soft':
                        score -= 1

                    candidates.append((score, emp['DateHired'], emp))

                candidates.sort(key=lambda x: (-x[0], x[1]) if RULES['use_seniority_weighting'] else (0, x[1]))

                for _, _, emp in candidates:
                    emp_id = emp['EmployeeID']
                    if (emp_id, date) in schedule:
                        continue
                    schedule[(emp_id, date)] = {
                        'Shift': shift,
                        'Location': location,
                        'Locked': False
                    }
                    current_count += 1
                    if current_count >= RULES['min_staff_threshold']:
                        break

    return schedule

# ----------------------------
# Fill Gaps
# ----------------------------

def fill_schedule_gaps(schedule, employees_df, schedule_days, shift_types, locations):
    for date in schedule_days:
        if date.strftime('%Y-%m-%d') in RULES['holiday_dates']:
            continue

        for location in locations:
            for shift in shift_types:
                current_count = sum(
                    1 for (eid, d), v in schedule.items()
                    if d == date and v['Shift'] == shift and v['Location'] == location
                )

                while current_count < RULES['max_staff_per_shift']:
                    candidates = []

                    for _, emp in employees_df.iterrows():
                        emp_id = emp['EmployeeID']
                        if (emp_id, date) in schedule:
                            continue
                        if is_locked(schedule, emp_id, date): continue
                        if not is_working_today(emp, date): continue
                        if is_unavailable(emp, date): continue
                        if RULES['enforce_max_one_shift_per_day'] and is_already_scheduled(schedule, emp_id, date): continue
                        if count_weekly_assignments(schedule, emp_id) >= RULES['max_shifts_per_employee']: continue

                        loc_mode = RULES['location_preference_mode']
                        if loc_mode == 'strict' and location not in emp['PreferredLocations']:
                            continue

                        shift_mode = RULES['shift_preference_mode']
                        if shift_mode == 'strict' and shift not in emp['PreferredShifts']:
                            continue

                        prev_shift = get_assigned_shift(schedule, emp_id, date - timedelta(days=1))
                        if RULES['enforce_no_morning_after_night'] and shift == 'Morning' and prev_shift == 'Night':
                            continue

                        if RULES['enforce_consecutive_day_limit']:
                            if count_consecutive_days(schedule, emp_id, date) >= RULES['max_consecutive_days']:
                                continue

                        if RULES['enforce_shift_cooldown']:
                            last_shift_time = get_last_shift_datetime(schedule, emp_id, date)
                            if last_shift_time:
                                current_time = datetime.combine(date, datetime.min.time()) + timedelta(
                                    hours={'Morning': 8, 'Afternoon': 16, 'Night': 22}[shift])
                                if (current_time - last_shift_time).total_seconds() < RULES['min_hours_between_shifts'] * 3600:
                                    continue

                        score = 0
                        if location in emp['PreferredLocations']:
                            score += 1
                        elif loc_mode == 'soft':
                            score -= 1

                        if shift in emp['PreferredShifts']:
                            score += 1
                        elif shift_mode == 'soft':
                            score -= 1

                        candidates.append((score, emp['DateHired'], emp))

                    if not candidates:
                        break

                    candidates.sort(key=lambda x: (-x[0], x[1]) if RULES['use_seniority_weighting'] else (0, x[1]))
                    _, _, chosen = candidates[0]
                    schedule[(chosen['EmployeeID'], date)] = {
                        'Shift': shift,
                        'Location': location,
                        'Locked': False
                    }
                    current_count += 1

# ----------------------------
# Entry Point
# ----------------------------

def run_scheduler():
    employees = load_employees()
    employees['DateHired'] = pd.to_datetime(employees['DateHired'])

    def safe_json_load(x): return json.loads(x) if isinstance(x, str) else x
    for col in ['WorkPattern', 'PreferredLocations', 'PreferredShifts']:
        employees[col] = employees[col].apply(safe_json_load)

    save_schedule(pd.DataFrame(columns=['EmployeeID', 'Date', 'Shift', 'Location', 'Locked']))

    start_date = datetime.today()
    schedule_days = [start_date + timedelta(days=i) for i in range(RULES['schedule_days'])]

    schedule_dict = generate_schedule(employees, schedule_days, RULES['shift_types'], RULES['active_locations'])
    fill_schedule_gaps(schedule_dict, employees, schedule_days, RULES['shift_types'], RULES['active_locations'])
    
    # Create a mapping from EmployeeID to FullName
    id_to_name = dict(zip(employees['EmployeeID'], employees['Name']))

    schedule_df = pd.DataFrame([
        {
            'EmployeeID': emp_id,
            'Name': id_to_name.get(emp_id, "Unknown"),
            'Date': date,
            'Shift': info['Shift'],
            'Location': info['Location'],
            'Locked': info.get('Locked', False)
        }
        for (emp_id, date), info in schedule_dict.items()
    ])

    save_schedule(schedule_df)
