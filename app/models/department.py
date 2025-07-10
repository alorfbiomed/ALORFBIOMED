"""
Department model for centralized department management.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

class DepartmentCreate(BaseModel):
    """Model for creating a new department."""
    department_name: str = Field(..., min_length=1, max_length=100, description="Department name")
    information: Optional[str] = Field(None, max_length=500, description="Department description/notes")
    
    @validator('department_name')
    def validate_department_name(cls, v):
        """Validate department name."""
        if not v or not v.strip():
            raise ValueError("Department name cannot be empty")
        return v.strip()
    
    @validator('information')
    def validate_information(cls, v):
        """Validate information field."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v

class DepartmentUpdate(BaseModel):
    """Model for updating an existing department."""
    department_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Department name")
    information: Optional[str] = Field(None, max_length=500, description="Department description/notes")
    
    @validator('department_name')
    def validate_department_name(cls, v):
        """Validate department name."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Department name cannot be empty")
            return v.strip()
        return v
    
    @validator('information')
    def validate_information(cls, v):
        """Validate information field."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v

class Department:
    """Department model for managing department data."""
    
    def __init__(self, id: int, department_name: str, information: Optional[str] = None, 
                 created_date: Optional[str] = None, updated_date: Optional[str] = None):
        self.id = id
        self.department_name = department_name
        self.information = information
        self.created_date = created_date or datetime.now().isoformat()
        self.updated_date = updated_date or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert department to dictionary."""
        return {
            'id': self.id,
            'department_name': self.department_name,
            'information': self.information,
            'created_date': self.created_date,
            'updated_date': self.updated_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Department':
        """Create department from dictionary."""
        return cls(
            id=data.get('id'),
            department_name=data.get('department_name'),
            information=data.get('information'),
            created_date=data.get('created_date'),
            updated_date=data.get('updated_date')
        )
    
    def update(self, update_data: DepartmentUpdate):
        """Update department with new data."""
        if update_data.department_name is not None:
            self.department_name = update_data.department_name
        if update_data.information is not None:
            self.information = update_data.information
        self.updated_date = datetime.now().isoformat()
    
    def __repr__(self):
        return f'<Department {self.id}: {self.department_name}>'
