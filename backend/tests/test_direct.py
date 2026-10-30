import sys
import os
import time

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base
from app.models.user import User, UserRole, PatientProfile, DoctorProfile
from app.models.report import MedicalReport, OCRStatus
from app.models.extracted_value import ExtractedMedicalValue, DataSourceEnum
from app.schemas.user import UserRegisterPatient, UserRegisterDoctor, UserLogin
from app.services.authentication.auth_service import AuthService
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.exceptions import DuplicateResourceException, CredentialsException, PermissionDeniedException

def test_phase_1():
    print("==================================================", flush=True)
    print("   AI MEDICAL REPORT SYSTEM: PHASE 1 TEST SUITE   ", flush=True)
    print("==================================================", flush=True)

    # 1. Setup isolated in-memory DB
    print("[1] Initializing in-memory SQLite database...", flush=True)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    print("    -> Database schema initialized with all 11 tables.", flush=True)

    # 2. Test Password Hashing and Truncation
    print("[2] Testing bcrypt password hashing and verification...", flush=True)
    raw_pwd = "MySecretSecurePassword123!"
    hashed = get_password_hash(raw_pwd)
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    print("    -> Password hashing and verification passed.", flush=True)

    # 3. Test JWT Creation and Decoding
    print("[3] Testing JWT creation and role claims...", flush=True)
    token = create_access_token(subject="patient@test.com", role="patient", user_id=42)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "patient@test.com"
    assert payload["role"] == "patient"
    assert payload["user_id"] == 42
    print(f"    -> Token payload verified: sub={payload['sub']}, role={payload['role']}, user_id={payload['user_id']}", flush=True)

    # 4. Test Patient Registration
    print("[4] Testing Patient Registration Service...", flush=True)
    patient_in = UserRegisterPatient(
        email="patient@hospital.org",
        password="PatientPassword123!",
        full_name="Aarav Sharma",
        date_of_birth="1992-08-20",
        gender="Male",
        phone="+91 9876543210",
        blood_group="B+",
    )
    user_p = AuthService.register_patient(db, patient_in)
    assert user_p.id is not None
    assert user_p.email == "patient@hospital.org"
    assert user_p.role == UserRole.PATIENT
    assert user_p.patient_profile is not None
    assert user_p.patient_profile.full_name == "Aarav Sharma"
    assert user_p.patient_profile.blood_group == "B+"
    print(f"    -> Patient registered: ID={user_p.id}, FullName={user_p.patient_profile.full_name}", flush=True)

    # 5. Test Duplicate Email Rejection
    print("[5] Testing duplicate email rejection...", flush=True)
    try:
        AuthService.register_patient(db, patient_in)
        assert False, "Should have raised DuplicateResourceException"
    except DuplicateResourceException as e:
        print(f"    -> Duplicate correctly rejected: {e.detail}", flush=True)

    # 6. Test Doctor Registration
    print("[6] Testing Doctor Registration Service...", flush=True)
    doc_in = UserRegisterDoctor(
        email="doctor@hospital.org",
        password="DoctorPassword123!",
        full_name="Dr. Priya Patel",
        specialization="Cardiology",
        license_number="MED-123456",
        hospital="City Memorial Hospital",
        phone="+91 9123456780",
    )
    user_d = AuthService.register_doctor(db, doc_in)
    assert user_d.id is not None
    assert user_d.email == "doctor@hospital.org"
    assert user_d.role == UserRole.DOCTOR
    assert user_d.doctor_profile is not None
    assert user_d.doctor_profile.specialization == "Cardiology"
    print(f"    -> Doctor registered: ID={user_d.id}, Specialization={user_d.doctor_profile.specialization}", flush=True)

    # 7. Test Authentication & Token Issuance
    print("[7] Testing AuthService.authenticate_user...", flush=True)
    auth_token = AuthService.authenticate_user(db, "patient@hospital.org", "PatientPassword123!")
    assert auth_token.access_token is not None
    assert auth_token.role == UserRole.PATIENT
    assert auth_token.full_name == "Aarav Sharma"

    # Test bad password
    try:
        AuthService.authenticate_user(db, "patient@hospital.org", "BadPassword!")
        assert False, "Should have raised CredentialsException"
    except CredentialsException:
        print("    -> Invalid password correctly raised CredentialsException (401)", flush=True)

    # 8. Test Admin Seed
    print("[8] Testing Admin Seed creation...", flush=True)
    admin = AuthService.seed_admin(db, "admin@medicalai.local", "AdminSecurePassword123!", "System Administrator")
    assert admin.id is not None
    assert admin.role == UserRole.ADMIN
    print(f"    -> Admin seed verified: ID={admin.id}, Role={admin.role.value}", flush=True)

    # 9. Test Data Provenance & Extracted Medical Values
    print("[9] Testing Medical Report & Extracted Value Provenance Models...", flush=True)
    report = MedicalReport(
        patient_id=user_p.patient_profile.id,
        report_uuid="uuid-report-test-123",
        original_filename="sample_blood_report.pdf",
        file_path="./uploads/test.pdf",
        file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_type="pdf",
        file_size_bytes=1048576,
        report_category="Complete Blood Count & Metabolic Panel",
        ocr_status=OCRStatus.COMPLETED,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    val_ocr = ExtractedMedicalValue(
        report_id=report.id,
        test_name_raw="Fasting Blood Glucose",
        test_name_standardized="fasting_glucose_mg_dl",
        value_original=142.0,
        unit_original="mg/dL",
        unit_normalized="mg/dL",
        reference_range="70 - 99 mg/dL",
        ocr_confidence=0.96,
        data_source=DataSourceEnum.OCR,
        is_manually_corrected=False,
    )
    db.add(val_ocr)
    db.commit()
    db.refresh(val_ocr)

    assert val_ocr.final_value == 142.0
    assert val_ocr.data_source == DataSourceEnum.OCR

    # Now simulate patient manual correction
    val_ocr.value_corrected = 140.0
    val_ocr.data_source = DataSourceEnum.CORRECTED
    val_ocr.is_manually_corrected = True
    db.commit()
    db.refresh(val_ocr)

    assert val_ocr.final_value == 140.0
    assert val_ocr.value_original == 142.0  # Original preserved!
    assert val_ocr.is_manually_corrected is True
    print("    -> Provenance tracking verified: original preserved, corrected value honored.", flush=True)

    print("\n==================================================", flush=True)
    print("   ALL 9 TEST MODULES PASSED 100% SUCCESSFULLY!   ", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    test_phase_1()
