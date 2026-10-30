import os
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.report import MedicalReport
from app.models.extracted_value import ExtractedMedicalValue
from app.models.disease_model import DiseaseModel
from app.models.prediction import Prediction
from app.models.audit import AuditLog
from app.services.disease_registry.registry import DiseaseModelRegistry
from app.schemas.prediction import (
    ReportEligibilityResponse,
    DiseaseEligibilityItem,
    MissingFeatureInfo,
    PredictionRequest,
    PredictionResponse,
)

# Standard cross-model feature mapping from extracted standard_name to model feature keys
FEATURE_NAME_MAPPINGS = {
    # Diabetes
    "fasting_blood_glucose": ["glucose_mg_dl"],
    "random_blood_glucose": ["glucose_mg_dl"],
    "systolic_blood_pressure": ["blood_pressure_mmhg", "resting_blood_pressure"],
    "diastolic_blood_pressure": ["blood_pressure_mmhg"],
    "body_mass_index": ["bmi"],
    # Heart disease
    "serum_cholesterol": ["serum_cholesterol"],
    "cholesterol_total": ["serum_cholesterol"],
    "resting_heart_rate": ["max_heart_rate"],
}


class PredictionService:

    @staticmethod
    def get_extracted_features_for_report(db: Session, report_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Gathers verified or extracted values from a report, prioritizing corrected values.
        Returns mapped feature dictionary with values and provenance.
        """
        records = db.query(ExtractedMedicalValue).filter(ExtractedMedicalValue.report_id == report_id).all()
        features = {}

        for rec in records:
            # Prefer manually corrected value if present
            val = rec.final_value
            if val is None:
                continue

            try:
                numeric_val = float(val)
            except (ValueError, TypeError):
                continue

            provenance = "corrected" if rec.is_manually_corrected else "ocr"
            features[rec.test_name_standardized] = {
                "value": numeric_val,
                "unit": rec.unit_normalized or rec.unit_original,
                "provenance": provenance,
            }

            # Map to target model keys
            mapped_keys = FEATURE_NAME_MAPPINGS.get(rec.test_name_standardized, [])
            for mkey in mapped_keys:
                if mkey not in features:
                    features[mkey] = {
                        "value": numeric_val,
                        "unit": rec.unit_normalized or rec.unit_original,
                        "provenance": provenance,
                    }

            # Specific rule: fasting blood sugar > 120 -> binary 1 for heart disease
            if rec.test_name_standardized == "fasting_blood_glucose":
                features["fasting_blood_sugar"] = {
                    "value": 1.0 if numeric_val > 120 else 0.0,
                    "unit": "binary",
                    "provenance": provenance,
                }

        return features

    @staticmethod
    def evaluate_report_eligibility(
        db: Session, patient_id: int, report_id: Optional[int]
    ) -> ReportEligibilityResponse:
        """
        Evaluates which registered disease models are eligible based on the report extracted values.
        """
        extracted_features_map = {}
        if report_id:
            report = (
                db.query(MedicalReport)
                .filter(
                    MedicalReport.id == report_id,
                    MedicalReport.patient_id == patient_id,
                    MedicalReport.is_deleted == False,
                )
                .first()
            )
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Medical report not found or access denied.",
                )
            extracted_features_map = PredictionService.get_extracted_features_for_report(db, report_id)

        available_keys = list(extracted_features_map.keys())
        models_meta = DiseaseModelRegistry.list_available_models()

        diseases_eligibility = []
        for meta in models_meta:
            disease_name = meta["disease_name"]
            chk = DiseaseModelRegistry.check_required_features(disease_name, available_keys)
            diseases_eligibility.append(
                DiseaseEligibilityItem(
                    disease_name=disease_name,
                    display_name=meta.get("display_name", disease_name),
                    is_supported=True,
                    is_eligible=chk["is_eligible"],
                    can_auto_impute=chk["can_auto_impute"],
                    available_features=chk["available_features"],
                    missing_features=chk["missing_features"],
                    strictly_required_missing=chk["strictly_required_missing"],
                )
            )

        return ReportEligibilityResponse(
            report_id=report_id,
            extracted_features=extracted_features_map,
            diseases=diseases_eligibility,
        )

    @staticmethod
    def get_missing_features_for_disease(
        db: Session, patient_id: int, disease_name: str, report_id: Optional[int]
    ) -> List[MissingFeatureInfo]:
        """
        Returns list of missing inputs required to run the specific disease model.
        """
        extracted_features_map = {}
        if report_id:
            extracted_features_map = PredictionService.get_extracted_features_for_report(db, report_id)

        meta = DiseaseModelRegistry.get_model_metadata(disease_name)
        if not meta:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disease model '{disease_name}' not found.",
            )

        required = meta.get("required_features", [])
        units = meta.get("feature_units", {})
        defaults = meta.get("feature_defaults_for_missing", {})

        missing_list = []
        for feat in required:
            if feat not in extracted_features_map:
                missing_list.append(
                    MissingFeatureInfo(
                        feature_name=feat,
                        unit=units.get(feat, ""),
                        display_name=feat.replace("_", " ").title(),
                        default_value=defaults.get(feat),
                    )
                )
        return missing_list

    @staticmethod
    def run_prediction(
        db: Session, patient_id: int, req: PredictionRequest
    ) -> PredictionResponse:
        """
        Executes disease risk prediction, records provenance and saves result to DB.
        """
        # Ensure models in DB
        DiseaseModelRegistry.sync_models_to_db(db)

        # Validate report if provided
        report = None
        if req.report_id:
            report = (
                db.query(MedicalReport)
                .filter(
                    MedicalReport.id == req.report_id,
                    MedicalReport.patient_id == patient_id,
                    MedicalReport.is_deleted == False,
                )
                .first()
            )
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Associated medical report not found or access denied.",
                )

        # Lookup disease model in DB
        db_model = (
            db.query(DiseaseModel)
            .filter(DiseaseModel.disease_name == req.disease_name, DiseaseModel.is_active == True)
            .first()
        )
        if not db_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active model for disease '{req.disease_name}' is not registered.",
            )

        # Prepare inputs: combine extracted features if report provided and user-supplied inputs
        combined_inputs = {}
        provenance = {}

        if req.report_id:
            extracted = PredictionService.get_extracted_features_for_report(db, req.report_id)
            for k, v in extracted.items():
                combined_inputs[k] = v["value"]
                provenance[k] = v["provenance"]

        # Override or supplement with patient inputs
        for k, v in req.inputs.items():
            combined_inputs[k] = float(v)
            prov = req.input_provenance.get(k, "patient_entered")
            provenance[k] = prov

        try:
            pred_result = DiseaseModelRegistry.predict_disease(req.disease_name, combined_inputs)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Model inference failed: {str(e)}",
            )

        # Persist prediction in DB
        prediction = Prediction(
            patient_id=patient_id,
            report_id=req.report_id,
            model_id=db_model.id,
            disease_name=req.disease_name,
            prediction_class=pred_result["prediction_class"],
            model_score=pred_result["model_score"],
            probability=pred_result["probability"],
            is_calibrated_probability=pred_result["is_calibrated_probability"],
            input_features=pred_result["used_features"],
            input_provenance=provenance,
            model_version_used=pred_result["model_version"],
            clinical_disclaimer=pred_result["clinical_disclaimer"],
        )
        db.add(prediction)

        # Audit log
        audit = AuditLog(
            action="DISEASE_PREDICTION_RUN",
            user_id=patient_id,
            resource_type="prediction",
            details={
                "disease_name": req.disease_name,
                "prediction_class": pred_result["prediction_class"],
                "model_score": pred_result["model_score"],
                "report_id": req.report_id,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(prediction)

        return PredictionResponse(
            id=prediction.id,
            disease_name=prediction.disease_name,
            display_name=pred_result["display_name"],
            prediction_class=prediction.prediction_class,
            model_score=prediction.model_score,
            probability=prediction.probability,
            is_calibrated_probability=prediction.is_calibrated_probability,
            score_label=pred_result["score_label"],
            input_features=prediction.input_features,
            input_provenance=prediction.input_provenance,
            model_version_used=prediction.model_version_used,
            clinical_disclaimer=prediction.clinical_disclaimer,
            predicted_at=prediction.predicted_at,
            report_id=prediction.report_id,
        )

    @staticmethod
    def get_patient_history(
        db: Session, patient_id: int, disease_name: Optional[str] = None
    ) -> List[PredictionResponse]:
        """Retrieves prediction history for the authenticated patient."""
        query = db.query(Prediction).filter(Prediction.patient_id == patient_id)
        if disease_name:
            query = query.filter(Prediction.disease_name == disease_name)

        predictions = query.order_by(Prediction.predicted_at.desc()).all()

        results = []
        for p in predictions:
            meta = DiseaseModelRegistry.get_model_metadata(p.disease_name) or {}
            display_name = meta.get("display_name", p.disease_name)
            score_label = "Calibrated Probability" if p.is_calibrated_probability else "Model Risk Score"
            results.append(
                PredictionResponse(
                    id=p.id,
                    disease_name=p.disease_name,
                    display_name=display_name,
                    prediction_class=p.prediction_class,
                    model_score=p.model_score,
                    probability=p.probability,
                    is_calibrated_probability=p.is_calibrated_probability,
                    score_label=score_label,
                    input_features=p.input_features,
                    input_provenance=p.input_provenance,
                    model_version_used=p.model_version_used,
                    clinical_disclaimer=p.clinical_disclaimer,
                    predicted_at=p.predicted_at,
                    report_id=p.report_id,
                )
            )
        return results

    @staticmethod
    def get_prediction_by_id(
        db: Session, patient_id: int, prediction_id: int
    ) -> PredictionResponse:
        """Retrieves single prediction by id ensuring patient ownership."""
        p = (
            db.query(Prediction)
            .filter(Prediction.id == prediction_id, Prediction.patient_id == patient_id)
            .first()
        )
        if not p:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction record not found or access denied.",
            )

        meta = DiseaseModelRegistry.get_model_metadata(p.disease_name) or {}
        display_name = meta.get("display_name", p.disease_name)
        score_label = "Calibrated Probability" if p.is_calibrated_probability else "Model Risk Score"

        return PredictionResponse(
            id=p.id,
            disease_name=p.disease_name,
            display_name=display_name,
            prediction_class=p.prediction_class,
            model_score=p.model_score,
            probability=p.probability,
            is_calibrated_probability=p.is_calibrated_probability,
            score_label=score_label,
            input_features=p.input_features,
            input_provenance=p.input_provenance,
            model_version_used=p.model_version_used,
            clinical_disclaimer=p.clinical_disclaimer,
            predicted_at=p.predicted_at,
            report_id=p.report_id,
        )
