from typing import List, Optional
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import decode_access_token
from app.core.exceptions import CredentialsException, PermissionDeniedException
from app.database.session import get_db
from app.models.user import User, UserRole, PatientProfile, DoctorProfile
from app.models.audit import AuditLog

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Extracts and validates JWT from request Authorization header."""
    payload = decode_access_token(token)
    if not payload:
        raise CredentialsException("Invalid or expired authentication token")

    email: Optional[str] = payload.get("sub")
    user_id: Optional[int] = payload.get("user_id")
    if not email or user_id is None:
        raise CredentialsException("Token payload missing required identity claims")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise CredentialsException("User associated with token does not exist or is inactive")

    return user


def require_role(*allowed_roles: UserRole):
    """Factory dependency to enforce role-based access control."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException(
                f"Operation requires one of the following roles: {[r.value for r in allowed_roles]}. "
                f"Current role: {current_user.role.value}"
            )
        return current_user

    return role_checker


def get_current_patient(
    current_user: User = Depends(require_role(UserRole.PATIENT)),
    db: Session = Depends(get_db),
) -> PatientProfile:
    """Retrieves the PatientProfile for the authenticated patient user."""
    profile = (
        db.query(PatientProfile)
        .filter(PatientProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise CredentialsException("Patient profile not initialized for this account")
    return profile


def get_current_doctor(
    current_user: User = Depends(require_role(UserRole.DOCTOR)),
    db: Session = Depends(get_db),
) -> DoctorProfile:
    """Retrieves the DoctorProfile for the authenticated doctor user."""
    profile = (
        db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user.id).first()
    )
    if not profile:
        raise CredentialsException("Doctor profile not initialized for this account")
    return profile


def get_current_admin(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
) -> User:
    """Retrieves authenticated admin user."""
    return current_user


def log_audit_event(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[int] = None,
    request: Optional[Request] = None,
    details: Optional[dict] = None,
):
    """Utility helper to record security and operational audit trails in the database."""
    ip_addr = request.client.host if request and request.client else None
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        ip_address=ip_addr,
        details=details or {},
    )
    db.add(audit)
    db.commit()
