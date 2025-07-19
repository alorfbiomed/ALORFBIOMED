#!/usr/bin/env python3
"""
Test script to verify the quarter progression fix works correctly.
"""

import sys
import os
from datetime import datetime, date

sys.path.insert(0, '.')

def test_quarter_fix():
    """Test the quarter progression fix with various scenarios."""
    print("🔧 Testing Quarter Progression Fix")
    print("=" * 50)
    
    try:
        from app.services.quarter_service import QuarterService
        
        current_date = date(2025, 7, 4)  # July 4, 2025 (Q3)
        
        test_scenarios = [
            {
                'name': 'Q3 Current - Should Show Q3',
                'data': {
                    'PPM_Q_II': {'quarter_date': '15/05/2025', 'engineer': 'JOHN'},  # Past, complete
                    'PPM_Q_III': {'quarter_date': '15/07/2025', 'engineer': ''},     # Future, no engineer
                    'PPM_Q_IV': {'quarter_date': '15/10/2025', 'engineer': ''}
                },
                'expected_quarter': 'PPM_Q_III',
                'expected_status': 'Upcoming'
            },
            {
                'name': 'Q3 Past but Recent - Should Show Q3',
                'data': {
                    'PPM_Q_II': {'quarter_date': '15/05/2025', 'engineer': 'JOHN'},  # Past, complete
                    'PPM_Q_III': {'quarter_date': '02/07/2025', 'engineer': 'JANE'}, # Past but recent, complete
                    'PPM_Q_IV': {'quarter_date': '15/10/2025', 'engineer': ''}
                },
                'expected_quarter': 'PPM_Q_III',
                'expected_status': 'Maintained'
            },
            {
                'name': 'Q3 Overdue - Should Show Q3',
                'data': {
                    'PPM_Q_II': {'quarter_date': '15/05/2025', 'engineer': 'JOHN'},  # Past, complete
                    'PPM_Q_III': {'quarter_date': '01/07/2025', 'engineer': ''},     # Past, no engineer (overdue)
                    'PPM_Q_IV': {'quarter_date': '15/10/2025', 'engineer': ''}
                },
                'expected_quarter': 'PPM_Q_III',
                'expected_status': 'Overdue'
            },
            {
                'name': 'Q2 Overdue - Should Show Q2',
                'data': {
                    'PPM_Q_II': {'quarter_date': '15/05/2025', 'engineer': ''},      # Past, no engineer (overdue)
                    'PPM_Q_III': {'quarter_date': '15/07/2025', 'engineer': ''},     # Future, no engineer
                    'PPM_Q_IV': {'quarter_date': '15/10/2025', 'engineer': ''}
                },
                'expected_quarter': 'PPM_Q_II',
                'expected_status': 'Overdue'
            }
        ]
        
        all_passed = True
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 Test {i}: {scenario['name']}")
            print("-" * 50)
            
            # Test the quarter selection
            active_quarter_num, active_quarter_key, active_quarter_data = \
                QuarterService.get_active_quarter_for_equipment(scenario['data'], current_date)
            
            # Test the display data
            display_data = QuarterService.get_display_data_for_equipment(scenario['data'], current_date)
            
            print(f"  Expected: {scenario['expected_quarter']} with {scenario['expected_status']}")
            print(f"  Actual:   {active_quarter_key} with {display_data.get('Status', 'N/A')}")
            
            # Check results
            quarter_correct = active_quarter_key == scenario['expected_quarter']
            status_correct = display_data.get('Status') == scenario['expected_status']
            
            if quarter_correct and status_correct:
                print(f"  ✅ PASSED")
            else:
                print(f"  ❌ FAILED")
                if not quarter_correct:
                    print(f"     Quarter mismatch: expected {scenario['expected_quarter']}, got {active_quarter_key}")
                if not status_correct:
                    print(f"     Status mismatch: expected {scenario['expected_status']}, got {display_data.get('Status')}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases for the quarter progression."""
    print(f"\n🧪 Testing Edge Cases")
    print("=" * 30)
    
    try:
        from app.services.quarter_service import QuarterService
        
        # Test different dates within Q3
        test_dates = [
            (date(2025, 7, 1), "Beginning of Q3"),
            (date(2025, 7, 15), "Middle of Q3"),
            (date(2025, 9, 30), "End of Q3")
        ]
        
        equipment_data = {
            'PPM_Q_II': {'quarter_date': '15/05/2025', 'engineer': 'JOHN'},  # Past, complete
            'PPM_Q_III': {'quarter_date': '15/08/2025', 'engineer': ''},     # August, no engineer
            'PPM_Q_IV': {'quarter_date': '15/11/2025', 'engineer': ''}
        }
        
        all_passed = True
        
        for test_date, description in test_dates:
            print(f"\n📅 Testing {description} ({test_date}):")
            
            active_quarter_num, active_quarter_key, active_quarter_data = \
                QuarterService.get_active_quarter_for_equipment(equipment_data, test_date)
            
            display_data = QuarterService.get_display_data_for_equipment(equipment_data, test_date)
            
            print(f"  Selected: {active_quarter_key}")
            print(f"  Status: {display_data.get('Status', 'N/A')}")
            
            if active_quarter_key == 'PPM_Q_III':
                print(f"  ✅ Correctly showing Q3 data")
            else:
                print(f"  ❌ Should show Q3 data, got {active_quarter_key}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Edge case test error: {e}")
        return False

def main():
    """Main test function."""
    print("🏥 Hospital Equipment Maintenance Management System")
    print("🔧 Quarter Progression Fix Validation")
    print("=" * 60)
    
    test1_result = test_quarter_fix()
    test2_result = test_edge_cases()
    
    print("\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Quarter progression logic is working correctly")
        print("✅ Current quarter is properly prioritized")
        print("✅ Overdue quarters are handled correctly")
        print("✅ Edge cases work as expected")
        print("\n🚀 The quarter progression fix is ready for production!")
    else:
        print("❌ SOME TESTS FAILED!")
        if not test1_result:
            print("❌ Main quarter progression tests failed")
        if not test2_result:
            print("❌ Edge case tests failed")
    
    return test1_result and test2_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
