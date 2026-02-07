"""
Optimization module for assigning employees to unfilled shifts using constrained optimization.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpStatus
from compute_employee_profile import extract_shift_features, get_compatibility_score


def compute_compatibility_matrix(
    unfilled_shifts: pd.DataFrame,
    employee_profiles: pd.DataFrame
) -> pd.DataFrame:
    """
    Compute compatibility scores for all employee-shift pairs.
    
    Args:
        unfilled_shifts: DataFrame with unfilled shifts (must have shift features)
        employee_profiles: DataFrame with employee profiles
        
    Returns:
        DataFrame with columns: EmployeeNumber, ScheduleDetailID, DayNum, CompatibilityScore
    """
    unfilled_shifts = extract_shift_features(unfilled_shifts.copy())
    
    compatibility_scores = []
    
    for _, shift in unfilled_shifts.iterrows():
        shift_day = int(shift['DayNum'])
        shift_time_cat = shift['ShiftTimeCategory']
        shift_duration_cat = shift['ShiftDurationCategory']
        shift_job = int(shift['JobNumber'])
        shift_type = shift['ShiftType']
        shift_id = (int(shift['ScheduleDetailID']), shift_day)
        
        for _, emp_profile in employee_profiles.iterrows():
            emp_num = int(emp_profile['EmployeeNumber'])
            
            # Compute compatibility score
            score = get_compatibility_score(
                emp_profile,
                shift_day,
                shift_time_cat,
                shift_duration_cat,
                shift_job,
                shift_type
            )
            
            compatibility_scores.append({
                'EmployeeNumber': emp_num,
                'ScheduleDetailID': shift['ScheduleDetailID'],
                'DayNum': shift_day,
                'CompatibilityScore': score,
                'ShiftDurationHours': shift['ShiftDurationHours']
            })
    
    return pd.DataFrame(compatibility_scores)


def group_shifts_by_week(shifts: pd.DataFrame) -> Dict[int, List[Tuple[int, int]]]:
    """
    Group shifts by scheduling week.
    Since we don't have actual dates, we'll assume all shifts in latest snapshot
    are in the same scheduling week (Friday=Day1 to Thursday=Day7).
    
    Args:
        shifts: DataFrame with shifts (must have ScheduleDetailID and DayNum)
        
    Returns:
        Dictionary mapping week_id to list of (ScheduleDetailID, DayNum) tuples
    """
    # For now, assume all shifts are in week 0 (single week)
    # In a full implementation, we'd use actual dates to determine weeks
    week_shifts = {}
    week_id = 0
    
    shift_list = []
    for _, shift in shifts.iterrows():
        shift_id = (int(shift['ScheduleDetailID']), int(shift['DayNum']))
        shift_list.append(shift_id)
    
    week_shifts[week_id] = shift_list
    return week_shifts


def solve_assignment(
    unfilled_shifts: pd.DataFrame,
    employee_profiles: pd.DataFrame,
    filled_shifts: pd.DataFrame
) -> Dict[Tuple[int, int], int]:
    """
    Solve the optimization problem to assign employees to unfilled shifts.
    
    Args:
        unfilled_shifts: DataFrame with unfilled shifts
        employee_profiles: DataFrame with employee profiles
        filled_shifts: DataFrame with already filled shifts (for constraint checking)
        
    Returns:
        Dictionary mapping (ScheduleDetailID, DayNum) to EmployeeNumber
    """
    # Compute compatibility matrix
    compatibility_df = compute_compatibility_matrix(unfilled_shifts, employee_profiles)
    
    # Get unique employees and shifts
    employees = sorted(employee_profiles['EmployeeNumber'].astype(int).unique())
    shift_ids = []
    for _, shift in unfilled_shifts.iterrows():
        shift_id = (int(shift['ScheduleDetailID']), int(shift['DayNum']))
        shift_ids.append(shift_id)
    
    # Create shift lookup for duration
    shift_durations = {}
    for _, shift in unfilled_shifts.iterrows():
        shift_id = (int(shift['ScheduleDetailID']), int(shift['DayNum']))
        shift_durations[shift_id] = shift['ShiftDurationHours']
    
    # Create compatibility lookup
    compatibility = {}
    for _, row in compatibility_df.iterrows():
        emp = int(row['EmployeeNumber'])
        shift_id = (int(row['ScheduleDetailID']), int(row['DayNum']))
        compatibility[(emp, shift_id)] = row['CompatibilityScore']
    
    # Group shifts by week (for now, all in same week)
    week_shifts = group_shifts_by_week(unfilled_shifts)
    
    # Calculate current assignments for constraint checking
    # For filled shifts, calculate hours and days per employee per week
    employee_week_hours = {}  # (emp, week) -> hours
    employee_week_days = {}   # (emp, week) -> set of days
    employee_day_shifts = {}  # (emp, day) -> count
    
    for _, shift in filled_shifts.iterrows():
        if pd.notna(shift['EmployeeNumber']):
            emp = int(shift['EmployeeNumber'])
            day = int(shift['DayNum'])
            week = 0  # All in same week for now
            duration = shift.get('ShiftDurationHours', 8.0)
            
            # Update hours
            key = (emp, week)
            employee_week_hours[key] = employee_week_hours.get(key, 0) + duration
            
            # Update days
            if key not in employee_week_days:
                employee_week_days[key] = set()
            employee_week_days[key].add(day)
            
            # Update daily shifts
            day_key = (emp, day)
            employee_day_shifts[day_key] = employee_day_shifts.get(day_key, 0) + 1
    
    # Filter out employees who already violate constraints
    # These employees cannot be assigned any more shifts
    valid_employees = []
    excluded_employees = []
    exclusion_reasons = {'hours': 0, 'days': 0, 'daily': 0}
    
    for emp in employees:
        week = 0
        key = (emp, week)
        
        # Check if employee already violates constraints
        current_hours = employee_week_hours.get(key, 0)
        current_days = len(employee_week_days.get(key, set()))
        
        # Check if employee has any day with > 1 shift
        has_daily_violation = any(
            count > 1 for (e, d), count in employee_day_shifts.items() if e == emp
        )
        
        # Exclude if already at or over constraint limits
        # Employees at the limit (40 hrs, 5 days) cannot take more shifts
        if current_hours >= 40:
            excluded_employees.append(emp)
            exclusion_reasons['hours'] += 1
        elif current_days >= 5:
            excluded_employees.append(emp)
            exclusion_reasons['days'] += 1
        elif has_daily_violation:
            excluded_employees.append(emp)
            exclusion_reasons['daily'] += 1
        else:
            valid_employees.append(emp)
    
    if len(excluded_employees) > 0:
        print(f"  Excluding {len(excluded_employees)} employees who already violate constraints:")
        print(f"    Hours > 40: {exclusion_reasons['hours']}")
        print(f"    Days > 5: {exclusion_reasons['days']}")
        print(f"    Daily shifts > 1: {exclusion_reasons['daily']}")
    
    if len(valid_employees) == 0:
        print("  No valid employees available for assignment (all violate constraints)")
        return {}
    
    # Create optimization problem
    prob = LpProblem("Shift_Assignment", LpMaximize)
    
    # Decision variables: x[emp, shift_id] = 1 if assigned, 0 otherwise
    # Only create variables for valid employees
    x = {}
    for emp in valid_employees:
        for shift_id in shift_ids:
            x[(emp, shift_id)] = LpVariable(f"x_{emp}_{shift_id[0]}_{shift_id[1]}", cat='Binary')
    
    # Objective: Maximize total compatibility
    prob += lpSum([compatibility.get((emp, shift_id), 0.0) * x[(emp, shift_id)]
                   for emp in valid_employees for shift_id in shift_ids])
    
    # Constraint 1: Each shift assigned to at most one employee
    for shift_id in shift_ids:
        prob += lpSum([x[(emp, shift_id)] for emp in valid_employees]) <= 1
    
    # Constraint 2: Weekly hours limit (40 hours per week)
    for emp in valid_employees:
        for week, week_shift_list in week_shifts.items():
            # Current hours from filled shifts
            current_hours = employee_week_hours.get((emp, week), 0)
            
            # Hours from new assignments
            new_hours = lpSum([shift_durations[shift_id] * x[(emp, shift_id)]
                              for shift_id in week_shift_list if shift_id in shift_ids])
            
            prob += current_hours + new_hours <= 40
    
    # Constraint 3: Work days limit (5 days per week)
    # For each employee and week, count unique days worked
    for emp in valid_employees:
        for week, week_shift_list in week_shifts.items():
            # Current days from filled shifts
            current_days = len(employee_week_days.get((emp, week), set()))
            
            # Get unique days in unfilled shifts for this week
            days_in_week = set()
            for shift_id in week_shift_list:
                if shift_id in shift_ids:
                    days_in_week.add(shift_id[1])  # DayNum is second element
            
            # For each unique day, create a binary variable indicating if employee works that day
            day_vars = {}
            for day in days_in_week:
                day_vars[day] = LpVariable(f"day_{emp}_{week}_{day}", cat='Binary')
                # Link day variable to shift assignments: if any shift on this day is assigned, day_var = 1
                shifts_on_day = [shift_id for shift_id in week_shift_list 
                               if shift_id in shift_ids and shift_id[1] == day]
                if shifts_on_day:
                    for shift_id in shifts_on_day:
                        prob += day_vars[day] >= x[(emp, shift_id)]
                    prob += day_vars[day] <= lpSum([x[(emp, shift_id)] for shift_id in shifts_on_day])
            
            # Total days worked (current + new) <= 5
            if day_vars:
                prob += current_days + lpSum(day_vars.values()) <= 5
            else:
                prob += current_days <= 5
    
    # Constraint 4: Daily shift limit (1 shift per day)
    # Group shifts by employee and day, then sum all assignments for that day
    for emp in valid_employees:
        # Get all unique days in unfilled shifts
        days_with_shifts = set(shift_id[1] for shift_id in shift_ids)
        
        for day in days_with_shifts:
            day_key = (emp, day)
            
            # Current shifts on this day from filled shifts
            current_shifts = employee_day_shifts.get(day_key, 0)
            
            # All new shifts on this day for this employee
            shifts_on_day = [shift_id for shift_id in shift_ids if shift_id[1] == day]
            new_shifts_sum = lpSum([x[(emp, shift_id)] for shift_id in shifts_on_day])
            
            # Total shifts (current + new) <= 1
            prob += current_shifts + new_shifts_sum <= 1
    
    # Solve
    status = prob.solve()
    
    # Check if solution was found
    if status != 1:  # 1 = Optimal, -1 = Infeasible, -2 = Unbounded, etc.
        print(f"  Warning: Solver status: {LpStatus[status]}")
        if status == -1:
            print("  Problem is infeasible - no solution found that satisfies all constraints")
            return {}
    
    # Extract solution
    assignments = {}
    for emp in valid_employees:
        for shift_id in shift_ids:
            var_value = x[(emp, shift_id)].varValue
            if var_value is not None and var_value > 0.5:  # Binary variable, check > 0.5
                if shift_id not in assignments:  # Only assign once per shift
                    assignments[shift_id] = emp
                else:
                    # This shouldn't happen, but log if it does
                    print(f"  Warning: Shift {shift_id} already assigned to {assignments[shift_id]}, skipping assignment to {emp}")
    
    return assignments


def fill_unfilled_shifts(
    latest_snapshot: pd.DataFrame,
    employee_profiles: pd.DataFrame
) -> pd.DataFrame:
    """
    Fill unfilled shifts in the latest snapshot using optimization.
    
    Args:
        latest_snapshot: Preprocessed latest snapshot DataFrame
        employee_profiles: DataFrame with employee profiles
        
    Returns:
        DataFrame with filled assignments (EmployeeNumber filled in for previously unfilled shifts)
    """
    result = latest_snapshot.copy()
    
    # Separate filled and unfilled shifts
    filled_shifts = result[result['EmployeeNumber'].notna()].copy()
    unfilled_shifts = result[result['EmployeeNumber'].isna()].copy()
    
    if len(unfilled_shifts) == 0:
        return result
    
    # Deduplicate unfilled shifts before solving (one row per ScheduleDetailID/DayNum)
    # This ensures we don't try to assign the same shift multiple times
    unfilled_shifts_deduped = unfilled_shifts.drop_duplicates(
        subset=['ScheduleDetailID', 'DayNum'], 
        keep='first'
    ).copy()
    
    # Solve assignment problem
    assignments = solve_assignment(unfilled_shifts_deduped, employee_profiles, filled_shifts)
    
    if len(assignments) == 0:
        print("  No assignments made (problem may be infeasible)")
        return result
    
    # Apply assignments (only to first row per ScheduleDetailID/DayNum to avoid duplicates)
    for shift_id, emp_num in assignments.items():
        schedule_detail_id, day_num = shift_id
        # Find unfilled rows matching this shift
        mask = (
            (result['ScheduleDetailID'] == schedule_detail_id) & 
            (result['DayNum'] == day_num) & 
            (result['IsUnfilled'])
        )
        # Only update the first matching row to avoid duplicate assignments
        matching_indices = result[mask].index
        if len(matching_indices) > 0:
            result.loc[matching_indices[0], 'EmployeeNumber'] = float(emp_num)
            result.loc[matching_indices[0], 'IsUnfilled'] = False
    
    return result
