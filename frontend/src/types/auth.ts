export type UserRole = 'patient' | 'doctor' | 'admin';

export interface User {
  id: number;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  patient_profile?: PatientProfile;
  doctor_profile?: DoctorProfile;
}

export interface PatientProfile {
  id: number;
  full_name: string;
  date_of_birth?: string;
  gender?: string;
  phone?: string;
  blood_group?: string;
}

export interface DoctorProfile {
  id: number;
  full_name: string;
  specialization: string;
  license_number?: string;
  hospital?: string;
  phone?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  user_id: number;
  full_name: string;
  email: string;
}
