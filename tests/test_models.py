"""
Test cases for data models.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.history import (
    HistoryNote,
    HistoryNoteCreate,
    HistoryNoteUpdate,
    HistoryAttachment,
    HistorySearchFilter
)
from app.models.ppm import PPMEntry, PPMEntryCreate, QuarterData
from app.models.ocm import OCMEntry, OCMEntryCreate
from app.models.department import Department, DepartmentCreate
from app.models.trainer import Trainer, TrainerCreate


class TestHistoryModels:
    """Test cases for history-related models."""

    def test_history_note_create_valid(self):
        """Test creating a valid HistoryNoteCreate."""
        note_data = {
            "equipment_id": "TEST001",
            "equipment_type": "ppm",
            "author_id": "admin",
            "author_name": "Admin User",
            "note_text": "Test history note"
        }
        
        note = HistoryNoteCreate(**note_data)
        
        assert note.equipment_id == "TEST001"
        assert note.equipment_type == "ppm"
        assert note.author_id == "admin"
        assert note.note_text == "Test history note"

    def test_history_note_create_invalid_equipment_type(self):
        """Test creating HistoryNoteCreate with invalid equipment type."""
        note_data = {
            "equipment_id": "TEST001",
            "equipment_type": "invalid",  # Should be 'ppm' or 'ocm'
            "author_id": "admin",
            "author_name": "Admin User",
            "note_text": "Test note"
        }
        
        with pytest.raises(ValidationError):
            HistoryNoteCreate(**note_data)

    def test_history_note_create_empty_note_text(self):
        """Test creating HistoryNoteCreate with empty note text."""
        note_data = {
            "equipment_id": "TEST001",
            "equipment_type": "ppm",
            "author_id": "admin",
            "author_name": "Admin User",
            "note_text": ""  # Empty text should be invalid
        }
        
        with pytest.raises(ValidationError):
            HistoryNoteCreate(**note_data)

    def test_history_note_full_model(self):
        """Test creating a full HistoryNote model."""
        note_data = {
            "id": "test-id-123",
            "equipment_id": "TEST001",
            "equipment_type": "ppm",
            "author_id": "admin",
            "author_name": "Admin User",
            "note_text": "Test history note",
            "created_at": "2025-07-30 10:00:00",
            "attachments": []
        }
        
        note = HistoryNote(**note_data)
        
        assert note.id == "test-id-123"
        assert note.is_edited is False
        assert note.updated_at is None

    def test_history_attachment_valid(self):
        """Test creating a valid HistoryAttachment."""
        attachment_data = {
            "id": "attach-123",
            "original_filename": "document.pdf",
            "stored_filename": "uuid-123.pdf",
            "file_size": 1024,
            "content_type": "application/pdf",
            "uploaded_by": "admin",
            "uploaded_at": "2025-07-30 10:00:00"
        }
        
        attachment = HistoryAttachment(**attachment_data)
        
        assert attachment.original_filename == "document.pdf"
        assert attachment.file_size == 1024

    def test_history_attachment_invalid_file_size(self):
        """Test creating HistoryAttachment with invalid file size."""
        attachment_data = {
            "id": "attach-123",
            "original_filename": "document.pdf",
            "stored_filename": "uuid-123.pdf",
            "file_size": 101 * 1024 * 1024,  # Larger than 100MB limit
            "content_type": "application/pdf",
            "uploaded_by": "admin",
            "uploaded_at": "2025-07-30 10:00:00"
        }
        
        with pytest.raises(ValidationError, match="File size cannot exceed 100MB"):
            HistoryAttachment(**attachment_data)

    def test_history_search_filter(self):
        """Test creating HistorySearchFilter."""
        filter_data = {
            "search_text": "maintenance",
            "equipment_type": "ppm",
            "department": "X-RAY",
            "author": "admin",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31"
        }
        
        search_filter = HistorySearchFilter(**filter_data)
        
        assert search_filter.search_text == "maintenance"
        assert search_filter.equipment_type == "ppm"


class TestPPMModels:
    """Test cases for PPM-related models."""

    def test_quarter_data_valid(self):
        """Test creating valid QuarterData."""
        quarter_data = {
            "quarter_date": "15/07/2025",
            "engineer": "JOHN DOE"
        }
        
        quarter = QuarterData(**quarter_data)
        
        assert quarter.quarter_date == "15/07/2025"
        assert quarter.engineer == "JOHN DOE"

    def test_ppm_entry_create_valid(self):
        """Test creating valid PPMEntryCreate."""
        ppm_data = {
            "SERIAL": "TEST001",
            "DEPARTMENT": "X-RAY",
            "NAME": "X-Ray Machine",
            "MODEL": "XR-2000",
            "MANUFACTURER": "Medical Corp",
            "LOG_NO": "12345"
        }
        
        ppm = PPMEntryCreate(**ppm_data)
        
        assert ppm.SERIAL == "TEST001"
        assert ppm.DEPARTMENT == "X-RAY"

    def test_ppm_entry_create_invalid_serial(self):
        """Test creating PPMEntryCreate with invalid serial."""
        ppm_data = {
            "SERIAL": "",  # Empty serial should be invalid
            "DEPARTMENT": "X-RAY",
            "NAME": "X-Ray Machine"
        }
        
        with pytest.raises(ValidationError):
            PPMEntryCreate(**ppm_data)


class TestOCMModels:
    """Test cases for OCM-related models."""

    def test_ocm_entry_create_valid(self):
        """Test creating valid OCMEntryCreate."""
        ocm_data = {
            "SERIAL": "OCM001",
            "DEPARTMENT": "SURGERY",
            "NAME": "Surgical Equipment",
            "MODEL": "SURG-100",
            "MANUFACTURER": "Surgical Corp",
            "LOG_NO": "54321"
        }
        
        ocm = OCMEntryCreate(**ocm_data)
        
        assert ocm.SERIAL == "OCM001"
        assert ocm.DEPARTMENT == "SURGERY"


class TestDepartmentModels:
    """Test cases for Department-related models."""

    def test_department_create_valid(self):
        """Test creating valid DepartmentCreate."""
        dept_data = {
            "name": "RADIOLOGY",
            "description": "Radiology Department"
        }
        
        dept = DepartmentCreate(**dept_data)
        
        assert dept.name == "RADIOLOGY"
        assert dept.description == "Radiology Department"

    def test_department_create_invalid_name(self):
        """Test creating DepartmentCreate with invalid name."""
        dept_data = {
            "name": "",  # Empty name should be invalid
            "description": "Test Department"
        }
        
        with pytest.raises(ValidationError):
            DepartmentCreate(**dept_data)

    def test_department_full_model(self):
        """Test creating full Department model."""
        dept_data = {
            "id": "dept-123",
            "name": "CARDIOLOGY",
            "description": "Cardiology Department",
            "created_at": "2025-07-30 10:00:00"
        }
        
        dept = Department(**dept_data)
        
        assert dept.id == "dept-123"
        assert dept.name == "CARDIOLOGY"


class TestTrainerModels:
    """Test cases for Trainer-related models."""

    def test_trainer_create_valid(self):
        """Test creating valid TrainerCreate."""
        trainer_data = {
            "name": "Dr. John Smith",
            "specialization": "Radiology Equipment",
            "email": "john.smith@hospital.com",
            "phone": "+1234567890"
        }
        
        trainer = TrainerCreate(**trainer_data)
        
        assert trainer.name == "Dr. John Smith"
        assert trainer.email == "john.smith@hospital.com"

    def test_trainer_create_invalid_email(self):
        """Test creating TrainerCreate with invalid email."""
        trainer_data = {
            "name": "Dr. John Smith",
            "specialization": "Radiology",
            "email": "invalid-email",  # Invalid email format
            "phone": "+1234567890"
        }
        
        with pytest.raises(ValidationError):
            TrainerCreate(**trainer_data)

    def test_trainer_create_empty_name(self):
        """Test creating TrainerCreate with empty name."""
        trainer_data = {
            "name": "",  # Empty name should be invalid
            "specialization": "Radiology",
            "email": "john@hospital.com"
        }
        
        with pytest.raises(ValidationError):
            TrainerCreate(**trainer_data)

    def test_trainer_full_model(self):
        """Test creating full Trainer model."""
        trainer_data = {
            "id": "trainer-123",
            "name": "Dr. Jane Doe",
            "specialization": "Surgical Equipment",
            "email": "jane.doe@hospital.com",
            "phone": "+0987654321",
            "created_at": "2025-07-30 10:00:00",
            "is_active": True
        }
        
        trainer = Trainer(**trainer_data)
        
        assert trainer.id == "trainer-123"
        assert trainer.is_active is True
