import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  Upload,
  FileText,
  Cpu,
  ShieldCheck,
  Share2,
  HeartPulse,
  Clock,
  ArrowRight,
} from 'lucide-react';

export const PatientDashboard: React.FC = () => {
  const { user } = useAuth();
  const patient = user?.patient_profile;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-sky-600 to-indigo-700 rounded-3xl p-8 text-white shadow-xl shadow-sky-900/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <span className="text-xs uppercase tracking-widest font-bold bg-white/20 text-white px-3 py-1 rounded-full">
            Patient Portal
          </span>
          <h1 className="text-3xl font-extrabold mt-3 tracking-tight">
            Hello, {patient?.full_name || user?.email}
          </h1>
          <p className="mt-2 text-sky-100 max-w-xl text-sm leading-relaxed">
            Welcome to your intelligent medical records hub. Upload clinical reports to extract diagnostic parameters, assess predictive disease risks, and cryptographically verify report integrity.
          </p>
        </div>
        <Link
          to="/patient/upload"
          className="flex items-center space-x-2 bg-white text-sky-700 hover:bg-sky-50 font-bold px-5 py-3 rounded-2xl shadow-lg transition"
        >
          <Upload className="w-5 h-5" />
          <span>Upload Lab Report</span>
        </Link>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Reports Uploaded</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">0</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Predictions Run</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">0</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Blockchain Verified</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">0</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center">
            <Share2 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Doctor Shares</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">0</h3>
          </div>
        </div>
      </div>

      {/* Main Action Hub */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center mb-4">
              <Upload className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Upload & Parse Clinical Report</h3>
            <p className="text-sm text-slate-600 mt-2 leading-relaxed">
              Upload blood biochemistry, lipid panel, or diabetic profile in PDF or image format. Our OCR pipeline automatically isolates clinical features for multi-disease models.
            </p>
          </div>
          <Link
            to="/patient/upload"
            className="mt-6 inline-flex items-center space-x-2 text-sm font-semibold text-sky-600 hover:text-sky-700"
          >
            <span>Proceed to Upload</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-4">
              <HeartPulse className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Multi-Disease Risk Prediction</h3>
            <p className="text-sm text-slate-600 mt-2 leading-relaxed">
              Check compatibility of uploaded biomarkers with our trained Scikit-learn disease models (Diabetes & Heart Disease). Supplement missing parameters on demand.
            </p>
          </div>
          <Link
            to="/patient/predict"
            className="mt-6 inline-flex items-center space-x-2 text-sm font-semibold text-emerald-600 hover:text-emerald-700"
          >
            <span>View Disease Models</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Clinical Disclaimer Box */}
      <div className="p-4 rounded-2xl bg-slate-100 border border-slate-200 text-xs text-slate-600 flex items-start space-x-3">
        <Clock className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
        <p>
          <strong>Notice:</strong> All risk scoring and statistical estimations produced by this system are designed for university major project demonstration. They do not constitute formal medical diagnosis or clinical prescription.
        </p>
      </div>
    </div>
  );
};
