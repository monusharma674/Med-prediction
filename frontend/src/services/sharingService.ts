import api from './api';

export interface DoctorDirectoryItem {
  doctor_id: number;
  user_id: number;
  full_name: string;
  email: string;
  specialization?: string | null;
  hospital?: string | null;
}

export interface SharedReportItem {
  id: number;
  report_id: number;
  report_uuid: string;
  original_filename: string;
  report_category?: string | null;
  patient_name: string;
  doctor_name: string;
  doctor_email: string;
  doctor_specialization?: string | null;
  is_active: boolean;
  notes?: string | null;
  granted_at: string;
  expires_at?: string | null;
  revoked_at?: string | null;
}

export interface GrantSharePayload {
  report_id: number;
  doctor_id?: number | null;
  doctor_email?: string | null;
  notes?: string | null;
  expires_at?: string | null;
}

export interface DoctorReportDetail {
  report_id: number;
  report_uuid: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  report_category?: string | null;
  report_date?: string | null;
  created_at: string;
  patient_name: string;
  extracted_values: Array<{
    test_name_raw: string;
    test_name_standardized: string;
    value: number;
    unit: string;
    reference_range?: string | null;
    is_corrected: boolean;
  }>;
  predictions: Array<{
    id: number;
    disease_name: string;
    prediction_class: string;
    model_score: number;
    probability?: number | null;
    predicted_at: string;
  }>;
  blockchain_verified: boolean;
  blockchain_tx_hash?: string | null;
}

export const sharingService = {
  async getDoctorDirectory(): Promise<DoctorDirectoryItem[]> {
    const res = await api.get('/sharing/doctors');
    return res.data;
  },

  async grantShare(payload: GrantSharePayload): Promise<SharedReportItem> {
    const res = await api.post('/sharing/grant', payload);
    return res.data;
  },

  async getMyShares(): Promise<SharedReportItem[]> {
    const res = await api.get('/sharing/my-shares');
    return res.data;
  },

  async revokeShare(shareId: number): Promise<void> {
    await api.delete(`/sharing/${shareId}/revoke`);
  },

  async getDoctorSharedReports(): Promise<SharedReportItem[]> {
    const res = await api.get('/sharing/doctor/reports');
    return res.data;
  },

  async getDoctorReportDetails(reportId: number): Promise<DoctorReportDetail> {
    const res = await api.get(`/sharing/doctor/reports/${reportId}`);
    return res.data;
  },
};
