@echo off
call venv\Scripts\activate.bat
set FLASK_APP=app:create_app
set FLASK_ENV=development
set FLASK_DEBUG=1
python app\main.py
pause
