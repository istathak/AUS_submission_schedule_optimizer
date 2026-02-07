"""
API endpoints for schedule assignment.
"""
from flask import jsonify, request
import pandas as pd
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_loader import load_schedule_data, split_historical_and_latest
from preprocessing import preprocess_schedule
from compute_employee_profile import compute_compatibility
from optimizer import solve_assignment

# Cache for loaded data
_data_cache = None
_employee_profiles_cache = None
_latest_snapshot_cache = None


def _load_and_cache_data():
    """Load and cache data for API requests."""
    global _data_cache, _employee_profiles_cache, _latest_snapshot_cache
    
    if _data_cache is None:
        print("Loading and caching data...")
        # Load data
        df = load_schedule_data()
        historical_data, latest_snapshot = split_historical_and_latest(df, target_date="10/8/2024")
        
        # Preprocess
        processed_historical = preprocess_schedule(historical_data, deduplicate_by_date=True)
        processed_latest = preprocess_schedule(latest_snapshot, deduplicate_by_date=True)
        
        # Compute employee profiles
        employee_profiles = compute_compatibility(processed_historical)
        
        # Cache
        _data_cache = {
            'historical': processed_historical,
            'latest': processed_latest
        }
        _employee_profiles_cache = employee_profiles
        _latest_snapshot_cache = processed_latest.copy()
        print(f"✓ Data cached: {len(_latest_snapshot_cache)} shifts, {len(_employee_profiles_cache)} employees")
    
    return _data_cache, _employee_profiles_cache, _latest_snapshot_cache


def assign_cell():
    """
    API endpoint to assign an employee to a schedule cell.
    
    Query parameters (GET) or JSON body (POST):
        schedule_detail_id (int): ScheduleDetailID of the cell
        day_num (int): DayNum of the cell (1-7)
    
    Returns:
        JSON response with assignment information
    """
    try:
        # Get parameters
        if request.method == 'POST':
            data = request.get_json() or {}
            schedule_detail_id = data.get('schedule_detail_id') or data.get('ScheduleDetailID')
            day_num = data.get('day_num') or data.get('DayNum')
        else:  # GET
            schedule_detail_id = request.args.get('schedule_detail_id') or request.args.get('ScheduleDetailID')
            day_num = request.args.get('day_num') or request.args.get('DayNum')
        
        # Validate parameters
        if schedule_detail_id is None or day_num is None:
            return jsonify({
                'error': 'Missing required parameters',
                'required': ['schedule_detail_id', 'day_num']
            }), 400
        
        try:
            schedule_detail_id = int(schedule_detail_id)
            day_num = int(day_num)
        except ValueError:
            return jsonify({
                'error': 'Invalid parameter types',
                'schedule_detail_id': 'must be integer',
                'day_num': 'must be integer (1-7)'
            }), 400
        
        if day_num < 1 or day_num > 7:
            return jsonify({
                'error': 'Invalid day_num',
                'day_num': f'{day_num} is not valid (must be 1-7)'
            }), 400
        
        # Load cached data
        _, employee_profiles, latest_snapshot = _load_and_cache_data()
        
        # Find the cell in the latest snapshot
        cell_mask = (
            (latest_snapshot['ScheduleDetailID'] == schedule_detail_id) &
            (latest_snapshot['DayNum'] == day_num)
        )
        cell_rows = latest_snapshot[cell_mask]
        
        if len(cell_rows) == 0:
            return jsonify({
                'error': 'Cell not found',
                'schedule_detail_id': int(schedule_detail_id),
                'day_num': int(day_num)
            }), 404
        
        # Get the first row (should be only one after deduplication)
        cell = cell_rows.iloc[0]
        
        # Check if cell is already filled
        if pd.notna(cell['EmployeeNumber']):
            return jsonify({
                'status': 'filled',
                'schedule_detail_id': int(schedule_detail_id),
                'day_num': int(day_num),
                'employee_number': int(cell['EmployeeNumber']),
                'source': 'existing_schedule',
                'message': 'Cell is already filled in the dataset'
            }), 200
        
        # Cell is unfilled - run on-demand assignment
        # Get only this specific unfilled shift
        unfilled_shift = cell_rows.iloc[0:1].copy()
        
        # Get all filled shifts for constraint checking
        filled_shifts = latest_snapshot[latest_snapshot['EmployeeNumber'].notna()].copy()
        
        # Solve assignment for this single shift
        assignments = solve_assignment(unfilled_shift, employee_profiles, filled_shifts)
        
        if len(assignments) == 0:
            # No feasible assignment found
            return jsonify({
                'status': 'unfilled',
                'schedule_detail_id': int(schedule_detail_id),
                'day_num': int(day_num),
                'employee_number': None,
                'source': 'optimization',
                'message': 'Cell is unfilled and no feasible assignment found (constraints cannot be satisfied)'
            }), 200
        
        # Get the assigned employee
        shift_id = (schedule_detail_id, day_num)
        if shift_id in assignments:
            assigned_employee = assignments[shift_id]
            # Convert to native Python int (handles numpy int64)
            assigned_employee = int(assigned_employee)
            
            return jsonify({
                'status': 'assigned',
                'schedule_detail_id': int(schedule_detail_id),
                'day_num': int(day_num),
                'employee_number': assigned_employee,
                'source': 'optimization',
                'message': 'Cell was unfilled and employee assigned via optimization'
            }), 200
        else:
            # Assignment didn't include this shift (shouldn't happen)
            return jsonify({
                'status': 'unfilled',
                'schedule_detail_id': int(schedule_detail_id),
                'day_num': int(day_num),
                'employee_number': None,
                'source': 'optimization',
                'message': 'Cell is unfilled but was not assigned in optimization solution'
            }), 200
    
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
