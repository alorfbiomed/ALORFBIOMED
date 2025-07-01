# app/routes/views.py

"""
Frontend routes for rendering HTML pages.
"""
import logging
import io
import json
import os
from pathlib import Path
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app, send_file
from flask_login import current_user, login_required
import tempfile
import zipfile
from app.services.data_service import DataService
from app.services import training_service
from app.services.audit_service import AuditService
from app.services.email_service import EmailService
from app.services.barcode_service import BarcodeService
from app.services.backup_service import BackupService
from app.services.import_export import ImportExportService
from app.services.history_service import HistoryService
from app.models.history import HistoryNoteCreate, HistoryNoteUpdate
from app.constants import (
    DEPARTMENTS, TRAINING_MODULES, QUARTER_STATUS_OPTIONS, GENERAL_STATUS_OPTIONS,
    DEVICES_BY_DEPARTMENT, ALL_DEVICES, TRAINERS
)
from werkzeug.security import generate_password_hash, check_password_hash
import functools # For wraps decorator

views_bp = Blueprint('views', __name__)
logger = logging.getLogger('app')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'csv'}
SETTINGS_FILE = Path("data/settings.json")

def permission_required(required_permissions):
    """
    Decorator to check if a user has the required permissions to access a view.
    `required_permissions` is a list of permission names (strings).
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('You need to be logged in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            # Allow if user has ANY of the required permissions
            has_any_permission = False
            for perm in required_permissions:
                if current_user.has_permission(perm):
                    has_any_permission = True
                    break

            if not has_any_permission:
                flash(f'You do not have permission to access this page. Required: {", ".join(required_permissions)}.', 'danger')
                return redirect(url_for('views.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Login route has been moved to auth.py to consolidate authentication logic

@views_bp.route('/')
@permission_required(['dashboard_view'])
def index():
    """Display the dashboard with maintenance statistics."""
    ppm_data = DataService.get_all_entries(data_type='ppm')
    if isinstance(ppm_data, dict):
        ppm_data = [ppm_data]
    for item in ppm_data:
        item['data_type'] = 'ppm'

    ocm_data = DataService.get_all_entries(data_type='ocm')
    if isinstance(ocm_data, dict):
        ocm_data = [ocm_data]
    for item in ocm_data:
        item['data_type'] = 'ocm'
    
    all_equipment = ppm_data + ocm_data
    current_date_str = datetime.now().strftime("%A, %d %B %Y - %I:%M:%S %p")
    today = datetime.now().date()
    
    total_machines = len(all_equipment)
    overdue_count = upcoming_count = maintained_count = 0
    upcoming_7_days = upcoming_14_days = upcoming_21_days = 0
    upcoming_30_days = upcoming_60_days = upcoming_90_days = 0
    
    ppm_machine_count = len(ppm_data)
    ocm_machine_count = len(ocm_data)

    for item in all_equipment:
        if item['data_type'] == 'ppm':
            q2_info = item.get('PPM_Q_II', {})
            if isinstance(q2_info, dict):
                q2_date = q2_info.get('quarter_date')
                q2_engineer = q2_info.get('engineer', '')
                item['display_next_maintenance'] = q2_date if q2_date else 'N/A'
                
                if q2_date:
                    try:
                        q2_date_obj = EmailService.parse_date_flexible(q2_date).date()
                        if q2_date_obj < today:
                            q2_status = 'maintained' if q2_engineer and (q2_engineer.strip() if q2_engineer else '') else 'overdue'
                        elif q2_date_obj == today:
                            q2_status = 'maintained'
                        else:
                            q2_status = 'upcoming'
                        item['Status'] = q2_status.capitalize()
                    except ValueError:
                        item['display_next_maintenance'] = 'N/A'
            else:
                item['display_next_maintenance'] = 'N/A'
        else:
            item['display_next_maintenance'] = item.get('Next_Maintenance', 'N/A')
        
        status = item.get('Status', 'N/A').lower()
        if status == 'overdue':
            overdue_count += 1
            item['status_class'] = 'danger'
        elif status == 'upcoming':
            upcoming_count += 1
            item['status_class'] = 'warning'
            
            if item['data_type'] == 'ocm':
                next_maintenance = item.get('Next_Maintenance')
                if next_maintenance and next_maintenance != 'N/A':
                    try:
                        next_date = EmailService.parse_date_flexible(next_maintenance).date()
                        days_until = (next_date - today).days
                        if days_until <= 7: upcoming_7_days += 1
                        if days_until <= 14: upcoming_14_days += 1
                        if days_until <= 21: upcoming_21_days += 1
                        if days_until <= 30: upcoming_30_days += 1
                        if days_until <= 60: upcoming_60_days += 1
                        if days_until <= 90: upcoming_90_days += 1
                    except ValueError:
                        pass
            elif item['data_type'] == 'ppm':
                quarter_keys = ['PPM_Q_I', 'PPM_Q_II', 'PPM_Q_III', 'PPM_Q_IV']
                for q_key in quarter_keys:
                    quarter_info = item.get(q_key, {})
                    if isinstance(quarter_info, dict):
                        quarter_date_str = quarter_info.get('quarter_date')
                        if quarter_date_str:
                            try:
                                quarter_date = EmailService.parse_date_flexible(quarter_date_str).date()
                                if quarter_date >= today:
                                    days_until = (quarter_date - today).days
                                    if days_until <= 7: upcoming_7_days += 1
                                    if days_until <= 14: upcoming_14_days += 1
                                    if days_until <= 21: upcoming_21_days += 1
                                    if days_until <= 30: upcoming_30_days += 1
                                    if days_until <= 60: upcoming_60_days += 1
                                    if days_until <= 90: upcoming_90_days += 1
                            except ValueError:
                                pass
        elif status == 'maintained':
            maintained_count += 1
            item['status_class'] = 'success'
        else:
            item['status_class'] = 'secondary'

    return render_template('index.html',
                           current_date=current_date_str,
                           total_machines=total_machines,
                           overdue_count=overdue_count,
                           upcoming_count=upcoming_count,
                           maintained_count=maintained_count,
                           ppm_machine_count=ppm_machine_count,
                           ocm_machine_count=ocm_machine_count,
                           upcoming_7_days=upcoming_7_days,
                           upcoming_14_days=upcoming_14_days,
                           upcoming_21_days=upcoming_21_days,
                           upcoming_30_days=upcoming_30_days,
                           upcoming_60_days=upcoming_60_days,
                           upcoming_90_days=upcoming_90_days,
                           equipment=all_equipment)

@views_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    username = current_user.username
    logout_user()
    logger.info(f"User '{username}' logged out successfully.")
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@views_bp.route('/healthz')
def health_check():
    """Simple health check endpoint."""
    logger.info("Health check endpoint /healthz was accessed.")
    return "OK", 200

@views_bp.route('/equipment/<data_type>')
@permission_required(['equipment_ppm_read', 'equipment_ocm_read'])
def list_equipment(data_type):
    """Display list of equipment (either PPM or OCM)."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    if data_type not in ('ppm', 'ocm'):
        flash("Invalid equipment type specified.", "warning")
        return redirect(url_for('views.index'))
    
    try:
        equipment_data = DataService.get_all_entries(data_type)
        if isinstance(equipment_data, dict):
            equipment_data = [equipment_data]
            
        for item in equipment_data:
            status = item.get('Status', 'N/A').lower()
            item['status_class'] = {
                'overdue': 'danger',
                'upcoming': 'warning',
                'maintained': 'success'
            }.get(status, 'secondary')
            
            if data_type == 'ppm':
                today = datetime.now().date()
                quarter_keys = ['PPM_Q_I', 'PPM_Q_II', 'PPM_Q_III', 'PPM_Q_IV']
                for q_key in quarter_keys:
                    quarter_info = item.get(q_key, {})
                    if isinstance(quarter_info, dict):
                        quarter_date_str = quarter_info.get('quarter_date')
                        engineer = quarter_info.get('engineer', '')
                        engineer = engineer.strip() if engineer else ''
                        if quarter_date_str:
                            try:
                                quarter_date = EmailService.parse_date_flexible(quarter_date_str).date()
                                if quarter_date < today:
                                    quarter_status = 'Maintained' if engineer else 'Overdue'
                                    status_class = 'success' if engineer else 'danger'
                                elif quarter_date == today:
                                    quarter_status = 'Maintained'
                                    status_class = 'success'
                                else:
                                    quarter_status = 'Upcoming'
                                    status_class = 'warning'
                                quarter_info['status'] = quarter_status
                                quarter_info['status_class'] = status_class
                            except ValueError:
                                quarter_info['status'] = 'N/A'
                                quarter_info['status_class'] = 'secondary'
                        else:
                            quarter_info['status'] = 'N/A'
                            quarter_info['status_class'] = 'secondary'
        
        return render_template('equipment/list.html', equipment=equipment_data, data_type=data_type)
    except Exception as e:
        logger.error(f"Error loading {data_type} list: {str(e)}")
        flash(f"Error loading {data_type.upper()} equipment data.", "danger")
        return render_template('equipment/list.html', equipment=[], data_type=data_type)

