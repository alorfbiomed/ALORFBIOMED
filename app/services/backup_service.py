"""
Backup service for creating and managing application backups.
"""
import asyncio
import json
import logging
import os
import shutil
import threading
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal

from app.config import Config
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class BackupService:
    """Service for managing application backups."""

    # Backup paths - use absolute paths to avoid confusion
    BACKUPS_DIR = os.path.abspath(os.path.join(Config.DATA_DIR, "backups"))
    FULL_BACKUPS_DIR = os.path.join(BACKUPS_DIR, "full")
    SETTINGS_BACKUPS_DIR = os.path.join(BACKUPS_DIR, "settings")

    # Scheduler state
    _scheduler_thread = None
    _scheduler_running = False

    # File deletion lock to prevent race conditions between user deletion and automatic cleanup
    _deletion_locks = {}
    _deletion_lock_mutex = threading.Lock()
    
    @classmethod
    def _acquire_deletion_lock(cls, filename: str) -> bool:
        """
        Acquire a deletion lock for a specific filename to prevent race conditions.

        Args:
            filename: Name of the backup file

        Returns:
            True if lock was acquired, False if already locked
        """
        with cls._deletion_lock_mutex:
            if filename in cls._deletion_locks:
                return False  # Already locked
            cls._deletion_locks[filename] = threading.Lock()
            cls._deletion_locks[filename].acquire()
            return True

    @classmethod
    def _release_deletion_lock(cls, filename: str):
        """
        Release a deletion lock for a specific filename.

        Args:
            filename: Name of the backup file
        """
        with cls._deletion_lock_mutex:
            if filename in cls._deletion_locks:
                cls._deletion_locks[filename].release()
                del cls._deletion_locks[filename]

    @classmethod
    def initialize_backup_directories(cls):
        """Initialize backup directories if they don't exist."""
        try:
            os.makedirs(cls.BACKUPS_DIR, exist_ok=True)
            os.makedirs(cls.FULL_BACKUPS_DIR, exist_ok=True)
            os.makedirs(cls.SETTINGS_BACKUPS_DIR, exist_ok=True)
            logger.info("Backup directories initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing backup directories: {str(e)}")
            raise
    
    @classmethod
    def create_full_backup(cls) -> Dict[str, Any]:
        """
        Create a full application backup including all data files and settings.
        
        Returns:
            Dict containing backup result information
        """
        try:
            cls.initialize_backup_directories()
            
            # Use microseconds to prevent filename collisions in rapid succession
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_filename = f"full_backup_{timestamp}.zip"
            backup_path = os.path.join(cls.FULL_BACKUPS_DIR, backup_filename)
            
            # Files and directories to backup (optimized for smaller size)
            backup_items = [
                "data/",
                # Only backup essential config files, not entire directories
                "app/config.py",
                "app/constants.py",
                "app/__init__.py",
                "app/main.py"
            ]
            
            # Files to exclude for smaller backup size
            exclude_patterns = [
                '*.pyc', '__pycache__', '*.log', '*.log.*', 
                'backups/', 'logs/', '.git/', '.venv/', 
                '*.tmp', '*.temp', 'cache/', 'sessions/'
            ]
            
            def should_exclude_file(file_path):
                """Check if file should be excluded from backup."""
                file_name = os.path.basename(file_path)
                dir_name = os.path.dirname(file_path)
                
                for pattern in exclude_patterns:
                    if pattern.endswith('/'):
                        # Directory pattern
                        if pattern[:-1] in dir_name:
                            return True
                    elif '*' in pattern:
                        # Wildcard pattern
                        import fnmatch
                        if fnmatch.fnmatch(file_name, pattern):
                            return True
                    elif pattern in file_path:
                        return True
                return False
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                files_added = 0
                for item in backup_items:
                    if os.path.exists(item):
                        if os.path.isdir(item):
                            # Add directory recursively with filtering
                            for root, dirs, files in os.walk(item):
                                # Skip excluded directories
                                dirs[:] = [d for d in dirs if not any(pattern[:-1] in d for pattern in exclude_patterns if pattern.endswith('/'))]
                                
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    if not should_exclude_file(file_path):
                                        arcname = os.path.relpath(file_path)
                                        zipf.write(file_path, arcname)
                                        files_added += 1
                        else:
                            # Add single file if not excluded
                            if not should_exclude_file(item):
                                zipf.write(item, item)
                                files_added += 1
            
            # Get backup file size
            backup_size = os.path.getsize(backup_path)
            backup_size_mb = round(backup_size / (1024 * 1024), 2)
            
            # Log audit event
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['BACKUP_CREATED'],
                performed_by="System",
                description=f"Full application backup created: {backup_filename}",
                status=AuditService.STATUS_SUCCESS,
                details={
                    "backup_type": "full",
                    "filename": backup_filename,
                    "size_mb": backup_size_mb,
                    "files_backed_up": files_added,
                    "compression_level": 9
                }
            )
            
            logger.info(f"Full backup created successfully: {backup_filename} ({backup_size_mb} MB)")
            
            return {
                "success": True,
                "filename": backup_filename,
                "path": backup_path,
                "size_mb": backup_size_mb,
                "timestamp": timestamp,
                "message": f"Full backup created successfully ({backup_size_mb} MB)"
            }
            
        except Exception as e:
            logger.error(f"Error creating full backup: {str(e)}")
            
            # Log audit event for failure
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['BACKUP_CREATED'],
                performed_by="System",
                description="Full application backup failed",
                status=AuditService.STATUS_FAILED,
                details={
                    "backup_type": "full",
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create full backup: {str(e)}"
            }
    
    @classmethod
    def create_settings_backup(cls) -> Dict[str, Any]:
        """
        Create a settings-only backup.
        
        Returns:
            Dict containing backup result information
        """
        try:
            cls.initialize_backup_directories()
            
            # Use microseconds to prevent filename collisions in rapid succession
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_filename = f"settings_backup_{timestamp}.json"
            backup_path = os.path.join(cls.SETTINGS_BACKUPS_DIR, backup_filename)
            
            # Load current settings
            from app.services.data_service import DataService
            settings = DataService.load_settings()
            
            # Create backup with metadata
            backup_data = {
                "backup_info": {
                    "created_at": datetime.now().isoformat(),
                    "backup_type": "settings",
                    "version": "1.0"
                },
                "settings": settings
            }
            
            # Write backup file
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Get backup file size
            backup_size = os.path.getsize(backup_path)
            backup_size_kb = round(backup_size / 1024, 2)
            
            # Log audit event
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['BACKUP_CREATED'],
                performed_by="System",
                description=f"Settings backup created: {backup_filename}",
                status=AuditService.STATUS_SUCCESS,
                details={
                    "backup_type": "settings",
                    "filename": backup_filename,
                    "size_kb": backup_size_kb,
                    "settings_count": len(settings)
                }
            )
            
            logger.info(f"Settings backup created successfully: {backup_filename} ({backup_size_kb} KB)")
            
            return {
                "success": True,
                "filename": backup_filename,
                "path": backup_path,
                "size_kb": backup_size_kb,
                "timestamp": timestamp,
                "message": f"Settings backup created successfully ({backup_size_kb} KB)"
            }
            
        except Exception as e:
            logger.error(f"Error creating settings backup: {str(e)}")
            
            # Log audit event for failure
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['BACKUP_CREATED'],
                performed_by="System",
                description="Settings backup failed",
                status=AuditService.STATUS_FAILED,
                details={
                    "backup_type": "settings",
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create settings backup: {str(e)}"
            }
    
    @classmethod
    def restore_settings_backup(cls, backup_file_path: str) -> Dict[str, Any]:
        """
        Restore settings from a backup file.
        
        Args:
            backup_file_path: Path to the settings backup JSON file
            
        Returns:
            Dict containing restore result information
        """
        try:
            # Read and validate backup file
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Validate backup structure
            if 'backup_info' not in backup_data or 'settings' not in backup_data:
                return {
                    "success": False,
                    "error": "Invalid backup file format",
                    "message": "The backup file is not a valid settings backup"
                }
            
            if backup_data['backup_info'].get('backup_type') != 'settings':
                return {
                    "success": False,
                    "error": "Wrong backup type",
                    "message": "This is not a settings backup file"
                }
            
            # Restore settings
            from app.services.data_service import DataService
            settings = backup_data['settings']
            
            # Save the restored settings
            DataService.save_settings(settings)
            
            # Log audit event
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['BACKUP_RESTORED'],
                performed_by="User",
                description="Settings backup restored successfully",
                status=AuditService.STATUS_SUCCESS,
                details={
                    "backup_type": "settings",
                    "backup_created_at": backup_data['backup_info'].get('created_at'),
                    "settings_count": len(settings)
                }
            )
            
            logger.info("Settings backup restored successfully")
            
            return {
                "success": True,
                "message": "Settings backup restored successfully",
                "restored_items": len(settings)
            }
            
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Backup file not found",
                "message": "The specified backup file could not be found"
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "Invalid JSON format",
                "message": "The backup file is corrupted or not a valid JSON file"
            }
        except Exception as e:
            logger.error(f"Error restoring settings backup: {str(e)}")
            
            # Log audit event for failure
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['BACKUP_RESTORED'],
                performed_by="User",
                description="Settings backup restore failed",
                status=AuditService.STATUS_FAILED,
                details={
                    "backup_type": "settings",
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to restore settings backup: {str(e)}"
            }
    
    @classmethod
    def restore_full_backup(cls, backup_file_path: str) -> Dict[str, Any]:
        """
        Restore a full application backup.
        
        Args:
            backup_file_path: Path to the full backup ZIP file
            
        Returns:
            Dict containing restore result information
        """
        try:
            import tempfile
            import shutil
            
            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract backup file
                with zipfile.ZipFile(backup_file_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                restored_items = 0
                
                # Restore data directory
                data_backup_path = os.path.join(temp_dir, "data")
                if os.path.exists(data_backup_path):
                    # Create backup of current data before restoration
                    current_data_backup = f"data_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.move("data", current_data_backup)
                    
                    # Restore data from backup
                    shutil.copytree(data_backup_path, "data")
                    restored_items += len(os.listdir("data"))
                    logger.info(f"Data directory restored. Current data backed up as: {current_data_backup}")
                
                # Note: For full restoration of application files, we would need to restart the application
                # This is a simplified version that only restores data files
                
                # Log audit event
                AuditService.log_event(
                    event_type=AuditService.EVENT_TYPES['BACKUP_RESTORED'],
                    performed_by="User",
                    description="Full application backup restored successfully",
                    status=AuditService.STATUS_SUCCESS,
                    details={
                        "backup_type": "full",
                        "restored_items": restored_items,
                        "previous_data_backup": current_data_backup
                    }
                )
                
                logger.info(f"Full backup restored successfully. {restored_items} items restored.")
                
                return {
                    "success": True,
                    "message": f"Full backup restored successfully. Previous data backed up as: {current_data_backup}",
                    "restored_items": restored_items
                }
                
        except zipfile.BadZipFile:
            return {
                "success": False,
                "error": "Invalid ZIP file",
                "message": "The backup file is corrupted or not a valid ZIP file"
            }
        except Exception as e:
            logger.error(f"Error restoring full backup: {str(e)}")
            
            # Log audit event for failure
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['BACKUP_RESTORED'],
                performed_by="User",
                description="Full application backup restore failed",
                status=AuditService.STATUS_FAILED,
                details={
                    "backup_type": "full",
                    "error": str(e)
                }
            )
            
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to restore full backup: {str(e)}"
            }
    
    @classmethod
    def list_backups(cls, backup_type: Literal["full", "settings"] = None) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Args:
            backup_type: Type of backups to list ("full", "settings", or None for all)
            
        Returns:
            List of backup information dictionaries
        """
        try:
            cls.initialize_backup_directories()
            backups = []
            
            # List full backups
            if backup_type is None or backup_type == "full":
                if os.path.exists(cls.FULL_BACKUPS_DIR):
                    for filename in os.listdir(cls.FULL_BACKUPS_DIR):
                        if filename.endswith('.zip'):
                            file_path = os.path.join(cls.FULL_BACKUPS_DIR, filename)
                            stat = os.stat(file_path)
                            backups.append({
                                "type": "full",
                                "filename": filename,
                                "path": file_path,
                                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "age_days": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                            })
            
            # List settings backups
            if backup_type is None or backup_type == "settings":
                if os.path.exists(cls.SETTINGS_BACKUPS_DIR):
                    for filename in os.listdir(cls.SETTINGS_BACKUPS_DIR):
                        if filename.endswith('.json'):
                            file_path = os.path.join(cls.SETTINGS_BACKUPS_DIR, filename)
                            stat = os.stat(file_path)
                            backups.append({
                                "type": "settings",
                                "filename": filename,
                                "path": file_path,
                                "size_kb": round(stat.st_size / 1024, 2),
                                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "age_days": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                            })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return []
    
    @classmethod
    def delete_backup(cls, filename: str) -> Dict[str, Any]:
        """
        Delete a backup file with race condition protection.

        Args:
            filename: Name of the backup file to delete

        Returns:
            Dict containing deletion result information
        """
        try:
            # Input validation
            if not filename or not filename.strip():
                logger.warning("Empty filename provided for backup deletion")
                return {
                    "success": False,
                    "error": "Invalid filename",
                    "message": "Backup filename cannot be empty"
                }

            # Sanitize filename to prevent path traversal
            filename = filename.strip()
            if '..' in filename or '/' in filename or '\\' in filename:
                logger.warning(f"Invalid filename provided for backup deletion: {filename}")
                return {
                    "success": False,
                    "error": "Invalid filename",
                    "message": "Invalid backup filename provided"
                }

            # Acquire deletion lock to prevent race conditions with automatic cleanup
            if not cls._acquire_deletion_lock(filename):
                logger.warning(f"Backup file {filename} is already being deleted by another process")
                return {
                    "success": False,
                    "error": "File being deleted",
                    "message": f"Backup file '{filename}' is currently being deleted by another process. Please try again."
                }

            try:
                cls.initialize_backup_directories()

                # Find the backup file
                full_path = os.path.join(cls.FULL_BACKUPS_DIR, filename)
                settings_path = os.path.join(cls.SETTINGS_BACKUPS_DIR, filename)

                backup_path = None
                backup_type = None

                # Check both locations for the backup file
                if os.path.exists(full_path):
                    backup_path = full_path
                    backup_type = "full"
                elif os.path.exists(settings_path):
                    backup_path = settings_path
                    backup_type = "settings"

                if not backup_path:
                    # Enhanced error message with more context
                    logger.warning(f"Backup file not found for deletion: {filename}")
                    logger.debug(f"Checked paths: {full_path}, {settings_path}")

                    return {
                        "success": False,
                        "error": "Backup file not found",
                        "message": f"Backup file '{filename}' not found. It may have already been deleted or moved."
                    }

                # Verify file still exists just before deletion (race condition protection)
                if not os.path.exists(backup_path):
                    logger.warning(f"Backup file disappeared between check and deletion: {filename}")
                    return {
                        "success": False,
                        "error": "Backup file not found",
                        "message": f"Backup file '{filename}' was not found at deletion time. It may have been deleted by another process."
                    }

                # Delete the file
                os.remove(backup_path)

                # Verify deletion was successful
                if os.path.exists(backup_path):
                    logger.error(f"Failed to delete backup file: {filename} - file still exists after deletion attempt")
                    return {
                        "success": False,
                        "error": "Deletion failed",
                        "message": f"Failed to delete backup '{filename}' - file still exists after deletion attempt"
                    }

                # Log audit event
                AuditService.log_event(
                    event_type=AuditService.EVENT_TYPES['BACKUP_DELETED'],
                    performed_by="User",
                    description=f"Backup deleted: {filename}",
                    status=AuditService.STATUS_SUCCESS,
                    details={
                        "backup_type": backup_type,
                        "filename": filename,
                        "file_path": backup_path
                    }
                )

                logger.info(f"Backup deleted successfully: {filename} (type: {backup_type})")

                return {
                    "success": True,
                    "filename": filename,
                    "backup_type": backup_type,
                    "message": f"Backup '{filename}' deleted successfully"
                }

            finally:
                # Always release the deletion lock
                cls._release_deletion_lock(filename)
            
        except Exception as e:
            logger.error(f"Error deleting backup {filename}: {str(e)}")

            # Release the deletion lock in case of exception
            cls._release_deletion_lock(filename)

            # Log audit event for failure
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['BACKUP_DELETED'],
                performed_by="User",
                description=f"Failed to delete backup: {filename}",
                status=AuditService.STATUS_FAILED,
                details={
                    "filename": filename,
                    "error": str(e)
                }
            )

            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete backup '{filename}': {str(e)}"
            }
    
    @classmethod
    def cleanup_old_backups(cls, max_age_days: int = 30) -> Dict[str, Any]:
        """
        Clean up old backup files.
        
        Args:
            max_age_days: Maximum age of backups to keep (default: 30 days)
            
        Returns:
            Dict containing cleanup result information
        """
        try:
            backups = cls.list_backups()
            deleted_count = 0
            deleted_files = []
            
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            for backup in backups:
                backup_date = datetime.fromisoformat(backup['created_at'])
                if backup_date < cutoff_date:
                    result = cls.delete_backup(backup['filename'])
                    if result['success']:
                        deleted_count += 1
                        deleted_files.append(backup['filename'])
            
            logger.info(f"Cleanup completed: {deleted_count} old backups deleted")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "deleted_files": deleted_files,
                "message": f"Cleanup completed: {deleted_count} old backups deleted"
            }
            
        except Exception as e:
            logger.error(f"Error during backup cleanup: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Backup cleanup failed: {str(e)}"
            }
    
    @classmethod
    def start_automatic_backup_scheduler(cls):
        """Start the automatic backup scheduler."""
        if cls._scheduler_running:
            logger.info("Backup scheduler is already running")
            return
        
        cls._scheduler_running = True
        cls._scheduler_thread = threading.Thread(target=cls._run_backup_scheduler, daemon=True)
        cls._scheduler_thread.start()
        logger.info("Automatic backup scheduler started")
    
    @classmethod
    def stop_automatic_backup_scheduler(cls):
        """Stop the automatic backup scheduler."""
        if not cls._scheduler_running:
            logger.info("Backup scheduler is not running")
            return
        
        cls._scheduler_running = False
        if cls._scheduler_thread:
            cls._scheduler_thread.join(timeout=5)
        logger.info("Automatic backup scheduler stopped")
    
    @classmethod
    def _run_backup_scheduler(cls):
        """Run the automatic backup scheduler loop."""
        logger.info("Backup scheduler loop started")

        while cls._scheduler_running:
            try:
                # Load settings to check if automatic backups are enabled
                from app.services.data_service import DataService
                settings = DataService.load_settings()

                automatic_backup_enabled = settings.get('automatic_backup_enabled', False)
                backup_interval_hours = settings.get('automatic_backup_interval_hours', 24)

                if automatic_backup_enabled:
                    logger.info(f"Automatic backup is enabled, creating backup every {backup_interval_hours} hours")

                    # Create full backup including PPM, OCM, and Training data
                    result = cls.create_full_backup()
                    if result['success']:
                        logger.info(f"Automatic full backup created: {result['filename']} ({result['size_mb']} MB)")

                        # Log audit event for successful backup
                        AuditService.log_event(
                            event_type=AuditService.EVENT_TYPES['BACKUP_CREATED'],
                            performed_by="System",
                            description=f"Automatic full backup created successfully (interval: {backup_interval_hours}h)",
                            status=AuditService.STATUS_SUCCESS,
                            details={
                                "backup_type": "full",
                                "filename": result['filename'],
                                "size_mb": result['size_mb'],
                                "interval_hours": backup_interval_hours,
                                "automatic": True
                            }
                        )
                    else:
                        logger.error(f"Automatic full backup failed: {result['message']}")

                    # Clean up old backups (keep backups for 30 days)
                    cleanup_result = cls.cleanup_old_backups(max_age_days=30)
                    if cleanup_result['success'] and cleanup_result['deleted_count'] > 0:
                        logger.info(f"Cleaned up {cleanup_result['deleted_count']} old backups")

                else:
                    logger.debug("Automatic backup is disabled")

                # Sleep for the specified interval
                sleep_seconds = backup_interval_hours * 3600
                logger.info(f"Backup scheduler sleeping for {backup_interval_hours} hours ({sleep_seconds} seconds)")

                # Use smaller sleep intervals to allow for graceful shutdown
                for _ in range(int(sleep_seconds / 60)):  # Sleep in 1-minute intervals
                    if not cls._scheduler_running:
                        break
                    time.sleep(60)  # Fixed: Use time.sleep instead of asyncio.sleep

            except Exception as e:
                logger.error(f"Error in backup scheduler loop: {str(e)}")
                # Sleep for 1 hour on error to avoid rapid retries
                for _ in range(60):
                    if not cls._scheduler_running:
                        break
                    time.sleep(60)  # Fixed: Use time.sleep instead of asyncio.sleep

        logger.info("Backup scheduler loop ended")