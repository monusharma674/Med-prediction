from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole, PatientProfile, DoctorProfile
from app.schemas.user import DoctorProfileSummary
from app.schemas.profile import (
    PatientProfileDetail,
    PatientProfileUpdate,
    DoctorProfileDetail,
    DoctorProfileUpdate,
)
from app.core.dependencies import (
    get_current_user,
    get_current_patient,
    get_current_doctor,
    log_audit_event,
)

router = APIRouter(prefix="/users", tags=["User Profiles"])


@router.get("/doctors", response_model=List[DoctorProfileSummary])
def list_available_doctors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve list of registered medical practitioners available for report sharing."""
    doctors = db.query(DoctorProfile).join(User).filter(User.is_active == True).all()
    return doctors


@router.get("/profile/patient", response_model=PatientProfileDetail)
def get_my_patient_profile(
    patient: PatientProfile = Depends(get_current_patient),
):
    """Get the profile details of the logged-in patient."""
    return patient


@router.put("/profile/patient", response_model=PatientProfileDetail)
def update_my_patient_profile(
    payload: PatientProfileUpdate,
    request: Request,
    patient: PatientProfile = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Update profile details for the authenticated patient."""
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)

    log_audit_event(
        db=db,
        action="UPDATE_PATIENT_PROFILE",
        resource_type="patient_profile",
        resource_id=str(patient.id),
        user_id=patient.user_id,
        request=request,
    )
    return patient


@router.get("/profile/doctor", response_model=DoctorProfileDetail)
def get_my_doctor_profile(
    doctor: DoctorProfile = Depends(get_current_doctor),
):
    """Get the profile details of the logged-in doctor."""
    return doctor


@router.put("/profile/doctor", response_model=DoctorProfileDetail)
def update_my_doctor_profile(
    payload: DoctorProfileUpdate,
    request: Request,
    doctor: DoctorProfile = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Update profile details for the authenticated medical practitioner."""
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)

    log_audit_event(
        db=db,
        action="UPDATE_DOCTOR_PROFILE",
        resource_type="doctor_profile",
        resource_id=str(doctor.id),
        user_id=doctor.user_id,
        request=request,
    )
    return doctor
