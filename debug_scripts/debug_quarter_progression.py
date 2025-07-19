#!/usr/bin/env python3
"""
Debug script to investigate the quarter progression issue.
"""

import sys
import os
from datetime import datetime, date

sys.path.insert(0, '.')

def debug_quarter_progression():
    """Debug the quarter progression logic with sample data."""
    print("🔍 Debugging Quarter Progression Logic")
    print("=" * 50)
    
    try:
        from app.services.quarter_service import QuarterService
        
        # Current date (July 2025 = Q3)
        current_date = date(2025, 7, 4)
        print(f"📅 Current Date: {current_date}")
        print(f"📅 Current Calendar Quarter: Q{QuarterService.get_current_calendar_quarter(current_date)}")
        
        # Sample equipment data based on the screenshot
        sample_equipment = {
            'SERIAL': 'TEST-001',
            'PPM_Q_I': {
                'quarter_date': '15/01/2025',  # Q1 - January (past, should be complete)
                'engineer': 'JOHN'
            },
            'PPM_Q_II': {
                'quarter_date': '15/04/2025',  # Q2 - April (past, complete - has engineer)
                'engineer': 'JANE'
            },
            'PPM_Q_III': {
                'quarter_date': '15/07/2025',  # Q3 - July (current quarter, no engineer yet)
                'engineer': ''
            },
            'PPM_Q_IV': {
                'quarter_date': '15/10/2025',  # Q4 - October (future)
                'engineer': ''
            }
        }
        
        print("\n📋 Sample Equipment Data:")
        for quarter_key in ['PPM_Q_I', 'PPM_Q_II', 'PPM_Q_III', 'PPM_Q_IV']:
            quarter_data = sample_equipment.get(quarter_key, {})
            date_str = quarter_data.get('quarter_date', 'N/A')
            engineer = quarter_data.get('engineer', 'N/A')
            print(f"  {quarter_key}: Date={date_str}, Engineer='{engineer}'")
        
        print("\n🎯 Testing Quarter Selection Logic:")
        
        # Test the quarter selection
        active_quarter_num, active_quarter_key, active_quarter_data = \
            QuarterService.get_active_quarter_for_equipment(sample_equipment, current_date)
        
        print(f"✅ Selected Quarter: Q{active_quarter_num} ({active_quarter_key})")
        print(f"✅ Selected Data: {active_quarter_data}")
        
        # Test the display data generation
        display_data = QuarterService.get_display_data_for_equipment(sample_equipment, current_date)
        print(f"\n📊 Display Data: {display_data}")
        
        # Expected vs Actual
        print(f"\n🎯 Analysis:")
        print(f"Expected: Should show Q3 data (15/07/2025) since Q2 is complete")
        print(f"Actual: Shows {active_quarter_key} data ({active_quarter_data.get('quarter_date', 'N/A')})")
        
        if active_quarter_key == 'PPM_Q_III':
            print("✅ CORRECT: Showing Q3 data as expected")
        else:
            print("❌ INCORRECT: Should be showing Q3 data")
            
        # Let's trace through the logic step by step
        print(f"\n🔍 Step-by-step Logic Trace:")
        current_quarter = QuarterService.get_current_calendar_quarter(current_date)
        print(f"1. Current calendar quarter: Q{current_quarter}")
        
        print(f"2. Checking quarters in order:")
        for offset in range(4):
            quarter_to_check = ((current_quarter - 1 + offset) % 4) + 1
            quarter_key = QuarterService.QUARTER_KEYS[quarter_to_check - 1]
            quarter_data = sample_equipment.get(quarter_key, {})
            
            if not isinstance(quarter_data, dict):
                print(f"   Q{quarter_to_check} ({quarter_key}): Not a dict, skipping")
                continue
                
            quarter_date_str = quarter_data.get('quarter_date')
            engineer = quarter_data.get('engineer', '')
            
            if not quarter_date_str:
                print(f"   Q{quarter_to_check} ({quarter_key}): No date, skipping")
                continue
                
            try:
                from app.services.email_service import EmailService
                quarter_date = EmailService.parse_date_flexible(quarter_date_str).date()
                
                print(f"   Q{quarter_to_check} ({quarter_key}): Date={quarter_date}, Engineer='{engineer}'")
                
                if quarter_date < current_date:
                    if engineer and engineer.strip():
                        print(f"     → Past quarter, complete (has engineer) - continue looking")
                    else:
                        print(f"     → Past quarter, OVERDUE (no engineer) - RETURN THIS")
                        break
                elif quarter_date >= current_date:
                    print(f"     → Current/future quarter - add to candidates")
                    
            except Exception as e:
                print(f"   Q{quarter_to_check} ({quarter_key}): Date parsing error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_different_scenarios():
    """Test different equipment scenarios."""
    print(f"\n🧪 Testing Different Scenarios")
    print("=" * 40)
    
    try:
        from app.services.quarter_service import QuarterService
        
        current_date = date(2025, 7, 4)  # July 2025 = Q3
        
        scenarios = [
            {
                'name': 'Q2 Complete, Q3 Pending',
                'data': {
                    'PPM_Q_II': {'quarter_date': '15/04/2025', 'engineer': 'JOHN'},
                    'PPM_Q_III': {'quarter_date': '15/07/2025', 'engineer': ''},
                    'PPM_Q_IV': {'quarter_date': '15/10/2025', 'engineer': ''}
                }
            },
            {
                'name': 'Q2 Incomplete (Overdue)',
                'data': {
                    'PPM_Q_II': {'quarter_date': '15/04/2025', 'engineer': ''},
                    'PPM_Q_III': {'quarter_date': '15/07/2025', 'engineer': ''},
                    'PPM_Q_IV': {'quarter_date': '15/10/2025', 'engineer': ''}
                }
            },
            {
                'name': 'All Q3 Complete, Should Show Q4',
                'data': {
                    'PPM_Q_II': {'quarter_date': '15/04/2025', 'engineer': 'JOHN'},
                    'PPM_Q_III': {'quarter_date': '15/07/2025', 'engineer': 'JANE'},
                    'PPM_Q_IV': {'quarter_date': '15/10/2025', 'engineer': ''}
                }
            }
        ]
        
        for scenario in scenarios:
            print(f"\n📋 Scenario: {scenario['name']}")
            
            active_quarter_num, active_quarter_key, active_quarter_data = \
                QuarterService.get_active_quarter_for_equipment(scenario['data'], current_date)
            
            display_data = QuarterService.get_display_data_for_equipment(scenario['data'], current_date)
            
            print(f"   Selected: Q{active_quarter_num} ({active_quarter_key})")
            print(f"   Date: {active_quarter_data.get('quarter_date', 'N/A')}")
            print(f"   Status: {display_data.get('Status', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scenario test error: {e}")
        return False

def main():
    """Main debug function."""
    print("🏥 Hospital Equipment Maintenance Management System")
    print("🔧 Quarter Progression Debug")
    print("=" * 60)
    
    debug_result = debug_quarter_progression()
    scenario_result = test_with_different_scenarios()
    
    print("\n" + "=" * 60)
    print("📊 DEBUG RESULTS")
    print("=" * 60)
    
    if debug_result and scenario_result:
        print("✅ Debug completed successfully")
    else:
        print("❌ Debug encountered errors")
    
    return debug_result and scenario_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
