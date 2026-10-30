from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship
from app.database.session import Base


class SharedReport(Base):
    __tablename__ = "shared_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(Integer, ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(String(500), nullable=True)

    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Optional expiry
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    patient = relationship("PatientProfile", back_populates="shared_permissions")
    doctor = relationship("DoctorProfile", back_populates="received_shares")
    report = relationship("MedicalReport", back_populates="shares")
