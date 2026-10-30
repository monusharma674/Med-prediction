# B.Tech Major Project Technical Evaluation & Viva Voce Guide

**Project Title:** AI-Powered Medical Report Management and Multi-Disease Risk Prediction System with Blockchain Verification  
**Degree:** B.Tech in Computer Engineering (Artificial Intelligence & Machine Learning)  
**Difficulty Level:** Medium–High (Full-Stack + Scikit-Learn Pipelines + PyMuPDF/OCR + Solidity Smart Contracts)  

---

## 1. System Architecture & Backend Engineering

### Q1: Why did you choose FastAPI over traditional frameworks like Django or Flask?
**Answer:**
1. **Asynchronous Concurrency (ASGI):** FastAPI is built on Starlette and Uvicorn, delivering near-Go performance for I/O-bound operations such as multi-page PDF ingestion, hashing, and blockchain JSON-RPC calls.
2. **Strict Data Validation & Provenance:** Built-in integration with Pydantic ensures compile-time and runtime type safety, schema validation, and automatic OpenAPI (Swagger) generation.
3. **Dependency Injection System:** Enables modular database sessions, token-based authentication guards, and role-based access control (RBAC) injected cleanly into route handlers.

### Q2: How does the application enforce Role-Based Access Control (RBAC)? Is hiding frontend navigation buttons sufficient?
**Answer:**
Hiding UI buttons is purely cosmetic and offers **zero security**. A malicious user can directly invoke REST endpoints using cURL or Postman.
In this project, RBAC is enforced **strictly at the backend route dependency level**:
- Each API endpoint injects `get_current_user` and `require_role(UserRole.PATIENT)` or `require_role(UserRole.DOCTOR)`.
- If an authenticated doctor attempts to fetch a report ID that the patient has not actively shared, the database query checks `SharedReport.is_active == True` and returns `403 Forbidden`.

---

## 2. OCR & Medical Data Extraction Pipeline

### Q3: How does your extraction engine handle digital PDFs versus scanned document images?
**Answer:**
The extraction pipeline implements a dual-mode heuristic:
1. **Selectable Text Detection:** PyMuPDF (`fitz`) first queries the PDF page for vector text blocks.
2. **Direct Parsing:** If selectable text exists, it bypasses heavy vision OCR, ensuring 100% character fidelity and near-instant processing.
3. **Rasterized Fallback:** If selectable text is empty (scanned lab report), the engine converts the PDF page into a high-DPI image (Pillow/PyMuPDF pixmap) and executes Tesseract OCR with adaptive image thresholding.

### Q4: In medical reports, tests like "HbA1c", "Vitamin B12", and "CO2" have numbers in their names. How did you prevent regex parsers from capturing those numbers as the test value?
**Answer:**
Naive regexes searching for the first floating-point number in a text line fail on `"HbA1c: 7.4%"` because they extract `1` from `HbA1c`.
Our `MedicalValueParser`:
1. First identifies the exact string span index of the matched alias (e.g. `span = line.find("HbA1c")`).
2. Slices the line strictly **after** the alias name (`search_slice = line[span + len(alias):]`).
3. Extracts numerical values and units only from that remaining slice.

### Q5: What is "Data Provenance", and why is it critical in healthcare software?
**Answer:**
Data provenance refers to documenting the exact origin and modification history of clinical values. Every extracted parameter is tagged with an immutable provenance label:
- `"ocr"`: Automatically extracted by PyMuPDF/Tesseract.
- `"corrected"`: Manually adjusted and verified by the patient after reviewing an OCR ambiguity.
- `"patient_entered"`: Inputted directly by the patient for missing biomarkers.
Both original OCR outputs and corrected values are preserved side-by-side in `extracted_medical_values` for clinical auditability.

---

## 3. Machine Learning Engineering & Clinical Limitations

### Q6: Why did you not replace missing clinical measurements with 0 in your datasets?
**Answer:**
In biological datasets (like Pima Indians Diabetes), zero values for Glucose, Blood Pressure, Skinfold Thickness, Insulin, or BMI are **physiologically impossible in living humans**—they signify missing, unrecorded measurements.
- Replacing missing values with 0 skews distribution curves, biases the decision boundary, and artificially destroys model accuracy.
- Our training pipeline (`train_diabetes.py`) codes biological zeros as `NaN` and applies `SimpleImputer(strategy="median")` inside an isolated `Pipeline` object.

