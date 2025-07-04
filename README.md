# ALORF BIOMED System

Hospital Equipment Maintenance Management System - A comprehensive Flask application for managing PPM (Preventive Maintenance Program), OCM (Operational and Clinical Maintenance) equipment, and training records with mobile-optimized responsive design.

## 🏥 Overview

The ALORF BIOMED System is a professional healthcare equipment management platform designed for biomedical engineering departments in hospitals and medical facilities. It provides comprehensive tracking, maintenance scheduling, and documentation for medical equipment while offering a modern, mobile-first user experience.

## ✨ Key Features

### 📱 Mobile-First Design
- **Responsive Layout**: Fully optimized for mobile devices with CSS Grid and Flexbox
- **Touch-Friendly Navigation**: Hamburger menu with backdrop blur effects
- **Adaptive Tables**: Equipment tables automatically convert to cards on mobile (≤768px)
- **Touch Gestures**: Swipe actions and pull-to-refresh functionality
- **Native Mobile Elements**: iOS/Android optimized date pickers and form inputs
- **Ripple Effects**: Modern button feedback for enhanced user interaction

### 🔧 Equipment Management
- **PPM Equipment**: Preventive maintenance program tracking
- **OCM Equipment**: Operational and clinical maintenance management
- **Equipment History**: Comprehensive maintenance and service records
- **Barcode Generation**: QR codes for easy equipment identification
- **Department Organization**: Equipment categorized by hospital departments

### 👥 User Management & Security
- **Role-Based Access Control**: Admin, Editor, and Viewer roles
- **Permission System**: Granular permissions for different operations
- **Secure Authentication**: Password hashing and session management
- **Audit Logging**: Complete activity tracking for compliance

### 📊 Dashboard & Analytics
- **Overview Dashboard**: Equipment status and maintenance summaries
- **Responsive Cards**: Mobile-optimized dashboard layout
- **Timeline View**: Maintenance history visualization
- **Quick Actions**: Fast access to common tasks

### 📋 Training Management
- **Staff Training Records**: Track training certifications and renewals
- **Training History**: Comprehensive staff development tracking
- **Certification Management**: Monitor training compliance

### 🔄 Data Management
- **Import/Export**: CSV templates for bulk data operations
- **Automatic Backups**: Scheduled system backups
- **Data Validation**: Comprehensive input validation and sanitization
- **Email Notifications**: Automated maintenance reminders

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry (recommended) or pip (Python package manager)

### Installation

#### Option 1: Using Poetry (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/lolotam/ALORFBIOMED.git
   cd ALORFBIOMED
   ```

2. **Install Poetry** (if not already installed)
   ```bash
   # Windows (PowerShell)
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

   # Linux/Mac
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Activate the virtual environment**
   ```bash
   poetry shell
   ```

5. **Run the application**
   ```bash
   poetry run start-app
   # or
   python app/main.py
   ```

#### Option 2: Using pip

1. **Clone the repository**
   ```bash
   git clone https://github.com/lolotam/ALORFBIOMED.git
   cd ALORFBIOMED
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app/main.py
   ```

### Access the Application
- Open your browser and navigate to `http://localhost:5001`
- Login with test credentials: **Username:** `testuser` **Password:** `test123`

## 📱 Mobile Features

### Responsive Design
- **Breakpoints**: Optimized for mobile (≤768px), tablet (769px-1024px), and desktop (>1024px)
- **Touch Targets**: Minimum 44px touch targets for accessibility
- **Viewport Optimization**: Prevents zoom on input focus for iOS devices

### Mobile Navigation
- **Hamburger Menu**: Collapsible navigation with smooth animations
- **Backdrop Blur**: Modern iOS-style backdrop effects
- **Touch-Friendly**: Large touch areas and intuitive gestures

### Equipment Lists
- **Card Conversion**: Tables automatically become cards on mobile
- **Swipe Actions**: Touch gestures for equipment operations
- **Pull-to-Refresh**: Native mobile refresh experience

### Forms & Inputs
- **Mobile Keyboards**: Optimized input types for mobile keyboards
- **Date Pickers**: Native date/time pickers for mobile devices
- **Form Validation**: Real-time validation with mobile-friendly messages

## 🏗️ Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLite**: Lightweight database for development
- **Werkzeug**: WSGI utilities and security
- **APScheduler**: Background task scheduling
- **Mailjet**: Email service integration

### Frontend
- **Bootstrap 5**: Responsive CSS framework
- **Vanilla JavaScript**: Mobile enhancement scripts
- **CSS Grid & Flexbox**: Modern layout techniques
- **Progressive Enhancement**: Works without JavaScript

