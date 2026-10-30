import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Date,
)
from sqlalchemy.orm import relationship
from app.database.session import Base


class OCRStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False)
    report_uuid = Column(String(64), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_hash_sha256 = Column(String(64), index=True, nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, png, jpg, jpeg
    file_size_bytes = Column(Integer, nullable=False)
    report_category = Column(String(100), nullable=True, default="General Blood Report")
    report_date = Column(Date, nullable=True)

    ocr_status = Column(Enum(OCRStatus), default=OCRStatus.PENDING, nullable=False)
    ocr_raw_text = Column(String, nullable=True)

    blockchain_registered = Column(Boolean, default=False, nullable=False)
    blockchain_tx_hash = Column(String(128), nullable=True)

    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    patient = relationship("PatientProfile", back_populates="reports")
    extracted_values = relationship(
        "ExtractedMedicalValue", back_populates="report", cascade="all, delete-orphan"
    )
    predictions = relationship("Prediction", back_populates="report")
    shares = relationship("SharedReport", back_populates="report", cascade="all, delete-orphan")
    blockchain_record = relationship(
        "BlockchainRecord", back_populates="report", uselist=False, cascade="all, delete-orphan"
    )
