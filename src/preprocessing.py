"""
Preprocessing module for cleaning and validating schedule data.
"""
import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta


def handle_midnight_shifts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle shifts that span midnight. 
    Shifts are attributed entirely to their start day for constraint purposes.
    
    Args:
        df: DataFrame with shift data
        
    Returns:
        DataFrame with processed shifts
    """
    df = df.copy()
    
    # Parse shift times
    df['ShiftStartTime_parsed'] = pd.to_datetime(df['ShiftStartTime'], format='%H:%M:%S').dt.time
    df['ShiftEndTime_parsed'] = pd.to_datetime(df['ShiftEndTime'], format='%H:%M:%S').dt.time
    
    # Calculate shift duration in hours
    def calculate_hours(row):
        start = row['ShiftStartTime_parsed']
        end = row['ShiftEndTime_parsed']
        
        # Convert to datetime for calculation
        start_dt = datetime.combine(datetime.today(), start)
        end_dt = datetime.combine(datetime.today(), end)
        
        # If end time is earlier than start, it spans midnight
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        duration = (end_dt - start_dt).total_seconds() / 3600
        return duration
    
    df['ShiftDurationHours'] = df.apply(calculate_hours, axis=1)
    
    return df


def deduplicate_schedule_details(df: pd.DataFrame, by_date: bool = True) -> pd.DataFrame:
    """
    Deduplicate rows by ScheduleDetailID and DayNum combination.
    Keep only one row per unique ScheduleDetailID/DayNum pair.
    
    Args:
        df: DataFrame with schedule data
        by_date: If True, deduplicate within each date. If False, deduplicate globally.
        
    Returns:
        DataFrame with deduplicated rows
    """
    if by_date and 'date' in df.columns:
        # Deduplicate within each date snapshot
        df_deduped = df.drop_duplicates(subset=['date', 'ScheduleDetailID', 'DayNum'], keep='first')
    else:
        # Global deduplication (for latest snapshot where date is constant)
        df_deduped = df.drop_duplicates(subset=['ScheduleDetailID', 'DayNum'], keep='first')
    
    return df_deduped


def identify_unfilled_shifts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify unfilled shifts (where EmployeeNumber is null).
    
    Args:
        df: DataFrame with schedule data
        
    Returns:
        DataFrame with 'IsUnfilled' column added
    """
    df = df.copy()
    df['IsUnfilled'] = df['EmployeeNumber'].isna()
    return df


def parse_scheduling_weeks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse scheduling weeks. 
    Scheduling week runs Friday (day 1) → Thursday (day 7).
    
    Args:
        df: DataFrame with DayNum column
        
    Returns:
        DataFrame with scheduling week information
    """
    df = df.copy()
    
    # DayNum 1 = Friday, 2 = Saturday, ..., 7 = Thursday
    # For now, we'll add a helper column to identify which week a day belongs to
    # This will be more complex when we have actual dates, but for now DayNum is relative
    
    # Note: We'll need actual dates to properly group into weeks
    # For now, we'll assume DayNum is within a single scheduling week
    df['DayOfWeek'] = df['DayNum'].map({
        1: 'Friday',
        2: 'Saturday', 
        3: 'Sunday',
        4: 'Monday',
        5: 'Tuesday',
        6: 'Wednesday',
        7: 'Thursday'
    })
    
    return df


def validate_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the preprocessed data and return validation results.
    
    Args:
        df: Preprocessed DataFrame
        
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'total_rows': len(df),
        'unfilled_shifts': df['IsUnfilled'].sum() if 'IsUnfilled' in df.columns else df['EmployeeNumber'].isna().sum(),
        'filled_shifts': len(df) - (df['IsUnfilled'].sum() if 'IsUnfilled' in df.columns else df['EmployeeNumber'].isna().sum()),
        'unique_schedule_details': df['ScheduleDetailID'].nunique(),
        'unique_employees': df['EmployeeNumber'].nunique() if 'EmployeeNumber' in df.columns else 0,
        'unique_jobs': df['JobNumber'].nunique(),
        'daynum_range': (df['DayNum'].min(), df['DayNum'].max()),
        'has_duplicates': len(df) != len(df.drop_duplicates(subset=['ScheduleDetailID', 'DayNum']))
    }
    
    return validation_results


def preprocess_schedule(df: pd.DataFrame, deduplicate_by_date: bool = True) -> pd.DataFrame:
    """
    Main preprocessing function that applies all preprocessing steps.
    
    Args:
        df: Raw schedule DataFrame
        deduplicate_by_date: If True, deduplicate within each date snapshot (for historical data).
                            If False, deduplicate globally (for latest snapshot).
        
    Returns:
        Preprocessed DataFrame
    """
    # Step 1: Handle midnight-spanning shifts
    df = handle_midnight_shifts(df)
    
    # Step 2: Deduplicate by ScheduleDetailID/DayNum
    df = deduplicate_schedule_details(df, by_date=deduplicate_by_date)
    
    # Step 3: Identify unfilled shifts
    df = identify_unfilled_shifts(df)
    
    # Step 4: Parse scheduling weeks
    df = parse_scheduling_weeks(df)
    
    return df
