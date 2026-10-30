import pytest
from fastapi import HTTPException
from app.database.session import Base, engine, SessionLocal
from app.models.user import User, UserRole, PatientProfile
from app.services.admin.admin_service import AdminService
from app.api.v1.admin import require_admin


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_admin_service_and_rbac(setup_db):
    db = setup_db

    # 1. Create Admin User
    admin_user = db.query(User).filter(User.email == "admin_test@medicalai.local").first()
    if not admin_user:
        admin_user = User(
            email="admin_test@medicalai.local",
            hashed_password="hashedpassword123",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    # 2. Create Regular Patient
    regular_user = db.query(User).filter(User.email == "regular_patient@example.com").first()
    if not regular_user:
        regular_user = User(
            email="regular_patient@example.com",
            hashed_password="hashedpassword123",
            role=UserRole.PATIENT,
            is_active=True,
        )
        db.add(regular_user)
        db.commit()
        db.refresh(regular_user)

    # 3. RBAC Check: require_admin succeeds for admin
    validated_admin = require_admin(admin_user)
    assert validated_admin.id == admin_user.id

    # 4. RBAC Check: require_admin raises 403 Forbidden for regular patient
    with pytest.raises(HTTPException) as exc_info:
        require_admin(regular_user)
    assert exc_info.value.status_code == 403

    # 5. Admin System Stats
    stats = AdminService.get_system_stats(db)
    assert stats.total_patients >= 1
    assert stats.total_reports >= 0

    # 6. Admin User Listing
    users = AdminService.get_users_list(db)
    assert len(users) >= 2
    emails = [u.email for u in users]
    assert "admin_test@medicalai.local" in emails
    assert "regular_patient@example.com" in emails

    # 7. Admin Toggle User Status
    toggled = AdminService.toggle_user_status(db, user_id=regular_user.id, is_active=False, admin_id=admin_user.id)
    assert toggled.is_active is False

    toggled_back = AdminService.toggle_user_status(db, user_id=regular_user.id, is_active=True, admin_id=admin_user.id)
    assert toggled_back.is_active is True

    # 8. Admin Audit Logs
    logs = AdminService.get_audit_logs(db, limit=20)
    assert len(logs) >= 1
    actions = [l.action for l in logs]
    assert "ADMIN_TOGGLE_USER_STATUS" in actions
