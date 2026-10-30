from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr


class UserRegisterPatient(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, description="Male, Female, Other")
    phone: Optional[str] = None
    blood_group: Optional[str] = None


class UserRegisterDoctor(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2)
    specialization: str = Field(..., min_length=2)
    license_number: Optional[str] = None
    hospital: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: int
    full_name: str
    email: EmailStr


class PatientProfileSummary(BaseModel):
    id: int
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    blood_group: Optional[str] = None

    class Config:
        from_attributes = True


class DoctorProfileSummary(BaseModel):
    id: int
    full_name: str
    specialization: str
    license_number: Optional[str] = None
    hospital: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    patient_profile: Optional[PatientProfileSummary] = None
    doctor_profile: Optional[DoctorProfileSummary] = None

    class Config:
        from_attributes = True
