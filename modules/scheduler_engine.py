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
    'shift_preference_mode': 'soft',  # 'strict', 'soft', 'ignore'
    'location_preference_mode': 'soft',  # 'strict', 'soft', 'ignore'
    'use_seniority_weighting': True,

    'enforce_consecutive_day_limit': True,
    'max_consecutive_days': 5,
    'enforce_shift_cooldown': True,
    'min_hours_between_shifts': 12,

    'min_staff_threshold': 3,
    'max_staff_per_shift': 5,
    'max_shifts_per_employee': 5,
    'shift_types': ['Morning', 'Afternoon', 'Night'],
    'schedule_days': 7,
    'active_locations': ["ZoneA", "ZoneB", "ZoneC"],

    'balance_enabled': True,
    'balance_prefer_seniority': True,

    # NEWLY ENFORCED RULES
    'holiday_dates': [],
    'locked_locations': []
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

def count_consecutive_days_df(emp_id, date, df):
    count = 0
    for i in range(1, RULES['max_consecutive_days'] + 2):
        prev_day = date - timedelta(days=i)
        if not df[(df['EmployeeID'] == emp_id) & (df['Date'] == prev_day)].empty:
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
        if date.strftime('%Y-%m-%d') in RULES.get('holiday_dates', []):
            continue

        for location in locations:
            if location in RULES.get('locked_locations', []):
                continue

            for shift in shift_types:
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
                    elif loc_mode == 'soft' and location not in emp['PreferredLocations']:
                        pass

                    shift_mode = RULES['shift_preference_mode']
                    if shift_mode == 'strict' and shift not in emp['PreferredShifts']:
                        continue
                    elif shift_mode == 'soft' and shift not in emp['PreferredShifts']:
                        pass

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
                for _, _, emp in candidates[:RULES['max_staff_per_shift']]:
                    emp_id = emp['EmployeeID']
                    if (emp_id, date) not in schedule:
                        schedule[(emp_id, date)] = {
                            'Shift': shift,
                            'Location': location,
                            'Locked': False
                        }

    return schedule

# ----------------------------
# Rebalancer
# ----------------------------

def _rebalance_schedule(schedule_df, employees_df):
    if not RULES['balance_enabled']:
        return

    schedule_df['Date'] = pd.to_datetime(schedule_df['Date'])
    employees_df['DateHired'] = pd.to_datetime(employees_df['DateHired'])

    enriched = schedule_df.merge(
        employees_df[['EmployeeID', 'DateHired', 'WorkPattern']],
        on='EmployeeID',
        how='left'
    )

    shift_counts = (
        enriched.groupby(['Date', 'Location', 'Shift'])['EmployeeID']
        .count()
        .reset_index(name='Count')
    )

    for _, row in shift_counts.iterrows():
        date, loc, shift, count = row['Date'], row['Location'], row['Shift'], row['Count']
        if count >= RULES['min_staff_threshold']:
            continue
        if date.strftime('%Y-%m-%d') in RULES['holiday_dates']:
            continue
        if loc in RULES['locked_locations']:
            continue

        # Find overstaffed shift same day
        overs = shift_counts[
            (shift_counts['Date'] == date) &
            (shift_counts['Count'] >= RULES['max_staff_per_shift'])
        ]

        for _, over in overs.iterrows():
            donor_loc, donor_shift = over['Location'], over['Shift']
            if donor_loc == loc and donor_shift == shift:
                continue

            donor_emps = enriched[
                (enriched['Date'] == date) &
                (enriched['Location'] == donor_loc) &
                (enriched['Shift'] == donor_shift)
            ]

            if RULES['balance_prefer_seniority']:
                donor_emps = donor_emps.sort_values(by='DateHired')

            for _, emp in donor_emps.iterrows():
                emp_id = emp['EmployeeID']
                if emp.get('Locked'):
                    continue

                if RULES['enforce_work_pattern']:
                    if date.strftime('%A') not in emp['WorkPattern']:
                        continue

                # Morning-after-night rule
                if RULES['enforce_no_morning_after_night'] and shift == 'Morning':
                    prev_shift = enriched[
                        (enriched['EmployeeID'] == emp_id) &
                        (enriched['Date'] == date - timedelta(days=1))
                    ]
                    if not prev_shift.empty and prev_shift.iloc[0]['Shift'] == 'Night':
                        continue

                # Consecutive day limit
                if RULES['enforce_consecutive_day_limit']:
                    if count_consecutive_days_df(emp_id, date, enriched) >= RULES['max_consecutive_days']:
                        continue

                # Cooldown enforcement
                if RULES['enforce_shift_cooldown']:
                    prev_shift_df = enriched[
                        (enriched['EmployeeID'] == emp_id) &
                        (enriched['Date'] == date - timedelta(days=1))
                    ]
                    shift_hours = {'Morning': 8, 'Afternoon': 16, 'Night': 22}
                    if not prev_shift_df.empty:
                        prev_shift = prev_shift_df.iloc[0]['Shift']
                        prev_end = datetime.combine(date - timedelta(days=1), datetime.min.time()) + timedelta(
                            hours=shift_hours.get(prev_shift, 0))
                        new_start = datetime.combine(date, datetime.min.time()) + timedelta(
                            hours=shift_hours.get(shift, 0))
                        if (new_start - prev_end).total_seconds() < RULES['min_hours_between_shifts'] * 3600:
                            continue

                # Perform swap
                enriched.loc[
                    (enriched['EmployeeID'] == emp_id) & (enriched['Date'] == date),
                    ['Shift', 'Location']
                ] = [shift, loc]

                # One move per loop
                save_schedule(enriched.drop(columns=['DateHired', 'WorkPattern']))
                return


# ----------------------------
# Entry Points
# ----------------------------

def run_scheduler():
    employees = load_employees()
    employees['DateHired'] = pd.to_datetime(employees['DateHired'])

    def safe_json_load(x): return json.loads(x) if isinstance(x, str) else x
    for col in ['WorkPattern', 'PreferredLocations', 'PreferredShifts']:
        employees[col] = employees[col].apply(safe_json_load)

    # 🧹 Clear previous schedule
    save_schedule(pd.DataFrame(columns=['EmployeeID', 'Date', 'Shift', 'Location', 'Locked']))

    start_date = datetime.today()
    schedule_days = [start_date + timedelta(days=i) for i in range(RULES['schedule_days'])]
    schedule_dict = generate_schedule(employees, schedule_days, RULES['shift_types'], RULES['active_locations'])

    schedule_df = pd.DataFrame([
        {
            'EmployeeID': emp_id,
            'Date': date,
            'Shift': info['Shift'],
            'Location': info['Location'],
            'Locked': info.get('Locked', False)
        }
        for (emp_id, date), info in schedule_dict.items()
    ])

    save_schedule(schedule_df)

    if RULES['balance_enabled']:
        run_rebalancer()

def run_rebalancer():
    employees = load_employees()
    employees['DateHired'] = pd.to_datetime(employees['DateHired'])
    schedule_df = load_schedule()
    _rebalance_schedule(schedule_df, employees)
