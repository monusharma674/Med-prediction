from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.services.disease_registry.registry import DiseaseModelRegistry
from app.services.predictions.prediction_service import PredictionService
from app.schemas.prediction import (
    ReportEligibilityResponse,
    MissingFeatureInfo,
    PredictionRequest,
    PredictionResponse,
)

router = APIRouter()


@router.get("/models", response_model=List[dict])
def list_available_models():
    """Returns available disease prediction models and their clinical metadata."""
    return DiseaseModelRegistry.list_available_models()


@router.get("/eligibility", response_model=ReportEligibilityResponse)
def check_report_eligibility(
    report_id: Optional[int] = Query(None, description="Optional medical report ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evaluates which disease prediction models can be run with the currently extracted report values.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    return PredictionService.evaluate_report_eligibility(db, patient_id=patient_id, report_id=report_id)


@router.get("/missing-inputs", response_model=List[MissingFeatureInfo])
def get_missing_features(
    disease_name: str = Query(..., description="Disease model identifier, e.g. diabetes or heart_disease"),
    report_id: Optional[int] = Query(None, description="Optional medical report ID to check extracted values"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns list of required input parameters not present in report, with units and default values.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    return PredictionService.get_missing_features_for_disease(
        db, patient_id=patient_id, disease_name=disease_name, report_id=report_id
    )


@router.post("/run", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def run_disease_prediction(
    req: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Runs the selected machine learning disease prediction model with strict input provenance tracking.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    return PredictionService.run_prediction(db, patient_id=patient_id, req=req)


@router.get("/history", response_model=List[PredictionResponse])
def get_prediction_history(
    disease_name: Optional[str] = Query(None, description="Optional filter by disease name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves chronological prediction history for the authenticated patient.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    return PredictionService.get_patient_history(db, patient_id=patient_id, disease_name=disease_name)


@router.get("/{prediction_id}", response_model=PredictionResponse)
def get_prediction_details(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a single prediction run by ID with its feature inputs and provenance.
    """
    patient_id = current_user.patient_profile.id if current_user.patient_profile else current_user.id
    return PredictionService.get_prediction_by_id(db, patient_id=patient_id, prediction_id=prediction_id)