@views_bp.route('/equipment/ppm/add', methods=['GET', 'POST'])
@permission_required(['equipment_ppm_write'])
def add_ppm_equipment():
    """Handle adding new PPM equipment."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        form_data = request.form.to_dict()
        ppm_data = {
            "MODEL": form_data.get("MODEL"),
            "Name": form_data.get("Name") or None,
            "SERIAL": form_data.get("SERIAL"),
            "MANUFACTURER": form_data.get("MANUFACTURER"),
            "Department": form_data.get("Department"),
            "LOG_Number": form_data.get("LOG_Number"),
            "Installation_Date": form_data.get("Installation_Date", "").strip() or None,
            "Warranty_End": form_data.get("Warranty_End", "").strip() or None,
            "PPM_Q_I": {
                "engineer": form_data.get("PPM_Q_I_engineer", "").strip() or None,
                "quarter_date": form_data.get("PPM_Q_I_date", "").strip() or None,
                "status": form_data.get("PPM_Q_I_status", "").strip() or None
            },
            "PPM_Q_II": {
                "engineer": form_data.get("PPM_Q_II_engineer", "").strip() or None,
                "quarter_date": form_data.get("PPM_Q_II_date", "").strip() or None,
                "status": form_data.get("PPM_Q_II_status", "").strip() or None
            },
            "PPM_Q_III": {
                "engineer": form_data.get("PPM_Q_III_engineer", "").strip() or None,
                "quarter_date": form_data.get("PPM_Q_III_date", "").strip() or None,
                "status": form_data.get("PPM_Q_III_status", "").strip() or None
            },
            "PPM_Q_IV": {
                "engineer": form_data.get("PPM_Q_IV_engineer", "").strip() or None,
                "quarter_date": form_data.get("PPM_Q_IV_date", "").strip() or None,
                "status": form_data.get("PPM_Q_IV_status", "").strip() or None
            }
        }
        
        # Calculate the overall Status based on quarter data (matching OCM pattern)
        calculated_status = DataService.calculate_status(ppm_data, 'ppm')
        ppm_data['Status'] = calculated_status
        
        try:
            DataService.add_entry('ppm', ppm_data)
            flash('PPM equipment added successfully!', 'success')
            return redirect(url_for('views.list_equipment', data_type='ppm'))
        except ValueError as e:
            flash(f"Error adding equipment: {str(e)}", 'danger')
            return render_template('equipment/add_ppm.html', data_type='ppm', form_data=form_data, 
                                 departments=DEPARTMENTS, quarter_status_options=QUARTER_STATUS_OPTIONS)
        except Exception as e:
            logger.error(f"Error adding PPM equipment: {str(e)}")
            flash('An unexpected error occurred while adding.', 'danger')
            return render_template('equipment/add_ppm.html', data_type='ppm', form_data=form_data,
                                 departments=DEPARTMENTS, quarter_status_options=QUARTER_STATUS_OPTIONS)
    
    return render_template('equipment/add_ppm.html', data_type='ppm', form_data={},
                         departments=DEPARTMENTS, quarter_status_options=QUARTER_STATUS_OPTIONS)

@views_bp.route('/equipment/ocm/add', methods=['GET', 'POST'])
@permission_required(['equipment_ocm_write'])
def add_ocm_equipment():
    """Handle adding new OCM equipment."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        form_data = request.form.to_dict()
        ocm_data = {
            "Department": form_data.get("Department"),
            "Name": form_data.get("Name"),
            "Model": form_data.get("Model"),
            "Serial": form_data.get("Serial"),
            "Manufacturer": form_data.get("Manufacturer"),
            "Log_Number": form_data.get("Log_Number"),
            "Installation_Date": form_data.get("Installation_Date"),
            "Warranty_End": form_data.get("Warranty_End"),
            "Service_Date": form_data.get("Service_Date"),
            "Engineer": form_data.get("Engineer"),
            "Next_Maintenance": form_data.get("Next_Maintenance"),
            "Status": form_data.get("Status")
        }
        
        try:
            DataService.add_entry('ocm', ocm_data)
            flash('OCM equipment added successfully!', 'success')
            return redirect(url_for('views.list_equipment', data_type='ocm'))
        except ValueError as e:
            flash(f"Error adding equipment: {str(e)}", 'danger')
            return render_template('equipment/add_ocm.html', data_type='ocm', form_data=form_data,
                                 departments=DEPARTMENTS, general_status_options=GENERAL_STATUS_OPTIONS)
        except Exception as e:
            logger.error(f"Error adding OCM equipment: {str(e)}")
            flash('An unexpected error occurred while adding.', 'danger')
            return render_template('equipment/add_ocm.html', data_type='ocm', form_data=form_data,
                                 departments=DEPARTMENTS, general_status_options=GENERAL_STATUS_OPTIONS)
    
    return render_template('equipment/add_ocm.html', data_type='ocm', form_data={},
                         departments=DEPARTMENTS, general_status_options=GENERAL_STATUS_OPTIONS)

