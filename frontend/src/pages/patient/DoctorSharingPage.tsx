import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Share2,
  UserCheck,
  UserX,
  Calendar,
  AlertCircle,
  CheckCircle2,
  Clock,
  Shield,
  FileText,
  Plus,
  Loader2,
  Lock,
} from 'lucide-react';
import {
  sharingService,
  DoctorDirectoryItem,
  SharedReportItem,
} from '../../services/sharingService';
import { reportService, MedicalReportSummary } from '../../services/reportService';

export const DoctorSharingPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const reportIdParam = searchParams.get('report_id');

  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState<MedicalReportSummary[]>([]);
  const [doctors, setDoctors] = useState<DoctorDirectoryItem[]>([]);
  const [shares, setShares] = useState<SharedReportItem[]>([]);

  // Form State
  const [selectedReportId, setSelectedReportId] = useState<number | ''>(
    reportIdParam ? parseInt(reportIdParam, 10) : ''
  );
  const [selectedDoctorId, setSelectedDoctorId] = useState<number | ''>('');
  const [notes, setNotes] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [revokingId, setRevokingId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [reportsData, doctorsData, sharesData] = await Promise.all([
        reportService.getMyReports(),
        sharingService.getDoctorDirectory(),
        sharingService.getMyShares(),
      ]);
      setReports(reportsData);
      setDoctors(doctorsData);
      setShares(sharesData);

      if (!selectedReportId && reportsData.length > 0) {
        setSelectedReportId(reportsData[0].id);
      }
      if (doctorsData.length > 0) {
        setSelectedDoctorId(doctorsData[0].doctor_id);
      }
    } catch (err: any) {
      setErrorMessage('Failed to load sharing settings.');
    } finally {
      setLoading(false);
    }
  };

  const handleGrantShare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReportId || !selectedDoctorId) {
      setErrorMessage('Please select both a medical report and a physician.');
      return;
    }

    try {
      setSubmitting(true);
      setErrorMessage(null);
      setSuccessMessage(null);

      await sharingService.grantShare({
        report_id: Number(selectedReportId),
        doctor_id: Number(selectedDoctorId),
        notes: notes || undefined,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : undefined,
      });

      setSuccessMessage('Report access successfully granted to the physician.');
      setNotes('');
      setExpiresAt('');
      const updatedShares = await sharingService.getMyShares();
      setShares(updatedShares);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to grant doctor access.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevokeShare = async (shareId: number) => {
    if (!window.confirm('Are you sure you want to immediately revoke this physician’s access?')) {
      return;
    }

    try {
      setRevokingId(shareId);
      await sharingService.revokeShare(shareId);
      setShares((prev) =>
        prev.map((s) => (s.id === shareId ? { ...s, is_active: false, revoked_at: new Date().toISOString() } : s))
      );
      setSuccessMessage('Physician access revoked immediately.');
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to revoke access.');
    } finally {
      setRevokingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-10 h-10 text-teal-600 animate-spin mb-4" />
        <p className="text-gray-600 font-medium">Loading physician access control...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs uppercase tracking-wider font-bold text-teal-600 mb-1">
          <Share2 className="w-4 h-4" />
          Patient Consent & Access Control
        </div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-gray-900 tracking-tight">
          Doctor Sharing & Permission Management
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Share your diagnostic reports with certified healthcare providers with granular control and instant revocation.
        </p>
      </div>

      {/* HIPAA / Consent Notice */}
      <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex items-start gap-3 text-sky-900 text-sm">
        <Lock className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Granular Patient Sovereignty:</span> Only doctors explicitly selected by
          you receive permission to view your clinical report. You retain the right to revoke physician access at any
          instant, immediately disabling their view privileges.
        </div>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-lg text-sm flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Grant Access Form */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-5">
          <div className="border-b border-gray-100 pb-3">
            <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
              <Plus className="w-4 h-4 text-teal-600" /> Grant Doctor Access
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Authorize a registered physician to view your lab report.
            </p>
          </div>

          <form onSubmit={handleGrantShare} className="space-y-4 text-sm">
            {/* Select Report */}
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-gray-700">Select Lab Report</label>
              <select
                value={selectedReportId}
                onChange={(e) => setSelectedReportId(Number(e.target.value))}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 outline-none"
              >
                <option value="">-- Choose Report --</option>
                {reports.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.original_filename} ({r.report_category || 'General'})
                  </option>
                ))}
              </select>
            </div>

            {/* Select Doctor */}
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-gray-700">Select Physician</label>
              <select
                value={selectedDoctorId}
                onChange={(e) => setSelectedDoctorId(Number(e.target.value))}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 outline-none"
              >
                <option value="">-- Choose Doctor --</option>
                {doctors.map((d) => (
                  <option key={d.doctor_id} value={d.doctor_id}>
                    {d.full_name} ({d.specialization || 'General'} • {d.hospital || 'Hospital'})
                  </option>
                ))}
              </select>
            </div>

            {/* Notes */}
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-gray-700">
                Clinical Notes / Message (Optional)
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Please review my fasting glucose levels before Monday."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 outline-none"
              />
            </div>

            {/* Expiry Date */}
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-gray-700">
                Access Expiration Date (Optional)
              </label>
              <input
                type="date"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 outline-none"
              />
              <p className="text-[11px] text-gray-400">Leave blank for indefinite access until manual revocation.</p>
            </div>

            <button
              type="submit"
              disabled={submitting || reports.length === 0}
              className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg text-sm shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Authorizing...
                </>
              ) : (
                <>
                  <UserCheck className="w-4 h-4" /> Grant Permission
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right: Active & Past Permissions Table */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col justify-between">
          <div>
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-gray-900">Active & Historical Access Grants</h3>
                <p className="text-xs text-gray-500">
                  Real-time status of reports shared with healthcare providers.
                </p>
              </div>
              <span className="text-xs font-semibold text-gray-500">
                {shares.filter((s) => s.is_active).length} Active Shares
              </span>
            </div>

            {shares.length === 0 ? (
              <div className="p-12 text-center space-y-3">
                <Clock className="w-12 h-12 text-gray-300 mx-auto" />
                <h4 className="text-sm font-semibold text-gray-700">No Reports Currently Shared</h4>
                <p className="text-xs text-gray-400 max-w-sm mx-auto">
                  Use the form on the left to grant secure, revocable access to your physicians.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                    <tr>
                      <th className="px-6 py-3">Physician</th>
                      <th className="px-6 py-3">Report</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3">Granted Date</th>
                      <th className="px-6 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {shares.map((share) => (
                      <tr key={share.id} className="hover:bg-gray-50/60">
                        <td className="px-6 py-4">
                          <div className="font-semibold text-gray-900">{share.doctor_name}</div>
                          <div className="text-xs text-gray-500">{share.doctor_specialization || share.doctor_email}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="font-medium text-gray-800 text-xs truncate max-w-[150px]">
                            {share.original_filename}
                          </div>
                          <div className="text-[11px] text-gray-400">UUID: {share.report_uuid.slice(0, 10)}...</div>
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              share.is_active
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                share.is_active ? 'bg-emerald-600' : 'bg-gray-400'
                              }`}
                            />
                            {share.is_active ? 'Active' : 'Revoked'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs text-gray-500">
                          {new Date(share.granted_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 text-right">
                          {share.is_active ? (
                            <button
                              onClick={() => handleRevokeShare(share.id)}
                              disabled={revokingId === share.id}
                              className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold rounded-lg transition inline-flex items-center gap-1 disabled:opacity-50"
                            >
                              <UserX className="w-3.5 h-3.5" />
                              {revokingId === share.id ? 'Revoking...' : 'Revoke'}
                            </button>
                          ) : (
                            <span className="text-xs text-gray-400">Access Terminated</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
