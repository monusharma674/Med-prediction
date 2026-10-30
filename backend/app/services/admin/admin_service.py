from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole, PatientProfile, DoctorProfile
from app.models.report import MedicalReport
from app.models.prediction import Prediction
from app.models.blockchain import BlockchainRecord
from app.models.sharing import SharedReport
from app.models.audit import AuditLog
from app.schemas.admin import (
    AdminStatsResponse,
    AdminUserItem,
    AdminAuditLogItem,
)


class AdminService:

    @staticmethod
    def get_system_stats(db: Session) -> AdminStatsResponse:
        """Computes live system dashboard metrics."""
        total_patients = db.query(User).filter(User.role == UserRole.PATIENT).count()
        total_doctors = db.query(User).filter(User.role == UserRole.DOCTOR).count()
        total_reports = db.query(MedicalReport).filter(MedicalReport.is_deleted == False).count()
        total_predictions = db.query(Prediction).count()
        total_blockchain_records = db.query(BlockchainRecord).count()
        total_active_shares = db.query(SharedReport).filter(SharedReport.is_active == True).count()

        return AdminStatsResponse(
            total_patients=total_patients,
            total_doctors=total_doctors,
            total_reports=total_reports,
            total_predictions=total_predictions,
            total_blockchain_records=total_blockchain_records,
            total_active_shares=total_active_shares,
        )

    @staticmethod
    def get_users_list(db: Session, role: Optional[str] = None) -> List[AdminUserItem]:
        """Lists users with their specific role profile names."""
        query = db.query(User)
        if role:
            query = query.filter(User.role == role)

        users = query.order_by(User.created_at.desc()).all()
        items = []
        for u in users:
            name = u.email
            if u.patient_profile:
                name = u.patient_profile.full_name
            elif u.doctor_profile:
                name = u.doctor_profile.full_name

            items.append(
                AdminUserItem(
                    id=u.id,
                    email=u.email,
                    role=u.role.value if hasattr(u.role, "value") else str(u.role),
                    is_active=u.is_active,
                    full_name=name,
                    created_at=u.created_at,
                )
            )
        return items

    @staticmethod
    def toggle_user_status(db: Session, user_id: int, is_active: bool, admin_id: int) -> AdminUserItem:
        """Enables or disables user account access."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.is_active = is_active

        # Audit log
        audit = AuditLog(
            action="ADMIN_TOGGLE_USER_STATUS",
            user_id=admin_id,
            resource_type="user",
            resource_id=str(user.id),
            details={"target_user_email": user.email, "new_active_status": is_active},
        )
        db.add(audit)
        db.commit()
        db.refresh(user)

        name = user.email
        if user.patient_profile:
            name = user.patient_profile.full_name
        elif user.doctor_profile:
            name = user.doctor_profile.full_name

        return AdminUserItem(
            id=user.id,
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            is_active=user.is_active,
            full_name=name,
            created_at=user.created_at,
        )

    @staticmethod
    def get_audit_logs(
        db: Session, limit: int = 100, action: Optional[str] = None
    ) -> List[AdminAuditLogItem]:
        """Chronological audit trail for system compliance."""
        query = db.query(AuditLog)
        if action:
            query = query.filter(AuditLog.action == action)

        logs = query.order_by(AuditLog.logged_at.desc()).limit(limit).all()

        items = []
        for l in logs:
            user_email = l.user.email if l.user else None
            items.append(
                AdminAuditLogItem(
                    id=l.id,
                    user_id=l.user_id,
                    user_email=user_email,
                    action=l.action,
                    resource_type=l.resource_type,
                    resource_id=l.resource_id,
                    details=l.details,
                    logged_at=l.logged_at,
                )
            )
        return items
