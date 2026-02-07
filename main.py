"""
Main entry point for the schedule assignment system.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_loader import load_schedule_data, split_historical_and_latest
from src.preprocessing import preprocess_schedule, validate_data
from src.compute_employee_profile import compute_compatibility
from src.optimizer import compute_compatibility_matrix, solve_assignment, fill_unfilled_shifts
from src.validator import compute_assignment_compatibility, validate_constraints, validate_filled_shifts_constraints


def main():
    """
    Main function to load, preprocess, and compute employee compatibility profiles.
    """
    print("=" * 60)
    print("Schedule Assignment System")
    print("=" * 60)
    
    # Step 1: Load data
    print("\n[1/4] Loading schedule data...")
    df = load_schedule_data()
    print(f"✓ Loaded {len(df):,} total rows")
    
    # Step 2: Split into historical and latest
    print("\n[2/4] Splitting into historical and latest snapshot...")
    historical_data, latest_snapshot = split_historical_and_latest(df, target_date="10/8/2024")
    print(f"✓ Historical: {len(historical_data):,} rows | Latest: {len(latest_snapshot):,} rows")
    
    # Step 3: Preprocess data
    print("\n[3/4] Preprocessing data...")
    processed_historical = preprocess_schedule(historical_data, deduplicate_by_date=True)
    processed_latest = preprocess_schedule(latest_snapshot, deduplicate_by_date=True)
    print(f"✓ Preprocessed historical: {len(processed_historical):,} rows")
    print(f"✓ Preprocessed latest: {len(processed_latest):,} rows")
    print(f"  Unfilled shifts: {processed_latest['IsUnfilled'].sum()}")
    
    # Step 4: Compute employee profiles
    print("\n[4/7] Computing employee compatibility profiles...")
    employee_profiles = compute_compatibility(processed_historical)
    print(f"✓ Created profiles for {len(employee_profiles)} employees")
    
    # Step 5: Validate existing filled shifts
    print("\n[5/8] Validating existing filled shifts...")
    filled_shifts = processed_latest[processed_latest['EmployeeNumber'].notna()].copy()
    existing_validation = validate_filled_shifts_constraints(filled_shifts)
    
    if existing_validation['valid']:
        print("✓ All existing filled shifts satisfy constraints")
    else:
        print(f"⚠ Found {existing_validation['total_violations']} constraint violations in existing filled shifts:")
        
        if existing_validation['violations']['weekly_hours']:
            print(f"  Weekly Hours: {len(existing_validation['violations']['weekly_hours'])} violations")
            for v in existing_validation['violations']['weekly_hours'][:3]:  # Show first 3
                print(f"    Employee {v['employee']}: {v['hours']:.1f} hours (limit: {v['limit']})")
        
        if existing_validation['violations']['work_days']:
            print(f"  Work Days: {len(existing_validation['violations']['work_days'])} violations")
            for v in existing_validation['violations']['work_days'][:3]:
                print(f"    Employee {v['employee']}: {v['days']} days (limit: {v['limit']})")
        
        if existing_validation['violations']['daily_shifts']:
            print(f"  Daily Shifts: {len(existing_validation['violations']['daily_shifts'])} violations")
            for v in existing_validation['violations']['daily_shifts'][:3]:
                print(f"    Employee {v['employee']} on Day {v['day']}: {v['count']} shifts (limit: {v['limit']})")
    
    # Step 6: Compute compatibility matrix
    print("\n[6/8] Computing compatibility matrix...")
    unfilled_shifts = processed_latest[processed_latest['IsUnfilled']].copy()
    compatibility_matrix = compute_compatibility_matrix(unfilled_shifts, employee_profiles)
    print(f"✓ Computed {len(compatibility_matrix):,} employee-shift compatibility scores")
    
    # Step 7: Solve optimization problem
    print("\n[7/8] Solving optimization problem...")
    assignments = solve_assignment(unfilled_shifts, employee_profiles, filled_shifts)
    print(f"✓ Assigned {len(assignments)} shifts")
    
    # Step 8: Fill latest snapshot
    print("\n[8/8] Filling latest snapshot...")
    filled_snapshot = fill_unfilled_shifts(processed_latest, employee_profiles)
    remaining_unfilled = filled_snapshot['IsUnfilled'].sum()
    print(f"✓ Filled snapshot | Remaining unfilled: {remaining_unfilled}")
    
    # Validation: Compute mean compatibility for newly assigned shifts
    print("\n" + "=" * 60)
    print("Validation: Assignment Quality")
    print("=" * 60)
    newly_assigned = filled_snapshot[
        (filled_snapshot['EmployeeNumber'].notna()) & 
        (processed_latest['IsUnfilled'])
    ].copy()
    
    if len(newly_assigned) > 0:
        mean_compatibility = compute_assignment_compatibility(newly_assigned, employee_profiles)
        print(f"✓ Mean compatibility score for {len(newly_assigned)} newly assigned shifts: {mean_compatibility:.3f}")
    else:
        print("  No new assignments to validate")
    
    # Validation: Check constraints
    print("\n" + "=" * 60)
    print("Validation: Constraint Checking")
    print("=" * 60)
    constraint_validation = validate_constraints(filled_snapshot)
    
    if constraint_validation['valid']:
        print("✓ All constraints satisfied!")
    else:
        print(f"✗ Found {constraint_validation['total_violations']} constraint violations:")
        
        if constraint_validation['violations']['weekly_hours']:
            print(f"\n  Weekly Hours Violations ({len(constraint_validation['violations']['weekly_hours'])}):")
            for v in constraint_validation['violations']['weekly_hours']:
                print(f"    Employee {v['employee']}: {v['hours']:.1f} hours (limit: {v['limit']})")
        
        if constraint_validation['violations']['work_days']:
            print(f"\n  Work Days Violations ({len(constraint_validation['violations']['work_days'])}):")
            for v in constraint_validation['violations']['work_days']:
                print(f"    Employee {v['employee']}: {v['days']} days (limit: {v['limit']})")
        
        if constraint_validation['violations']['daily_shifts']:
            print(f"\n  Daily Shift Limit Violations ({len(constraint_validation['violations']['daily_shifts'])}):")
            for v in constraint_validation['violations']['daily_shifts']:
                print(f"    Employee {v['employee']} on Day {v['day']}: {v['count']} shifts (limit: {v['limit']})")
    
    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Initial unfilled shifts: {processed_latest['IsUnfilled'].sum()}")
    print(f"  Assigned shifts: {len(assignments)}")
    print(f"  Remaining unfilled: {remaining_unfilled}")
    if len(newly_assigned) > 0:
        print(f"  Mean compatibility score: {mean_compatibility:.3f}")
    print(f"  Constraint violations: {constraint_validation['total_violations']}")


if __name__ == "__main__":
    main()
