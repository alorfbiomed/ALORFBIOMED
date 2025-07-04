"""
Log Cleanup Utility for Hospital Equipment Maintenance Management System

This utility provides functions to clean up old log files and manage log retention.
"""

import os
import glob
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from app.config.logging_config import logging_config
from app.services.logging_service import LoggingService


logger = logging.getLogger(__name__)


class LogCleanup:
    """Utility class for log file cleanup and maintenance"""
    
    @staticmethod
    def cleanup_old_logs(retention_days: int = None) -> dict:
        """
        Clean up log files older than retention period
        
        Args:
            retention_days: Number of days to retain logs (default from config)
            
        Returns:
            Dictionary with cleanup results
        """
        if retention_days is None:
            retention_days = logging_config.get_log_retention_days()
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        log_dir = logging_config.LOG_DIR
        
        results = {
            'deleted_files': [],
            'errors': [],
            'total_size_freed': 0,
            'retention_days': retention_days,
            'cutoff_date': cutoff_date.isoformat()
        }
        
        try:
            # Ensure log directory exists
            log_dir.mkdir(exist_ok=True)
            
            # Find all log files (including rotated ones)
            log_patterns = [
                '*.log.*',  # Rotated logs (app.log.1, error.log.2, etc.)
                '*.log.*.gz',  # Compressed rotated logs
                '*.log.*.zip'  # Compressed rotated logs
            ]
            
            for pattern in log_patterns:
                log_files = glob.glob(str(log_dir / pattern))
                
                for log_file_path in log_files:
                    try:
                        log_file = Path(log_file_path)
                        
                        # Check file modification time
                        file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                        
                        if file_mtime < cutoff_date:
                            file_size = log_file.stat().st_size
                            log_file.unlink()  # Delete the file
                            
                            results['deleted_files'].append({
                                'file': str(log_file),
                                'size': file_size,
                                'modified': file_mtime.isoformat()
                            })
                            results['total_size_freed'] += file_size
                            
                            logger.info(f"Deleted old log file: {log_file}")
                    
                    except Exception as e:
                        error_msg = f"Error deleting log file {log_file_path}: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
            
            # Log cleanup summary
            LoggingService.log_info(
                f"Log cleanup completed: {len(results['deleted_files'])} files deleted",
                context={
                    'operation': 'log_cleanup',
                    'retention_days': retention_days,
                    'files_deleted': len(results['deleted_files']),
                    'size_freed_bytes': results['total_size_freed'],
                    'size_freed_mb': round(results['total_size_freed'] / (1024 * 1024), 2),
                    'errors': len(results['errors'])
                },
                logger_name='system'
            )
            
        except Exception as e:
            error_msg = f"Error during log cleanup: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
            
            LoggingService.log_error(
                "Log cleanup failed",
                exception=e,
                context={'operation': 'log_cleanup', 'retention_days': retention_days},
                logger_name='system'
            )
        
        return results
    
    @staticmethod
    def get_log_file_info() -> dict:
        """
        Get information about current log files
        
        Returns:
            Dictionary with log file information
        """
        log_dir = logging_config.LOG_DIR
        info = {
            'log_directory': str(log_dir),
            'files': [],
            'total_size': 0,
            'oldest_file': None,
            'newest_file': None
        }
        
        try:
            if not log_dir.exists():
                return info
            
            # Get all log files
            log_files = list(log_dir.glob('*.log*'))
            
            oldest_time = None
            newest_time = None
            
            for log_file in log_files:
                try:
                    stat = log_file.stat()
                    file_info = {
                        'name': log_file.name,
                        'path': str(log_file),
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    }
                    
                    info['files'].append(file_info)
                    info['total_size'] += stat.st_size
                    
                    # Track oldest and newest files
                    file_mtime = datetime.fromtimestamp(stat.st_mtime)
                    if oldest_time is None or file_mtime < oldest_time:
                        oldest_time = file_mtime
                        info['oldest_file'] = file_info
                    
                    if newest_time is None or file_mtime > newest_time:
                        newest_time = file_mtime
                        info['newest_file'] = file_info
                
                except Exception as e:
                    logger.warning(f"Error getting info for log file {log_file}: {str(e)}")
            
            # Sort files by modification time (newest first)
            info['files'].sort(key=lambda x: x['modified'], reverse=True)
            info['total_size_mb'] = round(info['total_size'] / (1024 * 1024), 2)
            
        except Exception as e:
            logger.error(f"Error getting log file info: {str(e)}", exc_info=True)
        
        return info
    
    @staticmethod
    def compress_old_logs(days_threshold: int = 7) -> dict:
        """
        Compress log files older than threshold
        
        Args:
            days_threshold: Compress files older than this many days
            
        Returns:
            Dictionary with compression results
        """
        import gzip
        import shutil
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        log_dir = logging_config.LOG_DIR
        
        results = {
            'compressed_files': [],
            'errors': [],
            'space_saved': 0,
            'threshold_days': days_threshold
        }
        
        try:
            # Find uncompressed log files
            log_files = list(log_dir.glob('*.log.*'))
            # Exclude already compressed files
            log_files = [f for f in log_files if not f.name.endswith(('.gz', '.zip'))]
            
            for log_file in log_files:
                try:
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    if file_mtime < cutoff_date:
                        original_size = log_file.stat().st_size
                        compressed_path = log_file.with_suffix(log_file.suffix + '.gz')
                        
                        # Compress the file
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        compressed_size = compressed_path.stat().st_size
                        space_saved = original_size - compressed_size
                        
                        # Remove original file
                        log_file.unlink()
                        
                        results['compressed_files'].append({
                            'original_file': str(log_file),
                            'compressed_file': str(compressed_path),
                            'original_size': original_size,
                            'compressed_size': compressed_size,
                            'space_saved': space_saved,
                            'compression_ratio': round((space_saved / original_size) * 100, 1)
                        })
                        results['space_saved'] += space_saved
                        
                        logger.info(f"Compressed log file: {log_file} -> {compressed_path}")
                
                except Exception as e:
                    error_msg = f"Error compressing log file {log_file}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
        
        except Exception as e:
            error_msg = f"Error during log compression: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        
        return results


# Convenience function for scheduled cleanup
def scheduled_log_cleanup():
    """Function to be called by scheduler for regular log cleanup"""
    try:
        cleanup = LogCleanup()
        results = cleanup.cleanup_old_logs()
        
        if results['deleted_files']:
            logger.info(f"Scheduled log cleanup: deleted {len(results['deleted_files'])} files, "
                       f"freed {results['total_size_freed'] / (1024*1024):.2f} MB")
        
        return results
    except Exception as e:
        logger.error(f"Scheduled log cleanup failed: {str(e)}", exc_info=True)
        return {'error': str(e)}
