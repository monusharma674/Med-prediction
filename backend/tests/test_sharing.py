import uuid
import pytest
from fastapi import HTTPException
from app.database.session import Base, engine, SessionLocal
from app.models.user import User, UserRole, PatientProfile, DoctorProfile
from app.models.report import MedicalReport
from app.models.sharing import SharedReport
from app.models.audit import AuditLog
from app.services.sharing.sharing_service import SharingService
from app.schemas.sharing import GrantShareRequest


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_sharing_service_lifecycle(setup_db):
    db = setup_db

    # 1. Create Patient
    patient_user = db.query(User).filter(User.email == "sharing_patient@example.com").first()
    if not patient_user:
        patient_user = User(
            email="sharing_patient@example.com",
            hashed_password="hashedpassword123",
            role=UserRole.PATIENT,
            is_active=True,
        )
        db.add(patient_user)
        db.commit()
        db.refresh(patient_user)

        p_profile = PatientProfile(user_id=patient_user.id, full_name="Alice Patient", gender="female")
        db.add(p_profile)
        db.commit()
        db.refresh(p_profile)
    else:
        p_profile = patient_user.patient_profile

    # 2. Create Authorized Doctor
    doc_user = db.query(User).filter(User.email == "dr_smith@example.com").first()
    if not doc_user:
        doc_user = User(
            email="dr_smith@example.com",
            hashed_password="hashedpassword123",
            role=UserRole.DOCTOR,
            is_active=True,
        )
        db.add(doc_user)
        db.commit()
        db.refresh(doc_user)

        d_profile = DoctorProfile(
            user_id=doc_user.id,
            full_name="Dr. Jane Smith",
            license_number="LIC-12345",
            specialization="Endocrinology",
            hospital="City Health Hospital",
        )
        db.add(d_profile)
        db.commit()
        db.refresh(d_profile)
    else:
        d_profile = doc_user.doctor_profile

    # 3. Create Unauthorized Doctor
    unauth_doc = db.query(User).filter(User.email == "dr_unauth@example.com").first()
    if not unauth_doc:
        unauth_doc = User(
            email="dr_unauth@example.com",
            hashed_password="hashedpassword123",
            role=UserRole.DOCTOR,
            is_active=True,
        )
        db.add(unauth_doc)
        db.commit()
        db.refresh(unauth_doc)

        unauth_profile = DoctorProfile(
            user_id=unauth_doc.id,
            full_name="Dr. Unauth Stranger",
            license_number="LIC-99999",
            specialization="Cardiology",
        )
        db.add(unauth_profile)
        db.commit()
        db.refresh(unauth_profile)
    else:
        unauth_profile = unauth_doc.doctor_profile

    # 4. Create Medical Report for Patient
    report = MedicalReport(
        patient_id=p_profile.id,
        report_uuid=f"rep-{uuid.uuid4().hex[:12]}",
        original_filename="complete_blood_count.pdf",
        file_path="mock/path/cbc.pdf",
        file_hash_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        file_size_bytes=2048,
        file_type="pdf",
        report_category="Complete Blood Count",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # 5. Check Doctor Directory
    directory = SharingService.get_doctor_directory(db)
    doc_emails = [d.email for d in directory]
    assert "dr_smith@example.com" in doc_emails

    # 6. Patient grants share to Dr. Smith
    grant_req = GrantShareRequest(
        report_id=report.id,
        doctor_id=d_profile.id,
        notes="Please review my recent blood count panel before my follow-up appointment.",
    )
    share_res = SharingService.grant_share(db, patient_id=p_profile.id, req=grant_req)
    assert share_res.id is not None
    assert share_res.is_active is True
    assert share_res.doctor_email == "dr_smith@example.com"
    assert share_res.patient_name == "Alice Patient"

    # 7. Dr. Smith queries shared reports -> report is present
    doc_reports = SharingService.get_doctor_shared_reports(db, doctor_id=d_profile.id)
    shared_report_ids = [r.report_id for r in doc_reports]
    assert report.id in shared_report_ids

    # 8. Dr. Smith accesses report details -> Authorized (200 OK)
    detail_res = SharingService.get_doctor_report_details(db, doctor_id=d_profile.id, report_id=report.id)
    assert detail_res.report_id == report.id
    assert detail_res.patient_name == "Alice Patient"

    # 9. Dr. Unauth attempts to access report details -> 403 Forbidden!
    with pytest.raises(HTTPException) as exc_info:
        SharingService.get_doctor_report_details(db, doctor_id=unauth_profile.id, report_id=report.id)
    assert exc_info.value.status_code == 403

    # 10. Patient revokes Dr. Smith's access
    SharingService.revoke_share(db, patient_id=p_profile.id, share_id=share_res.id)

    # 11. Dr. Smith attempts to access report details after revocation -> 403 Forbidden!
    with pytest.raises(HTTPException) as exc_info_revoked:
        SharingService.get_doctor_report_details(db, doctor_id=d_profile.id, report_id=report.id)
    assert exc_info_revoked.value.status_code == 403