@views_bp.route('/equipment/ppm/edit/<SERIAL>', methods=['GET', 'POST'])
@permission_required(['equipment_ppm_write'])
def edit_ppm_equipment(SERIAL):
    """Handle editing existing PPM equipment."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    entry = DataService.get_entry('ppm', SERIAL)
    if not entry:
        flash(f"PPM Equipment with serial '{SERIAL}' not found.", 'warning')
        return redirect(url_for('views.list_equipment', data_type='ppm'))
    
    if request.method == 'POST':
        form_data = request.form.to_dict()
        ppm_data_update = {
            "MODEL": form_data.get("MODEL"),
            "Name": form_data.get("Name") or None,
            "SERIAL": SERIAL,
            "MANUFACTURER": form_data.get("MANUFACTURER"),
            "Department": form_data.get("Department"),
            "LOG_Number": form_data.get("LOG_Number"),
            "Installation_Date": form_data.get("Installation_Date", "").strip() or None,
            "Warranty_End": form_data.get("Warranty_End", "").strip() or None,
            "PPM_Q_I": {
                "engineer": form_data.get("PPM_Q_I_engineer", "").strip() or None,
                "quarter_date": form_data.get("PPM_Q_I_date", "").strip() or None,
                "status": form_data.get("PPM_Q_I_status", "").strip() or None
            },
            "PPM_Q_II": {
                "engineer": form_data.get("PPM_Q_II_engineer", "").strip() or None,
                "quarter_date": form_data.get("PPM_Q_II_date", "").strip() or None,
                "status": form_data.get("PPM_Q_II_status", "").strip() or None
            },
            "PPM_Q_III": {
                "engineer": form_data.get("PPM_Q_III_engineer", "").strip() or None,
                "quarter_date": form_data.get("PPM_Q_III_date", "").strip() or None,
                "status": form_data.get("PPM_Q_III_status", "").strip() or None
            },
            "PPM_Q_IV": {
                "engineer": form_data.get("PPM_Q_IV_engineer", "").strip() or None,
                "quarter_date": form_data.get("PPM_Q_IV_date", "").strip() or None,
                "status": form_data.get("PPM_Q_IV_status", "").strip() or None
            }
        }
        
        calculated_status = DataService.calculate_status(ppm_data_update, 'ppm')
        ppm_data_update['Status'] = calculated_status
        
        try:
            DataService.update_entry('ppm', SERIAL, ppm_data_update)
            flash('PPM equipment updated successfully!', 'success')
            return redirect(url_for('views.list_equipment', data_type='ppm'))
        except ValueError as e:
            flash(f"Error updating equipment: {str(e)}", 'danger')
            return render_template('equipment/edit_ppm.html', data_type='ppm', entry=form_data,
                                 departments=DEPARTMENTS)
        except Exception as e:
            logger.error(f"Error updating PPM equipment {SERIAL}: {str(e)}")
            flash('An unexpected error occurred during update.', 'danger')
            return render_template('equipment/edit_ppm.html', data_type='ppm', entry=form_data,
                                 departments=DEPARTMENTS)
    
    return render_template('equipment/edit_ppm.html', data_type='ppm', entry=entry,
                         departments=DEPARTMENTS)

@views_bp.route('/equipment/ocm/edit/<Serial>', methods=['GET', 'POST'])
@permission_required(['equipment_ocm_write'])
def edit_ocm_equipment(Serial):
    """Handle editing OCM equipment."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    logger.info(f"Received {request.method} request to edit OCM equipment with Serial: {Serial}")
    try:
        entry = DataService.get_entry('ocm', Serial)
        if not entry:
            logger.warning(f"OCM Equipment with Serial '{Serial}' not found")
            flash(f"Equipment with Serial '{Serial}' not found.", 'warning')
            return redirect(url_for('views.list_equipment', data_type='ocm'))
        
        if request.method == 'POST':
            form_data = request.form.to_dict()
            ocm_data = {
                "NO": entry.get("NO"),
                "Department": form_data.get("Department"),
                "Name": form_data.get("Name"),
                "Model": form_data.get("Model"),
                "Serial": Serial,
                "Manufacturer": form_data.get("Manufacturer"),
                "Log_Number": form_data.get("Log_Number"),
                "Installation_Date": form_data.get("Installation_Date"),
                "Warranty_End": form_data.get("Warranty_End"),
                "Service_Date": form_data.get("Service_Date"),
                "Engineer": form_data.get("Engineer"),
                "Next_Maintenance": form_data.get("Next_Maintenance"),
                "Status": form_data.get("Status")
            }
            
            try:
                DataService.update_entry('ocm', Serial, ocm_data)
                flash('OCM equipment updated successfully!', 'success')
                return redirect(url_for('views.list_equipment', data_type='ocm'))
            except ValueError as e:
                logger.error(f"Validation error while updating OCM equipment {Serial}: {str(e)}")
                flash(f"Error updating equipment: {str(e)}", 'danger')
                return render_template('equipment/edit_ocm.html', data_type='ocm', entry=form_data,
                                     departments=DEPARTMENTS)
            except Exception as e:
                logger.error(f"Unexpected error updating OCM equipment {Serial}: {str(e)}")
                flash('An unexpected error occurred while updating.', 'danger')
                return render_template('equipment/edit_ocm.html', data_type='ocm', entry=form_data,
                                     departments=DEPARTMENTS)
        
        return render_template('equipment/edit_ocm.html', data_type='ocm', entry=entry,
                             departments=DEPARTMENTS)
    except Exception as e:
        logger.error(f"Critical error in edit_ocm_equipment for Serial {Serial}: {str(e)}")
        flash('An unexpected error occurred.', 'danger')
        return redirect(url_for('views.list_equipment', data_type='ocm'))

