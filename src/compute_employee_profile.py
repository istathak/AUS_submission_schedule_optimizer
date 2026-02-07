"""
Pattern learning module for extracting employee shift preferences from historical data.
"""
import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime, timedelta
from collections import defaultdict


def extract_shift_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract features from shift data for pattern learning.
    
    Args:
        df: Preprocessed DataFrame with shift data
        
    Returns:
        DataFrame with additional feature columns
    """
    df = df.copy()
    
    # Parse shift times if not already done
    if 'ShiftStartTime_parsed' not in df.columns:
        df['ShiftStartTime_parsed'] = pd.to_datetime(df['ShiftStartTime'], format='%H:%M:%S').dt.time
    
    # Categorize shift start times
    def categorize_shift_time(start_time):
        hour = start_time.hour
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 22:
            return 'evening'
        else:
            return 'night'
    
    df['ShiftTimeCategory'] = df['ShiftStartTime_parsed'].apply(categorize_shift_time)
    
    # Categorize shift duration
    if 'ShiftDurationHours' not in df.columns:
        # Calculate if not present
        def calculate_hours(row):
            start = pd.to_datetime(row['ShiftStartTime'], format='%H:%M:%S').time()
            end = pd.to_datetime(row['ShiftEndTime'], format='%H:%M:%S').time()
            start_dt = datetime.combine(datetime.today(), start)
            end_dt = datetime.combine(datetime.today(), end)
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            return (end_dt - start_dt).total_seconds() / 3600
        
        df['ShiftDurationHours'] = df.apply(calculate_hours, axis=1)
    
    def categorize_duration(hours):
        if hours <= 6:
            return 'short'
        elif hours <= 10:
            return 'medium'
        else:
            return 'long'
    
    df['ShiftDurationCategory'] = df['ShiftDurationHours'].apply(categorize_duration)
    
    # Create shift type identifier
    df['ShiftType'] = df['ShiftTimeCategory'] + '_' + df['ShiftDurationCategory']
    
    return df


def compute_compatibility(historical_data: pd.DataFrame) -> pd.DataFrame:
    """
    Compute employee shift preferences (profiles) from historical assignment data.
    Creates a DataFrame with one row per employee containing their preference probabilities.
    
    Args:
        historical_data: Preprocessed historical DataFrame (all historical snapshots)
        
    Returns:
        DataFrame with employee profiles. Each row contains:
        - EmployeeNumber
        - Total shifts worked
        - Preference probabilities for each dimension (day, time, duration, job, shift_type)
    """
    # Only consider filled shifts (where employee accepted)
    filled_shifts = historical_data[historical_data['EmployeeNumber'].notna()].copy()
    
    if filled_shifts.empty:
        return pd.DataFrame()
    
    # Extract features
    filled_shifts = extract_shift_features(filled_shifts)
    
    # Get all unique employees
    unique_employees = filled_shifts['EmployeeNumber'].dropna().unique()
    
    # Get all unique values for each dimension
    all_days = sorted(filled_shifts['DayNum'].unique())
    all_times = sorted(filled_shifts['ShiftTimeCategory'].unique())
    all_durations = sorted(filled_shifts['ShiftDurationCategory'].unique())
    all_jobs = sorted(filled_shifts['JobNumber'].unique())
    all_shift_types = sorted(filled_shifts['ShiftType'].unique())
    
    # Initialize employee profiles
    employee_profiles = []
    
    for emp_num in unique_employees:
        emp_shifts = filled_shifts[filled_shifts['EmployeeNumber'] == emp_num]
        total_shifts = len(emp_shifts)
        
        if total_shifts == 0:
            continue
        
        # Count preferences
        day_counts = emp_shifts['DayNum'].value_counts().to_dict()
        time_counts = emp_shifts['ShiftTimeCategory'].value_counts().to_dict()
        duration_counts = emp_shifts['ShiftDurationCategory'].value_counts().to_dict()
        job_counts = emp_shifts['JobNumber'].value_counts().to_dict()
        shift_type_counts = emp_shifts['ShiftType'].value_counts().to_dict()
        
        # Normalize to probabilities
        day_probs = {day: day_counts.get(day, 0) / total_shifts for day in all_days}
        time_probs = {time: time_counts.get(time, 0) / total_shifts for time in all_times}
        duration_probs = {dur: duration_counts.get(dur, 0) / total_shifts for dur in all_durations}
        job_probs = {job: job_counts.get(job, 0) / total_shifts for job in all_jobs}
        shift_type_probs = {st: shift_type_counts.get(st, 0) / total_shifts for st in all_shift_types}
        
        # Create profile row
        profile = {
            'EmployeeNumber': int(emp_num),
            'TotalShifts': total_shifts
        }
        
        # Add day preferences (Day1, Day2, ..., Day7)
        for day in all_days:
            profile[f'Day{day}_Prob'] = day_probs[day]
        
        # Add time preferences
        for time_cat in all_times:
            profile[f'Time_{time_cat}_Prob'] = time_probs[time_cat]
        
        # Add duration preferences
        for dur_cat in all_durations:
            profile[f'Duration_{dur_cat}_Prob'] = duration_probs[dur_cat]
        
        # Add job preferences
        for job in all_jobs:
            profile[f'Job_{job}_Prob'] = job_probs[job]
        
        # Add shift type preferences
        for shift_type in all_shift_types:
            # Replace special characters for column name
            col_name = f'ShiftType_{shift_type.replace("_", "_")}_Prob'
            profile[col_name] = shift_type_probs[shift_type]
        
        employee_profiles.append(profile)
    
    # Create DataFrame
    profiles_df = pd.DataFrame(employee_profiles)
    
    return profiles_df


def get_compatibility_score(
    employee_profile: pd.Series,
    shift_day: int,
    shift_time_category: str,
    shift_duration_category: str,
    shift_job: int,
    shift_type: str
) -> float:
    """
    Compute compatibility score for a single employee-shift pair.
    
    Args:
        employee_profile: Row from employee profiles DataFrame
        shift_day: DayNum of the shift
        shift_time_category: Time category of the shift
        shift_duration_category: Duration category of the shift
        shift_job: JobNumber of the shift
        shift_type: ShiftType of the shift
        
    Returns:
        Compatibility score (0.0 to 1.0)
    """
    weights = {
        'day': 0.3,
        'time': 0.25,
        'duration': 0.15,
        'job': 0.2,
        'shift_type': 0.1
    }
    
    score = 0.0
    
    # Day preference
    day_col = f'Day{shift_day}_Prob'
    if day_col in employee_profile:
        score += weights['day'] * employee_profile[day_col]
    
    # Time preference
    time_col = f'Time_{shift_time_category}_Prob'
    if time_col in employee_profile:
        score += weights['time'] * employee_profile[time_col]
    
    # Duration preference
    duration_col = f'Duration_{shift_duration_category}_Prob'
    if duration_col in employee_profile:
        score += weights['duration'] * employee_profile[duration_col]
    
    # Job preference
    job_col = f'Job_{shift_job}_Prob'
    if job_col in employee_profile:
        score += weights['job'] * employee_profile[job_col]
    
    # Shift type preference
    shift_type_col = f'ShiftType_{shift_type}_Prob'
    if shift_type_col in employee_profile:
        score += weights['shift_type'] * employee_profile[shift_type_col]
    
    return score
