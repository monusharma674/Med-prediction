import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FileText,
  User,
  Calendar,
  ChevronRight,
  ShieldCheck,
  Clock,
  Loader2,
  Stethoscope,
  Activity,
  AlertCircle,
} from 'lucide-react';
import { sharingService, SharedReportItem } from '../../services/sharingService';

export const DoctorSharedReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState<SharedReportItem[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    loadSharedReports();
  }, []);

  const loadSharedReports = async () => {
    try {
      setLoading(true);
      const data = await sharingService.getDoctorSharedReports();
      setReports(data);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load shared patient reports.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-xs uppercase tracking-wider font-bold text-teal-600 mb-1">
          <Stethoscope className="w-4 h-4" />
          Physician Consultation Vault
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Authorized Patient Reports</h1>
        <p className="text-sm text-gray-500 mt-1">
          Review patient diagnostic records, extracted biomarkers, and predictive machine learning risk assessments.
        </p>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh]">
          <Loader2 className="w-8 h-8 text-teal-600 animate-spin mb-3" />
          <p className="text-sm text-gray-500">Querying authorized records from patient vaults...</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center space-y-3">
          <FileText className="w-12 h-12 text-gray-300 mx-auto" />
          <h3 className="text-lg font-bold text-gray-800">No Patient Reports Shared</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            When patients grant you access to review their medical test documents, they will appear securely here.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                <tr>
                  <th className="px-6 py-3.5">Patient</th>
                  <th className="px-6 py-3.5">Medical Document</th>
                  <th className="px-6 py-3.5">Category</th>
                  <th className="px-6 py-3.5">Patient Message / Notes</th>
                  <th className="px-6 py-3.5">Granted On</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {reports.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50/60 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-700 font-bold text-xs flex items-center justify-center">
                          {r.patient_name[0]?.toUpperCase() || 'P'}
                        </div>
                        <div className="font-semibold text-gray-900">{r.patient_name}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-800">{r.original_filename}</div>
                      <div className="text-[11px] text-gray-400 font-mono">UUID: {r.report_uuid.slice(0, 12)}...</div>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      <span className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-md font-medium">
                        {r.report_category || 'General Lab'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-500 max-w-xs truncate">
                      {r.notes || <span className="italic text-gray-400">No notes provided</span>}
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-500">
                      {new Date(r.granted_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/doctor/reports/${r.report_id}`}
                        className="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg inline-flex items-center gap-1.5 transition"
                      >
                        Inspect Record <ChevronRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
