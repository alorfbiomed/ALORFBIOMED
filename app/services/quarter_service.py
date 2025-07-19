"""
Quarter Management Service for PPM Equipment Dashboard.
Handles automatic quarterly data progression and quarter detection logic.
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

class QuarterService:
    """Service for managing quarterly progression logic for PPM equipment."""
    
    # Quarter mappings
    QUARTER_KEYS = ['PPM_Q_I', 'PPM_Q_II', 'PPM_Q_III', 'PPM_Q_IV']
    QUARTER_NAMES = ['Q1', 'Q2', 'Q3', 'Q4']
    
    @staticmethod
    def get_current_calendar_quarter(target_date: Optional[date] = None) -> int:
        """
        Get the current calendar quarter (1-4) based on the date.
        
        Args:
            target_date: Date to check (defaults to today)
            
        Returns:
            Quarter number (1, 2, 3, or 4)
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        month = target_date.month
        if month <= 3:
            return 1
        elif month <= 6:
            return 2
        elif month <= 9:
            return 3
        else:
            return 4
    
    @staticmethod
    def get_active_quarter_for_equipment(equipment_data: Dict[str, Any],
                                       target_date: Optional[date] = None) -> Tuple[int, str, Dict[str, Any]]:
        """
        Determine which quarter should be displayed for a specific equipment item.

        This implements the automatic progression logic:
        1. Prioritize current calendar quarter if it needs attention
        2. If current quarter is complete and we're past its period, advance to next quarter
        3. Always show overdue quarters immediately
        4. Handle year-end rollover (Q4 -> Q1)

        Args:
            equipment_data: PPM equipment data dictionary
            target_date: Date to check (defaults to today)

        Returns:
            Tuple of (quarter_number, quarter_key, quarter_data)
        """
        if target_date is None:
            target_date = datetime.now().date()

        # Start with current calendar quarter
        current_quarter = QuarterService.get_current_calendar_quarter(target_date)

        # First, check the current calendar quarter specifically
        current_quarter_key = QuarterService.QUARTER_KEYS[current_quarter - 1]
        current_quarter_data = equipment_data.get(current_quarter_key, {})

        if isinstance(current_quarter_data, dict) and current_quarter_data.get('quarter_date'):
            try:
                current_quarter_date_str = current_quarter_data.get('quarter_date')
                current_quarter_date = EmailService.parse_date_flexible(current_quarter_date_str).date()
                current_engineer = current_quarter_data.get('engineer', '')

                # If current quarter is overdue (past date, no engineer), show it immediately
                if current_quarter_date < target_date and not (current_engineer and current_engineer.strip()):
                    return current_quarter, current_quarter_key, current_quarter_data

                # If current quarter is upcoming or current (future/today), show it
                if current_quarter_date >= target_date:
                    return current_quarter, current_quarter_key, current_quarter_data

                # If current quarter is complete (past date with engineer), we may need to progress
                # But only if we're significantly past the quarter period
                if current_quarter_date < target_date and current_engineer and current_engineer.strip():
                    # Check if we're still within a reasonable time of the current quarter
                    # If the maintenance was recent (within 30 days), still show current quarter
                    days_since_maintenance = (target_date - current_quarter_date).days
                    if days_since_maintenance <= 30:
                        return current_quarter, current_quarter_key, current_quarter_data

            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid date format in current quarter {current_quarter_key}: {current_quarter_date_str}")

        # If current quarter is not suitable, check other quarters
        incomplete_quarters = []  # Track quarters that need attention

        for offset in range(1, 4):  # Check next 3 quarters (skip current as we already checked it)
            quarter_to_check = ((current_quarter - 1 + offset) % 4) + 1
            quarter_key = QuarterService.QUARTER_KEYS[quarter_to_check - 1]
            quarter_data = equipment_data.get(quarter_key, {})

            if not isinstance(quarter_data, dict):
                continue

            quarter_date_str = quarter_data.get('quarter_date')
            engineer = quarter_data.get('engineer', '')

            if not quarter_date_str:
                continue

            try:
                quarter_date = EmailService.parse_date_flexible(quarter_date_str).date()

                # Check for overdue quarters (past date, no engineer)
                if quarter_date < target_date and not (engineer and engineer.strip()):
                    # Overdue quarter - this should be displayed immediately
                    return quarter_to_check, quarter_key, quarter_data
                elif quarter_date >= target_date:
                    # Current or future quarter - add to candidates
                    incomplete_quarters.append((quarter_to_check, quarter_key, quarter_data))

            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid date format in quarter {quarter_key}: {quarter_date_str}")
                continue

        # If we have incomplete quarters, return the first one (earliest)
        if incomplete_quarters:
            return incomplete_quarters[0]

        # Fallback: if no suitable quarter found, use current calendar quarter
        fallback_quarter = current_quarter
        fallback_key = QuarterService.QUARTER_KEYS[fallback_quarter - 1]
        fallback_data = equipment_data.get(fallback_key, {})

        return fallback_quarter, fallback_key, fallback_data
    
    @staticmethod
    def calculate_quarter_status(quarter_data: Dict[str, Any], target_date: Optional[date] = None) -> str:
        """
        Calculate the status of a quarter based on its date and engineer assignment.
        
        Args:
            quarter_data: Quarter data dictionary with 'quarter_date' and 'engineer'
            target_date: Date to compare against (defaults to today)
            
        Returns:
            Status string: 'Upcoming', 'Overdue', or 'Maintained'
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        quarter_date_str = quarter_data.get('quarter_date')
        engineer = quarter_data.get('engineer', '')
        
        if not quarter_date_str:
            return 'Upcoming'  # Default for missing dates
        
        try:
            quarter_date = EmailService.parse_date_flexible(quarter_date_str).date()
            
            if quarter_date < target_date:
                # Past date
                if engineer and engineer.strip():
                    return 'Maintained'
                else:
                    return 'Overdue'
            elif quarter_date == target_date:
                return 'Maintained'  # Due today counts as maintained
            else:
                return 'Upcoming'  # Future date
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid date format: {quarter_date_str}")
            return 'Upcoming'  # Default for invalid dates
    
    @staticmethod
    def get_display_data_for_equipment(equipment_data: Dict[str, Any], 
                                     target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get the display data for equipment on the dashboard.
        
        This determines which quarter's data should be shown and calculates
        the appropriate status and styling.
        
        Args:
            equipment_data: PPM equipment data dictionary
            target_date: Date to check (defaults to today)
            
        Returns:
            Dictionary with display_next_maintenance, Status, status_class, and active_quarter
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        # Get the active quarter for this equipment
        active_quarter_num, active_quarter_key, active_quarter_data = \
            QuarterService.get_active_quarter_for_equipment(equipment_data, target_date)
        
        # Calculate display values
        quarter_date_str = active_quarter_data.get('quarter_date')
        display_next_maintenance = quarter_date_str if quarter_date_str else 'N/A'
        
        # Calculate status
        status = QuarterService.calculate_quarter_status(active_quarter_data, target_date)
        
        # Determine status class for styling
        status_class = 'secondary'  # Default
        if status == 'Overdue':
            status_class = 'danger'
        elif status == 'Upcoming':
            status_class = 'warning'
        elif status == 'Maintained':
            status_class = 'success'
        
        return {
            'display_next_maintenance': display_next_maintenance,
            'Status': status,
            'status_class': status_class,
            'active_quarter': QuarterService.QUARTER_NAMES[active_quarter_num - 1],
            'active_quarter_key': active_quarter_key,
            'active_quarter_data': active_quarter_data
        }
    
    @staticmethod
    def get_dashboard_summary(target_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get a summary of which quarters are currently active across the system.
        
        Args:
            target_date: Date to check (defaults to today)
            
        Returns:
            Dictionary with current quarter info and system-wide statistics
        """
        if target_date is None:
            target_date = datetime.now().date()
        
        current_calendar_quarter = QuarterService.get_current_calendar_quarter(target_date)
        
        return {
            'current_date': target_date.strftime('%Y-%m-%d'),
            'current_calendar_quarter': current_calendar_quarter,
            'current_quarter_name': QuarterService.QUARTER_NAMES[current_calendar_quarter - 1],
            'quarter_keys': QuarterService.QUARTER_KEYS,
            'quarter_names': QuarterService.QUARTER_NAMES
        }
