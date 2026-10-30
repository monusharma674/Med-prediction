from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class PatientProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    blood_group: Optional[str] = None


class DoctorProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2)
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    hospital: Optional[str] = None
    phone: Optional[str] = None


class PatientProfileDetail(BaseModel):
    id: int
    user_id: int
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    blood_group: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorProfileDetail(BaseModel):
    id: int
    user_id: int
    full_name: str
    specialization: str
    license_number: Optional[str] = None
    hospital: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
