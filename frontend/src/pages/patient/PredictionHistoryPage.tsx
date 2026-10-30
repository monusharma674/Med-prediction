import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Activity,
  Heart,
  Calendar,
  ChevronRight,
  Filter,
  ShieldAlert,
  Loader2,
  FileText,
  Clock,
} from 'lucide-react';
import { predictionService, PredictionResult } from '../../services/predictionService';

export const PredictionHistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [predictions, setPredictions] = useState<PredictionResult[]>([]);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    loadHistory();
  }, [selectedFilter]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const diseaseParam = selectedFilter === 'all' ? undefined : selectedFilter;
      const data = await predictionService.getHistory(diseaseParam);
      setPredictions(data);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load prediction history.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Prediction History</h1>
          <p className="text-sm text-gray-500 mt-1">
            Review past disease risk assessments, biomarker scores, and classification outcomes.
          </p>
        </div>
        <Link
          to="/patient/predictions/select"
          className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-semibold shadow-sm flex items-center gap-2 self-start sm:self-auto"
        >
          <Activity className="w-4 h-4" /> Run New Prediction
        </Link>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 pb-2">
        <Filter className="w-4 h-4 text-gray-400 mr-1" />
        <span className="text-xs font-semibold text-gray-500 uppercase mr-2">Filter Disease:</span>
        {[
          { key: 'all', label: 'All Predictions' },
          { key: 'diabetes', label: 'Diabetes' },
          { key: 'heart_disease', label: 'Heart Disease' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setSelectedFilter(tab.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              selectedFilter === tab.key
                ? 'bg-teal-100 text-teal-800'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh]">
          <Loader2 className="w-8 h-8 text-teal-600 animate-spin mb-3" />
          <p className="text-sm text-gray-500">Loading prediction records...</p>
        </div>
      ) : predictions.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center space-y-4">
          <Clock className="w-12 h-12 text-gray-400 mx-auto" />
          <h3 className="text-lg font-bold text-gray-800">No Predictions Found</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            You haven't run any disease predictions yet. Upload a medical report or select a model to start.
          </p>
          <Link
            to="/patient/predictions/select"
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold rounded-lg"
          >
            Run First Prediction
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                <tr>
                  <th className="px-6 py-3.5">Disease Target</th>
                  <th className="px-6 py-3.5">Prediction Outcome</th>
                  <th className="px-6 py-3.5">Risk Score / Prob</th>
                  <th className="px-6 py-3.5">Source Report</th>
                  <th className="px-6 py-3.5">Date Assessed</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {predictions.map((p) => {
                  const isHigh =
                    p.prediction_class.toLowerCase().includes('positive') ||
                    p.prediction_class.toLowerCase().includes('high');
                  const isHeart = p.disease_name.includes('heart');

                  return (
                    <tr key={p.id} className="hover:bg-gray-50/60 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                              isHeart ? 'bg-rose-100 text-rose-600' : 'bg-teal-100 text-teal-700'
                            }`}
                          >
                            {isHeart ? <Heart className="w-4 h-4" /> : <Activity className="w-4 h-4" />}
                          </div>
                          <div>
                            <div className="font-bold text-gray-900">{p.display_name}</div>
                            <div className="text-xs text-gray-500">v{p.model_version_used}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                            isHigh
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isHigh ? 'bg-rose-600' : 'bg-emerald-600'
                            }`}
                          />
                          {p.prediction_class}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-semibold text-gray-900">
                          {p.probability !== undefined && p.probability !== null
                            ? `${(p.probability * 100).toFixed(1)}%`
                            : p.model_score.toFixed(3)}
                        </div>
                        <div className="text-[10px] text-gray-400">{p.score_label}</div>
                      </td>
                      <td className="px-6 py-4">
                        {p.report_id ? (
                          <Link
                            to={`/patient/reports/${p.report_id}`}
                            className="text-xs font-medium text-teal-600 hover:text-teal-800 flex items-center gap-1"
                          >
                            <FileText className="w-3.5 h-3.5" /> Report #{p.report_id}
                          </Link>
                        ) : (
                          <span className="text-xs text-gray-400">Direct Entry</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-xs text-gray-500">
                        {new Date(p.predicted_at).toLocaleDateString()}{' '}
                        <span className="text-gray-400">
                          {new Date(p.predicted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/patient/predictions/${p.id}`}
                          className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-lg inline-flex items-center gap-1"
                        >
                          View Details <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
