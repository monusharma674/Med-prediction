from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship
from app.database.session import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(Integer, ForeignKey("medical_reports.id", ondelete="SET NULL"), nullable=True)
    model_id = Column(Integer, ForeignKey("disease_models.id", ondelete="RESTRICT"), nullable=False)

    disease_name = Column(String(100), index=True, nullable=False)
    prediction_class = Column(String(50), nullable=False)  # "Positive (High Risk)", "Negative (Low Risk)"
    model_score = Column(Float, nullable=False)  # continuous score or probability
    probability = Column(Float, nullable=True)
    is_calibrated_probability = Column(Boolean, default=False, nullable=False)

    # Input tracking
    input_features = Column(JSON, nullable=False)  # {"glucose": 140, "bmi": 28.5, ...}
    input_provenance = Column(JSON, nullable=False)  # {"glucose": "ocr", "bmi": "patient_entered"}

    model_version_used = Column(String(50), nullable=False)
    clinical_disclaimer = Column(
        Text,
        default="This tool is developed for educational and research purposes. It is not a substitute for professional medical diagnosis or treatment.",
        nullable=False,
    )
    predicted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("PatientProfile", back_populates="predictions")
    report = relationship("MedicalReport", back_populates="predictions")
    model = relationship("DiseaseModel", back_populates="predictions")
