import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
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

# Benchmark Pima Indians Diabetes dataset URL (raw verified UCI archive)
PIMA_DATASET_URL = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
LOCAL_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "diabetes.csv")
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "..", "artifacts")

COLUMN_NAMES = [
    "pregnancies",
    "glucose_mg_dl",
    "blood_pressure_mmhg",
    "skin_thickness_mm",
    "insulin_uiu_ml",
    "bmi",
    "diabetes_pedigree_function",
    "age",
    "outcome",
]

# Biological zero fields where 0 indicates missing measurement
ZERO_AS_MISSING_COLS = [
    "glucose_mg_dl",
    "blood_pressure_mmhg",
    "skin_thickness_mm",
    "insulin_uiu_ml",
    "bmi",
]


def load_diabetes_data() -> pd.DataFrame:
    """Loads Pima Indians Diabetes dataset from local cache or remote source."""
    os.makedirs(os.path.dirname(LOCAL_CSV_PATH), exist_ok=True)
    if os.path.exists(LOCAL_CSV_PATH):
        print(f"Loading cached dataset from {LOCAL_CSV_PATH}")
        df = pd.read_csv(LOCAL_CSV_PATH)
    else:
        print(f"Fetching dataset from {PIMA_DATASET_URL}...")
        df = pd.read_csv(PIMA_DATASET_URL, header=None, names=COLUMN_NAMES)
        df.to_csv(LOCAL_CSV_PATH, index=False)
        print(f"Dataset cached at {LOCAL_CSV_PATH}")
    return df


def train_diabetes_model():
    print("==================================================")
    print("  TRAINING DIABETES RISK PREDICTION MODEL (ML)   ")
    print("==================================================")

    df = load_diabetes_data()
    print(f"Dataset shape: {df.shape} (Samples: {len(df)})")

    # 1. Missing Value Analysis: Replace impossible 0s with NaN
    df_clean = df.copy()
    for col in ZERO_AS_MISSING_COLS:
        missing_count = (df_clean[col] == 0).sum()
        print(f"  Feature '{col}': {missing_count} zeros coded as missing ({missing_count/len(df)*100:.1f}%)")
        df_clean[col] = df_clean[col].replace(0, np.nan)

    X = df_clean.drop(columns=["outcome"])
    y = df_clean["outcome"]

    # 2. Stratified Leakage-Safe Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # 3. Algorithms Comparison
    candidates = {
        "LogisticRegression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(random_state=42, max_iter=1000)),
        ]),
        "RandomForest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)),
        ]),
        "GradientBoosting": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", GradientBoostingClassifier(n_estimators=100, learning_rate=0.08, max_depth=3, random_state=42)),
        ]),
    }

    best_name = None
    best_pipe = None
    best_f1 = -1.0

    print("\nModel Cross-Validation Comparison (5-Fold Stratified):")
    for name, pipe in candidates.items():
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_res = cross_validate(pipe, X_train, y_train, cv=skf, scoring=["f1", "roc_auc"])
        f1_mean = cv_res["test_f1"].mean()
        f1_std = cv_res["test_f1"].std()
        auc_mean = cv_res["test_roc_auc"].mean()
        print(f"  - {name:20s}: Mean F1 = {f1_mean:.4f} (+/- {f1_std:.4f}) | Mean AUC = {auc_mean:.4f}")
        if f1_mean > best_f1:
            best_f1 = f1_mean
            best_name = name
            best_pipe = pipe

    print(f"\nSelected Best Model: {best_name} (Validation F1 = {best_f1:.4f})")

    # 4. Final Training on Training Set
    best_pipe.fit(X_train, y_train)

    # 5. Rigorous Evaluation on Unseen Test Set
    y_pred = best_pipe.predict(X_test)
    y_proba = best_pipe.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    brier = brier_score_loss(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    sensitivity = tp / (tp + fn)
    specificity = tn / (tn + fp)

    print("\n--- Test Set Evaluation Metrics ---")
    print(f"  Accuracy:    {acc:.4f}")
    print(f"  Precision:   {prec:.4f}")
    print(f"  Recall:      {rec:.4f} (Sensitivity: {sensitivity:.4f})")
    print(f"  Specificity: {specificity:.4f}")
    print(f"  F1-Score:    {f1:.4f}")
    print(f"  ROC-AUC:     {auc:.4f}")
    print(f"  Brier Score: {brier:.4f} (Probability Calibration Loss)")
    print(f"  Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")

    # 6. Save Pipeline & Model Artifacts
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    model_path = os.path.join(ARTIFACTS_DIR, "diabetes_model.joblib")
    joblib.dump(best_pipe, model_path)
    print(f"\nTrained Pipeline serialized to: {model_path}")

    # 7. Metadata JSON
    metadata = {
        "disease_name": "diabetes",
        "display_name": "Type 2 Diabetes Risk Prediction",
        "model_version": "1.0.0",
        "algorithm": best_name,
        "dataset_source": "Pima Indians Diabetes Database (NIDDK / UCI)",
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "training_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "required_features": [
            "pregnancies",
            "glucose_mg_dl",
            "blood_pressure_mmhg",
            "skin_thickness_mm",
            "insulin_uiu_ml",
            "bmi",
            "diabetes_pedigree_function",
            "age",
        ],
        "feature_order": list(X.columns),
        "feature_units": {
            "pregnancies": "count",
            "glucose_mg_dl": "mg/dL",
            "blood_pressure_mmhg": "mmHg",
            "skin_thickness_mm": "mm",
            "insulin_uiu_ml": "µU/mL",
            "bmi": "kg/m²",
            "diabetes_pedigree_function": "score",
            "age": "years",
        },
        "feature_defaults_for_missing": {
            "pregnancies": 0,
            "skin_thickness_mm": 23.0,
            "insulin_uiu_ml": 79.0,
            "diabetes_pedigree_function": 0.37,
        },
        "evaluation_metrics": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(auc), 4),
            "sensitivity": round(float(sensitivity), 4),
            "specificity": round(float(specificity), 4),
            "brier_score": round(float(brier), 4),
            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp),
            },
        },
        "is_calibrated": False,
        "score_label": "Model Risk Score",
        "limitations": "Trained on female cohort of Pima Indian heritage (>=21 yrs). Generalization across diverse international demographics requires local clinical validation.",
    }

    meta_path = os.path.join(ARTIFACTS_DIR, "diabetes_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Model Metadata saved to: {meta_path}")

    return metadata


if __name__ == "__main__":
    train_diabetes_model()
