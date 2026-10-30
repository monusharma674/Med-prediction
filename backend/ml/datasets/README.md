# Machine Learning Datasets Documentation

This directory houses the benchmark clinical datasets utilized to train the disease prediction models. In compliance with strict research integrity rules, **no fabricated or synthetic values are used for model training**.

---

## 1. Diabetes Risk Prediction Dataset

- **Primary Source:** National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK)
- **Archive Source:** UCI Machine Learning Repository / Kaggle Pima Indians Diabetes Database
- **Clinical Target:** Presence or absence of Type 2 Diabetes within 5 years (`Outcome`: 0 = Negative, 1 = Positive)
- **Cohort:** Female patients of Pima Indian heritage, at least 21 years of age

### Feature Schema & Biological Constraints
| Feature Name | Clinical Description | Accepted Unit | Biological Min-Max | Zero-Imputation Rule |
|---|---|---|---|---|
| `Pregnancies` | Number of times pregnant | Count | 0 – 17 | 0 is valid (non-missing) |
| `Glucose` | Plasma glucose concentration (2 hours in OGTT or Fasting) | mg/dL | 40 – 300 | 0 represents MISSING; median imputed |
| `BloodPressure` | Diastolic blood pressure | mm Hg | 40 – 140 | 0 represents MISSING; median imputed |
| `SkinThickness` | Triceps skin fold thickness | mm | 5 – 99 | 0 represents MISSING; median imputed |
| `Insulin` | 2-Hour serum insulin | µU/mL | 10 – 850 | 0 represents MISSING; median imputed |
| `BMI` | Body Mass Index (weight in kg / (height in m)²) | kg/m² | 15.0 – 67.0 | 0 represents MISSING; median imputed |
| `DiabetesPedigreeFunction` | Genetic pedigree score of diabetes history | Continuous | 0.078 – 2.42 | Non-zero |
| `Age` | Patient age | Years | 21 – 81 | Positive integer |

---

## 2. Heart Disease Risk Prediction Dataset

- **Primary Source:** Cleveland Clinic Foundation (Dr. Robert Detrano)
- **Archive Source:** UCI Machine Learning Repository (Heart Disease Dataset)
- **Clinical Target:** Diagnosis of Heart Disease (`target`: 0 = <50% diameter narrowing, 1 = >50% diameter narrowing)

### Feature Schema
| Feature Name | Description | Source Category |
|---|---|---|
| `age` | Age in years | Patient Demographics |
| `sex` | Biological Sex (1 = male; 0 = female) | Patient Demographics |
| `cp` | Chest pain type (0: typical angina, 1: atypical angina, 2: non-anginal pain, 3: asymptomatic) | Patient-Supplied Symptom |
| `trestbps` | Resting blood pressure (in mm Hg on admission to the hospital) | Vitals / Lab Report |
| `chol` | Serum cholesterol in mg/dL | Lipid Panel Lab Report |
| `fbs` | Fasting blood sugar > 120 mg/dL (1 = true; 0 = false) | Blood Glucose Lab Report |
| `restecg` | Resting electrocardiographic results (0, 1, 2) | Clinical Diagnostic Input |
| `thalach` | Maximum heart rate achieved during exercise | Stress Test Input |
| `exang` | Exercise induced angina (1 = yes; 0 = no) | Stress Test Input |
| `oldpeak` | ST depression induced by exercise relative to rest | ECG Stress Test Input |
| `slope` | The slope of the peak exercise ST segment (0, 1, 2) | ECG Stress Test Input |
| `ca` | Number of major vessels (0-3) colored by flourosopy | Angiography Input |
| `thal` | Thalassemia category (1 = normal; 2 = fixed defect; 3 = reversable defect) | Clinical Hematology Input |
