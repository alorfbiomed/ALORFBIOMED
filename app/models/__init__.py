"""
Models package for the application.
"""
from app.models.json_user import JSONUser as User
from app.models.base_model import BaseModel
from app.models.training import Training
from app.models.ppm import (
    PPMEntry,
    PPMEntryCreate,
    PPMImportEntry,
    QuarterData
)
from app.models.ocm import (
    OCMEntry,
    OCMEntryCreate
)
from app.models.history import (
    HistoryNote,
    HistoryNoteCreate,
    HistoryNoteUpdate,
    HistoryAttachment,
    HistorySearchFilter
)
from app.models.department import (
    Department,
    DepartmentCreate,
    DepartmentUpdate
)
from app.models.trainer import (
    Trainer,
    TrainerCreate,
    TrainerUpdate
)

# Export the models
__all__ = [
    'User',
    'BaseModel',
    'Training',
    'PPMEntry',
    'PPMEntryCreate',
    'PPMImportEntry',
    'QuarterData',
    'OCMEntry',
    'OCMEntryCreate',
    'HistoryNote',
    'HistoryNoteCreate',
    'HistoryNoteUpdate',
    'HistoryAttachment',
    'HistorySearchFilter',
    'Department',
    'DepartmentCreate',
    'DepartmentUpdate',
    'Trainer',
    'TrainerCreate',
    'TrainerUpdate'
]
