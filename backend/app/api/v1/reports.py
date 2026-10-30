import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import (
    get_current_user,
    get_current_patient,
    log_audit_event,
)
from app.core.exceptions import PermissionDeniedException, NotFoundException
from app.models.user import User, PatientProfile
from app.models.report import MedicalReport
from app.schemas.report import MedicalReportResponse, MedicalReportSummary
from app.services.reports.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Medical Reports"])


@router.post("/upload", response_model=MedicalReportResponse, status_code=status.HTTP_201_CREATED)
def upload_medical_report(
    request: Request,
    file: UploadFile = File(..., description="PDF or image lab report file"),
    report_category: Optional[str] = Form("General Lab Report"),
    report_date: Optional[str] = Form(None),
    patient: PatientProfile = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Securely uploads a clinical report, validates file bytes, stores outside public root, and computes SHA-256."""
    parsed_date = None
    if report_date:
        try:
            parsed_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    report = ReportService.save_uploaded_report(
        db=db,
        patient_id=patient.id,
        file=file,
        report_category=report_category,
        report_date=parsed_date,
    )

    log_audit_event(
        db=db,
        action="UPLOAD_REPORT",
        resource_type="report",
        resource_id=str(report.id),
        user_id=patient.user_id,
        request=request,
        details={
            "report_uuid": report.report_uuid,
            "filename": report.original_filename,
            "sha256": report.file_hash_sha256,
            "size_bytes": report.file_size_bytes,
        },
    )

    return report


@router.get("/", response_model=List[MedicalReportSummary])
def get_my_reports(
    skip: int = 0,
    limit: int = 50,
    patient: PatientProfile = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Retrieve all reports uploaded by the currently authenticated patient."""
    reports = ReportService.list_patient_reports(db, patient.id, skip=skip, limit=limit)
    return reports


@router.get("/{report_id}", response_model=MedicalReportResponse)
def get_report_details(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve report metadata and extracted parameters with strict role & consent verification."""
    report = ReportService.get_report_by_id(db, report_id)
    has_access = ReportService.check_user_report_access(
        db=db,
        report=report,
        user_id=current_user.id,
        user_role=current_user.role,
    )
    if not has_access:
        raise PermissionDeniedException("You do not have authorization to view this medical report.")

    return report


@router.get("/{report_id}/download")
def download_medical_report(
    report_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Streams the original medical report file to authorized patients, consented physicians, or admins."""
    report = ReportService.get_report_by_id(db, report_id)
    has_access = ReportService.check_user_report_access(
        db=db,
        report=report,
        user_id=current_user.id,
        user_role=current_user.role,
    )
    if not has_access:
        raise PermissionDeniedException("You are not authorized to download this medical report.")

    if not os.path.exists(report.file_path):
        raise NotFoundException("Physical report file on server disk")

    log_audit_event(
        db=db,
        action="DOWNLOAD_REPORT",
        resource_type="report",
        resource_id=str(report.id),
        user_id=current_user.id,
        request=request,
        details={"report_uuid": report.report_uuid},
    )

    media_type = "application/pdf" if report.file_type == "pdf" else f"image/{report.file_type}"
    return FileResponse(
        path=report.file_path,
        media_type=media_type,
        filename=report.original_filename,
    )


@router.get("/{report_id}/verify-file")
def verify_local_file_integrity(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verifies that the file currently on server disk matches the registered SHA-256 hash."""
    report = ReportService.get_report_by_id(db, report_id)
    has_access = ReportService.check_user_report_access(
        db=db,
        report=report,
        user_id=current_user.id,
        user_role=current_user.role,
    )
    if not has_access:
        raise PermissionDeniedException("You do not have permission to verify this report.")

    is_match, current_hash, stored_hash = ReportService.verify_report_integrity_on_disk(report)
    return {
        "report_id": report.id,
        "report_uuid": report.report_uuid,
        "is_intact": is_match,
        "stored_hash": stored_hash,
        "current_hash": current_hash,
        "status": "VERIFIED_AUTHENTIC" if is_match else "TAMPERED_OR_CORRUPT",
    }


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
def delete_medical_report(
    report_id: int,
    request: Request,
    patient: PatientProfile = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Patient-initiated safe deletion of a report with audit logging."""
    ReportService.delete_report(db, report_id=report_id, patient_id=patient.id)
    log_audit_event(
        db=db,
        action="DELETE_REPORT",
        resource_type="report",
        resource_id=str(report_id),
        user_id=patient.user_id,
        request=request,
    )
    return {"message": "Medical report deleted successfully.", "report_id": report_id}