@views_bp.route('/equipment/<data_type>/delete/<path:SERIAL>', methods=['POST'])
@permission_required(['equipment_ppm_delete', 'equipment_ocm_delete'])
def delete_equipment(data_type, SERIAL):
    """Handle deleting existing equipment."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    if data_type not in ('ppm', 'ocm'):
        flash("Invalid equipment type specified.", "warning")
        return redirect(url_for('views.index'))
    
    try:
        entry = DataService.get_entry(data_type, SERIAL)
        if not entry:
            flash(f"{data_type.upper()} equipment '{SERIAL}' not found.", 'warning')
            return redirect(url_for('views.list_equipment', data_type=data_type))
            
        deleted = DataService.delete_entry(data_type, SERIAL)
        if deleted:
            flash(f'{data_type.upper()} equipment \'{SERIAL}\' deleted successfully!', 'success')
        else:
            flash(f'{data_type.upper()} equipment \'{SERIAL}\' not found.', 'warning')
            
    except Exception as e:
        logger.error(f"Error deleting {data_type} equipment {SERIAL}: {str(e)}")
        flash('An unexpected error occurred during deletion.', 'danger')
    
    return redirect(url_for('views.list_equipment', data_type=data_type))

@views_bp.route('/import-export')
@permission_required(['equipment_ppm_import_export', 'equipment_ocm_import_export'])
def import_export_page():
    """Display the import/export page."""
    return render_template('import_export/main.html')

@views_bp.route('/import_equipment', methods=['POST'])
@permission_required(['equipment_ppm_import_export', 'equipment_ocm_import_export'])
def import_equipment():
    """Import equipment data from CSV file."""
    # Note: This route is called by a form POST, permission check is good.
    # No explicit session check was here before, but it's good to add.
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('views.import_export_page'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('views.import_export_page'))
    
    data_type = request.form.get('data_type', '').strip()
    if data_type not in ['ppm', 'ocm', 'training']:
        flash('Invalid data type specified', 'error')
        return redirect(url_for('views.import_export_page'))
    
    if file and allowed_file(file.filename):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                file.save(temp_file.name)
                temp_path = temp_file.name
            
            success, message, stats = ImportExportService.import_from_csv(data_type, temp_path)
            os.unlink(temp_path)
            
            if success:
                flash(f'{data_type.upper()} import successful: {message}', 'success')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({
                        'success': True,
                        'message': message,
                        'redirect_url': '/training' if data_type == 'training' else f'/equipment/{data_type}'
                    })
                return redirect(url_for('views.training_management_page' if data_type == 'training' else 'views.list_equipment', data_type=data_type))
            else:
                flash(f'{data_type.upper()} import failed: {message}', 'error')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return jsonify({'success': False, 'error': message}), 400
                return redirect(url_for('views.import_export_page'))
                
        except Exception as e:
            logger.error(f"Error during {data_type} import: {str(e)}")
            flash(f'Error during {data_type} import: {str(e)}', 'error')
            return redirect(url_for('views.import_export_page'))
    
    flash('Invalid file type', 'error')
    return redirect(url_for('views.import_export_page'))

@views_bp.route('/export/<data_type>')
@permission_required(['equipment_ppm_import_export', 'equipment_ocm_import_export'])
def export_equipment(data_type):
    """Export equipment data to CSV."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    if data_type not in ['ppm', 'ocm', 'training']:
        flash('Invalid data type specified', 'error')
        return redirect(url_for('views.import_export_page'))
    
    try:
        csv_content = DataService.export_data(data_type=data_type)
        mem_file = io.BytesIO()
        mem_file.write(csv_content.encode('utf-8'))
        mem_file.seek(0)
        filename = f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            mem_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error exporting {data_type} data: {str(e)}")
        flash(f"Error exporting {data_type.upper()} data: {str(e)}", 'danger')
        return redirect(url_for('views.import_export_page'))

@views_bp.route('/download/template/<template_type>')
@permission_required(['equipment_ppm_import_export', 'equipment_ocm_import_export', 'training_manage'])
def download_template(template_type):
    """Download template files for data import."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    if template_type not in ['ppm', 'ocm', 'training']:
        flash("Invalid template type specified.", "warning")
        return redirect(url_for('views.import_export_page'))
    
    try:
        template_path = os.path.join(current_app.root_path, "templates", "csv", f"{template_type}_template.csv")
        if not os.path.exists(template_path):
            flash(f"Template file not found: {template_type}_template.csv", 'danger')
            return redirect(url_for('views.import_export_page'))
        
        return send_file(
            template_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"{template_type}_template.csv"
        )
    except Exception as e:
        logger.error(f"Error downloading {template_type} template: {str(e)}")
        flash(f"Error downloading {template_type} template: {str(e)}", 'danger')
        return redirect(url_for('views.import_export_page'))

@views_bp.route('/settings', methods=['GET', 'POST'])
@permission_required(['settings_manage'])
def settings_page():
    """Handle settings page and updates."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    if request.method == 'POST':
        if not request.is_json:
            flash('Invalid request format. Expected JSON.', 'danger')
            return redirect(url_for('views.settings_page'))
        
        data = request.get_json()
        try:
            email_reminder_interval = int(data.get('email_reminder_interval_minutes', 0))
            email_send_time_hour = int(data.get('email_send_time_hour', 7))
            push_notification_interval = int(data.get('push_notification_interval_minutes', 0))
            scheduler_interval_hours = int(data.get('scheduler_interval_hours', 24))
            automatic_backup_interval = int(data.get('automatic_backup_interval_hours', 24))
            
            if email_reminder_interval <= 0:
                flash('Email reminder interval must be positive.', 'danger')
                return redirect(url_for('views.settings_page'))
            if not 0 <= email_send_time_hour <= 23:
                flash('Email send time must be between 0-23 hours.', 'danger')
                return redirect(url_for('views.settings_page'))
            if push_notification_interval <= 0:
                flash('Push notification interval must be positive.', 'danger')
                return redirect(url_for('views.settings_page'))
            if not 1 <= scheduler_interval_hours <= 168:
                flash('Scheduler interval must be between 1-168 hours.', 'danger')
                return redirect(url_for('views.settings_page'))
            if not 1 <= automatic_backup_interval <= 168:
                flash('Backup interval must be between 1-168 hours.', 'danger')
                return redirect(url_for('views.settings_page'))
            
            current_settings = DataService.load_settings()
            current_settings.update({
                'email_notifications_enabled': data.get('email_notifications_enabled', False),
                'email_reminder_interval_minutes': email_reminder_interval,
                'email_send_time_hour': email_send_time_hour,
                'recipient_email': data.get('recipient_email', '').strip(),
                'push_notifications_enabled': data.get('push_notifications_enabled', False),
                'push_notification_interval_minutes': push_notification_interval,
                'reminder_timing': {
                    '60_days_before': data.get('reminder_timing_60_days', False),
                    '14_days_before': data.get('reminder_timing_14_days', False),
                    '1_day_before': data.get('reminder_timing_1_day', False)
                },
                'scheduler_interval_hours': scheduler_interval_hours,
                'enable_automatic_reminders': data.get('enable_automatic_reminders', False),
                'cc_emails': data.get('cc_emails', '').strip(),
                'automatic_backup_enabled': data.get('automatic_backup_enabled', False),
                'automatic_backup_interval_hours': automatic_backup_interval
            })
            
            DataService.save_settings(current_settings)
            flash('Settings saved successfully!', 'success')
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            flash('An error occurred while saving settings.', 'danger')
        
        return redirect(url_for('views.settings_page'))
    
    settings = DataService.load_settings()
    return render_template('settings.html', settings=settings)

