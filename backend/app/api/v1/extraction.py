from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user, get_current_patient, log_audit_event
from app.core.exceptions import NotFoundException, PermissionDeniedException, BadRequestException
from app.models.user import User, PatientProfile
from app.models.report import MedicalReport, OCRStatus
from app.models.extracted_value import ExtractedMedicalValue, DataSourceEnum
from app.schemas.report import ExtractedValueResponse, ExtractedValueCorrection
from app.services.reports.report_service import ReportService
from app.services.extraction.pdf_extractor import PDFExtractor
from app.services.extraction.ocr_processor import OCRProcessor
from app.services.extraction.value_parser import MedicalValueParser
from app.services.validation.normalizer import MedicalNormalizer

router = APIRouter(prefix="/reports", tags=["OCR & Data Extraction"])


@router.post("/{report_id}/extract", response_model=List[ExtractedValueResponse])
def trigger_report_extraction(
    report_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Parses text from a PDF or image medical report, isolates biometric values, and maps aliases."""
    report = ReportService.get_report_by_id(db, report_id)
    if not ReportService.check_user_report_access(db, report, current_user.id, current_user.role):
        raise PermissionDeniedException("You do not have permission to trigger extraction for this report.")

    report.ocr_status = OCRStatus.PROCESSING
    db.commit()

    raw_text = ""
    confidence = 0.95

    # 1. Process based on file type
    if report.file_type == "pdf":
        raw_text, is_digital, conf = PDFExtractor.extract_text_from_pdf(report.file_path)
        confidence = conf
        if not is_digital and not raw_text.strip():
            # Scanned PDF: render pages to images and run OCR
            images = PDFExtractor.render_pages_to_images(report.file_path)
            ocr_texts = []
            for img in images:
                txt, c = OCRProcessor.process_image(img)
                if txt.strip():
                    ocr_texts.append(txt)
            if ocr_texts:
                raw_text = "\n".join(ocr_texts)
                confidence = 0.85
    else:
        # Direct image (png, jpg, jpeg)
        with open(report.file_path, "rb") as f:
            img_bytes = f.read()
        raw_text, confidence = OCRProcessor.process_image(img_bytes)

    report.ocr_raw_text = raw_text
    report.ocr_status = OCRStatus.COMPLETED

    # 2. Parse structured medical parameters
    parsed_items = MedicalValueParser.parse_report_text(raw_text, default_confidence=confidence)

    # 3. Clear existing auto-extracted values (preserve manually added patient values)
    db.query(ExtractedMedicalValue).filter(
        ExtractedMedicalValue.report_id == report.id,
        ExtractedMedicalValue.is_manually_corrected == False,
    ).delete()

    created_values = []
    for item in parsed_items:
        val = ExtractedMedicalValue(
            report_id=report.id,
            test_name_raw=item["test_name_raw"],
            test_name_standardized=item["test_name_standardized"],
            value_original=item["value_original"],
            value_corrected=None,
            unit_original=item["unit_original"],
            unit_normalized=item["unit_normalized"],
            reference_range=item["reference_range"],
            ocr_confidence=item["ocr_confidence"],
            data_source=DataSourceEnum.OCR,
            is_manually_corrected=False,
        )
        db.add(val)
        created_values.append(val)

    db.commit()

    log_audit_event(
        db=db,
        action="EXTRACT_REPORT_DATA",
        resource_type="report",
        resource_id=str(report.id),
        user_id=current_user.id,
        request=request,
        details={"values_found": len(created_values), "confidence": confidence},
    )

    return db.query(ExtractedMedicalValue).filter(ExtractedMedicalValue.report_id == report.id).all()


@router.get("/{report_id}/extracted-values", response_model=List[ExtractedValueResponse])
def get_extracted_values(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all parsed and patient-corrected biometric values for a report."""
    report = ReportService.get_report_by_id(db, report_id)
    if not ReportService.check_user_report_access(db, report, current_user.id, current_user.role):
        raise PermissionDeniedException("You do not have permission to view extracted values for this report.")

    return db.query(ExtractedMedicalValue).filter(ExtractedMedicalValue.report_id == report.id).all()


@router.patch("/{report_id}/extracted-values/{value_id}", response_model=ExtractedValueResponse)
def correct_extracted_value(
    report_id: int,
    value_id: int,
    correction: ExtractedValueCorrection,
    request: Request,
    patient: PatientProfile = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    """Allows patient to manually correct an inaccurate OCR value while preserving provenance of original."""
    report = ReportService.get_report_by_id(db, report_id)
    if report.patient_id != patient.id:
        raise PermissionDeniedException("You can only correct values for your own reports.")

    val_record = (
        db.query(ExtractedMedicalValue)
        .filter(ExtractedMedicalValue.id == value_id, ExtractedMedicalValue.report_id == report.id)
        .first()
    )
    if not val_record:
        raise NotFoundException("Extracted medical parameter")

    # Update corrected value while keeping original untouched
    val_record.value_corrected = correction.value_corrected
    if correction.unit_normalized:
        val_record.unit_normalized = correction.unit_normalized
    val_record.data_source = DataSourceEnum.CORRECTED
    val_record.is_manually_corrected = True

    db.commit()
    db.refresh(val_record)

    log_audit_event(
        db=db,
        action="CORRECT_EXTRACTED_VALUE",
        resource_type="extracted_value",
        resource_id=str(val_record.id),
        user_id=patient.user_id,
        request=request,
        details={
            "test": val_record.test_name_standardized,
            "original": val_record.value_original,
            "corrected": val_record.value_corrected,
        },
    )

    return val_record
