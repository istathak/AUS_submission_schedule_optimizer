"""
Validation module for checking constraints and computing compatibility scores.
"""
import pandas as pd
from typing import Dict, List, Tuple
from compute_employee_profile import get_compatibility_score, extract_shift_features


def compute_assignment_compatibility(
    assignments: pd.DataFrame,
    employee_profiles: pd.DataFrame
) -> float:
    """
    Compute mean compatibility score for assigned shifts.
    
    Args:
        assignments: DataFrame with assigned shifts (must have EmployeeNumber and shift features)
        employee_profiles: DataFrame with employee profiles
        
    Returns:
        Mean compatibility score
    """
    assignments = extract_shift_features(assignments.copy())
    
    compatibility_scores = []
    
    for _, shift in assignments.iterrows():
        if pd.notna(shift['EmployeeNumber']):
            emp_num = int(shift['EmployeeNumber'])
            
            # Find employee profile
            emp_profile = employee_profiles[employee_profiles['EmployeeNumber'] == emp_num]
            if len(emp_profile) == 0:
                continue
            
            emp_profile = emp_profile.iloc[0]
            
            # Compute compatibility score
            score = get_compatibility_score(
                emp_profile,
                int(shift['DayNum']),
                shift['ShiftTimeCategory'],
                shift['ShiftDurationCategory'],
                int(shift['JobNumber']),
                shift['ShiftType']
            )
            
            compatibility_scores.append(score)
    
    if len(compatibility_scores) == 0:
        return 0.0
    
    return sum(compatibility_scores) / len(compatibility_scores)


def validate_filled_shifts_constraints(filled_shifts: pd.DataFrame) -> Dict[str, any]:
    """
    Validate constraints on already-filled shifts (before optimization).
    
    Args:
        filled_shifts: DataFrame with filled shifts (must have EmployeeNumber, DayNum, ShiftDurationHours)
        
    Returns:
        Dictionary with validation results including violations
    """
    violations = {
        'weekly_hours': [],
        'work_days': [],
        'daily_shifts': []
    }
    
    if len(filled_shifts) == 0:
        return {
            'valid': True,
            'violations': violations,
            'total_violations': 0
        }
    
    # Assume all shifts are in week 0 (single scheduling week)
    week = 0
    
    employee_week_hours = {}
    employee_week_days = {}
    employee_day_shifts = {}
    
    for _, shift in filled_shifts.iterrows():
        if pd.notna(shift['EmployeeNumber']):
            emp = int(shift['EmployeeNumber'])
            day = int(shift['DayNum'])
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
    
    # Check constraints
    for (emp, w), hours in employee_week_hours.items():
        if hours > 40:
            violations['weekly_hours'].append({
                'employee': emp,
                'week': w,
                'hours': hours,
                'limit': 40
            })
    
    for (emp, w), days in employee_week_days.items():
        if len(days) > 5:
            violations['work_days'].append({
                'employee': emp,
                'week': w,
                'days': len(days),
                'limit': 5
            })
    
    for (emp, day), count in employee_day_shifts.items():
        if count > 1:
            violations['daily_shifts'].append({
                'employee': emp,
                'day': day,
                'count': count,
                'limit': 1
            })
    
    total_violations = (
        len(violations['weekly_hours']) +
        len(violations['work_days']) +
        len(violations['daily_shifts'])
    )
    
    return {
        'valid': total_violations == 0,
        'violations': violations,
        'total_violations': total_violations,
        'employee_week_hours': employee_week_hours,
        'employee_week_days': {k: len(v) for k, v in employee_week_days.items()},
        'employee_day_shifts': employee_day_shifts
    }


def validate_constraints(snapshot: pd.DataFrame) -> Dict[str, any]:
    """
    Validate that all scheduling constraints are satisfied.
    
    Args:
        snapshot: DataFrame with filled shifts (must have EmployeeNumber, DayNum, ShiftDurationHours)
        
    Returns:
        Dictionary with validation results including violations
    """
    violations = {
        'weekly_hours': [],  # List of (employee, week, hours) violations
        'work_days': [],      # List of (employee, week, days) violations
        'daily_shifts': []    # List of (employee, day, count) violations
    }
    
    # Group by employee
    filled_shifts = snapshot[snapshot['EmployeeNumber'].notna()].copy()
    
    if len(filled_shifts) == 0:
        return {
            'valid': True,
            'violations': violations,
            'total_violations': 0
        }
    
    # For simplicity, assume all shifts are in week 0 (single scheduling week)
    # In a full implementation, we'd group by actual scheduling weeks
    week = 0
    
    employee_week_hours = {}  # (emp, week) -> hours
    employee_week_days = {}   # (emp, week) -> set of days
    employee_day_shifts = {}  # (emp, day) -> count
    
    for _, shift in filled_shifts.iterrows():
        emp = int(shift['EmployeeNumber'])
        day = int(shift['DayNum'])
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
    
    # Check constraints
    for (emp, w), hours in employee_week_hours.items():
        if hours > 40:
            violations['weekly_hours'].append({
                'employee': emp,
                'week': w,
                'hours': hours,
                'limit': 40
            })
    
    for (emp, w), days in employee_week_days.items():
        if len(days) > 5:
            violations['work_days'].append({
                'employee': emp,
                'week': w,
                'days': len(days),
                'limit': 5
            })
    
    for (emp, day), count in employee_day_shifts.items():
        if count > 1:
            violations['daily_shifts'].append({
                'employee': emp,
                'day': day,
                'count': count,
                'limit': 1
            })
    
    total_violations = (
        len(violations['weekly_hours']) +
        len(violations['work_days']) +
        len(violations['daily_shifts'])
    )
    
    return {
        'valid': total_violations == 0,
        'violations': violations,
        'total_violations': total_violations,
        'employee_week_hours': employee_week_hours,
        'employee_week_days': {k: len(v) for k, v in employee_week_days.items()},
        'employee_day_shifts': employee_day_shifts
    }
