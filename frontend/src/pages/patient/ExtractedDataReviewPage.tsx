import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import { reportService } from '../../services/reportService';
import { MedicalReport, ExtractedMedicalValue } from '../../types/report';
import {
  FileText,
  CheckCircle,
  AlertCircle,
  Edit2,
  Save,
  RotateCcw,
  Cpu,
  ArrowRight,
  ShieldCheck,
  Check,
  Sparkles,
} from 'lucide-react';

export const ExtractedDataReviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [report, setReport] = useState<MedicalReport | null>(null);
  const [values, setValues] = useState<ExtractedMedicalValue[]>([]);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [savingId, setSavingId] = useState<number | null>(null);

  const fetchReportAndValues = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const rep = await reportService.getReportDetails(parseInt(id));
      setReport(rep);

      const valRes = await api.get<ExtractedMedicalValue[]>(
        `/reports/${id}/extracted-values`
      );
      setValues(valRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load report data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReportAndValues();
  }, [id]);

  const handleTriggerExtraction = async () => {
    if (!id) return;
    try {
      setExtracting(true);
      setError(null);
      const res = await api.post<ExtractedMedicalValue[]>(`/reports/${id}/extract`);
      setValues(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Extraction failed.');
    } finally {
      setExtracting(false);
    }
  };

  const handleSaveCorrection = async (valId: number) => {
    const num = parseFloat(editValue);
    if (isNaN(num)) {
      alert('Please enter a valid numeric parameter value.');
      return;
    }

    try {
      setSavingId(valId);
      const res = await api.patch<ExtractedMedicalValue>(
        `/reports/${id}/extracted-values/${valId}`,
        { value_corrected: num }
      );
      setValues((prev) => prev.map((v) => (v.id === valId ? res.data : v)));
      setEditingId(null);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update value.');
    } finally {
      setSavingId(null);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-3xl border border-slate-200 p-16 text-center">
        <div className="w-8 h-8 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
        <p className="text-sm font-medium text-slate-600">Analyzing OCR biometric parameters...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-rose-800 text-sm flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
        <span>{error || 'Report not found.'}</span>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            <Link to="/patient/reports" className="hover:text-sky-600">
              My Reports
            </Link>
            <span>/</span>
            <Link to={`/patient/reports/${report.id}`} className="hover:text-sky-600">
              {report.report_uuid}
            </Link>
            <span>/</span>
            <span className="text-slate-800">Extracted Medical Data</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
            Extracted Clinical Data Review
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Review automatically extracted diagnostic parameters. Verify accuracy and correct any OCR discrepancies before disease prediction.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleTriggerExtraction}
            disabled={extracting}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-semibold text-sm hover:bg-slate-100 transition shadow-sm disabled:opacity-50"
          >
            {extracting ? (
              <div className="w-4 h-4 border-2 border-sky-600 border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <RotateCcw className="w-4 h-4" />
            )}
            <span>{extracting ? 'Processing OCR...' : 'Re-Run OCR Extraction'}</span>
          </button>

          <button
            onClick={() => navigate(`/patient/predict?report_id=${report.id}`)}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-md shadow-emerald-600/20 transition"
          >
            <Cpu className="w-4 h-4" />
            <span>Proceed to Prediction</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Values Table */}
      {values.length === 0 ? (
        <div className="bg-white rounded-3xl border border-slate-200 p-16 text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center mx-auto">
            <Sparkles className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">No Parameters Extracted Yet</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
              Run the intelligent OCR pipeline on this report to extract blood sugar, lipid panel, and kidney markers automatically.
            </p>
          </div>
          <button
            onClick={handleTriggerExtraction}
            disabled={extracting}
            className="inline-flex items-center space-x-2 px-6 py-3 rounded-2xl font-bold text-white bg-sky-600 hover:bg-sky-700 shadow-lg shadow-sky-600/20 transition"
          >
            <RotateCcw className="w-5 h-5" />
            <span>Extract Medical Parameters Now</span>
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
            <p className="text-xs uppercase tracking-wider font-bold text-slate-600">
              Found {values.length} Validated Clinical Parameters
            </p>
            <p className="text-xs text-slate-500">
              Both original OCR scan values and your manual corrections are preserved for provenance.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 text-xs uppercase tracking-wider font-semibold">
                <tr>
                  <th className="px-6 py-4">Clinical Test Name</th>
                  <th className="px-6 py-4">Active Value</th>
                  <th className="px-6 py-4">Unit</th>
                  <th className="px-6 py-4">Reference Interval</th>
                  <th className="px-6 py-4">Confidence & Provenance</th>
                  <th className="px-6 py-4 text-right">Correct Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {values.map((v) => (
                  <tr key={v.id} className="hover:bg-slate-50/60 transition">
                    <td className="px-6 py-4">
                      <p className="font-bold text-slate-900">{v.test_name_raw}</p>
                      <p className="text-xs text-slate-400 font-mono">{v.test_name_standardized}</p>
                    </td>

                    <td className="px-6 py-4">
                      {editingId === v.id ? (
                        <input
                          type="number"
                          step="any"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="w-24 px-2 py-1 border border-sky-500 rounded-lg text-sm font-bold bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
                        />
                      ) : (
                        <div className="flex items-center space-x-2">
                          <span className="font-extrabold text-base text-slate-900">
                            {v.final_value ?? v.value_original}
                          </span>
                          {v.is_manually_corrected && (
                            <span className="text-[10px] bg-sky-100 text-sky-800 font-bold px-1.5 py-0.5 rounded">
                              Orig: {v.value_original}
                            </span>
                          )}
                        </div>
                      )}
                    </td>

                    <td className="px-6 py-4">
                      <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-1 rounded-md">
                        {v.unit_normalized || v.unit_original || '-'}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-500">
                      {v.reference_range || 'Standard range'}
                    </td>

                    <td className="px-6 py-4">
                      <div className="flex flex-col space-y-1">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-emerald-500 rounded-full"
                              style={{ width: `${(v.ocr_confidence || 0.95) * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-[11px] font-semibold text-slate-600">
                            {Math.round((v.ocr_confidence || 0.95) * 100)}%
                          </span>
                        </div>
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full w-max ${
                            v.data_source === 'corrected'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          Source: {v.data_source}
                        </span>
                      </div>
                    </td>

                    <td className="px-6 py-4 text-right">
                      {editingId === v.id ? (
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleSaveCorrection(v.id)}
                            disabled={savingId === v.id}
                            className="p-1.5 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition"
                            title="Save Correction"
                          >
                            <Save className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="p-1.5 bg-slate-200 text-slate-600 rounded-lg hover:bg-slate-300 transition"
                            title="Cancel"
                          >
                            <RotateCcw className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => {
                            setEditingId(v.id);
                            setEditValue(String(v.final_value ?? v.value_original));
                          }}
                          className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                          <span>Correct</span>
                        </button>
                      )}
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
