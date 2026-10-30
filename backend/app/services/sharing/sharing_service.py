from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole, DoctorProfile, PatientProfile
from app.models.report import MedicalReport
from app.models.extracted_value import ExtractedMedicalValue
from app.models.prediction import Prediction
from app.models.sharing import SharedReport
from app.models.audit import AuditLog
from app.schemas.sharing import (
    DoctorDirectoryItem,
    GrantShareRequest,
    SharedReportResponse,
    DoctorReportDetailResponse,
)


class SharingService:

    @staticmethod
    def get_doctor_directory(db: Session) -> List[DoctorDirectoryItem]:
        """Lists active doctors available for report sharing."""
        doctors = (
            db.query(DoctorProfile)
            .join(User, DoctorProfile.user_id == User.id)
            .filter(User.is_active == True)
            .all()
        )
        items = []
        for d in doctors:
            items.append(
                DoctorDirectoryItem(
                    doctor_id=d.id,
                    user_id=d.user_id,
                    full_name=d.full_name,
                    email=d.user.email,
                    specialization=d.specialization,
                    hospital=d.hospital,
                )
            )
        return items

    @staticmethod
    def grant_share(
        db: Session, patient_id: int, req: GrantShareRequest
    ) -> SharedReportResponse:
        """
        Grants explicit view access for a specific medical report to an authorized physician.
        """
        # Validate patient owns the report
        report = (
            db.query(MedicalReport)
            .filter(
                MedicalReport.id == req.report_id,
                MedicalReport.patient_id == patient_id,
                MedicalReport.is_deleted == False,
            )
            .first()
        )
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medical report not found or access denied.",
            )

        # Lookup doctor
        doctor = None
        if req.doctor_id:
            doctor = db.query(DoctorProfile).filter(DoctorProfile.id == req.doctor_id).first()
        elif req.doctor_email:
            user = (
                db.query(User)
                .filter(User.email == req.doctor_email, User.role == UserRole.DOCTOR)
                .first()
            )
            if user:
                doctor = user.doctor_profile

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified physician was not found in directory.",
            )

        # Check existing active share
        existing_share = (
            db.query(SharedReport)
            .filter(
                SharedReport.patient_id == patient_id,
                SharedReport.doctor_id == doctor.id,
                SharedReport.report_id == report.id,
                SharedReport.is_active == True,
            )
            .first()
        )
        now_utc = datetime.now(timezone.utc)

        if existing_share:
            existing_share.notes = req.notes or existing_share.notes
            existing_share.expires_at = req.expires_at
            db.commit()
            db.refresh(existing_share)
            share_obj = existing_share
        else:
            share_obj = SharedReport(
                patient_id=patient_id,
                doctor_id=doctor.id,
                report_id=report.id,
                notes=req.notes,
                expires_at=req.expires_at,
                is_active=True,
                granted_at=now_utc,
            )
            db.add(share_obj)

            # Audit log
            audit = AuditLog(
                action="SHARE_REPORT_GRANTED",
                user_id=patient_id,
                resource_type="sharing",
                resource_id=str(report.id),
                details={
                    "report_id": report.id,
                    "doctor_id": doctor.id,
                    "doctor_email": doctor.user.email,
                },
            )
            db.add(audit)
            db.commit()
            db.refresh(share_obj)

        patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()

        return SharedReportResponse(
            id=share_obj.id,
            report_id=report.id,
            report_uuid=report.report_uuid,
            original_filename=report.original_filename,
            report_category=report.report_category,
            patient_name=patient.full_name if patient else "Unknown Patient",
            doctor_name=doctor.full_name,
            doctor_email=doctor.user.email,
            doctor_specialization=doctor.specialization,
            is_active=share_obj.is_active,
            notes=share_obj.notes,
            granted_at=share_obj.granted_at,
            expires_at=share_obj.expires_at,
            revoked_at=share_obj.revoked_at,
        )

    @staticmethod
    def get_patient_shares(db: Session, patient_id: int) -> List[SharedReportResponse]:
        """Returns all sharing permissions granted by the patient."""
        shares = (
            db.query(SharedReport)
            .filter(SharedReport.patient_id == patient_id)
            .order_by(SharedReport.granted_at.desc())
            .all()
        )
        patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
        patient_name = patient.full_name if patient else "Patient"

        results = []
        for s in shares:
            results.append(
                SharedReportResponse(
                    id=s.id,
                    report_id=s.report_id,
                    report_uuid=s.report.report_uuid,
                    original_filename=s.report.original_filename,
                    report_category=s.report.report_category,
                    patient_name=patient_name,
                    doctor_name=s.doctor.full_name,
                    doctor_email=s.doctor.user.email,
                    doctor_specialization=s.doctor.specialization,
                    is_active=s.is_active,
                    notes=s.notes,
                    granted_at=s.granted_at,
                    expires_at=s.expires_at,
                    revoked_at=s.revoked_at,
                )
            )
        return results

    @staticmethod
    def revoke_share(db: Session, patient_id: int, share_id: int):
        """Immediately revokes access permissions granted to a doctor for a report."""
        share = (
            db.query(SharedReport)
            .filter(SharedReport.id == share_id, SharedReport.patient_id == patient_id)
            .first()
        )
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sharing record not found or access denied.",
            )

        now_utc = datetime.now(timezone.utc)
        share.is_active = False
        share.revoked_at = now_utc

        audit = AuditLog(
            action="SHARE_REPORT_REVOKED",
            user_id=patient_id,
            resource_type="sharing",
            resource_id=str(share.id),
            details={"share_id": share.id, "report_id": share.report_id, "doctor_id": share.doctor_id},
        )
        db.add(audit)
        db.commit()

    @staticmethod
    def get_doctor_shared_reports(db: Session, doctor_id: int) -> List[SharedReportResponse]:
        """Returns active medical reports shared with this specific doctor."""
        now_utc = datetime.now(timezone.utc)
        shares = (
            db.query(SharedReport)
            .filter(
                SharedReport.doctor_id == doctor_id,
                SharedReport.is_active == True,
            )
            .order_by(SharedReport.granted_at.desc())
            .all()
        )

        results = []
        for s in shares:
            # Check expiry
            if s.expires_at and s.expires_at < now_utc:
                continue

            results.append(
                SharedReportResponse(
                    id=s.id,
                    report_id=s.report_id,
                    report_uuid=s.report.report_uuid,
                    original_filename=s.report.original_filename,
                    report_category=s.report.report_category,
                    patient_name=s.patient.full_name,
                    doctor_name=s.doctor.full_name,
                    doctor_email=s.doctor.user.email,
                    doctor_specialization=s.doctor.specialization,
                    is_active=s.is_active,
                    notes=s.notes,
                    granted_at=s.granted_at,
                    expires_at=s.expires_at,
                    revoked_at=s.revoked_at,
                )
            )
        return results

    @staticmethod
    def get_doctor_report_details(
        db: Session, doctor_id: int, report_id: int
    ) -> DoctorReportDetailResponse:
        """
        Enforces strict authorization: Physician can only access report details if an active,
        unexpired patient share permission exists.
        """
        now_utc = datetime.now(timezone.utc)
        share = (
            db.query(SharedReport)
            .filter(
                SharedReport.doctor_id == doctor_id,
                SharedReport.report_id == report_id,
                SharedReport.is_active == True,
            )
            .first()
        )
        if not share or (share.expires_at and share.expires_at < now_utc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Forbidden: Patient has not authorized your access to this clinical report.",
            )

        report = share.report
        # Extracted values
        values = db.query(ExtractedMedicalValue).filter(ExtractedMedicalValue.report_id == report.id).all()
        val_list = []
        for v in values:
            val_list.append({
                "test_name_raw": v.test_name_raw,
                "test_name_standardized": v.test_name_standardized,
                "value": v.final_value,
                "unit": v.unit_normalized or v.unit_original,
                "reference_range": v.reference_range,
                "is_corrected": v.is_manually_corrected,
            })

        # Associated predictions
        preds = db.query(Prediction).filter(Prediction.report_id == report.id).all()
        pred_list = []
        for p in preds:
            pred_list.append({
                "id": p.id,
                "disease_name": p.disease_name,
                "prediction_class": p.prediction_class,
                "model_score": p.model_score,
                "probability": p.probability,
                "predicted_at": p.predicted_at.isoformat(),
            })

        # Audit log view
        audit = AuditLog(
            action="DOCTOR_VIEWED_REPORT",
            user_id=share.doctor.user_id,
            resource_type="report",
            resource_id=report.report_uuid,
            details={"report_id": report.id, "patient_id": share.patient_id},
        )
        db.add(audit)
        db.commit()

        return DoctorReportDetailResponse(
            report_id=report.id,
            report_uuid=report.report_uuid,
            original_filename=report.original_filename,
            file_type=report.file_type,
            file_size_bytes=report.file_size_bytes,
            report_category=report.report_category,
            report_date=str(report.report_date) if report.report_date else None,
            created_at=report.created_at,
            patient_name=share.patient.full_name,
            extracted_values=val_list,
            predictions=pred_list,
            blockchain_verified=report.blockchain_registered,
            blockchain_tx_hash=report.blockchain_tx_hash,
        )
