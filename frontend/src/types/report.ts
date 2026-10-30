export type OCRStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type DataSource = 'ocr' | 'corrected' | 'patient_entered';

export interface ExtractedMedicalValue {
  id: number;
  test_name_raw: string;
  test_name_standardized: string;
  value_original?: number;
  value_corrected?: number;
  final_value?: number;
  unit_original?: string;
  unit_normalized?: string;
  reference_range?: string;
  ocr_confidence?: number;
  data_source: DataSource;
  is_manually_corrected: boolean;
  extracted_at: string;
}

export interface MedicalReportSummary {
  id: number;
  report_uuid: string;
  original_filename: string;
  file_hash_sha256: string;
  file_type: string;
  file_size_bytes: number;
  report_category?: string;
  report_date?: string;
  ocr_status: OCRStatus;
  blockchain_registered: boolean;
  created_at: string;
}

export interface MedicalReport extends MedicalReportSummary {
  patient_id: number;
  blockchain_tx_hash?: string;
  extracted_values: ExtractedMedicalValue[];
}

export interface FileIntegrityCheckResponse {
  report_id: number;
  report_uuid: string;
  is_intact: boolean;
  stored_hash: string;
  current_hash: string;
  status: 'VERIFIED_AUTHENTIC' | 'TAMPERED_OR_CORRUPT';
}
