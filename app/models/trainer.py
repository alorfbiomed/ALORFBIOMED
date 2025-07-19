"""
Trainer model for centralized trainer management.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

class TrainerCreate(BaseModel):
    """Model for creating a new trainer."""
    name: str = Field(..., min_length=1, max_length=100, description="Trainer name")
    department_id: Optional[int] = Field(None, description="Department ID")
    telephone: Optional[str] = Field(None, max_length=20, description="Telephone number")
    information: Optional[str] = Field(None, max_length=500, description="Trainer description/notes")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate trainer name."""
        if not v or not v.strip():
            raise ValueError("Trainer name cannot be empty")
        return v.strip()
    
    @validator('telephone')
    def validate_telephone(cls, v):
        """Validate telephone number."""
        if v is not None:
            v = v.strip()
            if v:
                # Basic telephone validation - allow numbers, spaces, hyphens, parentheses, plus
                import re
                if not re.match(r'^[\d\s\-\(\)\+]+$', v):
                    raise ValueError("Invalid telephone number format")
                return v
            return None
        return v
    
    @validator('information')
    def validate_information(cls, v):
        """Validate information field."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v

class TrainerUpdate(BaseModel):
    """Model for updating an existing trainer."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Trainer name")
    department_id: Optional[int] = Field(None, description="Department ID")
    telephone: Optional[str] = Field(None, max_length=20, description="Telephone number")
    information: Optional[str] = Field(None, max_length=500, description="Trainer description/notes")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate trainer name."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Trainer name cannot be empty")
            return v.strip()
        return v
    
    @validator('telephone')
    def validate_telephone(cls, v):
        """Validate telephone number."""
        if v is not None:
            v = v.strip()
            if v:
                # Basic telephone validation
                import re
                if not re.match(r'^[\d\s\-\(\)\+]+$', v):
                    raise ValueError("Invalid telephone number format")
                return v
            return None
        return v
    
    @validator('information')
    def validate_information(cls, v):
        """Validate information field."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v

class Trainer:
    """Trainer model for managing trainer data."""
    
    def __init__(self, id: int, name: str, department_id: Optional[int] = None, 
                 telephone: Optional[str] = None, information: Optional[str] = None,
                 created_date: Optional[str] = None, updated_date: Optional[str] = None):
        self.id = id
        self.name = name
        self.department_id = department_id
        self.telephone = telephone
        self.information = information
        self.created_date = created_date or datetime.now().isoformat()
        self.updated_date = updated_date or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trainer to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'department_id': self.department_id,
            'telephone': self.telephone,
            'information': self.information,
            'created_date': self.created_date,
            'updated_date': self.updated_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trainer':
        """Create trainer from dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            department_id=data.get('department_id'),
            telephone=data.get('telephone'),
            information=data.get('information'),
            created_date=data.get('created_date'),
            updated_date=data.get('updated_date')
        )
    
    def update(self, update_data: TrainerUpdate):
        """Update trainer with new data."""
        if update_data.name is not None:
            self.name = update_data.name
        if update_data.department_id is not None:
            self.department_id = update_data.department_id
        if update_data.telephone is not None:
            self.telephone = update_data.telephone
        if update_data.information is not None:
            self.information = update_data.information
        self.updated_date = datetime.now().isoformat()
    
    def __repr__(self):
        return f'<Trainer {self.id}: {self.name}>'
