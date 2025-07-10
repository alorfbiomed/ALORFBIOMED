#!/usr/bin/env python3
"""
Data migration script to populate departments and trainers from existing constants.
This script should be run once after implementing the new department and trainer management system.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from app.constants import DEPARTMENTS, TRAINERS
from app.services.department_service import DepartmentService
from app.services.trainer_service import TrainerService
from app.models.department import DepartmentCreate
from app.models.trainer import TrainerCreate

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_departments():
    """Migrate departments from constants to the new department management system."""
    logger.info("Starting department migration...")
    
    try:
        # Check if departments already exist
        existing_departments = DepartmentService.get_all_departments()
        if existing_departments:
            logger.info(f"Found {len(existing_departments)} existing departments. Skipping migration.")
            return existing_departments
        
        migrated_departments = []
        
        for dept_name in DEPARTMENTS:
            try:
                # Create department data
                dept_data = DepartmentCreate(
                    department_name=dept_name,
                    information=f"Migrated from constants on {datetime.now().strftime('%Y-%m-%d')}"
                )
                
                # Create department
                new_department = DepartmentService.create_department(dept_data)
                migrated_departments.append(new_department)
                logger.info(f"Created department: {dept_name} (ID: {new_department.id})")
                
            except Exception as e:
                logger.error(f"Error creating department '{dept_name}': {str(e)}")
        
        logger.info(f"Successfully migrated {len(migrated_departments)} departments")
        return migrated_departments
        
    except Exception as e:
        logger.error(f"Error during department migration: {str(e)}")
        return []

def migrate_trainers(departments):
    """Migrate trainers from constants to the new trainer management system."""
    logger.info("Starting trainer migration...")
    
    try:
        # Check if trainers already exist
        existing_trainers = TrainerService.get_all_trainers()
        if existing_trainers:
            logger.info(f"Found {len(existing_trainers)} existing trainers. Skipping migration.")
            return existing_trainers
        
        migrated_trainers = []
        
        for trainer_name in TRAINERS:
            try:
                # Create trainer data (without department assignment for now)
                trainer_data = TrainerCreate(
                    name=trainer_name,
                    department_id=None,  # Will be assigned manually later
                    telephone=None,
                    information=f"Migrated from constants on {datetime.now().strftime('%Y-%m-%d')}"
                )
                
                # Create trainer
                new_trainer = TrainerService.create_trainer(trainer_data)
                migrated_trainers.append(new_trainer)
                logger.info(f"Created trainer: {trainer_name} (ID: {new_trainer.id})")
                
            except Exception as e:
                logger.error(f"Error creating trainer '{trainer_name}': {str(e)}")
        
        logger.info(f"Successfully migrated {len(migrated_trainers)} trainers")
        return migrated_trainers
        
    except Exception as e:
        logger.error(f"Error during trainer migration: {str(e)}")
        return []

def create_backup_of_constants():
    """Create a backup of the current constants for reference."""
    logger.info("Creating backup of current constants...")
    
    try:
        backup_data = {
            "departments": DEPARTMENTS,
            "trainers": TRAINERS,
            "migration_date": datetime.now().isoformat(),
            "note": "Backup created before migrating to new department/trainer management system"
        }
        
        backup_path = Path("data") / "constants_backup.json"
        backup_path.parent.mkdir(exist_ok=True)
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"Constants backup created at: {backup_path}")
        
    except Exception as e:
        logger.error(f"Error creating constants backup: {str(e)}")

def verify_migration():
    """Verify that the migration was successful."""
    logger.info("Verifying migration...")
    
    try:
        # Check departments
        departments = DepartmentService.get_all_departments()
        logger.info(f"Found {len(departments)} departments in the system:")
        for dept in departments:
            logger.info(f"  - {dept.department_name} (ID: {dept.id})")
        
        # Check trainers
        trainers = TrainerService.get_all_trainers()
        logger.info(f"Found {len(trainers)} trainers in the system:")
        for trainer in trainers:
            logger.info(f"  - {trainer.name} (ID: {trainer.id})")
        
        # Verify counts match original constants
        if len(departments) == len(DEPARTMENTS):
            logger.info("✅ Department count matches original constants")
        else:
            logger.warning(f"⚠️  Department count mismatch: {len(departments)} vs {len(DEPARTMENTS)}")
        
        if len(trainers) == len(TRAINERS):
            logger.info("✅ Trainer count matches original constants")
        else:
            logger.warning(f"⚠️  Trainer count mismatch: {len(trainers)} vs {len(TRAINERS)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        return False

def main():
    """Main migration function."""
    logger.info("=" * 60)
    logger.info("HOSPITAL EQUIPMENT MAINTENANCE SYSTEM")
    logger.info("Master Data Migration Script")
    logger.info("=" * 60)
    
    try:
        # Step 1: Create backup of constants
        create_backup_of_constants()
        
        # Step 2: Migrate departments
        departments = migrate_departments()
        if not departments:
            logger.error("Department migration failed. Aborting.")
            return False
        
        # Step 3: Migrate trainers
        trainers = migrate_trainers(departments)
        if not trainers:
            logger.error("Trainer migration failed. Aborting.")
            return False
        
        # Step 4: Verify migration
        if verify_migration():
            logger.info("=" * 60)
            logger.info("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info("Next steps:")
            logger.info("1. Test the new department and trainer management pages")
            logger.info("2. Verify that all dropdowns are working correctly")
            logger.info("3. Assign trainers to appropriate departments")
            logger.info("4. Update any hardcoded references to use the new system")
            return True
        else:
            logger.error("Migration verification failed.")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
