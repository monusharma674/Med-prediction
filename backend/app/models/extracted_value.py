import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from app.database.session import Base


class DataSourceEnum(str, enum.Enum):
    OCR = "ocr"
    CORRECTED = "corrected"
    PATIENT_ENTERED = "patient_entered"


class ExtractedMedicalValue(Base):
    __tablename__ = "extracted_medical_values"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("medical_reports.id", ondelete="CASCADE"), nullable=False)

    test_name_raw = Column(String(255), nullable=False)
    test_name_standardized = Column(String(255), index=True, nullable=False)

    value_original = Column(Float, nullable=True)
    value_corrected = Column(Float, nullable=True)

    unit_original = Column(String(50), nullable=True)
    unit_normalized = Column(String(50), nullable=True)

    reference_range = Column(String(100), nullable=True)
    ocr_confidence = Column(Float, nullable=True, default=1.0)

    data_source = Column(Enum(DataSourceEnum), default=DataSourceEnum.OCR, nullable=False)
    is_manually_corrected = Column(Boolean, default=False, nullable=False)

    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    report = relationship("MedicalReport", back_populates="extracted_values")

    @property
    def final_value(self) -> float:
        """Returns corrected value if present, else original value."""
        return self.value_corrected if self.value_corrected is not None else self.value_original
