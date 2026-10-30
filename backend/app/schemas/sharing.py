from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class DoctorDirectoryItem(BaseModel):
    doctor_id: int
    user_id: int
    full_name: str
    email: EmailStr
    specialization: Optional[str] = None
    hospital: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GrantShareRequest(BaseModel):
    report_id: int
    doctor_email: Optional[EmailStr] = None
    doctor_id: Optional[int] = None
    notes: Optional[str] = None
    expires_at: Optional[datetime] = None


class SharedReportResponse(BaseModel):
    id: int
    report_id: int
    report_uuid: str
    original_filename: str
    report_category: Optional[str] = None
    patient_name: str
    doctor_name: str
    doctor_email: str
    doctor_specialization: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    granted_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DoctorReportDetailResponse(BaseModel):
    report_id: int
    report_uuid: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    report_category: Optional[str] = None
    report_date: Optional[str] = None
    created_at: datetime
    patient_name: str
    extracted_values: List[Dict[str, Any]]
    predictions: List[Dict[str, Any]]
    blockchain_verified: bool
    blockchain_tx_hash: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
