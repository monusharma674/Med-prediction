from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship
from app.database.session import Base


class DiseaseModel(Base):
    __tablename__ = "disease_models"

    id = Column(Integer, primary_key=True, index=True)
    disease_name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    model_version = Column(String(50), nullable=False)
    algorithm = Column(String(100), nullable=False)
    model_file_path = Column(String(512), nullable=False)

    required_features = Column(JSON, nullable=False)
    feature_units = Column(JSON, nullable=False)
    feature_descriptions = Column(JSON, nullable=True)

    evaluation_metrics = Column(JSON, nullable=False)
    is_calibrated = Column(Boolean, default=False, nullable=False)
    dataset_source = Column(String(255), nullable=False)
    limitations = Column(Text, nullable=True)

    training_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    predictions = relationship("Prediction", back_populates="model")
