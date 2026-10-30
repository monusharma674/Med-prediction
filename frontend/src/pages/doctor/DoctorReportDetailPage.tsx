import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Stethoscope,
  ArrowLeft,
  FileText,
  User,
  ShieldCheck,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Download,
  Blocks,
  Clock,
} from 'lucide-react';
import { sharingService, DoctorReportDetail } from '../../services/sharingService';
import { reportService } from '../../services/reportService';

export const DoctorReportDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<DoctorReportDetail | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadReportDetails(parseInt(id, 10));
    }
  }, [id]);

  const loadReportDetails = async (reportId: number) => {
    try {
      setLoading(true);
      const data = await sharingService.getDoctorReportDetails(reportId);
      setReport(data);
    } catch (err: any) {
      setErrorMessage(
        err.response?.status === 403
          ? 'Access Forbidden: The patient has not authorized or has revoked your permission to view this report.'
          : err.response?.data?.detail || 'Failed to load report details.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadOriginal = async () => {
    if (!report) return;
    try {
      await reportService.downloadReport(report.report_id, report.original_filename);
    } catch (err) {
      alert('Failed to download report.');
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-10 h-10 text-teal-600 animate-spin mb-4" />
        <p className="text-gray-600 font-medium">Authorizing access & retrieving clinical record...</p>
      </div>
    );
  }

  if (errorMessage || !report) {
    return (
      <div className="max-w-2xl mx-auto p-8 bg-red-50 border border-red-200 rounded-xl text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-red-600 mx-auto" />
        <h2 className="text-lg font-bold text-red-900">Access Restricted</h2>
        <p className="text-sm text-red-700">{errorMessage || 'Record unavailable.'}</p>
        <button
          onClick={() => navigate('/doctor/shared-reports')}
          className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700"
        >
          Return to Shared Reports
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Navigation & Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/doctor/shared-reports')}
          className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Shared Reports
        </button>
        <button
          onClick={handleDownloadOriginal}
          className="px-3.5 py-2 bg-white border border-gray-300 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-50 flex items-center gap-1.5 shadow-sm"
        >
          <Download className="w-3.5 h-3.5" /> Download Original Document
        </button>
      </div>

      {/* Patient & Report Banner */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-teal-100 text-teal-700 font-bold text-lg flex items-center justify-center">
              {report.patient_name[0]?.toUpperCase() || 'P'}
            </div>
            <div>
              <div className="text-xs uppercase tracking-wider font-semibold text-gray-400">Patient Record</div>
              <h1 className="text-xl font-bold text-gray-900">{report.patient_name}</h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {report.blockchain_verified ? (
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-full">
                <Blocks className="w-3.5 h-3.5" /> Blockchain Integrity Anchored
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-600 text-xs font-semibold rounded-full">
                Unanchored
              </span>
            )}
          </div>
        </div>

        {/* Metadata Details */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-gray-400 block">File Name</span>
            <span className="font-semibold text-gray-800 truncate block mt-0.5">{report.original_filename}</span>
          </div>
          <div>
            <span className="text-gray-400 block">Category</span>
            <span className="font-semibold text-gray-800 block mt-0.5">{report.report_category || 'General'}</span>
          </div>
          <div>
            <span className="text-gray-400 block">Report UUID</span>
            <span className="font-mono text-gray-800 block mt-0.5">{report.report_uuid.slice(0, 14)}...</span>
          </div>
          <div>
            <span className="text-gray-400 block">Uploaded On</span>
            <span className="font-semibold text-gray-800 block mt-0.5">
              {new Date(report.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>

      {/* Extracted Biomarkers Section */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-gray-900">Extracted Clinical Biomarkers</h3>
            <p className="text-xs text-gray-500">
              Normalized diagnostic parameters extracted from this report.
            </p>
          </div>
          <span className="text-xs text-gray-500">
            {report.extracted_values.length} Measurements Extracted
          </span>
        </div>

        {report.extracted_values.length === 0 ? (
          <div className="p-8 text-center text-xs text-gray-400">
            No diagnostic parameters have been extracted from this report yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                <tr>
                  <th className="px-6 py-3">Biomarker / Test Name</th>
                  <th className="px-6 py-3">Extracted Value</th>
                  <th className="px-6 py-3">Unit</th>
                  <th className="px-6 py-3">Reference Range</th>
                  <th className="px-6 py-3">Verification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {report.extracted_values.map((v, idx) => (
                  <tr key={idx} className="hover:bg-gray-50/50">
                    <td className="px-6 py-3.5 font-medium text-gray-800 capitalize">
                      {v.test_name_standardized.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-3.5 font-bold text-gray-900">
                      {v.value}
                    </td>
                    <td className="px-6 py-3.5 text-xs text-gray-600">
                      <span className="px-2 py-0.5 bg-gray-100 rounded">{v.unit}</span>
                    </td>
                    <td className="px-6 py-3.5 text-xs text-gray-500">
                      {v.reference_range || 'Normal'}
                    </td>
                    <td className="px-6 py-3.5 text-xs">
                      {v.is_corrected ? (
                        <span className="text-purple-700 font-medium">Patient Verified</span>
                      ) : (
                        <span className="text-teal-700 font-medium">OCR Parsed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Associated Machine Learning Predictions */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-gray-900">Machine Learning Disease Risk Assessments</h3>
            <p className="text-xs text-gray-500">
              Evaluations generated from this report's biometric features.
            </p>
          </div>
          <span className="text-xs text-gray-500">{report.predictions.length} Predictions Logged</span>
        </div>

        {report.predictions.length === 0 ? (
          <div className="p-8 text-center text-xs text-gray-400">
            No disease predictions have been calculated for this specific report.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                <tr>
                  <th className="px-6 py-3">Disease Target</th>
                  <th className="px-6 py-3">Outcome</th>
                  <th className="px-6 py-3">Model Risk Score</th>
                  <th className="px-6 py-3">Executed At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {report.predictions.map((p) => {
                  const isHigh =
                    p.prediction_class.toLowerCase().includes('positive') ||
                    p.prediction_class.toLowerCase().includes('high');

                  return (
                    <tr key={p.id} className="hover:bg-gray-50/50">
                      <td className="px-6 py-3.5 font-bold text-gray-900 capitalize">
                        {p.disease_name.replace(/_/g, ' ')}
                      </td>
                      <td className="px-6 py-3.5">
                        <span
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                            isHigh ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {p.prediction_class}
                        </span>
                      </td>
                      <td className="px-6 py-3.5 font-semibold text-gray-900">
                        {p.probability !== undefined && p.probability !== null
                          ? `${(p.probability * 100).toFixed(1)}%`
                          : p.model_score.toFixed(3)}
                      </td>
                      <td className="px-6 py-3.5 text-xs text-gray-500">
                        {new Date(p.predicted_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
