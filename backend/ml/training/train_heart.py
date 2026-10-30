import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    brier_score_loss,
)

UCI_HEART_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
LOCAL_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "heart_disease.csv")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "artifacts")

RAW_COLUMNS = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
    "target",
]

STANDARDIZED_COLUMNS = [
    "age",
    "sex",
    "chest_pain_type",
    "resting_blood_pressure",
    "serum_cholesterol",
    "fasting_blood_sugar",
    "resting_ecg",
    "max_heart_rate",
    "exercise_induced_angina",
    "st_depression",
    "st_slope",
    "num_major_vessels",
    "thalassemia",
    "target",
]


def load_heart_data() -> pd.DataFrame:
    """Loads Cleveland Heart Disease dataset, handles '?' missing tokens and standardizes columns."""
    os.makedirs(os.path.dirname(LOCAL_CSV_PATH), exist_ok=True)
    if os.path.exists(LOCAL_CSV_PATH):
        print(f"Loading cached dataset from {LOCAL_CSV_PATH}")
        df = pd.read_csv(LOCAL_CSV_PATH)
    else:
        print(f"Fetching dataset from {UCI_HEART_URL}...")
        df = pd.read_csv(UCI_HEART_URL, header=None, names=RAW_COLUMNS, na_values="?")
        # Binary target: 0 = no disease, >0 = disease present
        df["target"] = (df["target"] > 0).astype(int)
        df.columns = STANDARDIZED_COLUMNS
        df.to_csv(LOCAL_CSV_PATH, index=False)
        print(f"Dataset cached at {LOCAL_CSV_PATH}")
    return df


def train_heart_model():
    print("==================================================")
    print("  TRAINING HEART DISEASE RISK PREDICTION MODEL    ")
    print("==================================================")

    df = load_heart_data()
    print(f"Dataset shape: {df.shape} (Samples: {len(df)})")

    # Binary classification target
    X = df.drop(columns=["target"])
    y = df["target"]

    feature_names = list(X.columns)

    # Stratified Leakage-Safe Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Impute missing values with median, scale continuous features
    preprocessor = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    candidates = {
        "LogisticRegression": Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(random_state=42, max_iter=1000)),
        ]),
        "RandomForest": Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)),
        ]),
        "GradientBoosting": Pipeline([
            ("preprocessor", preprocessor),
            ("classifier", GradientBoostingClassifier(n_estimators=80, learning_rate=0.08, max_depth=3, random_state=42)),
        ]),
    }

    best_name = None
    best_pipe = None
    best_f1 = -1.0

    print("\nModel Cross-Validation Comparison (5-Fold Stratified):")
    for name, pipe in candidates.items():
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_res = cross_validate(pipe, X_train, y_train, cv=skf, scoring=["f1", "roc_auc"])
        f1_mean = float(cv_res["test_f1"].mean())
        f1_std = float(cv_res["test_f1"].std())
        auc_mean = float(cv_res["test_roc_auc"].mean())
        print(f"  - {name:20s}: Mean F1 = {f1_mean:.4f} (+/- {f1_std:.4f}) | Mean AUC = {auc_mean:.4f}")
        if f1_mean > best_f1:
            best_f1 = f1_mean
            best_name = name
            best_pipe = pipe

    print(f"\nSelected Best Model: {best_name} (Validation F1 = {best_f1:.4f})")

    # Fit best model on training set
    best_pipe.fit(X_train, y_train)

    # Evaluate on test set
    y_pred = best_pipe.predict(X_test)
    y_proba = best_pipe.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred))
    rec = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    auc = float(roc_auc_score(y_test, y_proba))
    brier = float(brier_score_loss(y_test, y_proba))
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]
    sensitivity = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

    print("\n--- Test Set Evaluation Metrics ---")
    print(f"  Accuracy:    {acc:.4f}")
    print(f"  Precision:   {prec:.4f}")
    print(f"  Recall:      {rec:.4f} (Sensitivity: {sensitivity:.4f})")
    print(f"  Specificity: {specificity:.4f}")
    print(f"  F1-Score:    {f1:.4f}")
    print(f"  ROC-AUC:     {auc:.4f}")
    print(f"  Brier Score: {brier:.4f}")
    print(f"  Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")

    # Serialize artifacts
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    model_path = os.path.join(ARTIFACTS_DIR, "heart_model.joblib")
    joblib.dump(best_pipe, model_path)
    print(f"\nTrained Pipeline serialized to: {model_path}")

    metadata = {
        "disease_name": "heart_disease",
        "display_name": "Coronary Heart Disease Risk Prediction",
        "model_version": "1.0.0",
        "algorithm": best_name,
        "dataset_source": "UCI Heart Disease Repository (Cleveland Clinic Foundation)",
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "training_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "required_features": feature_names,
        "feature_order": feature_names,
        "feature_units": {
            "age": "years",
            "sex": "binary (1=M, 0=F)",
            "chest_pain_type": "category (1-4)",
            "resting_blood_pressure": "mmHg",
            "serum_cholesterol": "mg/dL",
            "fasting_blood_sugar": "binary (1 if >120 mg/dL, 0 otherwise)",
            "resting_ecg": "category (0-2)",
            "max_heart_rate": "bpm",
            "exercise_induced_angina": "binary (1=yes, 0=no)",
            "st_depression": "mm",
            "st_slope": "category (1-3)",
            "num_major_vessels": "count (0-3)",
            "thalassemia": "category (3, 6, 7)",
        },
        "feature_defaults_for_missing": {
            "chest_pain_type": 1,
            "resting_ecg": 0,
            "exercise_induced_angina": 0,
            "st_depression": 0.0,
            "st_slope": 1,
            "num_major_vessels": 0,
            "thalassemia": 3,
        },
        "evaluation_metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(auc, 4),
            "sensitivity": round(sensitivity, 4),
            "specificity": round(specificity, 4),
            "brier_score": round(brier, 4),
            "confusion_matrix": {
                "true_negative": tn,
                "false_positive": fp,
                "false_negative": fn,
                "true_positive": tp,
            },
        },
        "is_calibrated": False,
        "score_label": "Model Risk Score",
        "limitations": "Trained on Cleveland Clinic historical cohort (303 patients). Does not substitute for clinical angiography or multi-slice CT coronary scanning.",
    }

    meta_path = os.path.join(ARTIFACTS_DIR, "heart_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Model Metadata saved to: {meta_path}")

    return metadata


if __name__ == "__main__":
    train_heart_model()
