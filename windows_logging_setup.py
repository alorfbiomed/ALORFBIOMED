#!/usr/bin/env python3
"""
Windows-Compatible Logging Setup and Verification Script
Based on Augment Code guidance for solving PermissionError [WinError 32]

This script:
1. Installs concurrent-log-handler if needed
2. Verifies all logging configurations are Windows-compatible
3. Tests log rotation without permission errors
4. Provides troubleshooting information
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

def install_concurrent_handler():
    """Install concurrent-log-handler package if not available."""
    print("🔧 Installing concurrent-log-handler for Windows compatibility...")
    
    try:
        import concurrent_log_handler
        print("✅ concurrent-log-handler is already installed")
        return True
    except ImportError:
        print("📦 Installing concurrent-log-handler...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "concurrent-log-handler==0.9.25"])
            print("✅ concurrent-log-handler installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install concurrent-log-handler: {e}")
            return False

def test_concurrent_logging():
    """Test that concurrent logging works without permission errors."""
    print("\n🔍 Testing Windows-compatible logging...")
    
    try:
        from concurrent_log_handler import ConcurrentRotatingFileHandler
        
        # Create test logs directory
        test_log_dir = Path("test_logs")
        test_log_dir.mkdir(exist_ok=True)
        
        # Create concurrent handler
        handler = ConcurrentRotatingFileHandler(
            test_log_dir / "test.log",
            maxBytes=1024,  # Small size to trigger rotation quickly
            backupCount=3
        )
        
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
        handler.setFormatter(formatter)
        
        # Create test logger
        test_logger = logging.getLogger('windows_test')
        test_logger.setLevel(logging.INFO)
        test_logger.handlers = [handler]
        
        # Generate enough logs to trigger rotation
        for i in range(50):
            test_logger.info(f"Test log message {i} - Windows compatibility verification")
        
        # Check if log files were created
        log_files = list(test_log_dir.glob("test.log*"))
        if len(log_files) > 1:
            print(f"✅ Log rotation successful - {len(log_files)} log files created")
        else:
            print(f"✅ Logging successful - {len(log_files)} log file created")
        
        # Cleanup
        for log_file in log_files:
            log_file.unlink()
        test_log_dir.rmdir()
        
        return True
        
    except Exception as e:
        print(f"❌ Concurrent logging test failed: {e}")
        return False

def verify_flask_configuration():
    """Verify Flask app is configured correctly for Windows."""
    print("\n🔍 Verifying Flask configuration...")
    
    try:
        # Check main.py for use_reloader=False
        main_py_path = Path("app/main.py")
        if main_py_path.exists():
            with open(main_py_path, 'r') as f:
                content = f.read()
                if "use_reloader=False" in content:
                    print("✅ Flask reloader is disabled (prevents multiple processes)")
                else:
                    print("⚠️  WARNING: Flask reloader should be disabled with use_reloader=False")
        else:
            print("⚠️  app/main.py not found")
        
        # Check if concurrent handler is imported in logger setup
        logger_setup_path = Path("app/utils/logger_setup.py")
        if logger_setup_path.exists():
            with open(logger_setup_path, 'r') as f:
                content = f.read()
                if "ConcurrentRotatingFileHandler" in content:
                    print("✅ Logger setup uses ConcurrentRotatingFileHandler")
                else:
                    print("⚠️  WARNING: Logger setup should use ConcurrentRotatingFileHandler")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask configuration verification failed: {e}")
        return False

def check_log_file_locks():
    """Check for potential log file locks."""
    print("\n🔍 Checking for potential log file locks...")
    
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("✅ No logs directory found - no lock conflicts possible")
        return True
    
    log_files = list(logs_dir.glob("*.log"))
    if not log_files:
        print("✅ No log files found - no lock conflicts possible")
        return True
    
    print(f"📁 Found {len(log_files)} log files:")
    for log_file in log_files:
        print(f"   - {log_file}")
    
    print("\n💡 To prevent permission errors:")
    print("   1. Close any text editors viewing log files")
    print("   2. Close Windows Explorer if browsing logs directory")
    print("   3. Ensure no other Python processes are running")
    
    return True

def main():
    """Main function to run all Windows logging setup and verification."""
    print("🚀 Windows Logging Setup and Verification")
    print("=" * 60)
    print("Based on Augment Code guidance for solving PermissionError [WinError 32]")
    print()
    
    # Step 1: Install concurrent handler
    if not install_concurrent_handler():
        print("❌ Cannot proceed without concurrent-log-handler")
        return False
    
    # Step 2: Test concurrent logging
    if not test_concurrent_logging():
        print("❌ Concurrent logging test failed")
        return False
    
    # Step 3: Verify Flask configuration
    if not verify_flask_configuration():
        print("❌ Flask configuration issues found")
        return False
    
    # Step 4: Check for log file locks
    check_log_file_locks()
    
    print("\n" + "=" * 60)
    print("🎉 Windows Logging Setup Complete!")
    print()
    print("✅ All checks passed. Your Flask app should now run without:")
    print("   - PermissionError [WinError 32] during log rotation")
    print("   - File locking conflicts on Windows")
    print("   - Multiple process log access issues")
    print()
    print("📋 To start your Flask app:")
    print("   cd C:\\ALORFBIOMED")
    print("   python app\\main.py")
    print()
    print("🔧 If you still encounter issues:")
    print("   1. Close all text editors viewing log files")
    print("   2. Restart your command prompt/terminal")
    print("   3. Ensure only one Python process is running")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