### Q7: How did you prevent Data Leakage during preprocessing?
**Answer:**
If you scale or impute your entire dataset *before* splitting into train and test sets, information from the test set (e.g. overall mean or standard deviation) leaks into the model training phase.
We prevented leakage by:
1. Splitting raw data into 80% train and 20% test sets using `StratifiedShuffleSplit`.
2. Encapsulating imputation and scaling strictly inside an `sklearn.pipeline.Pipeline`. The pipeline fits statistics **only on `X_train`** and transforms `X_test` without fitting.

### Q8: What algorithms did you train, and why did you select the final model?
**Answer:**
We trained and evaluated three competing algorithms on 5-Fold Stratified Cross-Validation:
1. **Logistic Regression (L2 penalized):** High interpretability, monotonic feature responses, and well-calibrated linear log-odds.
2. **Random Forest Classifier:** Non-linear decision boundaries and robust resistance to feature outliers.
3. **Gradient Boosting Classifier (GBDT):** Sequential boosting targeting residual errors.
Model selection was governed by validation F1-score and ROC-AUC rather than raw accuracy, because medical classification must penalize false negatives (missed disease diagnoses) heavily.

### Q9: What is the difference between "Model Risk Score" and "Calibrated Probability"?
**Answer:**
- Many machine learning classifiers output scores between 0 and 1 via `predict_proba()` or sigmoid transformations. However, unless formally calibrated against empirical population base rates (using isotonic regression or Platt scaling), these scores reflect **uncalibrated rank-ordering scores**, not true frequentist probabilities.
- To maintain clinical ethics, our UI and API strictly label outputs as **"Model Risk Score"** rather than "Diagnosed Probability" unless calibrated, and display a persistent medical disclaimer.

---

## 4. Blockchain Integrity & Cryptographic Verification

### Q10: Why did you store SHA-256 hashes on the blockchain instead of storing the actual medical reports or patient records?
**Answer:**
Storing actual medical files or patient PII on a blockchain violates fundamental computer engineering, legal, and privacy principles:
1. **HIPAA & GDPR "Right to be Forgotten":** Blockchains are immutable; if medical data or patient names are stored on-chain, they can never be removed or edited.
2. **Zero-Knowledge Privacy:** Anchoring only the 32-byte cryptographic SHA-256 digest reveals **zero** personal or diagnostic information to unauthorized blockchain nodes.
3. **Storage Scalability & Gas Costs:** Storing multi-megabyte PDF files on an EVM ledger would cost immense gas fees and bloat state storage. Storing a 32-byte `bytes32` digest requires minimal gas.

### Q11: How does bitwise tamper detection work?
**Answer:**
1. During upload, the server computes the SHA-256 hash of the file bytes and anchors it via `MedicalReportRegistry.sol` using `registerReportHash(reportUUID, fileHashSha256)`.
2. When verification is requested, the server reads the file currently on disk, calculates its current SHA-256 digest, and executes an exact bitwise equality check against the on-chain recorded digest.
3. If an attacker or compromised server administrator alters even a single byte (e.g. changing glucose from 180 to 80), the **Avalanche Effect** of cryptographic hashing causes the entire SHA-256 output to change drastically, immediately triggering a `MISMATCH - Tampering Detected` alert.

---

## 5. Doctor Sharing & Access Revocation

### Q12: How does your system implement patient consent and access revocation?
**Answer:**
1. A patient navigates to the Doctor Sharing console, selects a report, and specifies a licensed physician from the verified directory with an optional expiration date.
2. A `SharedReport` record is created linking `patient_id`, `doctor_id`, and `report_id`.
3. When the physician logs in, their portal queries only reports where `doctor_id == current_user.id AND is_active == True`.
4. When the patient clicks **"Revoke"**, `is_active` is immediately set to `False` and `revoked_at` is timestamped. Any subsequent request by the doctor triggers an immediate `403 Forbidden` error. All access events are permanently recorded in `audit_logs`.
