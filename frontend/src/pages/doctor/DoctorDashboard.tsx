import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FileText, Stethoscope, Users, CheckCircle, ArrowRight } from 'lucide-react';

export const DoctorDashboard: React.FC = () => {
  const { user } = useAuth();
  const doctor = user?.doctor_profile;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-700 to-teal-800 rounded-3xl p-8 text-white shadow-xl shadow-teal-900/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <span className="text-xs uppercase tracking-widest font-bold bg-white/20 text-white px-3 py-1 rounded-full">
            Physician Portal
          </span>
          <h1 className="text-3xl font-extrabold mt-3 tracking-tight">
            Dr. {doctor?.full_name || user?.email}
          </h1>
          <p className="mt-2 text-emerald-100 max-w-xl text-sm leading-relaxed">
            Specialization: <span className="font-semibold text-white">{doctor?.specialization || 'Physician'}</span> | License: {doctor?.license_number || 'Verified'}
          </p>
        </div>
        <Link
          to="/doctor/shared-reports"
          className="flex items-center space-x-2 bg-white text-teal-800 hover:bg-teal-50 font-bold px-5 py-3 rounded-2xl shadow-lg transition"
        >
          <FileText className="w-5 h-5" />
          <span>View Shared Reports</span>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-teal-100 text-teal-600 flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Authorized Patients</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">0</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Reports Shared with You</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">0</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center">
            <CheckCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Verified Authentications</p>
            <h3 className="text-2xl font-bold text-slate-900 mt-0.5">100%</h3>
          </div>
        </div>
      </div>

      {/* Overview Card */}
      <div className="bg-white p-8 rounded-3xl border border-slate-200/80 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-2">Consent-Governed Clinical Records</h3>
        <p className="text-sm text-slate-600 leading-relaxed max-w-3xl">
          You only have access to medical reports explicitly shared with you by registered patients. Patients retain full authority to set access expiration dates or revoke access at any time. All file access events are cryptographically audited.
        </p>
        <Link
          to="/doctor/shared-reports"
          className="mt-6 inline-flex items-center space-x-2 text-sm font-semibold text-teal-700 hover:text-teal-800"
        >
          <span>Open Shared Patient Records</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};
