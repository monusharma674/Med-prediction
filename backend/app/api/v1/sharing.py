from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.services.sharing.sharing_service import SharingService
from app.schemas.sharing import (
    DoctorDirectoryItem,
    GrantShareRequest,
    SharedReportResponse,
    DoctorReportDetailResponse,
)

router = APIRouter()


# ---------------- Patient Sharing Endpoints ----------------

@router.get("/doctors", response_model=List[DoctorDirectoryItem])
def list_available_doctors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns directory of verified physicians registered in the system."""
    return SharingService.get_doctor_directory(db)


@router.post("/grant", response_model=SharedReportResponse, status_code=status.HTTP_201_CREATED)
def grant_doctor_access(
    req: GrantShareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Grants a physician permission to access a specific medical report and its extracted values.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    return SharingService.grant_share(db, patient_id=patient_id, req=req)


@router.get("/my-shares", response_model=List[SharedReportResponse])
def get_my_shared_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists all report access permissions granted by the authenticated patient.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    return SharingService.get_patient_shares(db, patient_id=patient_id)


@router.delete("/{share_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_doctor_access(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Immediately revokes access permissions granted to a doctor.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    SharingService.revoke_share(db, patient_id=patient_id, share_id=share_id)
    return None


# ---------------- Doctor Portal Endpoints ----------------

@router.get("/doctor/reports", response_model=List[SharedReportResponse])
def list_shared_patient_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves only the medical reports for which patients have actively granted access.
    Strictly enforced in backend; unauthorized reports are filtered out.
    """
    if current_user.role != UserRole.DOCTOR or not current_user.doctor_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only authorized medical doctors can access the physician portal.",
        )
    return SharingService.get_doctor_shared_reports(db, doctor_id=current_user.doctor_profile.id)


@router.get("/doctor/reports/{report_id}", response_model=DoctorReportDetailResponse)
def get_shared_patient_report_details(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accesses full report details, extracted clinical biomarkers, and prediction history
    for an authorized patient report.
    """
    if current_user.role != UserRole.DOCTOR or not current_user.doctor_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only authorized medical doctors can access the physician portal.",
        )
    return SharingService.get_doctor_report_details(
        db, doctor_id=current_user.doctor_profile.id, report_id=report_id
    )
