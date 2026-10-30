import api from './api';

export interface ModelMetadata {
  disease_name: string;
  display_name: string;
  model_version: string;
  algorithm: string;
  dataset_source: string;
  required_features: string[];
  feature_units: Record<string, string>;
  evaluation_metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
    roc_auc: number;
    sensitivity?: number;
    specificity?: number;
    brier_score?: number;
  };
  limitations?: string;
  is_calibrated: boolean;
  score_label: string;
}

export interface DiseaseEligibility {
  disease_name: string;
  display_name: string;
  is_supported: boolean;
  is_eligible: boolean;
  can_auto_impute: boolean;
  available_features: string[];
  missing_features: string[];
  strictly_required_missing: string[];
}

export interface EligibilityResponse {
  report_id: number | null;
  extracted_features: Record<string, { value: number; unit: string; provenance: string }>;
  diseases: DiseaseEligibility[];
}

export interface MissingFeature {
  feature_name: string;
  unit: string;
  display_name: string;
  default_value?: number;
}

export interface PredictionPayload {
  disease_name: string;
  report_id?: number | null;
  inputs: Record<string, number>;
  input_provenance: Record<string, string>;
}

export interface PredictionResult {
  id: number;
  disease_name: string;
  display_name: string;
  prediction_class: string;
  model_score: number;
  probability?: number | null;
  is_calibrated_probability: boolean;
  score_label: string;
  input_features: Record<string, any>;
  input_provenance: Record<string, string>;
  model_version_used: string;
  clinical_disclaimer: string;
  predicted_at: string;
  report_id?: number | null;
}

export const predictionService = {
  async getModels(): Promise<ModelMetadata[]> {
    const res = await api.get('/predictions/models');
    return res.data;
  },

  async checkEligibility(reportId?: number): Promise<EligibilityResponse> {
    const params = reportId ? { report_id: reportId } : {};
    const res = await api.get('/predictions/eligibility', { params });
    return res.data;
  },

  async getMissingInputs(diseaseName: string, reportId?: number): Promise<MissingFeature[]> {
    const params: any = { disease_name: diseaseName };
    if (reportId) params.report_id = reportId;
    const res = await api.get('/predictions/missing-inputs', { params });
    return res.data;
  },

  async runPrediction(payload: PredictionPayload): Promise<PredictionResult> {
    const res = await api.post('/predictions/run', payload);
    return res.data;
  },

  async getHistory(diseaseName?: string): Promise<PredictionResult[]> {
    const params = diseaseName ? { disease_name: diseaseName } : {};
    const res = await api.get('/predictions/history', { params });
    return res.data;
  },

  async getPrediction(id: number): Promise<PredictionResult> {
    const res = await api.get(`/predictions/${id}`);
    return res.data;
  },
};
