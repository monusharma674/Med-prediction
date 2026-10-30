from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user, get_current_admin
from app.models.user import User, UserRole
from app.services.admin.admin_service import AdminService
from app.schemas.admin import (
    AdminStatsResponse,
    AdminUserItem,
    AdminAuditLogItem,
)

router = APIRouter()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to access this endpoint.",
        )
    return current_user


@router.get("/stats", response_model=AdminStatsResponse)
def get_system_statistics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Returns aggregated system metrics across patients, doctors, reports, and models."""
    return AdminService.get_system_stats(db)


@router.get("/users", response_model=List[AdminUserItem])
def list_system_users(
    role: Optional[str] = Query(None, description="Optional filter by role (patient, doctor, admin)"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Lists all registered user accounts with status and roles."""
    return AdminService.get_users_list(db, role=role)


@router.patch("/users/{user_id}/status", response_model=AdminUserItem)
def toggle_user_status(
    user_id: int,
    is_active: bool = Query(..., description="Target active state for the user"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Enables or disables a user account."""
    return AdminService.toggle_user_status(db, user_id=user_id, is_active=is_active, admin_id=admin.id)


@router.get("/audit-logs", response_model=List[AdminAuditLogItem])
def get_system_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = Query(None, description="Optional filter by action type"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Retrieves immutable system audit records for security and compliance monitoring."""
    return AdminService.get_audit_logs(db, limit=limit, action=action)
