import React, { useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { reportService } from '../../services/reportService';
import { MedicalReport } from '../../types/report';
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Shield,
  Copy,
  Check,
  Calendar,
  Layers,
  X,
} from 'lucide-react';

export const UploadReportPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState('Complete Blood Count & Metabolic Panel');
  const [reportDate, setReportDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedReport, setUploadedReport] = useState<MedicalReport | null>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const categories = [
    'Complete Blood Count & Metabolic Panel',
    'Blood Glucose & Glycated Hemoglobin (HbA1c)',
    'Lipid Profile & Cholesterol Panel',
    'Renal / Kidney Function Test (KFT)',
    'Liver Function Test (LFT)',
    'Thyroid Function Panel',
    'General Clinical Biochemistry',
  ];

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleSelectedFile(e.target.files[0]);
    }
  };

  const handleSelectedFile = (selectedFile: File) => {
    setError(null);
    const validExtensions = ['pdf', 'png', 'jpg', 'jpeg'];
    const ext = selectedFile.name.split('.').pop()?.toLowerCase();

    if (!ext || !validExtensions.includes(ext)) {
      setError(`Invalid file type. Allowed formats: PDF, PNG, JPG, JPEG.`);
      return;
    }

    if (selectedFile.size > 15 * 1024 * 1024) {
      setError('File size exceeds 15MB limit.');
      return;
    }

    setFile(selectedFile);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a valid report file first.');
      return;
    }

    setError(null);
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('report_category', category);
      formData.append('report_date', reportDate);

      const report = await reportService.uploadReport(formData);
      setUploadedReport(report);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 'Failed to upload report. Please check file format.'
      );
    } finally {
      setUploading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Upload Clinical Lab Report
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          Upload your blood test or biochemical lab report. Our server calculates a cryptographic SHA-256 digest on ingestion and prepares the document for OCR parameter extraction.
        </p>
      </div>

      {uploadedReport ? (
        /* Success Card with SHA-256 Badge */
        <div className="bg-white rounded-3xl border border-emerald-200 p-8 shadow-xl shadow-emerald-500/5 space-y-6">
          <div className="flex items-center space-x-3 text-emerald-600">
            <div className="w-12 h-12 rounded-2xl bg-emerald-100 flex items-center justify-center">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Medical Report Uploaded & Hashed Successfully!
              </h2>
              <p className="text-xs text-slate-500">
                Report UUID: <span className="font-mono font-semibold text-slate-700">{uploadedReport.report_uuid}</span>
              </p>
            </div>
          </div>

          {/* Cryptographic SHA-256 Hash Card */}
          <div className="p-5 bg-slate-900 text-white rounded-2xl space-y-2">
            <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
              <span className="flex items-center space-x-1.5">
                <Shield className="w-4 h-4 text-sky-400" />
                <span>SHA-256 Cryptographic Checksum</span>
              </span>
              <button
                type="button"
                onClick={() => copyToClipboard(uploadedReport.file_hash_sha256)}
                className="flex items-center space-x-1 text-sky-400 hover:text-sky-300 text-xs transition"
              >
                {copiedHash ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedHash ? 'Copied' : 'Copy Hash'}</span>
              </button>
            </div>
            <p className="font-mono text-sm text-sky-200 break-all select-all">
              {uploadedReport.file_hash_sha256}
            </p>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              This 256-bit hash uniquely finger-prints the exact binary content of your file. Any tampering or unauthorized modification will instantly invalidate this hash.
            </p>
          </div>

          {/* Action CTAs */}
          <div className="flex flex-wrap gap-4 pt-2">
            <button
              onClick={() => navigate('/patient/reports')}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition"
            >
              <span>View in My Reports</span>
            </button>
            <button
              onClick={() => {
                setUploadedReport(null);
                setFile(null);
              }}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-sky-600 bg-sky-50 hover:bg-sky-100 transition"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Another Report</span>
            </button>
            <button
              onClick={() => navigate(`/patient/reports/${uploadedReport.id}`)}
              className="flex items-center space-x-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white bg-sky-600 hover:bg-sky-700 shadow-md shadow-sky-600/20 transition ml-auto"
            >
              <span>View Report Details</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      ) : (
        /* Upload Form */
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-start space-x-3 text-rose-800 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Metadata Selection */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-2 flex items-center space-x-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-500" />
                <span>Report Category</span>
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-2 flex items-center space-x-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                <span>Test / Report Date</span>
              </label>
              <input
                type="date"
                value={reportDate}
                onChange={(e) => setReportDate(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-xl text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>

          {/* Drag & Drop Upload Container */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-3xl p-10 text-center cursor-pointer transition-all ${
              dragActive
                ? 'border-sky-500 bg-sky-50/60 scale-[1.01]'
                : file
                ? 'border-emerald-400 bg-emerald-50/30'
                : 'border-slate-300 bg-white hover:border-sky-400 hover:bg-slate-50/50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="hidden"
            />

            {file ? (
              <div className="flex flex-col items-center space-y-3">
                <div className="w-14 h-14 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center">
                  <FileText className="w-7 h-7" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-base">{file.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready for processing
                  </p>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="inline-flex items-center space-x-1 text-xs text-rose-600 hover:text-rose-700 font-semibold mt-2"
                >
                  <X className="w-4 h-4" />
                  <span>Remove file</span>
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-3">
                <div className="w-14 h-14 rounded-2xl bg-sky-100 text-sky-600 flex items-center justify-center shadow-inner">
                  <Upload className="w-7 h-7" />
                </div>
                <div>
                  <p className="text-base font-semibold text-slate-800">
                    Click to select file or drag & drop report here
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Supported formats: <strong className="text-slate-700">PDF, PNG, JPG, JPEG</strong> (Max size: 15MB)
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!file || uploading}
            className="w-full flex items-center justify-center space-x-2 py-3 px-6 rounded-2xl font-bold text-white bg-sky-600 hover:bg-sky-700 shadow-lg shadow-sky-600/25 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? (
              <div className="flex items-center space-x-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Securing File & Calculating SHA-256...</span>
              </div>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                <span>Upload & Digest Report</span>
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
};
