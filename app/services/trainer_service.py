"""
Trainer service for managing trainer data.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.config import Config
from app.models.trainer import Trainer, TrainerCreate, TrainerUpdate
from app.services.department_service import DepartmentService

logger = logging.getLogger(__name__)

class TrainerService:
    """Service for managing trainer data."""
    
    @staticmethod
    def get_trainers_file_path() -> Path:
        """Get the path to the trainers.json file."""
        return Path(Config.DATA_DIR) / "trainers.json"
    
    @staticmethod
    def ensure_trainers_file_exists():
        """Ensure trainers.json file exists with default structure."""
        trainers_path = TrainerService.get_trainers_file_path()
        if not trainers_path.exists():
            logger.info(f"Creating new trainers file: {trainers_path}")
            # Ensure data directory exists
            trainers_path.parent.mkdir(exist_ok=True)
            with open(trainers_path, 'w') as f:
                json.dump([], f, indent=2)
    
    @staticmethod
    def load_trainers() -> List[Dict[str, Any]]:
        """Load trainers from JSON file."""
        try:
            TrainerService.ensure_trainers_file_exists()
            trainers_path = TrainerService.get_trainers_file_path()
            
            with open(trainers_path, 'r') as f:
                data = json.load(f)
                logger.debug(f"Loaded {len(data)} trainers from {trainers_path}")
                return data
        except Exception as e:
            logger.error(f"Error loading trainers: {str(e)}")
            return []
    
    @staticmethod
    def save_trainers(trainers: List[Dict[str, Any]]):
        """Save trainers to JSON file."""
        try:
            TrainerService.ensure_trainers_file_exists()
            trainers_path = TrainerService.get_trainers_file_path()
            
            with open(trainers_path, 'w') as f:
                json.dump(trainers, f, indent=2)
            logger.info(f"Saved {len(trainers)} trainers to {trainers_path}")
        except Exception as e:
            logger.error(f"Error saving trainers: {str(e)}")
            raise ValueError("Failed to save trainers") from e
    
    @staticmethod
    def get_all_trainers() -> List[Trainer]:
        """Get all trainers."""
        try:
            data = TrainerService.load_trainers()
            return [Trainer.from_dict(trainer_data) for trainer_data in data]
        except Exception as e:
            logger.error(f"Error getting all trainers: {str(e)}")
            return []
    
    @staticmethod
    def get_trainer_by_id(trainer_id: int) -> Optional[Trainer]:
        """Get trainer by ID."""
        try:
            trainers = TrainerService.get_all_trainers()
            for trainer in trainers:
                if trainer.id == trainer_id:
                    return trainer
            return None
        except Exception as e:
            logger.error(f"Error getting trainer by ID {trainer_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_trainers_by_department(department_id: int) -> List[Trainer]:
        """Get trainers by department ID."""
        try:
            trainers = TrainerService.get_all_trainers()
            return [trainer for trainer in trainers if trainer.department_id == department_id]
        except Exception as e:
            logger.error(f"Error getting trainers by department {department_id}: {str(e)}")
            return []
    
    @staticmethod
    def create_trainer(trainer_data: TrainerCreate) -> Trainer:
        """Create a new trainer."""
        try:
            # Validate department exists if provided
            if trainer_data.department_id:
                department = DepartmentService.get_department_by_id(trainer_data.department_id)
                if not department:
                    raise ValueError(f"Department with ID {trainer_data.department_id} does not exist")
            
            # Load existing trainers
            trainers_data = TrainerService.load_trainers()
            
            # Generate new ID
            new_id = max([trainer.get('id', 0) for trainer in trainers_data], default=0) + 1
            
            # Create new trainer
            new_trainer = Trainer(
                id=new_id,
                name=trainer_data.name,
                department_id=trainer_data.department_id,
                telephone=trainer_data.telephone,
                information=trainer_data.information
            )
            
            # Add to data
            trainers_data.append(new_trainer.to_dict())
            
            # Save to file
            TrainerService.save_trainers(trainers_data)
            
            logger.info(f"Created new trainer: {new_trainer.name} (ID: {new_id})")
            return new_trainer
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error creating trainer: {str(e)}")
            raise ValueError("Failed to create trainer") from e
    
    @staticmethod
    def update_trainer(trainer_id: int, update_data: TrainerUpdate) -> Optional[Trainer]:
        """Update an existing trainer."""
        try:
            # Validate department exists if provided
            if update_data.department_id:
                department = DepartmentService.get_department_by_id(update_data.department_id)
                if not department:
                    raise ValueError(f"Department with ID {update_data.department_id} does not exist")
            
            # Load existing trainers
            trainers_data = TrainerService.load_trainers()
            
            # Find trainer to update
            trainer_index = None
            for i, trainer_data in enumerate(trainers_data):
                if trainer_data.get('id') == trainer_id:
                    trainer_index = i
                    break
            
            if trainer_index is None:
                return None
            
            # Update trainer
            trainer = Trainer.from_dict(trainers_data[trainer_index])
            trainer.update(update_data)
            
            # Update in data
            trainers_data[trainer_index] = trainer.to_dict()
            
            # Save to file
            TrainerService.save_trainers(trainers_data)
            
            logger.info(f"Updated trainer ID {trainer_id}: {trainer.name}")
            return trainer
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating trainer {trainer_id}: {str(e)}")
            raise ValueError("Failed to update trainer") from e
    
    @staticmethod
    def delete_trainer(trainer_id: int) -> bool:
        """Delete a trainer."""
        try:
            # Check if trainer is in use (this would need to be implemented based on usage)
            # For now, we'll allow deletion but this should be enhanced
            
            # Load existing trainers
            trainers_data = TrainerService.load_trainers()
            
            # Find and remove trainer
            original_count = len(trainers_data)
            trainers_data = [trainer for trainer in trainers_data if trainer.get('id') != trainer_id]
            
            if len(trainers_data) == original_count:
                return False  # Trainer not found
            
            # Save updated data
            TrainerService.save_trainers(trainers_data)
            
            logger.info(f"Deleted trainer ID {trainer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting trainer {trainer_id}: {str(e)}")
            raise ValueError("Failed to delete trainer") from e
    
    @staticmethod
    def get_trainers_for_dropdown() -> List[Dict[str, Any]]:
        """Get trainers formatted for dropdown use."""
        try:
            trainers = TrainerService.get_all_trainers()
            return [
                {
                    'id': trainer.id,
                    'name': trainer.name,
                    'department_id': trainer.department_id,
                    'value': trainer.name  # For backward compatibility
                }
                for trainer in sorted(trainers, key=lambda x: x.name)
            ]
        except Exception as e:
            logger.error(f"Error getting trainers for dropdown: {str(e)}")
            return []
    
    @staticmethod
    def get_trainers_with_department_info() -> List[Dict[str, Any]]:
        """Get trainers with department information for display."""
        try:
            trainers = TrainerService.get_all_trainers()
            departments = {dept.id: dept for dept in DepartmentService.get_all_departments()}
            
            result = []
            for trainer in trainers:
                trainer_dict = trainer.to_dict()
                if trainer.department_id and trainer.department_id in departments:
                    trainer_dict['department_name'] = departments[trainer.department_id].department_name
                else:
                    trainer_dict['department_name'] = None
                result.append(trainer_dict)
            
            return sorted(result, key=lambda x: x['name'])
        except Exception as e:
            logger.error(f"Error getting trainers with department info: {str(e)}")
            return []
