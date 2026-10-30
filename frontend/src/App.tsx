import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { DashboardLayout } from './layouts/DashboardLayout';

import { LandingPage } from './pages/public/LandingPage';
import { LoginPage } from './pages/public/LoginPage';
import { RegisterPage } from './pages/public/RegisterPage';

import { PatientDashboard } from './pages/patient/PatientDashboard';
import { UploadReportPage } from './pages/patient/UploadReportPage';
import { MyReportsPage } from './pages/patient/MyReportsPage';
import { ReportDetailsPage } from './pages/patient/ReportDetailsPage';
import { ExtractedDataReviewPage } from './pages/patient/ExtractedDataReviewPage';
import { DiseaseSelectionPage } from './pages/patient/DiseaseSelectionPage';
import { PredictionResultPage } from './pages/patient/PredictionResultPage';
import { PredictionHistoryPage } from './pages/patient/PredictionHistoryPage';
import { BlockchainVerificationPage } from './pages/patient/BlockchainVerificationPage';
import { DoctorSharingPage } from './pages/patient/DoctorSharingPage';

import { DoctorDashboard } from './pages/doctor/DoctorDashboard';
import { DoctorSharedReportsPage } from './pages/doctor/DoctorSharedReportsPage';
import { DoctorReportDetailPage } from './pages/doctor/DoctorReportDetailPage';
import { AdminDashboard } from './pages/admin/AdminDashboard';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Patient Routes */}
          <Route
            path="/patient"
            element={
              <ProtectedRoute allowedRoles={['patient']}>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/patient/dashboard" replace />} />
            <Route path="dashboard" element={<PatientDashboard />} />
            <Route path="upload" element={<UploadReportPage />} />
            <Route path="reports" element={<MyReportsPage />} />
            <Route path="reports/:id" element={<ReportDetailsPage />} />
            <Route path="reports/:id/extracted" element={<ExtractedDataReviewPage />} />
            <Route path="predict" element={<DiseaseSelectionPage />} />
            <Route path="predictions/select" element={<DiseaseSelectionPage />} />
            <Route path="predictions/:id" element={<PredictionResultPage />} />
            <Route path="history" element={<PredictionHistoryPage />} />
            <Route path="predictions/history" element={<PredictionHistoryPage />} />
            <Route path="sharing" element={<DoctorSharingPage />} />
            <Route path="blockchain" element={<BlockchainVerificationPage />} />
            <Route
              path="profile"
              element={
                <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
                  <h2 className="text-xl font-bold text-slate-900 mb-2">Patient Profile</h2>
                  <p className="text-sm text-slate-600">Personal clinical demographics and contact information.</p>
                </div>
              }
            />
          </Route>

          {/* Doctor Routes */}
          <Route
            path="/doctor"
            element={
              <ProtectedRoute allowedRoles={['doctor']}>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/doctor/dashboard" replace />} />
            <Route path="dashboard" element={<DoctorDashboard />} />
            <Route path="shared-reports" element={<DoctorSharedReportsPage />} />
            <Route path="reports/:id" element={<DoctorReportDetailPage />} />
            <Route
              path="profile"
              element={
                <div className="bg-white p-8 rounded-3xl border border-slate-200 shadow-sm">
                  <h2 className="text-xl font-bold text-slate-900 mb-2">Physician Profile</h2>
                  <p className="text-sm text-slate-600">Specialization, license number, and hospital affiliations.</p>
                </div>
              }
            />
          </Route>

          {/* Admin Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="users" element={<AdminDashboard />} />
            <Route path="models" element={<AdminDashboard />} />
            <Route path="logs" element={<AdminDashboard />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
