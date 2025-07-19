#!/usr/bin/env python3
"""
Comprehensive test suite for the automatic quarterly progression system.
Tests all scenarios including quarter detection, progression logic, and completion handling.
"""

import json
import logging
import os
import sys
from datetime import datetime, date
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.quarter_service import QuarterService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_equipment(q1_date: str, q1_eng: str, q2_date: str, q2_eng: str, 
                         q3_date: str, q3_eng: str, q4_date: str, q4_eng: str) -> Dict[str, Any]:
    """Create test equipment data with specified quarter information."""
    return {
        'SERIAL': 'TEST-001',
        'MODEL': 'Test Equipment',
        'PPM_Q_I': {'quarter_date': q1_date, 'engineer': q1_eng},
        'PPM_Q_II': {'quarter_date': q2_date, 'engineer': q2_eng},
        'PPM_Q_III': {'quarter_date': q3_date, 'engineer': q3_eng},
        'PPM_Q_IV': {'quarter_date': q4_date, 'engineer': q4_eng}
    }

def test_calendar_quarter_detection():
    """Test that calendar quarter detection works correctly."""
    logger.info("=== Testing Calendar Quarter Detection ===")
    
    test_cases = [
        (date(2024, 1, 15), 1, "January should be Q1"),
        (date(2024, 3, 31), 1, "March should be Q1"),
        (date(2024, 4, 1), 2, "April should be Q2"),
        (date(2024, 6, 30), 2, "June should be Q2"),
        (date(2024, 7, 1), 3, "July should be Q3"),
        (date(2024, 9, 30), 3, "September should be Q3"),
        (date(2024, 10, 1), 4, "October should be Q4"),
        (date(2024, 12, 31), 4, "December should be Q4")
    ]
    
    all_passed = True
    for test_date, expected_quarter, description in test_cases:
        actual_quarter = QuarterService.get_current_calendar_quarter(test_date)
        if actual_quarter == expected_quarter:
            logger.info(f"✅ {description}: Got Q{actual_quarter}")
        else:
            logger.error(f"❌ {description}: Expected Q{expected_quarter}, got Q{actual_quarter}")
            all_passed = False
    
    return all_passed

def test_quarter_progression_scenarios():
    """Test various quarter progression scenarios."""
    logger.info("=== Testing Quarter Progression Scenarios ===")
    
    # Test date: July 15, 2024 (Q3)
    test_date = date(2024, 7, 15)
    
    scenarios = [
        {
            'name': 'Current Quarter Active (Q3 upcoming)',
            'equipment': create_test_equipment(
                '15/01/2024', 'John',    # Q1 - past, maintained
                '15/04/2024', 'Jane',    # Q2 - past, maintained  
                '15/07/2024', '',        # Q3 - current, not maintained
                '15/10/2024', ''         # Q4 - future
            ),
            'expected_quarter': 3,
            'expected_status': 'Maintained'  # Due today counts as maintained
        },
        {
            'name': 'Current Quarter Overdue',
            'equipment': create_test_equipment(
                '15/01/2024', 'John',    # Q1 - past, maintained
                '15/04/2024', 'Jane',    # Q2 - past, maintained
                '10/07/2024', '',        # Q3 - past, not maintained (overdue)
                '15/10/2024', ''         # Q4 - future
            ),
            'expected_quarter': 3,
            'expected_status': 'Overdue'
        },
        {
            'name': 'Current Quarter Complete, Show Next',
            'equipment': create_test_equipment(
                '15/01/2024', 'John',    # Q1 - past, maintained
                '15/04/2024', 'Jane',    # Q2 - past, maintained
                '10/07/2024', 'Bob',     # Q3 - past, maintained
                '15/10/2024', ''         # Q4 - future, should be shown
            ),
            'expected_quarter': 4,
            'expected_status': 'Upcoming'
        },
        {
            'name': 'Current Quarter Future Date',
            'equipment': create_test_equipment(
                '15/01/2024', 'John',    # Q1 - past, maintained
                '15/04/2024', 'Jane',    # Q2 - past, maintained
                '20/07/2024', '',        # Q3 - future date, not maintained
                '15/10/2024', ''         # Q4 - future
            ),
            'expected_quarter': 3,  # Should show Q3 since it's upcoming
            'expected_status': 'Upcoming'
        }
    ]
    
    all_passed = True
    for scenario in scenarios:
        logger.info(f"\n--- Testing: {scenario['name']} ---")
        
        quarter_num, quarter_key, quarter_data = QuarterService.get_active_quarter_for_equipment(
            scenario['equipment'], test_date
        )
        
        display_data = QuarterService.get_display_data_for_equipment(
            scenario['equipment'], test_date
        )
        
        # Check quarter number
        if quarter_num == scenario['expected_quarter']:
            logger.info(f"✅ Quarter: Expected Q{scenario['expected_quarter']}, got Q{quarter_num}")
        else:
            logger.error(f"❌ Quarter: Expected Q{scenario['expected_quarter']}, got Q{quarter_num}")
            all_passed = False
        
        # Check status
        if display_data['Status'] == scenario['expected_status']:
            logger.info(f"✅ Status: Expected '{scenario['expected_status']}', got '{display_data['Status']}'")
        else:
            logger.error(f"❌ Status: Expected '{scenario['expected_status']}', got '{display_data['Status']}'")
            all_passed = False
        
        logger.info(f"   Active Quarter: {display_data['active_quarter']}")
        logger.info(f"   Next Maintenance: {display_data['display_next_maintenance']}")
        logger.info(f"   Status Class: {display_data['status_class']}")
    
    return all_passed