### Mobile Enhancements
- **Touch Events**: Native touch gesture support
- **Intersection Observer**: Performance-optimized scroll detection
- **CSS Variables**: Dynamic theming and responsive design
- **Modern CSS**: backdrop-filter, grid, flexbox, and animations

## 📁 Project Structure

```
ALORFBIOMED/
├── app/
│   ├── models/          # Data models
│   ├── routes/          # URL routes and views
│   ├── services/        # Business logic
│   ├── static/          # CSS, JS, and assets
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   └── mobile.css    # Mobile optimizations
│   │   └── js/
│   │       ├── main.js
│   │       └── mobile.js     # Mobile enhancements
│   ├── templates/       # Jinja2 templates
│   └── utils/          # Utility functions
├── data/               # Application data
├── migrations/         # Database migrations
└── tests/             # Test suite
```

## 🛡️ Security Features

- **Input Validation**: Comprehensive sanitization of all user inputs
- **Password Hashing**: Secure bcrypt password hashing
- **Session Management**: Secure session handling
- **CSRF Protection**: Cross-site request forgery prevention
- **Audit Logging**: Complete activity audit trail

## 📧 Email Configuration

The system supports automated email notifications:

1. Configure email settings in the admin panel
2. Set up Mailjet API credentials
3. Enable automatic maintenance reminders
4. Customize notification schedules

## � Authentication System

### Default User Accounts

The system comes with pre-configured test accounts:

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| `testuser` | `test123` | Admin | Full system access |
| `admin` | *encrypted* | Admin | Full system access |
| `editor1` | `editor` | Editor | Equipment management |
| `viewer1` | `viewer` | Viewer | Read-only access |

### User Roles & Permissions

#### Admin Role
- Full system access including user management
- Equipment management (PPM, OCM, Training)
- System configuration and settings
- Data import/export operations
- Audit log access

#### Editor Role
- Equipment management (create, read, update, delete)
- Training record management
- Data import/export (limited)
- Cannot manage users or system settings

#### Viewer Role
- Read-only access to equipment data
- View training records
- Generate reports
- Cannot modify any data

### Password Security
- Passwords are hashed using Werkzeug's secure hashing (scrypt/PBKDF2)
- Session-based authentication with Flask-Login
- Automatic session timeout for security

## �🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:
```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Email Service Configuration
MAILJET_API_KEY=your-mailjet-api-key
MAILJET_SECRET_KEY=your-mailjet-secret-key

# Scheduler Configuration
SCHEDULER_ENABLED=true

# Database Configuration (optional)
DATABASE_URL=sqlite:///data/equipment.db
```

### Application Settings File
The system uses `data/settings.json` for configuration:

```json
{
  "email_sender": "your-email@domain.com",
  "email_recipients": "recipient1@domain.com, recipient2@domain.com",
  "cc_emails": "cc1@domain.com, cc2@domain.com",
  "scheduler_interval_hours": 24,
  "enable_automatic_reminders": true,
  "automatic_backup_enabled": true,
  "automatic_backup_interval_hours": 8,
  "use_daily_send_time": true,
  "email_send_time": "07:35",
  "users": [
    {
      "username": "testuser",
      "password": "scrypt:32768:8:1$...",
      "role": "Admin"
    }
  ],
  "roles": {
    "Admin": {
      "permissions": ["all_permissions"]
    }
  }
}
```

