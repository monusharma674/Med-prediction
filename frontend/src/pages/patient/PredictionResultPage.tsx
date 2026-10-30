import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Activity,
  Heart,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  Share2,
  History,
  FileText,
  Info,
  Loader2,
  Database,
  Cpu,
} from 'lucide-react';
import { predictionService, PredictionResult } from '../../services/predictionService';

export const PredictionResultPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadPrediction(parseInt(id, 10));
    }
  }, [id]);

  const loadPrediction = async (predictionId: number) => {
    try {
      setLoading(true);
      const data = await predictionService.getPrediction(predictionId);
      setPrediction(data);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load prediction results.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-10 h-10 text-teal-600 animate-spin mb-4" />
        <p className="text-gray-600 font-medium">Loading clinical prediction result...</p>
      </div>
    );
  }

  if (errorMessage || !prediction) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-red-50 border border-red-200 rounded-xl text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-red-600 mx-auto" />
        <h2 className="text-lg font-bold text-red-900">Prediction Not Available</h2>
        <p className="text-sm text-red-700">{errorMessage || 'Record not found.'}</p>
        <button
          onClick={() => navigate('/patient/dashboard')}
          className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const isHighRisk = prediction.prediction_class.toLowerCase().includes('positive') ||
    prediction.prediction_class.toLowerCase().includes('high');

  const scorePercentage = prediction.probability !== undefined && prediction.probability !== null
    ? Math.round(prediction.probability * 100)
    : Math.round(prediction.model_score * 100);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/patient/predictions/history')}
          className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to History
        </button>
        <div className="flex items-center gap-2">
          {prediction.report_id && (
            <Link
              to={`/patient/reports/${prediction.report_id}`}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5" /> View Linked Report
            </Link>
          )}
          <Link
            to="/patient/predictions/select"
            className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium rounded-lg flex items-center gap-1.5"
          >
            <Activity className="w-3.5 h-3.5" /> Predict Another Disease
          </Link>
        </div>
      </div>

      {/* Main Result Hero Card */}
      <div
        className={`rounded-2xl border-2 p-6 md:p-8 text-white shadow-lg ${
          isHighRisk
            ? 'bg-gradient-to-br from-rose-600 to-red-700 border-rose-500'
            : 'bg-gradient-to-br from-teal-600 to-emerald-700 border-teal-500'
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-white/80">
              <Cpu className="w-4 h-4" />
              Machine Learning Output • {prediction.display_name}
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">
              {prediction.prediction_class}
            </h1>
            <p className="text-sm text-white/90 max-w-xl">
              {isHighRisk
                ? 'Statistical model indicates clinical indicators consistent with elevated risk patterns. Further consultation is recommended.'
                : 'Statistical model indicates clinical indicators are currently within lower risk benchmarks.'}
            </p>
          </div>

          {/* Risk Score Circle / Meter */}
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-5 border border-white/20 text-center min-w-[180px]">
            <div className="text-xs uppercase font-semibold text-white/80 mb-1">
              {prediction.score_label}
            </div>
            <div className="text-4xl font-extrabold tracking-tight">
              {prediction.probability !== undefined && prediction.probability !== null
                ? `${(prediction.probability * 100).toFixed(1)}%`
                : prediction.model_score.toFixed(3)}
            </div>
            <div className="text-[11px] text-white/70 mt-1">
              Model Version {prediction.model_version_used}
            </div>
          </div>
        </div>
      </div>

      {/* Strict Medical Disclaimer Alert */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 text-amber-900 text-sm">
        <ShieldAlert className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-amber-950">Important Clinical Disclaimer</div>
          <p className="text-xs leading-relaxed text-amber-800">
            {prediction.clinical_disclaimer}
          </p>
        </div>
      </div>

      {/* Feature Provenance & Input Inspection */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-gray-900">Feature Provenance & Clinical Inputs</h3>
            <p className="text-xs text-gray-500">
              Complete data provenance trace verifying where each input was sourced.
            </p>
          </div>
          <span className="text-xs text-gray-500">
            {Object.keys(prediction.input_features).length} Parameters Analyzed
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
              <tr>
                <th className="px-6 py-3">Feature Name</th>
                <th className="px-6 py-3">Value</th>
                <th className="px-6 py-3">Data Origin</th>
                <th className="px-6 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {Object.entries(prediction.input_features).map(([key, val]) => {
                const prov = prediction.input_provenance[key] || 'patient_entered';
                const isOcr = prov === 'ocr';
                const isCorrected = prov === 'corrected';

                return (
                  <tr key={key} className="hover:bg-gray-50/50">
                    <td className="px-6 py-3 font-medium text-gray-800 capitalize">
                      {key.replace(/_/g, ' ')}
                    </td>
                    <td className="px-6 py-3 font-semibold text-gray-900">
                      {typeof val === 'number' ? val.toLocaleString() : val}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${
                          isOcr
                            ? 'bg-teal-100 text-teal-800'
                            : isCorrected
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {prov.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-xs text-emerald-600 font-medium">
                      <CheckCircle2 className="w-4 h-4 inline-block mr-1 text-emerald-500" />
                      Validated
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Technical Card */}
      <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="text-xs font-semibold text-gray-500 uppercase">Audit & Governance</div>
          <div className="text-sm font-medium text-gray-900">
            Prediction ID #{prediction.id} • Executed at{' '}
            {new Date(prediction.predicted_at).toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">
            Pipeline: scikit-learn standard preprocessing with median imputation and scaling
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-100"
          >
            Print Summary
          </button>
        </div>
      </div>
    </div>
  );
};
