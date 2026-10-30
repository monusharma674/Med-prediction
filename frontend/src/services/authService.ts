import api from './api';
import { AuthResponse, User } from '../types/auth';

export const authService = {
  async registerPatient(data: any): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/register/patient', data);
    return res.data;
  },

  async registerDoctor(data: any): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/register/doctor', data);
    return res.data;
  },

  async login(credentials: { email: string; password: string }): Promise<AuthResponse> {
    const res = await api.post<AuthResponse>('/auth/login', credentials);
    return res.data;
  },

  async getCurrentUser(): Promise<User> {
    const res = await api.get<User>('/auth/me');
    return res.data;
  },
};
