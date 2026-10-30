import os
import hashlib
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException, PermissionDeniedException
from app.models.report import MedicalReport, OCRStatus
from app.models.sharing import SharedReport
from app.models.user import UserRole


class ReportService:
    @staticmethod
    def _compute_sha256(file_bytes: bytes) -> str:
        """Calculates the SHA-256 cryptographic digest of a binary byte stream."""
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def _validate_file(file: UploadFile, file_bytes: bytes):
        """Strictly validates file extension, magic bytes, and size."""
        # 1. Check file size
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise BadRequestException(
                f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )
        if len(file_bytes) == 0:
            raise BadRequestException("The uploaded file is empty.")

        # 2. Check file extension
        filename = file.filename or "unknown"
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise BadRequestException(
                f"Unsupported file format '.{ext}'. Supported formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        # 3. Magic bytes / MIME signature check
        if ext == "pdf":
            if not file_bytes.startswith(b"%PDF"):
                raise BadRequestException("Invalid PDF format. File header signature mismatch.")
        elif ext in ["jpg", "jpeg"]:
            if not (file_bytes.startswith(b"\xff\xd8\xff")):
                raise BadRequestException("Invalid JPEG image signature.")
        elif ext == "png":
            if not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
                raise BadRequestException("Invalid PNG image signature.")

    @classmethod
    def save_uploaded_report(
        cls,
        db: Session,
        patient_id: int,
        file: UploadFile,
        report_category: Optional[str] = "General Lab Report",
        report_date: Optional[datetime.date] = None,
    ) -> MedicalReport:
        """Saves file to secure storage, records metadata and computes SHA-256 hash."""
        # Read file into memory (or chunk if very large)
        file.file.seek(0)
        file_bytes = file.file.read()

        cls._validate_file(file, file_bytes)

        # Calculate cryptographic hash
        sha256_hash = cls._compute_sha256(file_bytes)

        # Generate unique report identifier & non-guessable storage path
        report_uuid = f"rep_{uuid.uuid4().hex}"
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "pdf"
        secure_filename = f"{report_uuid}.{ext}"

        # Ensure upload directory exists outside public web directory
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        disk_path = os.path.join(settings.UPLOAD_DIR, secure_filename)

        with open(disk_path, "wb") as f:
            f.write(file_bytes)

        new_report = MedicalReport(
            patient_id=patient_id,
            report_uuid=report_uuid,
            original_filename=file.filename or secure_filename,
            file_path=disk_path,
            file_hash_sha256=sha256_hash,
            file_type=ext,
            file_size_bytes=len(file_bytes),
            report_category=report_category,
            report_date=report_date or datetime.utcnow().date(),
            ocr_status=OCRStatus.PENDING,
            blockchain_registered=False,
            is_deleted=False,
        )

        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        return new_report

    @staticmethod
    def list_patient_reports(
        db: Session, patient_id: int, skip: int = 0, limit: int = 50
    ) -> List[MedicalReport]:
        """Lists active medical reports belonging to the patient."""
        return (
            db.query(MedicalReport)
            .filter(
                MedicalReport.patient_id == patient_id,
                MedicalReport.is_deleted == False,
            )
            .order_by(MedicalReport.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_report_by_id(db: Session, report_id: int) -> MedicalReport:
        """Retrieves a single report by integer primary key."""
        report = (
            db.query(MedicalReport)
            .filter(MedicalReport.id == report_id, MedicalReport.is_deleted == False)
            .first()
        )
        if not report:
            raise NotFoundException("Medical Report")
        return report

    @staticmethod
    def get_report_by_uuid(db: Session, report_uuid: str) -> MedicalReport:
        """Retrieves a single report by its UUID."""
        report = (
            db.query(MedicalReport)
            .filter(MedicalReport.report_uuid == report_uuid, MedicalReport.is_deleted == False)
            .first()
        )
        if not report:
            raise NotFoundException("Medical Report")
        return report

    @classmethod
    def verify_report_integrity_on_disk(cls, report: MedicalReport) -> Tuple[bool, str, str]:
        """Re-reads the file from disk, calculates current SHA-256 and compares to stored hash."""
        if not os.path.exists(report.file_path):
            return False, "File missing from disk storage", report.file_hash_sha256

        with open(report.file_path, "rb") as f:
            current_bytes = f.read()

        current_hash = cls._compute_sha256(current_bytes)
        is_match = (current_hash == report.file_hash_sha256)
        return is_match, current_hash, report.file_hash_sha256

    @staticmethod
    def check_user_report_access(
        db: Session,
        report: MedicalReport,
        user_id: int,
        user_role: UserRole,
    ) -> bool:
        """Enforces granular authorization for report view and download."""
        if user_role == UserRole.ADMIN:
            return True

        if user_role == UserRole.PATIENT:
            # Check if patient owns this report
            return report.patient.user_id == user_id

        if user_role == UserRole.DOCTOR:
            # Check if doctor has active, non-expired sharing permission
            now = datetime.utcnow()
            active_share = (
                db.query(SharedReport)
                .filter(
                    SharedReport.report_id == report.id,
                    SharedReport.doctor.has(user_id=user_id),
                    SharedReport.is_active == True,
                )
                .first()
            )
            if active_share:
                if active_share.expires_at and active_share.expires_at < now:
                    return False  # Permission has expired
                return True

        return False

    @staticmethod
    def delete_report(db: Session, report_id: int, patient_id: int) -> bool:
        """Soft-deletes a medical report if owned by the requesting patient."""
        report = (
            db.query(MedicalReport)
            .filter(
                MedicalReport.id == report_id,
                MedicalReport.patient_id == patient_id,
                MedicalReport.is_deleted == False,
            )
            .first()
        )
        if not report:
            raise NotFoundException("Medical Report")

        report.is_deleted = True
        db.commit()
        return True
