import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { reportService } from '../../services/reportService';
import { MedicalReport, FileIntegrityCheckResponse } from '../../types/report';
import {
  FileText,
  Shield,
  Download,
  CheckCircle,
  AlertCircle,
  Copy,
  Check,
  Calendar,
  Layers,
  Cpu,
  ArrowRight,
  ShieldAlert,
  ShieldCheck,
  Share2,
} from 'lucide-react';

export const ReportDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<MedicalReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [integrityStatus, setIntegrityStatus] = useState<FileIntegrityCheckResponse | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const data = await reportService.getReportDetails(parseInt(id));
        setReport(data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to retrieve report details.');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [id]);

  const copyHash = () => {
    if (!report) return;
    navigator.clipboard.writeText(report.file_hash_sha256);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleVerifyIntegrity = async () => {
    if (!report) return;
    try {
      setVerifying(true);
      const res = await reportService.verifyFileIntegrity(report.id);
      setIntegrityStatus(res);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to verify file integrity.');
    } finally {
      setVerifying(false);
    }
  };

  const handleDownload = async () => {
    if (!report) return;
    try {
      await reportService.downloadReport(report.id, report.original_filename);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Download failed.');
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 p-16 text-center">
        <div className="w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium text-slate-600">Retrieving report details & cryptographic parameters...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-3xl p-8 text-rose-800 space-y-4">
        <div className="flex items-center space-x-3">
          <AlertCircle className="w-6 h-6 text-rose-600" />
          <h3 className="font-bold text-lg">Unable to Load Medical Report</h3>
        </div>
        <p className="text-sm">{error || 'Report not found or access restricted.'}</p>
        <button
          onClick={() => navigate('/patient/reports')}
          className="px-4 py-2 bg-rose-600 text-white rounded-xl text-sm font-semibold hover:bg-rose-700"
        >
          Return to My Reports
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            <Link to="/patient/reports" className="hover:text-sky-600">
              My Reports
            </Link>
            <span>/</span>
            <span className="font-mono text-slate-800">{report.report_uuid}</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
            {report.original_filename}
          </h1>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleDownload}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-semibold text-sm hover:bg-slate-100 transition shadow-sm"
          >
            <Download className="w-4 h-4" />
            <span>Download Original</span>
          </button>
          <button
            onClick={() => navigate(`/patient/sharing?report_id=${report.id}`)}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-sky-50 text-sky-700 border border-sky-200 font-semibold text-sm hover:bg-sky-100 transition"
          >
            <Share2 className="w-4 h-4" />
            <span>Share with Doctor</span>
          </button>
        </div>
      </div>

      {/* Main Metadata Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-1">
          <p className="text-xs uppercase tracking-wider font-semibold text-slate-400">Report Category</p>
          <p className="text-base font-bold text-slate-800">{report.report_category || 'General Lab Record'}</p>
          <p className="text-xs text-slate-500">Classification for OCR feature mapping</p>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-1">
          <p className="text-xs uppercase tracking-wider font-semibold text-slate-400">File Type & Size</p>
          <p className="text-base font-bold text-slate-800 uppercase">
            {report.file_type} • {(report.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
          </p>
          <p className="text-xs text-slate-500">Stored outside public web directory</p>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-1">
          <p className="text-xs uppercase tracking-wider font-semibold text-slate-400">Upload & Test Date</p>
          <p className="text-base font-bold text-slate-800">
            {report.report_date || report.created_at.split('T')[0]}
          </p>
          <p className="text-xs text-slate-500">Ingested {new Date(report.created_at).toLocaleDateString()}</p>
        </div>
      </div>

      {/* Cryptographic SHA-256 Card & Disk Verification */}
      <div className="bg-slate-900 rounded-3xl p-6 md:p-8 text-white space-y-5 shadow-xl shadow-slate-900/10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-5 h-5 text-sky-400" />
            <span className="font-bold text-base text-slate-100">
              SHA-256 Cryptographic Report Integrity Checksum
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={copyHash}
              className="flex items-center space-x-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg transition"
            >
              {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedHash ? 'Copied' : 'Copy Checksum'}</span>
            </button>

            <button
              onClick={handleVerifyIntegrity}
              disabled={verifying}
              className="flex items-center space-x-1.5 text-xs font-semibold text-sky-400 hover:text-sky-300 bg-sky-950/80 border border-sky-800/80 hover:bg-sky-900 px-3 py-1.5 rounded-lg transition disabled:opacity-50"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>{verifying ? 'Checking...' : 'Verify Disk Integrity'}</span>
            </button>
          </div>
        </div>

        <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
          <p className="font-mono text-xs md:text-sm text-sky-300 break-all select-all">
            {report.file_hash_sha256}
          </p>
        </div>

        {integrityStatus && (
          <div
            className={`p-4 rounded-2xl border flex items-center space-x-3 text-sm ${
              integrityStatus.is_intact
                ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                : 'bg-rose-950/40 border-rose-800 text-rose-300'
            }`}
          >
            {integrityStatus.is_intact ? (
              <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            ) : (
              <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0" />
            )}
            <div>
              <p className="font-bold">
                {integrityStatus.is_intact
                  ? 'Server File Integrity Confirmed'
                  : 'Tampering or File Corruption Detected!'}
              </p>
              <p className="text-xs text-slate-300 mt-0.5">
                {integrityStatus.is_intact
                  ? 'The current file on disk matches the SHA-256 hash registered on upload bit-for-bit.'
                  : 'The file on server disk has been altered since initial ingestion! Checksum mismatch.'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Next Pipeline Modules (Phases 3, 6, 7) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* OCR Module Card */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs uppercase tracking-wider font-bold text-sky-600 bg-sky-50 px-2.5 py-1 rounded-full border border-sky-100">
                Phase 3: OCR Pipeline
              </span>
              <span
                className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                  report.ocr_status === 'completed'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-amber-100 text-amber-800'
                }`}
              >
                {report.ocr_status}
              </span>
            </div>
            <h3 className="text-lg font-bold text-slate-900">Extracted Clinical Biometrics</h3>
            <p className="text-sm text-slate-600 mt-2 leading-relaxed">
              Extract blood glucose, HbA1c, lipid fractions, and electrolytes using PyMuPDF and Tesseract OCR with interactive correction.
            </p>
          </div>
          <button
            onClick={() => navigate(`/patient/reports/${report.id}/extracted`)}
            className="mt-6 flex items-center justify-between px-4 py-2.5 bg-slate-50 hover:bg-slate-100 text-slate-800 font-semibold text-sm rounded-xl transition"
          >
            <span>Review Extracted Values</span>
            <ArrowRight className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Disease Risk Prediction Card */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs uppercase tracking-wider font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                Phase 6: Multi-Disease AI
              </span>
              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                2 Models Ready
              </span>
            </div>
            <h3 className="text-lg font-bold text-slate-900">Multi-Disease Risk Evaluation</h3>
            <p className="text-sm text-slate-600 mt-2 leading-relaxed">
              Check model feature eligibility (Diabetes & Heart Disease) using parameters extracted from this specific report.
            </p>
          </div>
          <button
            onClick={() => navigate(`/patient/predict?report_id=${report.id}`)}
            className="mt-6 flex items-center justify-between px-4 py-2.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-semibold text-sm rounded-xl transition"
          >
            <span>Evaluate Disease Risk</span>
            <ArrowRight className="w-4 h-4 text-emerald-600" />
          </button>
        </div>
      </div>
    </div>
  );
};
