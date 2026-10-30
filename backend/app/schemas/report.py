from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models.report import OCRStatus
from app.models.extracted_value import DataSourceEnum


class ExtractedValueResponse(BaseModel):
    id: int
    test_name_raw: str
    test_name_standardized: str
    value_original: Optional[float] = None
    value_corrected: Optional[float] = None
    final_value: Optional[float] = None
    unit_original: Optional[str] = None
    unit_normalized: Optional[str] = None
    reference_range: Optional[str] = None
    ocr_confidence: Optional[float] = 1.0
    data_source: DataSourceEnum
    is_manually_corrected: bool
    extracted_at: datetime

    class Config:
        from_attributes = True


class ExtractedValueCorrection(BaseModel):
    value_corrected: float
    unit_normalized: Optional[str] = None


class MedicalReportResponse(BaseModel):
    id: int
    patient_id: int
    report_uuid: str
    original_filename: str
    file_hash_sha256: str
    file_type: str
    file_size_bytes: int
    report_category: Optional[str] = None
    report_date: Optional[date] = None
    ocr_status: OCRStatus
    blockchain_registered: bool
    blockchain_tx_hash: Optional[str] = None
    created_at: datetime
    extracted_values: List[ExtractedValueResponse] = []

    class Config:
        from_attributes = True


class MedicalReportSummary(BaseModel):
    id: int
    report_uuid: str
    original_filename: str
    file_hash_sha256: str
    file_type: str
    file_size_bytes: int
    report_category: Optional[str] = None
    report_date: Optional[date] = None
    ocr_status: OCRStatus
    blockchain_registered: bool
    created_at: datetime

    class Config:
        from_attributes = True
