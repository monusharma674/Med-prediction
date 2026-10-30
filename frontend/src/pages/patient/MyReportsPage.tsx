import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { reportService } from '../../services/reportService';
import { MedicalReportSummary } from '../../types/report';
import {
  FileText,
  Upload,
  Download,
  Trash2,
  ShieldCheck,
  Search,
  AlertCircle,
  Eye,
  CheckCircle2,
  Clock,
  ExternalLink,
} from 'lucide-react';

export const MyReportsPage: React.FC = () => {
  const [reports, setReports] = useState<MedicalReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [verifyingId, setVerifyingId] = useState<number | null>(null);
  const [verificationResult, setVerificationResult] = useState<{ [id: number]: boolean }>({});

  const navigate = useNavigate();

  const fetchReports = async () => {
    try {
      setLoading(true);
      const data = await reportService.getMyReports();
      setReports(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load medical reports.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleDownload = async (id: number, filename: string) => {
    try {
      await reportService.downloadReport(id, filename);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to download file.');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this medical report? This action is logged.')) {
      return;
    }
    try {
      setDeletingId(id);
      await reportService.deleteReport(id);
      setReports(reports.filter((r) => r.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete report.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleVerifyIntegrity = async (id: number) => {
    try {
      setVerifyingId(id);
      const res = await reportService.verifyFileIntegrity(id);
      setVerificationResult((prev) => ({ ...prev, [id]: res.is_intact }));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Verification request failed.');
    } finally {
      setVerifyingId(null);
    }
  };

  const filteredReports = reports.filter((r) => {
    const matchesSearch =
      r.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.file_hash_sha256.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.report_uuid.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === 'All' || r.report_category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = [
    'All',
    ...Array.from(new Set(reports.map((r) => r.report_category).filter(Boolean))),
  ];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            My Medical Reports
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Secure vault of your clinical lab records, cryptographic hashes, and OCR parameters
          </p>
        </div>
        <Link
          to="/patient/upload"
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-sky-600 hover:bg-sky-700 shadow-md shadow-sky-600/20 transition self-start sm:self-auto"
        >
          <Upload className="w-4 h-4" />
          <span>Upload New Report</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search by filename, hash, or report UUID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>
        <div className="w-full sm:w-auto">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full sm:w-56 px-3 py-2 border border-slate-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Reports Table or Loading / Empty View */}
      {loading ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-16 text-center">
          <div className="w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm font-medium text-slate-600">Loading your medical repository...</p>
        </div>
      ) : error ? (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-rose-800 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-16 text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto">
            <FileText className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">No medical reports found</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
              {searchQuery || selectedCategory !== 'All'
                ? 'No reports match your search query or selected category.'
                : 'You have not uploaded any lab reports yet. Upload a report to start OCR parameter extraction.'}
            </p>
          </div>
          <Link
            to="/patient/upload"
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-sky-600 hover:bg-sky-700 transition"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Your First Report</span>
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 text-xs uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-6 py-4">Report Details</th>
                  <th className="px-6 py-4">Category & Date</th>
                  <th className="px-6 py-4">SHA-256 Hash</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredReports.map((report) => (
                  <tr key={report.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold text-xs uppercase flex-shrink-0">
                          {report.file_type}
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-slate-900 truncate max-w-xs">
                            {report.original_filename}
                          </p>
                          <p className="text-xs text-slate-400 font-mono">
                            {report.report_uuid} • {(report.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <p className="font-medium text-slate-800 text-xs">
                        {report.report_category || 'General'}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {report.report_date || report.created_at.split('T')[0]}
                      </p>
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs text-slate-600 bg-slate-100 px-2 py-1 rounded-md max-w-[140px] truncate">
                          {report.file_hash_sha256}
                        </span>
                        {verificationResult[report.id] !== undefined && (
                          <span
                            className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                              verificationResult[report.id]
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}
                          >
                            {verificationResult[report.id] ? 'Intact' : 'Tampered'}
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex flex-col space-y-1">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider w-max ${
                            report.ocr_status === 'completed'
                              ? 'bg-emerald-100 text-emerald-800'
                              : report.ocr_status === 'processing'
                              ? 'bg-sky-100 text-sky-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          OCR {report.ocr_status}
                        </span>

                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider w-max ${
                            report.blockchain_registered
                              ? 'bg-indigo-100 text-indigo-800'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {report.blockchain_registered ? 'Blockchain Anchored' : 'Local Only'}
                        </span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-1">
                        <button
                          onClick={() => navigate(`/patient/reports/${report.id}`)}
                          title="View Details & Extracted Parameters"
                          className="p-2 text-slate-600 hover:text-sky-600 hover:bg-slate-100 rounded-lg transition"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleVerifyIntegrity(report.id)}
                          disabled={verifyingId === report.id}
                          title="Verify File Integrity (SHA-256)"
                          className="p-2 text-slate-600 hover:text-indigo-600 hover:bg-slate-100 rounded-lg transition"
                        >
                          <ShieldCheck className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleDownload(report.id, report.original_filename)}
                          title="Download Original Report"
                          className="p-2 text-slate-600 hover:text-emerald-600 hover:bg-slate-100 rounded-lg transition"
                        >
                          <Download className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleDelete(report.id)}
                          disabled={deletingId === report.id}
                          title="Delete Report"
                          className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
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