### Email Configuration
1. **Mailjet Setup**: Register at [Mailjet](https://www.mailjet.com/) and get API credentials
2. **SMTP Fallback**: Configure SMTP settings for backup email delivery
3. **Notification Schedule**: Set daily email send times and intervals
4. **Recipients**: Configure primary and CC email addresses

### Data Storage
- **Equipment Data**: Stored in JSON files (`data/ppm.json`, `data/ocm.json`, `data/training.json`)
- **User Data**: Stored in `data/settings.json`
- **Logs**: Application logs in `logs/` directory
- **Backups**: Automatic backups in `backups/` directory

## 🧪 Testing

Run the test suite:
```bash
# Using Poetry
poetry run pytest tests/

# Using pip
python -m pytest tests/
```

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### 1. Authentication Problems

**Issue**: "Error loading PPM/OCM equipment data" or login failures
**Solutions**:
- Verify test user credentials: `testuser` / `test123`
- Check if Flask server is running properly
- Restart the Flask application: `python app/main.py`
- Clear browser cache and cookies
- Check `data/settings.json` for user configuration

#### 2. Email Scheduler Not Working

**Issue**: Scheduled emails not being sent
**Solutions**:
- Check email configuration in `data/settings.json`
- Verify Mailjet API credentials in environment variables
- Check scheduler logs in `logs/` directory
- Ensure `SCHEDULER_ENABLED=true` in environment
- Verify timezone settings and email send time format

#### 3. CSV Import Failures

**Issue**: "Encoding error" or "Invalid CSV format"
**Solutions**:
- Ensure CSV files are UTF-8 encoded
- Check column headers match expected format
- Use provided CSV templates for import
- Verify file permissions and accessibility

#### 4. Equipment Edit Errors

**Issue**: "Equipment with serial X not found" when editing
**Solutions**:
- Check for special characters in serial numbers
- Verify URL encoding for serial numbers with spaces/hyphens
- Restart Flask server to clear any caching issues
- Check equipment exists in the correct data file

#### 5. Mobile Display Issues

**Issue**: Poor mobile experience or layout problems
**Solutions**:
- Clear browser cache
- Ensure viewport meta tag is present
- Check CSS media queries are loading
- Test on different mobile browsers

#### 6. Performance Issues

**Issue**: Slow loading or timeouts
**Solutions**:
- Check data file sizes in `data/` directory
- Optimize large equipment lists with pagination
- Clear old log files from `logs/` directory
- Restart the Flask application

#### 7. Permission Denied Errors

**Issue**: Access denied to certain features
**Solutions**:
- Verify user role and permissions in `data/settings.json`
- Login with appropriate user role (Admin for full access)
- Check permission decorators in route handlers
- Ensure session is valid and not expired

### Log Files and Debugging

#### Application Logs
- **Location**: `logs/app.log`
- **Content**: Application errors, warnings, and info messages
- **Rotation**: Automatic log rotation to prevent large files

#### Error Logs
- **Location**: `logs/error.log`
- **Content**: Critical errors and exceptions
- **Format**: JSON structured logging with timestamps

#### Debug Mode
Enable debug mode for detailed error information:
```bash
# Set environment variable
export FLASK_ENV=development

# Or run with debug flag
python app/main.py --debug
```

### System Requirements Check

#### Python Version
```bash
python --version  # Should be 3.11+
```

#### Dependencies Check
```bash
# Using Poetry
poetry check

# Using pip
pip check
```

#### Port Availability
```bash
# Check if port 5001 is available
netstat -an | findstr :5001  # Windows
netstat -an | grep :5001     # Linux/Mac
```

### Data Recovery

#### Backup Restoration
1. Locate backup files in `backups/` directory
2. Copy backup files to `data/` directory
3. Restart the application
4. Verify data integrity

#### Manual Data Recovery
1. Check JSON file syntax in `data/` directory
2. Validate JSON format using online validators
3. Restore from version control if available
4. Contact support for data recovery assistance

## 📚 API Documentation

The application provides comprehensive REST API endpoints:

### Equipment Management APIs

#### PPM Equipment
- `GET /api/equipment/ppm` - List all PPM equipment
- `GET /api/equipment/ppm/{serial}` - Get specific PPM equipment
- `POST /api/equipment/ppm` - Create new PPM equipment
- `PUT /api/equipment/ppm/{serial}` - Update PPM equipment
- `DELETE /api/equipment/ppm/{serial}` - Delete PPM equipment

#### OCM Equipment
- `GET /api/equipment/ocm` - List all OCM equipment
- `GET /api/equipment/ocm/{serial}` - Get specific OCM equipment
- `POST /api/equipment/ocm` - Create new OCM equipment
- `PUT /api/equipment/ocm/{serial}` - Update OCM equipment
- `DELETE /api/equipment/ocm/{serial}` - Delete OCM equipment

#### Training Records
- `GET /api/equipment/training` - List all training records
- `GET /api/equipment/training/{id}` - Get specific training record
- `POST /api/equipment/training` - Create new training record
- `PUT /api/equipment/training/{id}` - Update training record
- `DELETE /api/equipment/training/{id}` - Delete training record

### Data Import/Export APIs
- `POST /api/import/{data_type}` - Import CSV data (PPM, OCM, Training)
- `GET /api/export/{data_type}` - Export data as CSV
- `POST /api/backup` - Create system backup
- `GET /api/backup/list` - List available backups

### Authentication APIs
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/user` - Get current user info

### API Response Format
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏥 About ALORF BIOMED

Developed for healthcare facilities to streamline biomedical equipment management, ensuring compliance with medical device regulations and maintenance standards.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

---

**Built with ❤️ for healthcare professionals**


