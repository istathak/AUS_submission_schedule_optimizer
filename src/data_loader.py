"""
Data loader module for loading and extracting schedule data.
"""
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime


def load_schedule_data(data_path: str = "data/Schedule_Historical_Data.csv") -> pd.DataFrame:
    """
    Load the schedule historical data CSV file.
    
    Args:
        data_path: Path to the CSV file
        
    Returns:
        DataFrame with raw schedule data
    """
    file_path = Path(data_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    return df


def extract_latest_snapshot(df: pd.DataFrame, target_date: str = "10/8/2024") -> pd.DataFrame:
    """
    Extract the latest schedule snapshot for a given date.
    
    Args:
        df: Full schedule DataFrame
        target_date: Target date in format 'M/D/YYYY' (default: '10/8/2024')
        
    Returns:
        DataFrame containing only the latest snapshot
    """
    # Parse date column
    df['date_parsed'] = pd.to_datetime(df['date'], format='%m/%d/%Y')
    target_datetime = pd.to_datetime(target_date, format='%m/%d/%Y')
    
    # Filter for target date
    latest_snapshot = df[df['date_parsed'] == target_datetime].copy()
    
    if latest_snapshot.empty:
        raise ValueError(f"No data found for target date: {target_date}")
    
    return latest_snapshot


def split_historical_and_latest(df: pd.DataFrame, target_date: str = "10/8/2024") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into historical data (for learning) and latest snapshot (for filling).
    
    Args:
        df: Full schedule DataFrame
        target_date: Target date in format 'M/D/YYYY' (default: '10/8/2024')
        
    Returns:
        Tuple of (historical_data, latest_snapshot)
    """
    # Parse date column
    df['date_parsed'] = pd.to_datetime(df['date'], format='%m/%d/%Y')
    target_datetime = pd.to_datetime(target_date, format='%m/%d/%Y')
    
    # Split data
    historical_data = df[df['date_parsed'] < target_datetime].copy()
    latest_snapshot = df[df['date_parsed'] == target_datetime].copy()
    
    if latest_snapshot.empty:
        raise ValueError(f"No data found for target date: {target_date}")
    
    return historical_data, latest_snapshot
