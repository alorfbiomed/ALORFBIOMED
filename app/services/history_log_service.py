"""
Service for managing consolidated equipment history log.
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from app.config import Config
from app.services.data_service import DataService

logger = logging.getLogger(__name__)


class HistoryLogService:
    """Service for consolidated equipment history management."""

    HISTORY_DATA_PATH = Path(Config.DATA_DIR) / 'equipment_history.json'

    # Cache for equipment data to avoid repeated file loading
    _equipment_cache = {}
    _cache_timestamp = {}

    @staticmethod
    def _load_history_data() -> List[Dict[str, Any]]:
        """Load history data from JSON file."""
        try:
            if not HistoryLogService.HISTORY_DATA_PATH.exists():
                logger.warning(f"History file {HistoryLogService.HISTORY_DATA_PATH} not found")
                return []

            with open(HistoryLogService.HISTORY_DATA_PATH, 'r', encoding='utf-8') as file:
                data = json.load(file)
                logger.debug(f"Loaded {len(data)} history entries")
                return data
        except Exception as e:
            logger.error(f"Error loading history data: {e}")
            return []

    @staticmethod
    def _load_equipment_cache() -> Dict[str, Dict[str, Any]]:
        """Load and cache equipment data for both PPM and OCM."""
        try:
            current_time = time.time()
            cache_key = 'equipment_data'

            # Check if cache is still valid (5 minutes)
            if (cache_key in HistoryLogService._equipment_cache and
                cache_key in HistoryLogService._cache_timestamp and
                current_time - HistoryLogService._cache_timestamp[cache_key] < 300):
                return HistoryLogService._equipment_cache[cache_key]

            logger.debug("Loading equipment data into cache...")

            # Load PPM and OCM data
            ppm_data = DataService.load_data('ppm')
            ocm_data = DataService.load_data('ocm')

            # Build equipment lookup dictionary
            equipment_lookup = {}

            # Process PPM data
            for equipment in ppm_data:
                serial = equipment.get('SERIAL')
                if serial:
                    equipment_lookup[f"ppm_{serial}"] = {
                        'department': equipment.get('Department', 'Unknown'),
                        'name': equipment.get('Name') or equipment.get('MODEL') or equipment.get('EQUIPMENT', 'Unknown'),
                        'model': equipment.get('MODEL', 'Unknown'),
                        'manufacturer': equipment.get('MANUFACTURER', 'Unknown')
                    }

            # Process OCM data
            for equipment in ocm_data:
                serial = equipment.get('Serial')
                if serial:
                    equipment_lookup[f"ocm_{serial}"] = {
                        'department': equipment.get('Department', 'Unknown'),
                        'name': equipment.get('Name') or equipment.get('MODEL') or equipment.get('EQUIPMENT', 'Unknown'),
                        'model': equipment.get('MODEL') or equipment.get('Model', 'Unknown'),
                        'manufacturer': equipment.get('MANUFACTURER') or equipment.get('Manufacturer', 'Unknown')
                    }

            # Cache the data
            HistoryLogService._equipment_cache[cache_key] = equipment_lookup
            HistoryLogService._cache_timestamp[cache_key] = current_time

            logger.debug(f"Cached {len(equipment_lookup)} equipment records")
            return equipment_lookup

        except Exception as e:
            logger.error(f"Error loading equipment cache: {e}")
            return {}

    @staticmethod
    def _get_equipment_details(equipment_id: str, equipment_type: str) -> Dict[str, Any]:
        """Get equipment details from cached equipment data."""
        try:
            equipment_cache = HistoryLogService._load_equipment_cache()
            cache_key = f"{equipment_type.lower()}_{equipment_id}"

            if cache_key in equipment_cache:
                return equipment_cache[cache_key]

            # Equipment not found
            return {
                'department': 'Unknown',
                'name': 'Equipment Not Found',
                'model': 'Unknown',
                'manufacturer': 'Unknown'
            }

        except Exception as e:
            logger.error(f"Error getting equipment details for {equipment_type} {equipment_id}: {e}")
            return {
                'department': 'Error',
                'name': 'Error Loading',
                'model': 'Error',
                'manufacturer': 'Error'
            }
    
    @staticmethod
    def get_consolidated_history(
        search_query: str = '',
        equipment_type_filter: str = '',
        department_filter: str = '',
        start_date: str = '',
        end_date: str = '',
        sort_by: str = 'created_at',
        sort_order: str = 'desc',
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Get consolidated history data with filtering, sorting, and pagination.
        
        Returns:
            Dict containing history records, pagination info, and metadata
        """
        try:
            # Load raw history data
            history_data = HistoryLogService._load_history_data()
            
            # Build consolidated records
            consolidated_records = []
            record_id = 1
            
            for note in history_data:
                equipment_id = note.get('equipment_id', '')
                equipment_type = note.get('equipment_type', '').lower()
                
                # Get equipment details
                equipment_details = HistoryLogService._get_equipment_details(equipment_id, equipment_type)
                
                # Create consolidated record
                record = {
                    'id': record_id,
                    'note_id': note.get('id', ''),
                    'equipment_type': equipment_type.upper(),
                    'equipment_id': equipment_id,
                    'department': equipment_details['department'],
                    'name': equipment_details['name'],
                    'model': equipment_details['model'],
                    'manufacturer': equipment_details['manufacturer'],
                    'created_at': note.get('created_at', ''),
                    'updated_at': note.get('updated_at', ''),
                    'author_name': note.get('author_name', ''),
                    'note_text': note.get('note_text', ''),
                    'is_edited': note.get('is_edited', False),
                    'attachments_count': len(note.get('attachments', [])),
                    'attachments': note.get('attachments', [])
                }
                
                consolidated_records.append(record)
                record_id += 1
            
            # Apply filters
            filtered_records = HistoryLogService._apply_filters(
                consolidated_records,
                search_query,
                equipment_type_filter,
                department_filter,
                start_date,
                end_date
            )
            
            # Apply sorting
            sorted_records = HistoryLogService._apply_sorting(filtered_records, sort_by, sort_order)
            
            # Apply pagination
            total_records = len(sorted_records)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_records = sorted_records[start_idx:end_idx]
            
            # Calculate pagination info
            total_pages = (total_records + per_page - 1) // per_page
            has_prev = page > 1
            has_next = page < total_pages
            
            return {
                'records': paginated_records,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_records': total_records,
                    'total_pages': total_pages,
                    'has_prev': has_prev,
                    'has_next': has_next,
                    'prev_page': page - 1 if has_prev else None,
                    'next_page': page + 1 if has_next else None
                },
                'filters': {
                    'search_query': search_query,
                    'equipment_type_filter': equipment_type_filter,
                    'department_filter': department_filter,
                    'start_date': start_date,
                    'end_date': end_date,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting consolidated history: {e}")
            return {
                'records': [],
                'pagination': {
                    'page': 1,
                    'per_page': per_page,
                    'total_records': 0,
                    'total_pages': 0,
                    'has_prev': False,
                    'has_next': False,
                    'prev_page': None,
                    'next_page': None
                },
                'filters': {
                    'search_query': search_query,
                    'equipment_type_filter': equipment_type_filter,
                    'department_filter': department_filter,
                    'start_date': start_date,
                    'end_date': end_date,
                    'sort_by': sort_by,
                    'sort_order': sort_order
                }
            }
    
    @staticmethod
    def _apply_filters(
        records: List[Dict[str, Any]],
        search_query: str,
        equipment_type_filter: str,
        department_filter: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """Apply filters to history records."""
        filtered_records = records
        
        # Text search filter
        if search_query:
            search_lower = search_query.lower()
            filtered_records = [
                record for record in filtered_records
                if (search_lower in record.get('name', '').lower() or
                    search_lower in record.get('equipment_id', '').lower() or
                    search_lower in record.get('department', '').lower() or
                    search_lower in record.get('note_text', '').lower() or
                    search_lower in record.get('model', '').lower() or
                    search_lower in record.get('manufacturer', '').lower())
            ]
        
        # Equipment type filter
        if equipment_type_filter:
            filtered_records = [
                record for record in filtered_records
                if record.get('equipment_type', '').upper() == equipment_type_filter.upper()
            ]
        
        # Department filter
        if department_filter:
            filtered_records = [
                record for record in filtered_records
                if record.get('department', '') == department_filter
            ]
        
        # Date range filter
        if start_date or end_date:
            try:
                if start_date:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                if end_date:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                
                date_filtered_records = []
                for record in filtered_records:
                    try:
                        record_date = datetime.strptime(record.get('created_at', ''), '%Y-%m-%d %H:%M:%S')
                        
                        if start_date and record_date.date() < start_dt.date():
                            continue
                        if end_date and record_date.date() > end_dt.date():
                            continue
                        
                        date_filtered_records.append(record)
                    except ValueError:
                        # Skip records with invalid dates
                        continue
                
                filtered_records = date_filtered_records
                
            except ValueError as e:
                logger.warning(f"Invalid date format in filter: {e}")
        
        return filtered_records
    
    @staticmethod
    def _apply_sorting(records: List[Dict[str, Any]], sort_by: str, sort_order: str) -> List[Dict[str, Any]]:
        """Apply sorting to history records."""
        try:
            reverse = sort_order.lower() == 'desc'
            
            if sort_by == 'created_at':
                return sorted(records, key=lambda x: x.get('created_at', ''), reverse=reverse)
            elif sort_by == 'equipment_type':
                return sorted(records, key=lambda x: x.get('equipment_type', ''), reverse=reverse)
            elif sort_by == 'department':
                return sorted(records, key=lambda x: x.get('department', ''), reverse=reverse)
            elif sort_by == 'name':
                return sorted(records, key=lambda x: x.get('name', ''), reverse=reverse)
            elif sort_by == 'equipment_id':
                return sorted(records, key=lambda x: x.get('equipment_id', ''), reverse=reverse)
            else:
                # Default to created_at
                return sorted(records, key=lambda x: x.get('created_at', ''), reverse=reverse)
                
        except Exception as e:
            logger.error(f"Error applying sorting: {e}")
            return records
    
    @staticmethod
    def get_available_departments() -> List[str]:
        """Get list of all departments that have equipment with history."""
        try:
            history_data = HistoryLogService._load_history_data()
            departments = set()
            
            for note in history_data:
                equipment_id = note.get('equipment_id', '')
                equipment_type = note.get('equipment_type', '').lower()
                
                equipment_details = HistoryLogService._get_equipment_details(equipment_id, equipment_type)
                department = equipment_details.get('department', '')
                
                if department and department != 'Unknown' and department != 'Error':
                    departments.add(department)
            
            return sorted(list(departments))
            
        except Exception as e:
            logger.error(f"Error getting available departments: {e}")
            return []