@views_bp.route('/settings/reminder', methods=['POST'])
@permission_required(['settings_manage'])
def save_reminder_settings():
    """Handle saving reminder-specific settings."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login')) # This was incorrect for a JSON endpoint
    
    if not request.is_json:
        return jsonify({'error': 'Invalid request format. Expected JSON.'}), 400
    
    data = request.get_json()
    try:
        scheduler_interval_hours = int(data.get('scheduler_interval_hours', 24))
        if not 1 <= scheduler_interval_hours <= 168:
            return jsonify({'error': 'Scheduler interval must be between 1-168 hours.'}), 400
        
        current_settings = DataService.load_settings()
        current_settings.update({
            'reminder_timing': {
                '60_days_before': data.get('reminder_timing_60_days', False),
                '14_days_before': data.get('reminder_timing_14_days', False),
                '1_day_before': data.get('reminder_timing_1_day', False)
            },
            'scheduler_interval_hours': scheduler_interval_hours,
            'enable_automatic_reminders': data.get('enable_automatic_reminders', False)
        })
        
        DataService.save_settings(current_settings)
        return jsonify({'message': 'Reminder settings saved successfully!'}), 200
    except Exception as e:
        logger.error(f"Error saving reminder settings: {str(e)}")
        return jsonify({'error': 'An error occurred while saving reminder settings.'}), 500

@views_bp.route('/settings/email', methods=['POST'])
@permission_required(['settings_manage'])
def save_email_settings():
    """Handle saving email-specific settings."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login')) # Incorrect for JSON endpoint
    
    if not request.is_json:
        return jsonify({'error': 'Invalid request format. Expected JSON.'}), 400
    
    data = request.get_json()
    try:
        current_settings = DataService.load_settings()
        current_settings.update({
            'recipient_email': data.get('recipient_email', '').strip(),
            'cc_emails': data.get('cc_emails', '').strip(),
            'use_daily_send_time': data.get('use_daily_send_time', True),
            'use_legacy_interval': data.get('use_legacy_interval', False),
            'email_send_time': data.get('email_send_time', '09:00')
        })
        
        DataService.save_settings(current_settings)
        return jsonify({'message': 'Email settings saved successfully!'}), 200
    except Exception as e:
        logger.error(f"Error saving email settings: {str(e)}")
        return jsonify({'error': 'An error occurred while saving email settings.'}), 500

@views_bp.route('/settings/test-email', methods=['POST'])
@permission_required(['settings_email_test'])
def send_test_email():
    """Send a test email to verify email configuration."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login')) # Incorrect for JSON endpoint
    
    try:
        settings = DataService.load_settings()
        recipient_email = settings.get('recipient_email', '')
        cc_emails = settings.get('cc_emails', '')
        
        if not recipient_email:
            return jsonify({'error': 'No recipient email configured.'}), 400
        
        subject = "Hospital Equipment System - Test Email"
        body = f"""
        <h2>Test Email from Hospital Equipment System</h2>
        <p>This is a test email to verify your email configuration.</p>
        <p><strong>Sent to:</strong> {recipient_email}</p>
        {f'<p><strong>CC:</strong> {cc_emails}</p>' if cc_emails else ''}
        <p><strong>Sent at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>If you received this email, your email settings are working correctly!</p>
        """
        
        recipients = [recipient_email]
        if cc_emails:
            recipients.extend([email.strip() for email in cc_emails.split(',') if email.strip()])
        
        success = EmailService.send_immediate_email(recipients, subject, body)
        if success:
            logger.info(f"Test email sent successfully to {recipients}")
            return jsonify({'message': 'Test email sent successfully!'}), 200
        else:
            logger.error("Failed to send test email")
            return jsonify({'error': 'Failed to send test email. Please check your email configuration.'}), 500
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return jsonify({'error': f'Error sending test email: {str(e)}'}), 500

@views_bp.route('/training')
@permission_required(['training_manage'])
def training_management_page():
    """Display the training management page."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        all_trainings = training_service.get_all_trainings()
        return render_template('training/list.html',
                             trainings=all_trainings,
                             departments=DEPARTMENTS,
                             training_modules=TRAINING_MODULES,
                             trainers=TRAINERS,
                             devices_by_department=DEVICES_BY_DEPARTMENT,
                             all_devices=ALL_DEVICES)
    except Exception as e:
        logger.error(f"Error loading training management page: {str(e)}")
        flash("Error loading training data.", "danger")
        return render_template('training/list.html',
                             trainings=[],
                             departments=DEPARTMENTS,
                             training_modules=TRAINING_MODULES,
                             trainers=TRAINERS,
                             devices_by_department=DEVICES_BY_DEPARTMENT,
                             all_devices=ALL_DEVICES)

@views_bp.route('/equipment/<data_type>/<serial>/barcode')
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def generate_barcode(data_type, serial):
    """Generate and display barcode for a specific equipment."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        equipment = DataService.get_entry(data_type, serial)
        if not equipment:
            flash(f"Equipment with serial '{serial}' not found.", 'warning')
            return redirect(url_for('views.list_equipment', data_type=data_type))
        
        barcode_base64 = BarcodeService.generate_barcode_base64(serial)
        return render_template('equipment/barcode.html',
                             equipment=equipment,
                             barcode_base64=barcode_base64,
                             data_type=data_type,
                             serial=serial)
    except Exception as e:
        logger.error(f"Error generating barcode for {serial}: {str(e)}")
        flash('Error generating barcode.', 'danger')
        return redirect(url_for('views.list_equipment', data_type=data_type))

@views_bp.route('/equipment/<data_type>/<serial>/barcode/download')
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def download_barcode(data_type, serial):
    """Download barcode image for a specific equipment."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        equipment = DataService.get_entry(data_type, serial)
        if not equipment:
            flash(f"Equipment with serial '{serial}' not found.", 'warning')
            return redirect(url_for('views.list_equipment', data_type=data_type))
        
        equipment_name = equipment.get('Name') or equipment.get('MODEL') or equipment.get('Model')
        department = equipment.get('Department')
        barcode_bytes = BarcodeService.generate_printable_barcode(serial, equipment_name, department)
        
        barcode_file = io.BytesIO(barcode_bytes)
        barcode_file.seek(0)
        
        return send_file(
            barcode_file,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'barcode_{serial}.png'
        )
    except Exception as e:
        logger.error(f"Error downloading barcode for {serial}: {str(e)}")
        flash('Error downloading barcode.', 'danger')
        return redirect(url_for('views.list_equipment', data_type=data_type))

