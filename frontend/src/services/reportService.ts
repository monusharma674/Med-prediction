import api from './api';
import {
  MedicalReport,
  MedicalReportSummary,
  FileIntegrityCheckResponse,
} from '../types/report';

export type { MedicalReport, MedicalReportSummary, FileIntegrityCheckResponse };

export const reportService = {
  async uploadReport(formData: FormData): Promise<MedicalReport> {
    const res = await api.post<MedicalReport>('/reports/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async getMyReports(skip: number = 0, limit: number = 50): Promise<MedicalReportSummary[]> {
    const res = await api.get<MedicalReportSummary[]>('/reports/', {
      params: { skip, limit },
    });
    return res.data;
  },

  async getReportDetails(reportId: number): Promise<MedicalReport> {
    const res = await api.get<MedicalReport>(`/reports/${reportId}`);
    return res.data;
  },

  async verifyFileIntegrity(reportId: number): Promise<FileIntegrityCheckResponse> {
    const res = await api.get<FileIntegrityCheckResponse>(`/reports/${reportId}/verify-file`);
    return res.data;
  },

  async downloadReport(reportId: number, filename: string): Promise<void> {
    const res = await api.get(`/reports/${reportId}/download`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  async deleteReport(reportId: number): Promise<void> {
    await api.delete(`/reports/${reportId}`);
  },
};
