import uuid
import pytest
from app.database.session import Base, engine, SessionLocal
from app.models.user import User, UserRole, PatientProfile
from app.models.report import MedicalReport
from app.models.extracted_value import ExtractedMedicalValue, DataSourceEnum
from app.services.disease_registry.registry import DiseaseModelRegistry
from app.services.predictions.prediction_service import PredictionService
from app.schemas.prediction import PredictionRequest


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_registry_lists_models(setup_db):
    models = DiseaseModelRegistry.list_available_models()
    names = [m["disease_name"] for m in models]
    assert "diabetes" in names
    assert "heart_disease" in names


def test_diabetes_metadata(setup_db):
    meta = DiseaseModelRegistry.get_model_metadata("diabetes")
    assert meta is not None
    assert "glucose_mg_dl" in meta["required_features"]
    assert "bmi" in meta["required_features"]
    assert meta["evaluation_metrics"]["accuracy"] > 0.65


def test_heart_disease_metadata(setup_db):
    meta = DiseaseModelRegistry.get_model_metadata("heart_disease")
    assert meta is not None
    assert "serum_cholesterol" in meta["required_features"]
    assert "resting_blood_pressure" in meta["required_features"]
    assert meta["evaluation_metrics"]["roc_auc"] > 0.85


def test_prediction_service_flow(setup_db):
    db = setup_db

    # Create test patient
    patient_user = db.query(User).filter(User.email == "ml_patient@example.com").first()
    if not patient_user:
        patient_user = User(
            email="ml_patient@example.com",
            hashed_password="hashedpassword123",
            role=UserRole.PATIENT,
            is_active=True,
        )
        db.add(patient_user)
        db.commit()
        db.refresh(patient_user)

        profile = PatientProfile(user_id=patient_user.id, full_name="ML Test Patient", gender="female")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    else:
        profile = patient_user.patient_profile

    # Create dummy report with extracted glucose
    report = MedicalReport(
        patient_id=profile.id,
        report_uuid=f"uuid-{uuid.uuid4().hex[:12]}",
        original_filename="lab_test_report.pdf",
        file_path="mock/path/lab.pdf",
        file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_size_bytes=1024,
        file_type="pdf",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    val = ExtractedMedicalValue(
        report_id=report.id,
        test_name_raw="Fasting Glucose: 165 mg/dL",
        test_name_standardized="fasting_blood_glucose",
        value_original=165.0,
        unit_original="mg/dL",
        unit_normalized="mg/dL",
        ocr_confidence=0.98,
        data_source=DataSourceEnum.OCR,
        is_manually_corrected=False,
    )
    db.add(val)
    db.commit()

    # 1. Test Eligibility
    eligibility = PredictionService.evaluate_report_eligibility(db, patient_id=profile.id, report_id=report.id)
    assert eligibility.report_id == report.id
    assert "glucose_mg_dl" in eligibility.extracted_features

    # 2. Test Missing features
    missing = PredictionService.get_missing_features_for_disease(
        db, patient_id=profile.id, disease_name="diabetes", report_id=report.id
    )
    missing_names = [m.feature_name for m in missing]
    assert "glucose_mg_dl" not in missing_names  # Already extracted!
    assert "bmi" in missing_names
    assert "age" in missing_names

    # 3. Run Diabetes Prediction with OCR + Patient Entered features
    pred_req = PredictionRequest(
        disease_name="diabetes",
        report_id=report.id,
        inputs={
            "pregnancies": 2,
            "blood_pressure_mmhg": 85,
            "skin_thickness_mm": 28,
            "insulin_uiu_ml": 140,
            "bmi": 34.5,
            "diabetes_pedigree_function": 0.65,
            "age": 48,
        },
        input_provenance={
            "pregnancies": "patient_entered",
            "blood_pressure_mmhg": "patient_entered",
            "bmi": "patient_entered",
            "age": "patient_entered",
        },
    )

    pred_res = PredictionService.run_prediction(db, patient_id=profile.id, req=pred_req)
    assert pred_res.id is not None
    assert pred_res.disease_name == "diabetes"
    assert pred_res.prediction_class in ["Positive (High Risk)", "Negative (Low Risk)"]
    assert pred_res.input_provenance["glucose_mg_dl"] == "ocr"
    assert pred_res.input_provenance["bmi"] == "patient_entered"
    assert "DISCLAIMER" in pred_res.clinical_disclaimer

    # 4. Run Heart Disease Prediction
    heart_req = PredictionRequest(
        disease_name="heart_disease",
        report_id=None,
        inputs={
            "age": 58,
            "sex": 1,
            "chest_pain_type": 4,
            "resting_blood_pressure": 140,
            "serum_cholesterol": 280,
            "fasting_blood_sugar": 1,
            "resting_ecg": 2,
            "max_heart_rate": 120,
            "exercise_induced_angina": 1,
            "st_depression": 2.4,
            "st_slope": 2,
            "num_major_vessels": 2,
            "thalassemia": 7,
        },
        input_provenance={"age": "patient_entered", "serum_cholesterol": "patient_entered"},
    )
    heart_res = PredictionService.run_prediction(db, patient_id=profile.id, req=heart_req)
    assert heart_res.disease_name == "heart_disease"
    assert heart_res.model_score >= 0.0

    # 5. History check
    history = PredictionService.get_patient_history(db, patient_id=profile.id)
    assert len(history) >= 2
    history_ids = [h.id for h in history]
    assert pred_res.id in history_ids
    assert heart_res.id in history_ids
