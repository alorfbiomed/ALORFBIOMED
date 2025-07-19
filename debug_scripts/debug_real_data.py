#!/usr/bin/env python3
"""
Debug script to test with real data patterns from the PPM database.
"""

import sys
import os
from datetime import datetime, date

sys.path.insert(0, '.')

def test_real_data_patterns():
    """Test with actual data patterns from the database."""
    print("🔍 Testing Real Data Patterns")
    print("=" * 40)
    
    try:
        from app.services.quarter_service import QuarterService
        
        # Current date (July 4, 2025)
        current_date = date(2025, 7, 4)
        print(f"📅 Current Date: {current_date}")
        print(f"📅 Current Calendar Quarter: Q{QuarterService.get_current_calendar_quarter(current_date)}")
        
        # Real data patterns from the database
        test_cases = [
            {
                'name': 'Equipment with Q2 in April (past), Q3 in July (current)',
                'data': {
                    'PPM_Q_I': {'quarter_date': '03/01/2025', 'engineer': 'NIXON'},
                    'PPM_Q_II': {'quarter_date': '03/04/2025', 'engineer': 'ARUN'},  # April - past, complete
                    'PPM_Q_III': {'quarter_date': '02/07/2025', 'engineer': 'JAYAPRAKASH'},  # July - current/past
                    'PPM_Q_IV': {'quarter_date': '01/10/2025', 'engineer': ''}
                }
            },
            {
                'name': 'Equipment with Q2 in May (past), Q3 in August (future)',
                'data': {
                    'PPM_Q_I': {'quarter_date': '14/02/2025', 'engineer': 'ARUN'},
                    'PPM_Q_II': {'quarter_date': '15/05/2025', 'engineer': 'SUJITH'},  # May - past, complete
                    'PPM_Q_III': {'quarter_date': '13/08/2025', 'engineer': ''},  # August - future, no engineer
                    'PPM_Q_IV': {'quarter_date': '12/11/2025', 'engineer': ''}
                }
            },
            {
                'name': 'Equipment with Q2 in May (past), Q3 in August (future) with engineer',
                'data': {
                    'PPM_Q_I': {'quarter_date': '11/02/2025', 'engineer': 'NIXON'},
                    'PPM_Q_II': {'quarter_date': '12/05/2025', 'engineer': 'JAYAPRAKASH'},  # May - past, complete
                    'PPM_Q_III': {'quarter_date': '10/08/2025', 'engineer': 'NIXON'},  # August - future, has engineer
                    'PPM_Q_IV': {'quarter_date': '09/11/2025', 'engineer': ''}
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Test Case {i}: {test_case['name']}")
            print("-" * 60)
            
            # Show the quarter data
            for quarter_key in ['PPM_Q_I', 'PPM_Q_II', 'PPM_Q_III', 'PPM_Q_IV']:
                quarter_data = test_case['data'].get(quarter_key, {})
                date_str = quarter_data.get('quarter_date', 'N/A')
                engineer = quarter_data.get('engineer', 'N/A')
                print(f"  {quarter_key}: Date={date_str}, Engineer='{engineer}'")
            
            # Test the quarter selection
            active_quarter_num, active_quarter_key, active_quarter_data = \
                QuarterService.get_active_quarter_for_equipment(test_case['data'], current_date)
            
            # Test the display data generation
            display_data = QuarterService.get_display_data_for_equipment(test_case['data'], current_date)
            
            print(f"\n🎯 Results:")
            print(f"  Selected Quarter: Q{active_quarter_num} ({active_quarter_key})")
            print(f"  Display Date: {display_data.get('display_next_maintenance', 'N/A')}")
            print(f"  Status: {display_data.get('Status', 'N/A')}")
            print(f"  Status Class: {display_data.get('status_class', 'N/A')}")
            
            # Analysis
            print(f"\n📊 Analysis:")
            if active_quarter_key == 'PPM_Q_II':
                print(f"  ⚠️  Showing Q2 data - this might be the issue!")
                print(f"  ⚠️  Q2 is past and complete, should progress to Q3")
            elif active_quarter_key == 'PPM_Q_III':
                print(f"  ✅ Showing Q3 data - this is expected")
            else:
                print(f"  🤔 Showing {active_quarter_key} data - unexpected")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_quarter_progression_logic():
    """Test the specific progression logic step by step."""
    print(f"\n🔍 Testing Quarter Progression Logic")
    print("=" * 45)

    try:
        from app.services.quarter_service import QuarterService

        current_date = date(2025, 7, 4)  # July 4, 2025

        # Test case that matches the screenshot issue
        equipment_data = {
            'PPM_Q_I': {'quarter_date': '03/01/2025', 'engineer': 'NIXON'},
            'PPM_Q_II': {'quarter_date': '03/04/2025', 'engineer': 'ARUN'},  # April - past, complete
            'PPM_Q_III': {'quarter_date': '02/07/2025', 'engineer': 'JAYAPRAKASH'},  # July - current
            'PPM_Q_IV': {'quarter_date': '01/10/2025', 'engineer': ''}
        }

        print(f"📅 Current Date: {current_date}")
        current_quarter = QuarterService.get_current_calendar_quarter(current_date)
        print(f"📅 Current Calendar Quarter: Q{current_quarter}")

        # Test the actual Quarter Service method
        active_quarter_num, active_quarter_key, active_quarter_data = \
            QuarterService.get_active_quarter_for_equipment(equipment_data, current_date)

        print(f"\n🎯 NEW LOGIC RESULT:")
        print(f"  Selected Quarter: Q{active_quarter_num} ({active_quarter_key})")
        print(f"  Selected Date: {active_quarter_data.get('quarter_date', 'N/A')}")
        print(f"  Selected Engineer: '{active_quarter_data.get('engineer', 'N/A')}'")

        # Test the display data
        display_data = QuarterService.get_display_data_for_equipment(equipment_data, current_date)
        print(f"  Display Status: {display_data.get('Status', 'N/A')}")
        print(f"  Status Class: {display_data.get('status_class', 'N/A')}")

        # Analysis
        print(f"\n📊 Analysis:")
        if active_quarter_key == 'PPM_Q_III':
            print(f"  ✅ CORRECT: Showing Q3 data (current quarter)")
            print(f"  ✅ This matches the expected behavior")
            if display_data.get('Status') == 'Maintained':
                print(f"  ✅ Status 'Maintained' is correct (past date with engineer)")
            elif display_data.get('Status') == 'Upcoming':
                print(f"  ✅ Status 'Upcoming' is correct (future date)")
        else:
            print(f"  ❌ UNEXPECTED: Should be showing Q3 data")

        return True

    except Exception as e:
        print(f"❌ Logic test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debug function."""
    print("🏥 Hospital Equipment Maintenance Management System")
    print("🔧 Real Data Pattern Debug")
    print("=" * 60)
    
    test1_result = test_real_data_patterns()
    test2_result = test_quarter_progression_logic()
    
    print("\n" + "=" * 60)
    print("📊 DEBUG RESULTS")
    print("=" * 60)
    
    if test1_result and test2_result:
        print("✅ Debug completed successfully")
        print("\n🎯 KEY FINDINGS:")
        print("• Q2 dates are in April/May 2025 (past, complete)")
        print("• Q3 dates are in July/August 2025 (current/future)")
        print("• System should show Q3 data since Q2 is complete")
        print("• If showing Q2 data, there's a progression issue")
    else:
        print("❌ Debug encountered errors")
    
    return test1_result and test2_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
