import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  Activity,
  Heart,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ChevronRight,
  ShieldAlert,
  FileText,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import {
  predictionService,
  EligibilityResponse,
  DiseaseEligibility,
  MissingFeature,
} from '../../services/predictionService';

export const DiseaseSelectionPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const reportIdParam = searchParams.get('report_id');
  const reportId = reportIdParam ? parseInt(reportIdParam, 10) : undefined;

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [eligibility, setEligibility] = useState<EligibilityResponse | null>(null);
  const [selectedDisease, setSelectedDisease] = useState<string>('diabetes');
  const [missingFeatures, setMissingFeatures] = useState<MissingFeature[]>([]);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    loadEligibility();
  }, [reportId]);

  useEffect(() => {
    if (selectedDisease) {
      loadMissingInputs(selectedDisease);
    }
  }, [selectedDisease, reportId]);

  const loadEligibility = async () => {
    try {
      setLoading(true);
      const res = await predictionService.checkEligibility(reportId);
      setEligibility(res);
      if (res.diseases.length > 0) {
        setSelectedDisease(res.diseases[0].disease_name);
      }
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Failed to load model eligibility.');
    } finally {
      setLoading(false);
    }
  };

  const loadMissingInputs = async (disease: string) => {
    try {
      const missing = await predictionService.getMissingInputs(disease, reportId);
      setMissingFeatures(missing);
      // Pre-fill defaults if present
      const initial: Record<string, string> = {};
      missing.forEach((f) => {
        if (f.default_value !== undefined && f.default_value !== null) {
          initial[f.feature_name] = f.default_value.toString();
        }
      });
      setFormValues((prev) => ({ ...initial, ...prev }));
    } catch (err: any) {
      console.error('Failed to load missing fields:', err);
    }
  };

  const handleInputChange = (featureName: string, value: string) => {
    setFormValues((prev) => ({ ...prev, [featureName]: value }));
  };

  const handleRunPrediction = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Validate inputs
    const inputs: Record<string, number> = {};
    const provenance: Record<string, string> = {};

    for (const f of missingFeatures) {
      const val = formValues[f.feature_name];
      if (val === undefined || val === '') {
        setErrorMessage(`Please provide a value for '${f.display_name}'.`);
        return;
      }
      const num = parseFloat(val);
      if (isNaN(num)) {
        setErrorMessage(`'${f.display_name}' must be a valid number.`);
        return;
      }
      inputs[f.feature_name] = num;
      provenance[f.feature_name] = 'patient_entered';
    }

    try {
      setSubmitting(true);
      const res = await predictionService.runPrediction({
        disease_name: selectedDisease,
        report_id: reportId || null,
        inputs,
        input_provenance: provenance,
      });
      navigate(`/patient/predictions/${res.id}`);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Prediction failed. Please verify inputs.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-10 h-10 text-teal-600 animate-spin mb-4" />
        <p className="text-gray-600 font-medium">Evaluating disease prediction models...</p>
      </div>
    );
  }

  const selectedModelEligibility = eligibility?.diseases.find(
    (d) => d.disease_name === selectedDisease
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Disease Risk Prediction</h1>
        <p className="text-sm text-gray-500 mt-1">
          Select a clinical disease model, review extracted medical biomarkers, and provide any missing indicators.
        </p>
      </div>

      {/* Medical Disclaimer Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start gap-3 text-amber-900 text-sm">
        <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Research & Demonstration Use Only:</span> These machine learning models
          are trained on benchmark clinical datasets for educational demonstration. They do not constitute certified
          medical diagnosis or replace professional consultation.
        </div>
      </div>

      {/* Report Context Banner if linked */}
      {reportId && (
        <div className="bg-teal-50 border border-teal-200 rounded-lg p-4 flex items-center justify-between text-teal-900">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-teal-600" />
            <div>
              <span className="font-semibold text-sm">Linked to Report #{reportId}</span>
              <p className="text-xs text-teal-700">
                Values extracted from this report will be automatically mapped into model features.
              </p>
            </div>
          </div>
          <Link
            to={`/patient/reports/${reportId}`}
            className="text-xs font-semibold text-teal-700 hover:text-teal-900 underline"
          >
            View Original Report
          </Link>
        </div>
      )}

      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-800 p-4 rounded-lg text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0 text-red-600" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Disease Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {eligibility?.diseases.map((d) => {
          const isSelected = d.disease_name === selectedDisease;
          const isHeart = d.disease_name.includes('heart');
          return (
            <div
              key={d.disease_name}
              onClick={() => setSelectedDisease(d.disease_name)}
              className={`p-5 rounded-xl border-2 cursor-pointer transition-all ${
                isSelected
                  ? 'border-teal-600 bg-teal-50/40 shadow-sm ring-1 ring-teal-600'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                      isHeart ? 'bg-rose-100 text-rose-600' : 'bg-teal-100 text-teal-700'
                    }`}
                  >
                    {isHeart ? <Heart className="w-6 h-6" /> : <Activity className="w-6 h-6" />}
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900">{d.display_name}</h3>
                    <p className="text-xs text-gray-500">
                      {d.strictly_required_missing.length === 0
                        ? 'All mandatory features satisfied'
                        : `${d.strictly_required_missing.length} additional parameter(s) required`}
                    </p>
                  </div>
                </div>

                {/* Status Badge */}
                {d.is_eligible ? (
                  <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Eligible
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full bg-amber-100 text-amber-800">
                    <HelpCircle className="w-3.5 h-3.5" /> Inputs Needed
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Prediction Execution Section */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-6">
        <div className="border-b border-gray-100 pb-4">
          <h2 className="text-lg font-bold text-gray-900">
            Configure Features: {selectedModelEligibility?.display_name}
          </h2>
          <p className="text-xs text-gray-500">
            Features extracted from the medical report are locked with proof of origin. Fill in any missing patient parameters below.
          </p>
        </div>

        {/* Extracted Features from Report */}
        {eligibility && Object.keys(eligibility.extracted_features).length > 0 && (
          <div>
            <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
              Autofilled Biomarkers (From Medical Report)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(eligibility.extracted_features).map(([key, item]) => (
                <div key={key} className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                    <span className="font-medium text-gray-700 capitalize">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase bg-teal-100 text-teal-800">
                      {item.provenance}
                    </span>
                  </div>
                  <div className="text-base font-bold text-gray-900">
                    {item.value}{' '}
                    <span className="text-xs font-normal text-gray-500">{item.unit}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Form for Missing Features */}
        <form onSubmit={handleRunPrediction} className="space-y-4">
          {missingFeatures.length > 0 ? (
            <div>
              <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-3">
                Required Patient Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {missingFeatures.map((f) => (
                  <div key={f.feature_name} className="space-y-1">
                    <label className="block text-xs font-medium text-gray-700">
                      {f.display_name}{' '}
                      <span className="text-gray-400 font-normal">({f.unit})</span>
                    </label>
                    <input
                      type="number"
                      step="any"
                      required
                      placeholder={`e.g. ${f.default_value !== undefined ? f.default_value : ''}`}
                      value={formValues[f.feature_name] || ''}
                      onChange={(e) => handleInputChange(f.feature_name, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none"
                    />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span>All required inputs for this model are already satisfied from your medical report!</span>
            </div>
          )}

          <div className="pt-4 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/patient/dashboard')}
              className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold rounded-lg shadow-sm flex items-center gap-2 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running Inference Pipeline...
                </>
              ) : (
                <>
                  Run Disease Prediction
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
