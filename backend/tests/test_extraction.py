import os
import sys
import io
import fitz

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import UploadFile

from app.database.session import Base
from app.models.user import User, UserRole, PatientProfile
from app.models.report import MedicalReport, OCRStatus
from app.models.extracted_value import ExtractedMedicalValue, DataSourceEnum
from app.schemas.user import UserRegisterPatient
from app.services.authentication.auth_service import AuthService
from app.services.reports.report_service import ReportService
from app.services.extraction.pdf_extractor import PDFExtractor
from app.services.extraction.value_parser import MedicalValueParser
from app.services.validation.normalizer import MedicalNormalizer


def create_sample_medical_pdf(file_path: str):
    """Generates a realistic clinical PDF with standard lab parameters."""
    doc = fitz.open()
    page = doc.new_page()

    report_text = """
    METROPOLIS DIAGNOSTIC CLINICAL LABORATORIES
    PATIENT NAME: Aarav Sharma    AGE: 34 YRS    GENDER: Male
    DATE OF COLLECTION: 2026-10-25

    BIOCHEMISTRY & METABOLIC INVESTIGATION REPORT
    -----------------------------------------------------------------------------
    TEST DESCRIPTION               RESULT        UNIT        REFERENCE INTERVAL
    -----------------------------------------------------------------------------
    Fasting Blood Sugar (FBS)      142.0         mg/dL       70.0 - 99.0
    Glycated Hemoglobin (HbA1c)    7.4           %           4.0 - 5.6
    Total Cholesterol              215.0         mg/dL       < 200.0
    HDL Cholesterol                38.0          mg/dL       > 40.0
    LDL Cholesterol                135.0         mg/dL       < 100.0
    Triglycerides                  185.0         mg/dL       < 150.0
    Serum Creatinine               1.15          mg/dL       0.70 - 1.30
    Blood Urea Nitrogen (BUN)      16.5          mg/dL       7.0 - 20.0
    Systolic Blood Pressure        138.0         mmHg        90 - 120
    -----------------------------------------------------------------------------
    Notes: Fasting blood glucose and HbA1c indicative of hyperglycemic profile.
    """
    page.insert_text((50, 60), report_text, fontsize=10)
    doc.save(file_path)
    doc.close()