@views_bp.route('/equipment/<data_type>/barcodes/bulk')
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def bulk_barcodes(data_type):
    """Generate bulk barcodes for all equipment of a specific type."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        equipment_list = DataService.get_all_entries(data_type)
        barcodes = []
        for equipment in equipment_list:
            serial = equipment.get('SERIAL') if data_type == 'ppm' else equipment.get('Serial')
            if serial:
                try:
                    barcode_base64 = BarcodeService.generate_barcode_base64(serial)
                    barcodes.append({
                        'equipment': equipment,
                        'barcode_base64': barcode_base64,
                        'serial': serial
                    })
                except Exception as e:
                    logger.error(f"Error generating barcode for {serial}: {str(e)}")
        
        return render_template('equipment/bulk_barcodes.html',
                             barcodes=barcodes,
                             data_type=data_type)
    except Exception as e:
        logger.error(f"Error generating bulk barcodes for {data_type}: {str(e)}")
        flash('Error generating bulk barcodes.', 'danger')
        return redirect(url_for('views.list_equipment', data_type=data_type))

@views_bp.route('/equipment/<data_type>/barcodes/bulk/download')
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def download_bulk_barcodes(data_type):
    """Download all barcodes as a ZIP file."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        equipment_list = DataService.get_all_entries(data_type)
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for equipment in equipment_list:
                serial = equipment.get('SERIAL') if data_type == 'ppm' else equipment.get('Serial')
                if serial:
                    try:
                        equipment_name = equipment.get('Name') or equipment.get('MODEL') or equipment.get('Model')
                        department = equipment.get('Department')
                        barcode_bytes = BarcodeService.generate_printable_barcode(serial, equipment_name, department)
                        zip_file.writestr(f'barcode_{serial}.png', barcode_bytes)
                    except Exception as e:
                        logger.error(f"Error generating barcode for {serial}: {str(e)}")
        
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{data_type}_barcodes.zip'
        )
    except Exception as e:
        logger.error(f"Error downloading bulk barcodes for {data_type}: {str(e)}")
        flash('Error downloading bulk barcodes.', 'danger')
        return redirect(url_for('views.list_equipment', data_type=data_type))

@views_bp.route('/equipment/machine-assignment')
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def machine_assignment():
    """Display the machine assignment page."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    return render_template('equipment/machine_assignment.html',
                         departments=DEPARTMENTS,
                         training_modules=TRAINING_MODULES,
                         devices_by_department=DEVICES_BY_DEPARTMENT,
                         trainers=TRAINERS)

@views_bp.route('/equipment/machine-assignment', methods=['POST'])
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def save_machine_assignment():
    """Save machine assignments."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login')) # Incorrect for JSON endpoint
    
    try:
        data = request.get_json()
        assignments = data.get('assignments', [])
        logger.info(f"Machine assignments saved: {assignments}")
        return jsonify({
            'success': True,
            'message': f'Successfully saved {len(assignments)} machine assignments.'
        })
    except Exception as e:
        logger.error(f"Error saving machine assignments: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error saving machine assignments.'
        }), 500

