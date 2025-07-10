"""
Department service for managing department data.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import Config
from app.models.department import Department, DepartmentCreate, DepartmentUpdate

logger = logging.getLogger(__name__)

class DepartmentService:
    """Service for managing department data."""
    
    @staticmethod
    def get_departments_file_path() -> Path:
        """Get the path to the departments.json file."""
        return Path(Config.DATA_DIR) / "departments.json"
    
    @staticmethod
    def ensure_departments_file_exists():
        """Ensure departments.json file exists with default structure."""
        departments_path = DepartmentService.get_departments_file_path()
        if not departments_path.exists():
            logger.info(f"Creating new departments file: {departments_path}")
            # Ensure data directory exists
            departments_path.parent.mkdir(exist_ok=True)
            with open(departments_path, 'w') as f:
                json.dump([], f, indent=2)
    
    @staticmethod
    def load_departments() -> List[Dict[str, Any]]:
        """Load departments from JSON file."""
        try:
            DepartmentService.ensure_departments_file_exists()
            departments_path = DepartmentService.get_departments_file_path()
            
            with open(departments_path, 'r') as f:
                data = json.load(f)
                logger.debug(f"Loaded {len(data)} departments from {departments_path}")
                return data
        except Exception as e:
            logger.error(f"Error loading departments: {str(e)}")
            return []
    
    @staticmethod
    def save_departments(departments: List[Dict[str, Any]]):
        """Save departments to JSON file."""
        try:
            DepartmentService.ensure_departments_file_exists()
            departments_path = DepartmentService.get_departments_file_path()
            
            with open(departments_path, 'w') as f:
                json.dump(departments, f, indent=2)
            logger.info(f"Saved {len(departments)} departments to {departments_path}")
        except Exception as e:
            logger.error(f"Error saving departments: {str(e)}")
            raise ValueError("Failed to save departments") from e
    
    @staticmethod
    def get_all_departments() -> List[Department]:
        """Get all departments."""
        try:
            data = DepartmentService.load_departments()
            return [Department.from_dict(dept_data) for dept_data in data]
        except Exception as e:
            logger.error(f"Error getting all departments: {str(e)}")
            return []
    
    @staticmethod
    def get_department_by_id(department_id: int) -> Optional[Department]:
        """Get department by ID."""
        try:
            departments = DepartmentService.get_all_departments()
            for dept in departments:
                if dept.id == department_id:
                    return dept
            return None
        except Exception as e:
            logger.error(f"Error getting department by ID {department_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_department_by_name(department_name: str) -> Optional[Department]:
        """Get department by name."""
        try:
            departments = DepartmentService.get_all_departments()
            for dept in departments:
                if dept.department_name.lower() == department_name.lower():
                    return dept
            return None
        except Exception as e:
            logger.error(f"Error getting department by name {department_name}: {str(e)}")
            return None
    
    @staticmethod
    def create_department(department_data: DepartmentCreate) -> Department:
        """Create a new department."""
        try:
            # Check if department name already exists
            existing_dept = DepartmentService.get_department_by_name(department_data.department_name)
            if existing_dept:
                raise ValueError(f"Department '{department_data.department_name}' already exists")
            
            # Load existing departments
            departments_data = DepartmentService.load_departments()
            
            # Generate new ID
            new_id = max([dept.get('id', 0) for dept in departments_data], default=0) + 1
            
            # Create new department
            new_department = Department(
                id=new_id,
                department_name=department_data.department_name,
                information=department_data.information
            )
            
            # Add to data
            departments_data.append(new_department.to_dict())
            
            # Save to file
            DepartmentService.save_departments(departments_data)
            
            logger.info(f"Created new department: {new_department.department_name} (ID: {new_id})")
            return new_department
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating department: {str(e)}")
            raise ValueError("Failed to create department") from e
    
    @staticmethod
    def update_department(department_id: int, update_data: DepartmentUpdate) -> Optional[Department]:
        """Update an existing department."""
        try:
            # Load existing departments
            departments_data = DepartmentService.load_departments()
            
            # Find department to update
            dept_index = None
            for i, dept_data in enumerate(departments_data):
                if dept_data.get('id') == department_id:
                    dept_index = i
                    break
            
            if dept_index is None:
                return None
            
            # Check if new name conflicts with existing departments (excluding current)
            if update_data.department_name:
                for i, dept_data in enumerate(departments_data):
                    if (i != dept_index and 
                        dept_data.get('department_name', '').lower() == update_data.department_name.lower()):
                        raise ValueError(f"Department '{update_data.department_name}' already exists")
            
            # Update department
            department = Department.from_dict(departments_data[dept_index])
            department.update(update_data)
            
            # Update in data
            departments_data[dept_index] = department.to_dict()
            
            # Save to file
            DepartmentService.save_departments(departments_data)
            
            logger.info(f"Updated department ID {department_id}: {department.department_name}")
            return department
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating department {department_id}: {str(e)}")
            raise ValueError("Failed to update department") from e
    
    @staticmethod
    def delete_department(department_id: int) -> bool:
        """Delete a department."""
        try:
            # Check if department has associated trainers (foreign key constraint)
            from app.services.trainer_service import TrainerService
            associated_trainers = TrainerService.get_trainers_by_department(department_id)
            if associated_trainers:
                trainer_names = [trainer.name for trainer in associated_trainers]
                raise ValueError(f"Cannot delete department. It has {len(associated_trainers)} associated trainer(s): {', '.join(trainer_names)}")

            # Load existing departments
            departments_data = DepartmentService.load_departments()

            # Find and remove department
            original_count = len(departments_data)
            departments_data = [dept for dept in departments_data if dept.get('id') != department_id]

            if len(departments_data) == original_count:
                return False  # Department not found

            # Save updated data
            DepartmentService.save_departments(departments_data)

            logger.info(f"Deleted department ID {department_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting department {department_id}: {str(e)}")
            raise ValueError("Failed to delete department") from e
    
    @staticmethod
    def get_departments_for_dropdown() -> List[Dict[str, Any]]:
        """Get departments formatted for dropdown use."""
        try:
            departments = DepartmentService.get_all_departments()
            return [
                {
                    'id': dept.id,
                    'name': dept.department_name,
                    'value': dept.department_name  # For backward compatibility
                }
                for dept in sorted(departments, key=lambda x: x.department_name)
            ]
        except Exception as e:
            logger.error(f"Error getting departments for dropdown: {str(e)}")
            return []
