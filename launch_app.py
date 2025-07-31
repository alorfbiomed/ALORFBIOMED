#!/usr/bin/env python3
"""
Simple launcher script for the Hospital Equipment Maintenance Management System.
This script sets up the Python path correctly and launches the application.
"""

import sys
import os

# Add the current directory to Python path so 'app' module can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Now import and run the main application
try:
    from app.main import main
    print("🏥 Starting Hospital Equipment Maintenance Management System...")
    print("📍 Application directory:", current_dir)
    main()
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("📂 Current directory:", current_dir)
    print("🐍 Python path:", sys.path)
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting application: {e}")
    sys.exit(1)
