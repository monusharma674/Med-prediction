import api from './api';
import { ModelMetadata } from './predictionService';

export interface AdminStats {
  total_patients: number;
  total_doctors: number;
  total_reports: number;
  total_predictions: number;
  total_blockchain_records: number;
  total_active_shares: number;
}

export interface AdminUser {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  full_name: string;
  created_at: string;
}

export interface AdminAuditLog {
  id: number;
  user_id?: number | null;
  user_email?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  details?: Record<string, any> | null;
  logged_at: string;
}

export const adminService = {
  async getStats(): Promise<AdminStats> {
    const res = await api.get('/admin/stats');
    return res.data;
  },

  async getUsers(role?: string): Promise<AdminUser[]> {
    const params = role ? { role } : {};
    const res = await api.get('/admin/users', { params });
    return res.data;
  },

  async toggleUserStatus(userId: number, isActive: boolean): Promise<AdminUser> {
    const res = await api.patch(`/admin/users/${userId}/status`, null, {
      params: { is_active: isActive },
    });
    return res.data;
  },

  async getAuditLogs(limit: number = 50, action?: string): Promise<AdminAuditLog[]> {
    const params: any = { limit };
    if (action) params.action = action;
    const res = await api.get('/admin/audit-logs', { params });
    return res.data;
  },

  async getModels(): Promise<ModelMetadata[]> {
    const res = await api.get('/predictions/models');
    return res.data;
  },
};
