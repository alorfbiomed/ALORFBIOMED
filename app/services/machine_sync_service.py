"""
Service for synchronizing machine data with departments_and_machines.json
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.config import Config

logger = logging.getLogger(__name__)


class MachineSyncService:
    """Service for managing machine-department synchronization."""
    
    DEPARTMENTS_MACHINES_PATH = Path(Config.DATA_DIR) / 'departments_and_machines.json'
    
    @staticmethod
    def _load_departments_machines() -> Dict[str, List[str]]:
        """Load departments and machines data from JSON file."""
        try:
            if not MachineSyncService.DEPARTMENTS_MACHINES_PATH.exists():
                logger.warning(f"Departments and machines file not found: {MachineSyncService.DEPARTMENTS_MACHINES_PATH}")
                return {}
            
            with open(MachineSyncService.DEPARTMENTS_MACHINES_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Loaded departments and machines data with {len(data)} departments")
                return data
        except Exception as e:
            logger.error(f"Error loading departments and machines data: {e}")
            return {}
    
    @staticmethod
    def _save_departments_machines(data: Dict[str, List[str]]):
        """Save departments and machines data to JSON file."""
        try:
            with open(MachineSyncService.DEPARTMENTS_MACHINES_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                logger.debug(f"Saved departments and machines data with {len(data)} departments")
        except Exception as e:
            logger.error(f"Error saving departments and machines data: {e}")
            raise
    
    @staticmethod
    def sync_machine_to_department(machine_name: str, department: str, equipment_type: str = None):
        """
        Synchronize a machine to its department in departments_and_machines.json.
        
        Args:
            machine_name: Name of the machine (MODEL for PPM, EQUIPMENT for OCM)
            department: Department name
            equipment_type: Type of equipment ('ppm' or 'ocm') for logging purposes
        """
        try:
            if not machine_name or not department:
                logger.warning(f"Invalid machine_name '{machine_name}' or department '{department}' for sync")
                return
            
            # Clean up machine name (remove extra spaces, convert to uppercase)
            machine_name = machine_name.strip().upper()
            department = department.strip()
            
            # Load current data
            departments_data = MachineSyncService._load_departments_machines()
            
            if department not in departments_data:
                logger.warning(f"Department '{department}' not found in departments_and_machines.json")
                return
            
            # Check if machine already exists in the department
            if machine_name in departments_data[department]:
                logger.debug(f"Machine '{machine_name}' already exists in department '{department}'")
                return
            
            # Add machine to department (keep list sorted)
            departments_data[department].append(machine_name)
            departments_data[department].sort()
            
            # Save updated data
            MachineSyncService._save_departments_machines(departments_data)
            
            logger.info(f"Successfully added machine '{machine_name}' to department '{department}' "
                       f"({equipment_type or 'unknown'} equipment)")
            
        except Exception as e:
            logger.error(f"Error syncing machine '{machine_name}' to department '{department}': {e}")
    
    @staticmethod
    def remove_machine_from_department(machine_name: str, department: str, equipment_type: str = None):
        """
        Remove a machine from its department in departments_and_machines.json.
        
        Args:
            machine_name: Name of the machine
            department: Department name
            equipment_type: Type of equipment ('ppm' or 'ocm') for logging purposes
        """
        try:
            if not machine_name or not department:
                logger.warning(f"Invalid machine_name '{machine_name}' or department '{department}' for removal")
                return
            
            # Clean up machine name
            machine_name = machine_name.strip().upper()
            department = department.strip()
            
            # Load current data
            departments_data = MachineSyncService._load_departments_machines()
            
            if department not in departments_data:
                logger.warning(f"Department '{department}' not found in departments_and_machines.json")
                return
            
            # Remove machine from department if it exists
            if machine_name in departments_data[department]:
                departments_data[department].remove(machine_name)
                
                # Save updated data
                MachineSyncService._save_departments_machines(departments_data)
                
                logger.info(f"Successfully removed machine '{machine_name}' from department '{department}' "
                           f"({equipment_type or 'unknown'} equipment)")
            else:
                logger.debug(f"Machine '{machine_name}' not found in department '{department}'")
                
        except Exception as e:
            logger.error(f"Error removing machine '{machine_name}' from department '{department}': {e}")
    
    @staticmethod
    def sync_equipment_entry(entry_data: Dict[str, Any], equipment_type: str):
        """
        Synchronize an equipment entry with departments_and_machines.json.
        
        Args:
            entry_data: Equipment entry data
            equipment_type: Type of equipment ('ppm' or 'ocm')
        """
        try:
            # Extract machine name and department based on equipment type
            if equipment_type == 'ppm':
                machine_name = entry_data.get('MODEL')
                department = entry_data.get('Department')
            elif equipment_type == 'ocm':
                machine_name = entry_data.get('EQUIPMENT') or entry_data.get('Name')
                department = entry_data.get('Department')
            else:
                logger.warning(f"Unknown equipment type: {equipment_type}")
                return
            
            if machine_name and department:
                MachineSyncService.sync_machine_to_department(machine_name, department, equipment_type)
            else:
                logger.warning(f"Missing machine name or department in {equipment_type} entry: {entry_data}")
                
        except Exception as e:
            logger.error(f"Error syncing {equipment_type} equipment entry: {e}")
    
    @staticmethod
    def handle_equipment_update(old_entry: Dict[str, Any], new_entry: Dict[str, Any], equipment_type: str):
        """
        Handle equipment update by managing machine-department changes.
        
        Args:
            old_entry: Previous equipment entry data
            new_entry: Updated equipment entry data
            equipment_type: Type of equipment ('ppm' or 'ocm')
        """
        try:
            # Extract old and new machine names and departments
            if equipment_type == 'ppm':
                old_machine = old_entry.get('MODEL')
                old_department = old_entry.get('Department')
                new_machine = new_entry.get('MODEL')
                new_department = new_entry.get('Department')
            elif equipment_type == 'ocm':
                old_machine = old_entry.get('EQUIPMENT') or old_entry.get('Name')
                old_department = old_entry.get('Department')
                new_machine = new_entry.get('EQUIPMENT') or new_entry.get('Name')
                new_department = new_entry.get('Department')
            else:
                logger.warning(f"Unknown equipment type: {equipment_type}")
                return
            
            # If department changed, remove from old and add to new
            if old_department != new_department:
                if old_machine and old_department:
                    MachineSyncService.remove_machine_from_department(old_machine, old_department, equipment_type)
                if new_machine and new_department:
                    MachineSyncService.sync_machine_to_department(new_machine, new_department, equipment_type)
            
            # If machine name changed within same department, update the entry
            elif old_machine != new_machine:
                if old_machine and old_department:
                    MachineSyncService.remove_machine_from_department(old_machine, old_department, equipment_type)
                if new_machine and new_department:
                    MachineSyncService.sync_machine_to_department(new_machine, new_department, equipment_type)
            
            # If both machine and department are the same, just ensure it's synced
            else:
                if new_machine and new_department:
                    MachineSyncService.sync_machine_to_department(new_machine, new_department, equipment_type)
                    
        except Exception as e:
            logger.error(f"Error handling {equipment_type} equipment update: {e}")
