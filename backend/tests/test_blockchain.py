import os
import uuid
import hashlib
import tempfile
import pytest
from app.database.session import Base, engine, SessionLocal
from app.models.user import User, UserRole, PatientProfile
from app.models.report import MedicalReport
from app.models.blockchain import BlockchainRecord
from app.services.blockchain.blockchain_service import BlockchainService


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_blockchain_service_lifecycle(setup_db):
    db = setup_db

    # Create test patient
    user = db.query(User).filter(User.email == "chain_patient@example.com").first()
    if not user:
        user = User(
            email="chain_patient@example.com",
            hashed_password="hashedpassword123",
            role=UserRole.PATIENT,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = PatientProfile(user_id=user.id, full_name="Blockchain Patient", gender="male")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    else:
        profile = user.patient_profile

    # Create temporary file to act as the medical report
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(b"SAMPLE_AUTHENTIC_MEDICAL_REPORT_PDF_BYTES_12345")
        tmp_path = tmp.name

    sha256 = hashlib.sha256(b"SAMPLE_AUTHENTIC_MEDICAL_REPORT_PDF_BYTES_12345").hexdigest()

    report = MedicalReport(
        patient_id=profile.id,
        report_uuid=f"rep-{uuid.uuid4().hex[:12]}",
        original_filename="blood_panel.pdf",
        file_path=tmp_path,
        file_hash_sha256=sha256,
        file_size_bytes=len(b"SAMPLE_AUTHENTIC_MEDICAL_REPORT_PDF_BYTES_12345"),
        file_type="pdf",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # 1. Verification before anchoring -> NOT_ANCHORED
    verify_before = BlockchainService.verify_report_integrity(db, patient_id=profile.id, report_id=report.id)
    assert not verify_before.is_registered_on_chain
    assert verify_before.integrity_status == "NOT_ANCHORED"

    # 2. Register report hash on blockchain
    reg_res = BlockchainService.register_report_hash(db, patient_id=profile.id, report_id=report.id)
    assert reg_res.report_id == report.id
    assert reg_res.file_hash_sha256 == sha256
    assert reg_res.tx_hash.startswith("0x")
    assert reg_res.block_number > 0
    assert reg_res.contract_address.startswith("0x")

    # 3. Verify report integrity against blockchain -> MATCH
    verify_after = BlockchainService.verify_report_integrity(db, patient_id=profile.id, report_id=report.id)
    assert verify_after.is_registered_on_chain
    assert verify_after.is_verified
    assert "MATCH" in verify_after.integrity_status
    assert verify_after.current_disk_hash == sha256
    assert verify_after.blockchain_anchored_hash == sha256

    # 4. Simulate tampering (modify bytes of physical file on disk)
    with open(tmp_path, "wb") as f:
        f.write(b"TAMPERED_MODIFIED_REPORT_BYTES_HACKED")

    verify_tampered = BlockchainService.verify_report_integrity(db, patient_id=profile.id, report_id=report.id)
    assert verify_tampered.is_registered_on_chain
    assert not verify_tampered.is_verified
    assert "MISMATCH" in verify_tampered.integrity_status

    # 5. Check Audit Trail
    audit_trail = BlockchainService.get_audit_trail(db, limit=10)
    assert len(audit_trail) >= 1
    uuids = [a.report_uuid for a in audit_trail]
    assert report.report_uuid in uuids

    # Cleanup temp file
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
