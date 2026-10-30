import os
import sys
import io
import hashlib
from datetime import datetime

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import UploadFile

from app.database.session import Base
from app.models.user import User, UserRole, PatientProfile, DoctorProfile
from app.models.report import MedicalReport, OCRStatus
from app.schemas.user import UserRegisterPatient
from app.services.authentication.auth_service import AuthService
from app.services.reports.report_service import ReportService
from app.core.exceptions import BadRequestException, PermissionDeniedException, NotFoundException


def test_phase_2_reports():
    print("==================================================", flush=True)
    print("  AI MEDICAL REPORT SYSTEM: PHASE 2 TEST SUITE    ", flush=True)
    print("==================================================", flush=True)

    # 1. Setup isolated in-memory DB
    print("[1] Initializing isolated database session...", flush=True)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    # 2. Setup test patient and doctor users
    print("[2] Creating test patient and doctor accounts...", flush=True)
    patient_user = AuthService.register_patient(
        db,
        UserRegisterPatient(
            email="patient1@example.com",
            password="Password123!",
            full_name="Aarav Sharma",
            gender="Male",
        ),
    )
    patient2_user = AuthService.register_patient(
        db,
        UserRegisterPatient(
            email="patient2@example.com",
            password="Password123!",
            full_name="Other Patient",
            gender="Female",
        ),
    )
    patient1_profile = patient_user.patient_profile
    patient2_profile = patient2_user.patient_profile

    # 3. Test uploading valid synthetic PDF
    print("[3] Testing valid PDF report upload & SHA-256 hashing...", flush=True)
    synthetic_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Blood Lab Report) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    expected_hash = hashlib.sha256(synthetic_pdf_content).hexdigest()

    upload_file = UploadFile(
        filename="complete_blood_count.pdf",
        file=io.BytesIO(synthetic_pdf_content),
    )

    report = ReportService.save_uploaded_report(
        db=db,
        patient_id=patient1_profile.id,
        file=upload_file,
        report_category="Complete Blood Count",
    )

    assert report.id is not None
    assert report.patient_id == patient1_profile.id
    assert report.original_filename == "complete_blood_count.pdf"
    assert report.file_hash_sha256 == expected_hash
    assert report.file_type == "pdf"
    assert report.ocr_status == OCRStatus.PENDING
    assert os.path.exists(report.file_path)
    print(f"    -> Report uploaded: UUID={report.report_uuid}, SHA-256={report.file_hash_sha256[:16]}...", flush=True)

    # 4. Test uploading valid image report (PNG)
    print("[4] Testing valid PNG image report upload...", flush=True)
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    upload_png = UploadFile(
        filename="lipid_panel.png",
        file=io.BytesIO(png_content),
    )
    report_png = ReportService.save_uploaded_report(
        db=db,
        patient_id=patient1_profile.id,
        file=upload_png,
        report_category="Lipid Profile",
    )
    assert report_png.file_type == "png"
    assert report_png.file_hash_sha256 == hashlib.sha256(png_content).hexdigest()
    print(f"    -> PNG Report uploaded: UUID={report_png.report_uuid}", flush=True)

    # 5. Test File Validation Failures
    print("[5] Testing security file validation rules...", flush=True)

    # A. Invalid file extension (.exe)
    try:
        bad_ext_file = UploadFile(filename="malicious.exe", file=io.BytesIO(b"MZ\x90\x00"))
        ReportService.save_uploaded_report(db, patient1_profile.id, bad_ext_file)
        assert False, "Should have rejected .exe extension"
    except BadRequestException as e:
        print(f"    -> Rejected illegal extension: {e.detail}", flush=True)

    # B. Spoofed PDF (has .pdf extension but lacks %PDF header)
    try:
        spoofed_pdf = UploadFile(filename="fake.pdf", file=io.BytesIO(b"NOT A REAL PDF CONTENT"))
        ReportService.save_uploaded_report(db, patient1_profile.id, spoofed_pdf)
        assert False, "Should have rejected spoofed PDF"
    except BadRequestException as e:
        print(f"    -> Rejected spoofed PDF header: {e.detail}", flush=True)

    # C. Empty file
    try:
        empty_file = UploadFile(filename="empty.pdf", file=io.BytesIO(b""))
        ReportService.save_uploaded_report(db, patient1_profile.id, empty_file)
        assert False, "Should have rejected empty file"
    except BadRequestException as e:
        print(f"    -> Rejected empty file: {e.detail}", flush=True)

    # 6. Test Patient Report Listing
    print("[6] Testing Patient report listing...", flush=True)
    p1_reports = ReportService.list_patient_reports(db, patient1_profile.id)
    assert len(p1_reports) == 2  # The PDF and the PNG
    p2_reports = ReportService.list_patient_reports(db, patient2_profile.id)
    assert len(p2_reports) == 0  # Patient 2 has zero reports
    print(f"    -> Patient 1 has {len(p1_reports)} reports; Patient 2 has {len(p2_reports)} reports (strict isolation).", flush=True)

    # 7. Test Access Authorization
    print("[7] Testing Granular Access Authorization...", flush=True)
    # Patient 1 accessing own report -> True
    assert ReportService.check_user_report_access(db, report, patient_user.id, UserRole.PATIENT) is True

    # Patient 2 accessing Patient 1's report -> False
    assert ReportService.check_user_report_access(db, report, patient2_user.id, UserRole.PATIENT) is False

    # Admin accessing Patient 1's report -> True
    assert ReportService.check_user_report_access(db, report, 999, UserRole.ADMIN) is True
    print("    -> Ownership and access rules properly enforced.", flush=True)

    # 8. Test Local File Integrity & Tamper Detection
    print("[8] Testing SHA-256 File Tamper Detection...", flush=True)
    # Original file check -> Match
    is_intact, current_h, stored_h = ReportService.verify_report_integrity_on_disk(report)
    assert is_intact is True
    assert current_h == stored_h
    print("    -> Untampered file matches SHA-256 checksum perfectly.", flush=True)

    # Simulate tampering: modify 1 byte on disk
    with open(report.file_path, "ab") as f:
        f.write(b"\n// TAMPERED_PAYLOAD_TEST")

    is_intact_tampered, current_h_tampered, _ = ReportService.verify_report_integrity_on_disk(report)
    assert is_intact_tampered is False
    assert current_h_tampered != stored_h
    print(f"    -> Tampering detected! Stored={stored_h[:12]}... Current={current_h_tampered[:12]}...", flush=True)

    # 9. Test Safe Deletion
    print("[9] Testing Safe Report Deletion...", flush=True)
    ReportService.delete_report(db, report.id, patient1_profile.id)
    p1_reports_after = ReportService.list_patient_reports(db, patient1_profile.id)
    assert len(p1_reports_after) == 1  # 1 deleted, 1 remains
    print("    -> Report safely soft-deleted from active listings.", flush=True)

    # Clean up test files
    if os.path.exists(report.file_path):
        os.remove(report.file_path)
    if os.path.exists(report_png.file_path):
        os.remove(report_png.file_path)

    print("\n==================================================", flush=True)
    print("  ALL PHASE 2 REPORT TESTS PASSED 100%!           ", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    test_phase_2_reports()