def test_phase_3_and_4():
    print("==================================================", flush=True)
    print(" AI MEDICAL SYSTEM: PHASES 3 & 4 TEST SUITE       ", flush=True)
    print(" OCR EXTRACTION, VALIDATION & NORMALIZATION       ", flush=True)
    print("==================================================", flush=True)

    # 1. Setup in-memory DB
    print("[1] Initializing isolated database session...", flush=True)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    patient_user = AuthService.register_patient(
        db,
        UserRegisterPatient(
            email="patient.ocr@example.com",
            password="Password123!",
            full_name="Aarav Sharma",
        ),
    )
    patient = patient_user.patient_profile

    # 2. Generate sample PDF file
    print("[2] Creating realistic clinical PDF with PyMuPDF...", flush=True)
    test_pdf_path = "./backend/uploads/sample_test_report.pdf"
    os.makedirs("./backend/uploads", exist_ok=True)
    create_sample_medical_pdf(test_pdf_path)
    assert os.path.exists(test_pdf_path)
    print("    -> Realistic test PDF generated successfully.", flush=True)

    # 3. Test PDF text extraction
    print("[3] Testing PDF text extraction via PyMuPDF...", flush=True)
    extracted_text, is_digital, conf = PDFExtractor.extract_text_from_pdf(test_pdf_path)
    assert is_digital is True
    assert "Fasting Blood Sugar" in extracted_text
    assert "HbA1c" in extracted_text
    print(f"    -> Extracted {len(extracted_text)} characters. Digital={is_digital}, Confidence={conf}", flush=True)

    # 4. Test Medical Parameter Parser
    print("[4] Testing MedicalValueParser and alias mapping...", flush=True)
    parsed = MedicalValueParser.parse_report_text(extracted_text, default_confidence=conf)
    parsed_dict = {item["test_name_standardized"]: item for item in parsed}

    assert "fasting_glucose_mg_dl" in parsed_dict
    assert parsed_dict["fasting_glucose_mg_dl"]["value_original"] == 142.0
    assert parsed_dict["fasting_glucose_mg_dl"]["unit_normalized"] == "mg/dL"

    assert "hba1c_percentage" in parsed_dict
    assert parsed_dict["hba1c_percentage"]["value_original"] == 7.4

    assert "cholesterol_total_mg_dl" in parsed_dict
    assert parsed_dict["cholesterol_total_mg_dl"]["value_original"] == 215.0

    assert "serum_creatinine_mg_dl" in parsed_dict
    assert parsed_dict["serum_creatinine_mg_dl"]["value_original"] == 1.15

    print(f"    -> Successfully extracted and mapped {len(parsed)} clinical biomarkers!", flush=True)

    # 5. Test Unit Normalization (mmol/L -> mg/dL)
    print("[5] Testing unit conversion and normalization...", flush=True)
    # Glucose: 7.0 mmol/L should become ~126.1 mg/dL
    norm_val, norm_unit, _ = MedicalNormalizer.normalize_unit_and_value(
        "fasting_glucose_mg_dl", 7.0, "mmol/L"
    )
    assert norm_unit == "mg/dL"
    assert abs(norm_val - 126.1) < 0.2

    # Serum Creatinine: 100 µmol/L should become ~1.13 mg/dL
    norm_creat, creat_unit, _ = MedicalNormalizer.normalize_unit_and_value(
        "serum_creatinine_mg_dl", 100.0, "umol/L"
    )
    assert creat_unit == "mg/dL"
    assert abs(norm_creat - 1.13) < 0.05
    print("    -> Unit conversions (mmol/L -> mg/dL, umol/L -> mg/dL) verified.", flush=True)

    # 6. Test Biological Plausibility Checks
    print("[6] Testing biological plausibility validation...", flush=True)
    # Glucose = 140 (valid)
    valid_ok, _ = MedicalNormalizer.validate_biological_plausibility("fasting_glucose_mg_dl", 140.0)
    assert valid_ok is True

    # Glucose = 5 (biologically impossible, below min threshold 30)
    invalid_low, msg_low = MedicalNormalizer.validate_biological_plausibility("fasting_glucose_mg_dl", 5.0)
    assert invalid_low is False
    assert "below plausible" in msg_low

    # Glucose = 1200 (exceeds max plausible)
    invalid_high, msg_high = MedicalNormalizer.validate_biological_plausibility("fasting_glucose_mg_dl", 1200.0)
    assert invalid_high is False
    assert "exceeds plausible" in msg_high
    print("    -> Biological thresholds validated; impossible values properly flagged.", flush=True)

    # 7. Test Database Persistence and Provenance Tracking
    print("[7] Testing Database Storage and Provenance...", flush=True)
    with open(test_pdf_path, "rb") as f:
        upload_f = UploadFile(filename="sample_test_report.pdf", file=io.BytesIO(f.read()))

    report = ReportService.save_uploaded_report(db, patient.id, upload_f, "Metabolic Panel")

    # Persist extracted values
    for item in parsed:
        val = ExtractedMedicalValue(
            report_id=report.id,
            test_name_raw=item["test_name_raw"],
            test_name_standardized=item["test_name_standardized"],
            value_original=item["value_original"],
            unit_original=item["unit_original"],
            unit_normalized=item["unit_normalized"],
            reference_range=item["reference_range"],
            ocr_confidence=item["ocr_confidence"],
            data_source=DataSourceEnum.OCR,
            is_manually_corrected=False,
        )
        db.add(val)
    db.commit()

    saved_vals = db.query(ExtractedMedicalValue).filter(ExtractedMedicalValue.report_id == report.id).all()
    assert len(saved_vals) == len(parsed)

    # Simulate patient correcting a value (e.g. glucose from 142 to 140)
    glucose_entry = next(v for v in saved_vals if v.test_name_standardized == "fasting_glucose_mg_dl")
    glucose_entry.value_corrected = 140.0
    glucose_entry.data_source = DataSourceEnum.CORRECTED
    glucose_entry.is_manually_corrected = True
    db.commit()
    db.refresh(glucose_entry)

    assert glucose_entry.final_value == 140.0
    assert glucose_entry.value_original == 142.0  # Original preserved!
    assert glucose_entry.data_source == DataSourceEnum.CORRECTED
    print("    -> Provenance tracking verified: original OCR output preserved, corrected value active.", flush=True)

    # Clean up
    if os.path.exists(test_pdf_path):
        os.remove(test_pdf_path)
    if os.path.exists(report.file_path):
        os.remove(report.file_path)

    print("\n==================================================", flush=True)
    print("  PHASES 3 & 4 TEST SUITE PASSED 100%!            ", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    test_phase_3_and_4()
