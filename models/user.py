# models/user.py
"""
User data model
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    id: Optional[int] = None
    telegram_id: str = ''
    employee_id: str = ''
    name: str = ''
    redmine_url: str = ''
    api_key: str = ''
    default_project_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    def to_dict(self):
        return {
            'telegram_id': self.telegram_id,
            'employee_id': self.employee_id,
            'name': self.name,
            'redmine_url': self.redmine_url,
            'api_key': self.api_key,
            'default_project_id': self.default_project_id
        }