@views_bp.route('/refresh-dashboard')
@permission_required(['dashboard_view'])
def refresh_dashboard():
    """AJAX endpoint to refresh dashboard data."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login')) # Incorrect for JSON endpoint
    
    try:
        ppm_data = DataService.get_all_entries(data_type='ppm')
        if isinstance(ppm_data, dict):
            ppm_data = [ppm_data]
        
        ocm_data = DataService.get_all_entries(data_type='ocm')
        if isinstance(ocm_data, dict):
            ocm_data = [ocm_data]
        
        all_equipment = ppm_data + ocm_data
        today = datetime.now().date()
        
        total_machines = len(all_equipment)
        overdue_count = upcoming_count = maintained_count = 0
        upcoming_7_days = upcoming_14_days = upcoming_21_days = 0
        upcoming_30_days = upcoming_60_days = upcoming_90_days = 0
        
        for item in all_equipment:
            status = item.get('Status', 'N/A').lower()
            if status == 'overdue':
                overdue_count += 1
            elif status == 'upcoming':
                upcoming_count += 1
                if item.get('data_type') == 'ocm':
                    next_maintenance = item.get('Next_Maintenance')
                    if next_maintenance and next_maintenance != 'N/A':
                        try:
                            next_date = EmailService.parse_date_flexible(next_maintenance).date()
                            days_until = (next_date - today).days
                            if days_until <= 7: upcoming_7_days += 1
                            if days_until <= 14: upcoming_14_days += 1
                            if days_until <= 21: upcoming_21_days += 1
                            if days_until <= 30: upcoming_30_days += 1
                            if days_until <= 60: upcoming_60_days += 1
                            if days_until <= 90: upcoming_90_days += 1
                        except ValueError:
                            pass
            elif status == 'maintained':
                maintained_count += 1
        
        return jsonify({
            'success': True,
            'data': {
                'total_machines': total_machines,
                'ppm_machine_count': len(ppm_data),
                'ocm_machine_count': len(ocm_data),
                'overdue_count': overdue_count,
                'upcoming_count': upcoming_count,
                'maintained_count': maintained_count,
                'upcoming_7_days': upcoming_7_days,
                'upcoming_14_days': upcoming_14_days,
                'upcoming_21_days': upcoming_21_days,
                'upcoming_30_days': upcoming_30_days,
                'upcoming_60_days': upcoming_60_days,
                'upcoming_90_days': upcoming_90_days,
                'current_time': datetime.now().strftime("%A, %d %B %Y — %H:%M:%S")
            }
        })
    except Exception as e:
        logger.error(f"Error refreshing dashboard data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@views_bp.route('/audit-log')
@permission_required(['audit_log_view'])
def audit_log_page():
    """Display the audit log page with filtering options."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        event_type_filter = request.args.get('event_type', '')
        user_filter = request.args.get('user', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        search_query = request.args.get('search', '')
        
        logs = AuditService.get_all_logs()
        if event_type_filter and event_type_filter != 'all':
            logs = [log for log in logs if log.get('event_type') == event_type_filter]
        if user_filter and user_filter != 'all':
            logs = [log for log in logs if log.get('performed_by') == user_filter]
        if start_date and end_date:
            logs = AuditService.get_logs_by_date_range(start_date, end_date)
        if search_query:
            logs = AuditService.search_logs(search_query)
        
        event_types = AuditService.get_event_types()
        users = AuditService.get_unique_users()
        
        AuditService.log_event(
            event_type=AuditService.EVENT_TYPES['USER_ACTION'],
            performed_by="User",
            description="Accessed audit log page",
            status=AuditService.STATUS_INFO
        )
        
        return render_template('audit_log.html',
                             logs=logs,
                             event_types=event_types,
                             users=users,
                             current_filters={
                                 'event_type': event_type_filter,
                                 'user': user_filter,
                                 'start_date': start_date,
                                 'end_date': end_date,
                                 'search': search_query
                             })
    except Exception as e:
        logger.error(f"Error loading audit log page: {str(e)}")
        flash('Error loading audit logs.', 'danger')
        return redirect(url_for('views.index'))

@views_bp.route('/audit-log/export')
@permission_required(['audit_log_export'])
def export_audit_log():
    """Export audit logs to CSV."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        event_type_filter = request.args.get('event_type', '')
        user_filter = request.args.get('user', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        search_query = request.args.get('search', '')
        
        logs = AuditService.get_all_logs()
        if event_type_filter and event_type_filter != 'all':
            logs = [log for log in logs if log.get('event_type') == event_type_filter]
        if user_filter and user_filter != 'all':
            logs = [log for log in logs if log.get('performed_by') == user_filter]
        if start_date and end_date:
            logs = AuditService.get_logs_by_date_range(start_date, end_date)
        if search_query:
            logs = AuditService.search_logs(search_query)
        
        csv_content = "ID,Timestamp,Event Type,Performed By,Description,Status,Details\n"
        for log in logs:
            details_str = json.dumps(log.get('details', {})).replace('"', '""')
            description = log.get('description', '').replace('"', '""')
            csv_content += f"{log.get('id', '')},{log.get('timestamp', '')},{log.get('event_type', '')},{log.get('performed_by', '')},\"{description}\",{log.get('status', '')},\"{details_str}\"\n"
        output_bytes = io.BytesIO()
        output_bytes.write(csv_content.encode('utf-8'))
        output_bytes.seek(0)
        
        AuditService.log_event(
            event_type=AuditService.EVENT_TYPES['DATA_EXPORT'],
            performed_by="User",
            description=f"Exported {len(logs)} audit log entries to CSV",
            status=AuditService.STATUS_SUCCESS,
            details={"export_format": "CSV", "record_count": len(logs)}
        )
        
        return send_file(
            output_bytes,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'audit_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        logger.error(f"Error exporting audit log: {str(e)}")
        flash('Error exporting audit logs.', 'danger')
        return redirect(url_for('views.audit_log_page'))

@views_bp.route('/backup/create-full', methods=['POST'])
@permission_required(['backup_manage'])
def create_full_backup():
    """Create a full application backup."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        result = BackupService.create_full_backup()
        flash(result['message'], 'success' if result['success'] else 'danger')
        return redirect(url_for('views.settings_page'))
    except Exception as e:
        logger.error(f"Error creating full backup: {str(e)}")
        flash(f"Error creating full backup: {str(e)}", 'danger')
        return redirect(url_for('views.settings_page'))

@views_bp.route('/backup/create-settings', methods=['POST'])
@permission_required(['backup_manage'])
def create_settings_backup():
    """Create a settings-only backup."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        result = BackupService.create_settings_backup()
        flash(result['message'], 'success' if result['success'] else 'danger')
        return redirect(url_for('views.settings_page'))
    except Exception as e:
        logger.error(f"Error creating settings backup: {str(e)}")
        flash(f"Error creating settings backup: {str(e)}", 'danger')
        return redirect(url_for('views.settings_page'))

@views_bp.route('/backup/list')
@permission_required(['backup_manage'])
def list_backups():
    """List all available backups as JSON."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login')) # Incorrect for JSON endpoint
    
    try:
        backups = BackupService.list_backups()
        return jsonify({'success': True, 'backups': backups})
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@views_bp.route('/backup/delete/<filename>', methods=['POST'])
@permission_required(['backup_manage'])
def delete_backup(filename):
    """Delete a backup file."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        result = BackupService.delete_backup(filename)
        flash(result['message'], 'success' if result['success'] else 'danger')
        return redirect(url_for('views.settings_page'))
    except Exception as e:
        logger.error(f"Error deleting backup: {str(e)}")
        flash(f"Error deleting backup: {str(e)}", 'danger')
        return redirect(url_for('views.settings_page'))

@views_bp.route('/backup/download/<backup_type>/<filename>')
@permission_required(['backup_manage'])
def download_backup(backup_type, filename):
    """Download a backup file."""
    # if not session.get('is_admin'): # Replaced by decorator
    #     return redirect(url_for('views.login'))
    
    try:
        if backup_type not in ['full', 'settings']:
            flash('Invalid backup type', 'danger')
            return redirect(url_for('views.settings_page'))
        
        backup_path = os.path.join(
            BackupService.FULL_BACKUPS_DIR if backup_type == 'full' else BackupService.SETTINGS_BACKUPS_DIR,
            filename
        )
        
        if not os.path.exists(backup_path):
            flash('Backup file not found', 'danger')
            return redirect(url_for('views.settings_page'))
        
        AuditService.log_event(
            event_type=AuditService.EVENT_TYPES['DATA_EXPORT'],
            performed_by="User",
            description=f"Downloaded backup file: {filename}",
            status=AuditService.STATUS_SUCCESS,
            details={"backup_type": backup_type, "filename": filename}
        )
        
        return send_file(backup_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"Error downloading backup: {str(e)}")
        flash(f"Error downloading backup: {str(e)}", 'danger')
        return redirect(url_for('views.settings_page'))

@views_bp.route('/create_user', methods=['GET', 'POST'])
@permission_required(['user_manage'])
def create_user():
    """Handles user creation."""
    logger.critical("Entering create_user route")  # Log entry point
    # if check_admin(): # Replaced by decorator
    #     logger.critical("Admin check failed, redirecting")
    #     return check_admin()

    if request.method == 'POST':
        logger.critical("Received POST request")
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        logger.critical(f"Username: {username}, Role: {role}")

        if not username or not password or not role:
            logger.critical("Missing fields in the form")
            flash('Please fill in all fields.', 'danger')
            return render_template('create_user.html')

        try:
            logger.critical("Loading settings")
            settings = DataService.load_settings()
            users = settings.get('users', [])

            # Check if username already exists
            for existing_user in users:
                if existing_user.get('username') == username:
                    flash('Username already exists. Please choose a different username.', 'danger')
                    return render_template('create_user.html')

            # Hash the password
            logger.critical("Hashing the password")
            hashed_password = generate_password_hash(password)

            # Handle profile image upload
            profile_image_url = None
            if 'profile_image' in request.files:
                profile_image = request.files['profile_image']
                if profile_image and profile_image.filename:
                    logger.info(f"Processing profile image upload for user {username}")

                    # Import file utilities
                    from app.utils.file_utils import save_uploaded_file, ensure_upload_directories

                    # Ensure upload directories exist
                    ensure_upload_directories()

                    # Save the profile image
                    success, error_msg, file_info = save_uploaded_file(profile_image, 'profiles', 'image')
                    if success:
                        profile_image_url = file_info['relative_path']
                        logger.info(f"Profile image saved successfully: {profile_image_url}")
                    else:
                        logger.warning(f"Failed to save profile image: {error_msg}")
                        flash(f'Profile image upload failed: {error_msg}', 'warning')
                        # Continue with user creation even if image upload fails

            new_user = {
                'username': username,
                'password': hashed_password,
                'role': role,
                'profile_image_url': profile_image_url
            }

            logger.critical(f"New user: {new_user}")

            users.append(new_user)
            settings['users'] = users
            logger.critical("Saving settings")
            DataService.save_settings(settings)

            # Log audit event
            from app.services.audit_service import AuditService
            AuditService.log_event(
                event_type="User Created",
                performed_by=current_user.username if current_user.is_authenticated else "System",
                description=f"New user '{username}' created with role '{role}'",
                status=AuditService.STATUS_SUCCESS,
                details={"username": username, "role": role, "has_profile_image": profile_image_url is not None}
            )

            logger.critical("User created successfully")
            flash('User created successfully!', 'success')
            return redirect(url_for('views.create_user'))  # Redirect to the same page or another page
        except Exception as e:
            logger.critical(f"Error creating user: {str(e)}")
            flash(f'Error creating user: {str(e)}', 'danger')

    logger.critical("Rendering create_user.html template")
    return render_template('create_user.html')


@views_bp.route('/history/<note_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_history_note(note_id):
    """Edit an existing history note."""
    try:
        # Get the existing note
        note = HistoryService.get_history_note(note_id)
        if not note:
            flash('History note not found.', 'warning')
            return redirect(url_for('views.index'))

        # Check if user can modify this note
        if not HistoryService.can_user_modify_note(note, current_user.username, getattr(current_user, 'role', None)):
            flash('You do not have permission to edit this note.', 'danger')
            return redirect(url_for('views.equipment_history',
                                  equipment_type=note.equipment_type,
                                  equipment_id=note.equipment_id))

        # Get equipment details
        equipment = DataService.get_entry(note.equipment_type, note.equipment_id)
        if not equipment:
            flash(f'Equipment with serial {note.equipment_id} not found.', 'warning')
            return redirect(url_for('views.index'))

        if request.method == 'POST':
            note_text = request.form.get('note_text', '').strip()

            if not note_text:
                flash('Note text is required.', 'danger')
                return render_template('equipment/edit_history.html',
                                     note=note,
                                     equipment=equipment,
                                     form_data=request.form,
                                     current_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            # Create update data
            try:
                update_data = HistoryNoteUpdate(
                    note_text=note_text,
                    modified_by=current_user.username,
                    modified_by_name=current_user.username
                )
            except ValueError as e:
                flash(f'Validation error: {str(e)}', 'danger')
                return render_template('equipment/edit_history.html',
                                     note=note,
                                     equipment=equipment,
                                     form_data=request.form,
                                     current_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            # Update the note
            updated_note = HistoryService.update_history_note(note_id, update_data)
            if updated_note:
                # Handle file uploads if any
                uploaded_files = request.files.getlist('attachments')
                for file in uploaded_files:
                    if file and file.filename:
                        attachment = HistoryService.add_attachment_to_note(
                            note_id, file, current_user.username
                        )
                        if not attachment:
                            flash(f'Failed to upload file: {file.filename}', 'warning')

                flash('History note updated successfully!', 'success')
                return redirect(url_for('views.equipment_history',
                                      equipment_type=note.equipment_type,
                                      equipment_id=note.equipment_id))
            else:
                flash('Failed to update history note.', 'danger')

        return render_template('equipment/edit_history.html',
                             note=note,
                             equipment=equipment,
                             form_data={'note_text': note.note_text},
                             current_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    except Exception as e:
        logger.error(f"Error editing history note: {e}")
        flash('Error editing history note.', 'danger')
        return redirect(url_for('views.index'))


# Equipment History Routes

@views_bp.route('/equipment/<equipment_type>/<equipment_id>/history')
@login_required
def equipment_history(equipment_type, equipment_id):
    """Display equipment history page."""
    try:
        if equipment_type not in ['ppm', 'ocm']:
            flash('Invalid equipment type.', 'danger')
            return redirect(url_for('views.index'))

        # Get equipment details
        equipment = DataService.get_entry(equipment_type, equipment_id)
        if not equipment:
            flash(f'Equipment with serial {equipment_id} not found.', 'warning')
            return redirect(url_for('views.list_equipment', data_type=equipment_type))

        # Get equipment history
        history_notes = HistoryService.get_equipment_history(equipment_id, equipment_type)

        return render_template('equipment/history.html',
                             equipment=equipment,
                             equipment_type=equipment_type,
                             equipment_id=equipment_id,
                             history_notes=history_notes)

    except Exception as e:
        logger.error(f"Error loading equipment history: {e}")
        flash('Error loading equipment history.', 'danger')
        return redirect(url_for('views.list_equipment', data_type=equipment_type))


@views_bp.route('/equipment/<equipment_type>/<equipment_id>/history/add', methods=['GET', 'POST'])
@login_required
def add_equipment_history(equipment_type, equipment_id):
    """Add new history note to equipment."""
    try:
        if equipment_type not in ['ppm', 'ocm']:
            flash('Invalid equipment type.', 'danger')
            return redirect(url_for('views.index'))

        # Get equipment details
        equipment = DataService.get_entry(equipment_type, equipment_id)
        if not equipment:
            flash(f'Equipment with serial {equipment_id} not found.', 'warning')
            return redirect(url_for('views.list_equipment', data_type=equipment_type))

        if request.method == 'POST':
            note_text = request.form.get('note_text', '').strip()

            if not note_text:
                flash('Note text is required.', 'danger')
                return render_template('equipment/add_history.html',
                                     equipment=equipment,
                                     equipment_type=equipment_type,
                                     equipment_id=equipment_id,
                                     form_data=request.form,
                                     current_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            # Create history note
            note_data = HistoryNoteCreate(
                equipment_id=equipment_id,
                equipment_type=equipment_type,
                author_id=current_user.username,
                author_name=current_user.username,
                note_text=note_text
            )

            history_note = HistoryService.create_history_note(note_data)
            if history_note:
                # Handle file uploads if any
                uploaded_files = request.files.getlist('attachments')
                for file in uploaded_files:
                    if file and file.filename:
                        attachment = HistoryService.add_attachment_to_note(
                            history_note.id, file, current_user.username
                        )
                        if not attachment:
                            flash(f'Failed to upload file: {file.filename}', 'warning')

                # Log audit event
                from app.services.audit_service import log_equipment_action
                log_equipment_action(
                    'History Added',
                    equipment_type.upper(),
                    equipment_id,
                    current_user.username
                )

                flash('History note added successfully!', 'success')
                return redirect(url_for('views.equipment_history',
                                      equipment_type=equipment_type,
                                      equipment_id=equipment_id))
            else:
                flash('Failed to add history note.', 'danger')

        return render_template('equipment/add_history.html',
                             equipment=equipment,
                             equipment_type=equipment_type,
                             equipment_id=equipment_id,
                             form_data={},
                             current_datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    except Exception as e:
        logger.error(f"Error adding equipment history: {e}")
        flash('Error adding equipment history.', 'danger')
        return redirect(url_for('views.equipment_history',
                              equipment_type=equipment_type,
                              equipment_id=equipment_id))

