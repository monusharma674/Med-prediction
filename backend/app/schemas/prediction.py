from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class MissingFeatureInfo(BaseModel):
    feature_name: str
    unit: str
    display_name: str
    default_value: Optional[float] = None


class DiseaseEligibilityItem(BaseModel):
    disease_name: str
    display_name: str
    is_supported: bool
    is_eligible: bool
    can_auto_impute: bool
    available_features: List[str]
    missing_features: List[str]
    strictly_required_missing: List[str]


class ReportEligibilityResponse(BaseModel):
    report_id: Optional[int]
    extracted_features: Dict[str, Any]
    diseases: List[DiseaseEligibilityItem]


class PredictionRequest(BaseModel):
    disease_name: str
    report_id: Optional[int] = None
    inputs: Dict[str, float] = Field(..., description="Feature values for prediction")
    input_provenance: Dict[str, str] = Field(
        default_factory=dict,
        description="Source of each input: 'ocr', 'corrected', or 'patient_entered'"
    )


class PredictionResponse(BaseModel):
    id: int
    disease_name: str
    display_name: str
    prediction_class: str
    model_score: float
    probability: Optional[float] = None
    is_calibrated_probability: bool
    score_label: str
    input_features: Dict[str, Any]
    input_provenance: Dict[str, str]
    model_version_used: str
    clinical_disclaimer: str
    predicted_at: datetime
    report_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
