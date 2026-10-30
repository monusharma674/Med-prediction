import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.disease_model import DiseaseModel

ARTIFACTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "artifacts"))


class DiseaseModelRegistry:
    """
    Centralized Model Registry for managing disease-specific machine learning models,
    metadata, feature schemas, missing input requirements, and inference execution.
    """

    _loaded_models: Dict[str, Any] = {}
    _metadata_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_artifacts_dir(cls) -> str:
        return ARTIFACTS_DIR

    @classmethod
    def list_available_models(cls) -> List[Dict[str, Any]]:
        """Lists metadata summaries for all registered disease models."""
        models = []
        if not os.path.exists(ARTIFACTS_DIR):
            return models

        for fname in os.listdir(ARTIFACTS_DIR):
            if fname.endswith("_metadata.json"):
                meta_path = os.path.join(ARTIFACTS_DIR, fname)
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        models.append(meta)
                except Exception as e:
                    print(f"Error loading metadata from {fname}: {e}")
        return models

    @classmethod
    def get_model_metadata(cls, disease_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves complete metadata for a given disease."""
        disease_name = disease_name.lower().strip()
        if disease_name in cls._metadata_cache:
            return cls._metadata_cache[disease_name]

        candidate_paths = [
            os.path.join(ARTIFACTS_DIR, f"{disease_name}_metadata.json"),
            os.path.join(ARTIFACTS_DIR, f"{disease_name.replace('_disease', '')}_metadata.json"),
        ]
        meta_path = next((p for p in candidate_paths if os.path.exists(p)), None)
        if not meta_path:
            return None

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            cls._metadata_cache[disease_name] = meta
            return meta

    @classmethod
    def check_required_features(
        cls, disease_name: str, available_features: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluates whether available features (e.g. from extracted report) satisfy model requirements.
        Returns missing features and eligibility status.
        """
        meta = cls.get_model_metadata(disease_name)
        if not meta:
            return {
                "disease_name": disease_name,
                "is_supported": False,
                "is_eligible": False,
                "missing_features": [],
                "available_features": available_features,
            }

        required = meta.get("required_features", [])
        avail_set = set(available_features)
        missing = [f for f in required if f not in avail_set]

        # Check if the missing features have model default imputations or require patient entry
        defaults = meta.get("feature_defaults_for_missing", {})
        strictly_required = [f for f in missing if f not in defaults]

        return {
            "disease_name": disease_name,
            "display_name": meta.get("display_name", disease_name),
            "is_supported": True,
            "is_eligible": len(strictly_required) == 0,
            "required_features": required,
            "available_features": [f for f in required if f in avail_set],
            "missing_features": missing,
            "strictly_required_missing": strictly_required,
            "can_auto_impute": len(strictly_required) == 0 and len(missing) > 0,
        }

    @classmethod
    def get_missing_features(
        cls, disease_name: str, available_features: List[str]
    ) -> List[Dict[str, Any]]:
        """Returns details of missing features with units and standard descriptions."""
        meta = cls.get_model_metadata(disease_name)
        if not meta:
            return []

        required = meta.get("required_features", [])
        units = meta.get("feature_units", {})
        avail_set = set(available_features)

        missing = []
        for feat in required:
            if feat not in avail_set:
                missing.append({
                    "feature_name": feat,
                    "unit": units.get(feat, ""),
                    "display_name": feat.replace("_", " ").title(),
                })
        return missing

    @classmethod
    def load_model(cls, disease_name: str):
        """Loads and caches the scikit-learn pipeline for the specified disease."""
        disease_name = disease_name.lower().strip()
        if disease_name in cls._loaded_models:
            return cls._loaded_models[disease_name]

        candidate_paths = [
            os.path.join(ARTIFACTS_DIR, f"{disease_name}_model.joblib"),
            os.path.join(ARTIFACTS_DIR, f"{disease_name.replace('_disease', '')}_model.joblib"),
        ]
        model_path = next((p for p in candidate_paths if os.path.exists(p)), None)
        if not model_path:
            raise FileNotFoundError(f"Model artifact not found for disease: {disease_name}")

        model = joblib.load(model_path)
        cls._loaded_models[disease_name] = model
        return model

    @classmethod
    def predict_disease(cls, disease_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes model inference for the given disease.
        Validates feature order, imputes configured defaults where permissible,
        and computes prediction class, raw score/probability, and clinical disclaimer.
        """
        meta = cls.get_model_metadata(disease_name)
        if not meta:
            raise ValueError(f"Unknown disease model: {disease_name}")

        model = cls.load_model(disease_name)
        feature_order = meta.get("feature_order", meta.get("required_features", []))
        defaults = meta.get("feature_defaults_for_missing", {})

        row = {}
        for feat in feature_order:
            if feat in input_data and input_data[feat] is not None:
                try:
                    row[feat] = float(input_data[feat])
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid non-numeric value for feature '{feat}': {input_data[feat]}")
            elif feat in defaults:
                row[feat] = float(defaults[feat])
            else:
                raise ValueError(f"Missing mandatory input feature: '{feat}'")

        # Create single-row DataFrame with exact feature order
        df_input = pd.DataFrame([row], columns=feature_order)

        # Predict
        raw_pred = model.predict(df_input)[0]
        pred_class = "Positive (High Risk)" if raw_pred == 1 else "Negative (Low Risk)"

        score = None
        prob = None
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(df_input)[0]
            prob = float(proba[1])
            score = round(prob, 4)
        elif hasattr(model, "decision_function"):
            decision = model.decision_function(df_input)[0]
            score = float(decision)
        else:
            score = float(raw_pred)

        is_calibrated = meta.get("is_calibrated", False)
        score_label = "Calibrated Probability" if is_calibrated else "Model Risk Score"

        return {
            "disease_name": disease_name,
            "display_name": meta.get("display_name", disease_name),
            "prediction_class": pred_class,
            "model_score": score,
            "probability": prob,
            "score_label": score_label,
            "is_calibrated_probability": is_calibrated,
            "model_version": meta.get("model_version", "1.0.0"),
            "algorithm": meta.get("algorithm", "Unknown"),
            "used_features": row,
            "clinical_disclaimer": (
                "DISCLAIMER: This system is developed solely for educational and research purposes. "
                "The predictions generated represent statistical machine learning model outputs and DO NOT "
                "constitute medical advice, diagnosis, or treatment plans. Consult a certified medical "
                "professional for clinical decisions."
            ),
        }

    @classmethod
    def sync_models_to_db(cls, db: Session):
        """Synchronizes model metadata from disk into the disease_models database table."""
        models_meta = cls.list_available_models()
        for meta in models_meta:
            disease_name = meta.get("disease_name")
            if not disease_name:
                continue

            existing = db.query(DiseaseModel).filter(DiseaseModel.disease_name == disease_name).first()
            model_file = os.path.join(ARTIFACTS_DIR, f"{disease_name}_model.joblib")

            if not existing:
                db_model = DiseaseModel(
                    disease_name=disease_name,
                    display_name=meta.get("display_name", disease_name),
                    model_version=meta.get("model_version", "1.0.0"),
                    algorithm=meta.get("algorithm", "Standard"),
                    model_file_path=model_file,
                    required_features=meta.get("required_features", []),
                    feature_units=meta.get("feature_units", {}),
                    feature_descriptions=meta.get("feature_descriptions", {}),
                    evaluation_metrics=meta.get("evaluation_metrics", {}),
                    is_calibrated=meta.get("is_calibrated", False),
                    dataset_source=meta.get("dataset_source", "UCI Repository"),
                    limitations=meta.get("limitations", ""),
                    is_active=True,
                )
                db.add(db_model)
            else:
                existing.display_name = meta.get("display_name", disease_name)
                existing.model_version = meta.get("model_version", "1.0.0")
                existing.algorithm = meta.get("algorithm", "Standard")
                existing.model_file_path = model_file
                existing.required_features = meta.get("required_features", [])
                existing.feature_units = meta.get("feature_units", {})
                existing.evaluation_metrics = meta.get("evaluation_metrics", {})
                existing.is_calibrated = meta.get("is_calibrated", False)
                existing.dataset_source = meta.get("dataset_source", "UCI Repository")
                existing.limitations = meta.get("limitations", "")
                existing.is_active = True

        db.commit()