def test_year_end_rollover():
    """Test that quarter progression handles year-end rollover correctly."""
    logger.info("=== Testing Year-End Rollover ===")
    
    # Test date: December 15, 2024 (Q4)
    test_date = date(2024, 12, 15)
    
    # All quarters for 2024 are complete, should show Q1 2025
    equipment = create_test_equipment(
        '15/01/2024', 'John',    # Q1 2024 - past, maintained
        '15/04/2024', 'Jane',    # Q2 2024 - past, maintained
        '15/07/2024', 'Bob',     # Q3 2024 - past, maintained
        '10/12/2024', 'Alice'    # Q4 2024 - past, maintained
    )
    
    # Add Q1 2025 data
    equipment['PPM_Q_I']['quarter_date'] = '15/01/2025'
    equipment['PPM_Q_I']['engineer'] = ''
    
    quarter_num, quarter_key, quarter_data = QuarterService.get_active_quarter_for_equipment(
        equipment, test_date
    )
    
    display_data = QuarterService.get_display_data_for_equipment(equipment, test_date)
    
    # Should show Q1 (next year) as upcoming
    if quarter_num == 1 and display_data['Status'] == 'Upcoming':
        logger.info("✅ Year-end rollover working: Showing Q1 next year as upcoming")
        return True
    else:
        logger.error(f"❌ Year-end rollover failed: Got Q{quarter_num} with status '{display_data['Status']}'")
        return False

def test_edge_cases():
    """Test edge cases and error handling."""
    logger.info("=== Testing Edge Cases ===")
    
    test_date = date(2024, 7, 15)
    all_passed = True
    
    # Test with missing quarter data
    equipment_missing_data = {
        'SERIAL': 'TEST-002',
        'PPM_Q_I': {},
        'PPM_Q_II': {'quarter_date': '', 'engineer': ''},
        'PPM_Q_III': {'quarter_date': None, 'engineer': None},
        'PPM_Q_IV': {'quarter_date': 'invalid-date', 'engineer': 'John'}
    }
    
    try:
        display_data = QuarterService.get_display_data_for_equipment(equipment_missing_data, test_date)
        logger.info(f"✅ Handled missing data gracefully: Status='{display_data['Status']}', Maintenance='{display_data['display_next_maintenance']}'")
    except Exception as e:
        logger.error(f"❌ Failed to handle missing data: {str(e)}")
        all_passed = False
    
    # Test with invalid date formats
    equipment_invalid_dates = create_test_equipment(
        'invalid-date', 'John',
        '2024-07-15', 'Jane',  # Different format
        '15/07/24', 'Bob',     # Short year
        '15/13/2024', 'Alice'  # Invalid month
    )
    
    try:
        display_data = QuarterService.get_display_data_for_equipment(equipment_invalid_dates, test_date)
        logger.info(f"✅ Handled invalid dates gracefully: Status='{display_data['Status']}'")
    except Exception as e:
        logger.error(f"❌ Failed to handle invalid dates: {str(e)}")
        all_passed = False
    
    return all_passed

def test_dashboard_summary():
    """Test dashboard summary functionality."""
    logger.info("=== Testing Dashboard Summary ===")
    
    test_date = date(2024, 7, 15)  # Q3
    summary = QuarterService.get_dashboard_summary(test_date)
    
    expected_fields = ['current_date', 'current_calendar_quarter', 'current_quarter_name', 'quarter_keys', 'quarter_names']
    all_passed = True
    
    for field in expected_fields:
        if field in summary:
            logger.info(f"✅ Summary contains '{field}': {summary[field]}")
        else:
            logger.error(f"❌ Summary missing field: {field}")
            all_passed = False
    
    # Check specific values
    if summary.get('current_calendar_quarter') == 3:
        logger.info("✅ Correct calendar quarter detected")
    else:
        logger.error(f"❌ Wrong calendar quarter: Expected 3, got {summary.get('current_calendar_quarter')}")
        all_passed = False
    
    if summary.get('current_quarter_name') == 'Q3':
        logger.info("✅ Correct quarter name")
    else:
        logger.error(f"❌ Wrong quarter name: Expected 'Q3', got {summary.get('current_quarter_name')}")
        all_passed = False
    
    return all_passed

def main():
    """Main test function."""
    logger.info("🔧 Testing Automatic Quarterly Progression System")
    logger.info("=" * 60)
    
    test_results = []
    
    # Run all test suites
    test_results.append(("Calendar Quarter Detection", test_calendar_quarter_detection()))
    test_results.append(("Quarter Progression Scenarios", test_quarter_progression_scenarios()))
    test_results.append(("Year-End Rollover", test_year_end_rollover()))
    test_results.append(("Edge Cases", test_edge_cases()))
    test_results.append(("Dashboard Summary", test_dashboard_summary()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("🔍 QUARTER PROGRESSION TEST SUMMARY")
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("🎉 ALL TESTS PASSED - Quarterly progression system is working correctly!")
        logger.info("The dashboard will now automatically show the appropriate quarter data.")
    else:
        logger.error("❌ SOME TESTS FAILED - Quarterly progression system needs fixes")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
