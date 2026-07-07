# CAMCA Pilot Study Protocol (n=30) — v2.0 (English)
**Camera-based Automated Multi-agent Clinical Assessment of Inhaler Technique**

**Version**: 2.0 (2026-05-21)
**Status**: IRB-ready (post n=2 internal validation)
**PI**: Min-Gyu Kang, MD (Chungbuk National University Hospital, Allergy Medicine)
**Institution**: Chungbuk National University Hospital (CBNUH)
**Collaboration**: Massachusetts General Hospital · Harvard Medical School
**Contact**: drugnsafety@gmail.com

---

## 0. Revision History (v1.0 → v2.0)

| Area | v1.0 (2026-05-21 draft) | **v2.0 (2026-05-21 revision)** |
|---|---|---|
| **Preliminary data** | None | **n=2 internal validation (PARK·KIM) — κ_linear 0.0 vs 0.71 paired case** added |
| **System architecture** | 4-layer hybrid (conceptual) | **Verified v0.3.0 stack** — L1-L5 limitations resolved + L6-L8 prospective validation plan |
| **SAP (Statistical Analysis Plan)** | 1-page | **§5 refined** — primary IRR, secondary telemetry impact, tertiary κ-as-quality-proxy, pre-specified power calculation |
| **PIPA / MFDS / IRB compliance** | §7 summary | **§7 expanded** — Vertex AI Seoul, on-device anonymization spec, MFDS SaMD Class II follow-up path |
| **AI failure-mode catalog** | General prose | **Verified 8-mode matrix (L1-L8) with resolution status** |
| **Appendix D — schema** | 21 files | **24 files** (telemetry audit, VLM reasoning trace, reconciliation log added) |
| **Budget appendix** | None | **Appendix E — Budget table** added |

> ✅ The core distinction of v2.0 is the transition from "**hypothesis → verified data**." Where v1.0 was a prospective protocol, v2.0 incorporates n=2 internal validation outcomes plus the quantitative resolution of 5 system limitations → giving the IRB committee a **reproducible evidence base** to evaluate.

---

## 1. Background and Rationale

### 1.1 Clinical Problem

- **Widespread inhaler misuse**: 70-80% of asthma and COPD patients use inhalers incorrectly (Sanchis 2016, CRITIKAL 2017).
- **Health professionals are not exempt**: Prescribers themselves frequently demonstrate incorrect technique (Plaza 2018).
- **CRITIKAL critical errors** — errors statistically associated with worse asthma outcomes:
  - pMDI coordination failure (prevalence 45%, aOR 1.45 for uncontrolled asthma)
  - DPI inadequate inspiratory effort (38%)
  - Inadequate breath-hold (38%)
- **Absence of automated assessment**: PubMed search confirms no published computer-vision-based automated scoring system. The only commercial competitor (Kata® by VisionHealth) is built on 2017-era technology, and major digital inhaler companies exited the market in 2024.

### 1.2 Solution Architecture — Verified 4-Layer Hybrid (v0.3.0)

| Layer | Function | Component | v0.3.0 verification status |
|---|---|---|---|
| **0 — Quantitative measurement** | Deterministic physical metrics at 0.1s resolution | MediaPipe Pose+FaceMesh + librosa DSP | ✅ n=2 verified (L1-L5 resolved) |
| **1 — Probabilistic observation** | VLM uses telemetry as anchor | Dual-agent (Claude Opus + Gemini Pro) | ✅ Pydantic schema enforcement |
| **2 — IRR adjudication** | Cohen's κ + deterministic statistics | `kappa_calculator.py` (sha256 signature) | ✅ KIM κ=0.71 / PARK κ=0.0 |
| **3 — Final scoring** | Verdict + critical-error override | `scoring_engine.py` | ✅ 100% deterministic reproducibility |

This 4-layer separation addresses three fundamental problems:

1. **Hallucination** — single-VLM unreliability → Layer 0 telemetry anchors the VLM
2. **Black-box bias** — lack of auditability → Layer 1 VLM reasoning trace + Layer 2/3 deterministic
3. **Cross-vendor lock-in** — single-vendor risk → 3-way compatibility (Claude / Gemini / Ollama)

---

## 2. Study Aims (refined in v2.0)

### 2.1 Primary Aim

**Establish inter-rater reliability** between two independent VLM evaluator personas (GINA-strict vs pragmatic-clinical) on standardized inhaler-technique videos, **with and without quantitative telemetry augmentation**.

**Primary endpoint**: Cohen's κ_linear (overall, per-step, per-critical-error) — bootstrap 95% CI.

**Sample size justification**: n=30 yields ≥80% power to detect κ ≥ 0.7 (substantial agreement) vs null of κ=0.4 (moderate agreement) at α=0.05, based on the Fleiss-Cohen sample size table for ordinal κ with 7 steps × 4 levels.

### 2.2 Secondary Aims

1. **Telemetry impact on critical-error detection**: Quantify the change in CRIT-pMDI-04 (coordination) and CRIT-pMDI-08 (breath-hold) detection sensitivity before and after the telemetry layer.
2. **AI vs human gold-standard agreement**: Pairwise weighted κ between AI consensus and (PI + senior pharmacist + adjudicator) gold standard.
3. **Device sub-type telemetry profile**: Quantify the audio profile (peak dB, baseline dB, inhalation onset detection rate) of real pMDI vs AIM training simulator.
4. **Clinician review flag calibration**: Sensitivity/specificity of the κ-threshold (0.6) and critical-error-disagreement system that auto-assigns review priority (none / moderate / high).

### 2.3 Exploratory Aims

- **Cross-model validation**: Claude Opus vs Gemini 2.5 Pro vs local Gemma3:27b (on-premise Ollama) — agreement on identical videos.
- **Cost-quality tradeoff**: low-cost (Gemini Flash dual) vs research-grade (Opus + Gemini Pro + tie-breaker).
- **κ as a video-quality proxy** (n=2 finding): Prospective validation of the observation that κ varies 5-fold across identical verdicts depending on acquisition quality.

---

## 3. Study Design

### 3.1 Type

Prospective single-center observational study with cross-sectional video assessment.

### 3.2 Setting

- Outpatient allergy clinic + Pulmonary Function Lab at CBNUH
- Standardized brackets in the exam room (wall mount + 1.5 m distance)
- Analysis: on-premise secure NAS + Vertex AI Seoul (PIPA region)

### 3.3 Sample Size and Composition

| Group | n | Inclusion |
|---|---|---|
| Healthy volunteers | 15 | Age ≥19, no chronic respiratory disease, informed consent |
| Asthma patients | 15 | Age ≥19, physician-diagnosed asthma, on inhaled therapy ≥3 months |
| **Total** | **30** | |

**Inclusion criteria** (both groups):
- Able to give informed consent in Korean or English
- Owns or can access a pMDI inhaler (AIM-equivalent placebo provided if needed)

**Exclusion criteria**:
- Inability to perform the inhalation maneuver due to cognitive/physical impairment
- Active respiratory infection at enrollment
- Refusal of video recording
- Prior participation in another CAMCA validation study

### 3.4 Device Coverage

| Device | Expected n | Phase |
|---|---|---|
| pMDI standalone | 20 | MVP (this IRB) |
| pMDI + Spacer | 5-8 | Secondary subgroup |
| AIM training simulator | 30 (all subjects — educational comparison) | Same IRB |
| DPI-Turbuhaler | — | Phase 2 separate IRB |

---

## 4. Data Collection Procedures

### 4.1 Video Recording Specification (strengthened in v2.0)

| Parameter | Specification | Rationale |
|---|---|---|
| Camera | Smartphone (subject's own or provided iPhone 14 / Galaxy S24) | Real-world generalizability |
| Resolution | **≥1080p (1920×1080)** | KIM(1080p) vs PARK(720p) revealed MediaPipe landmark accuracy differences |
| Frame rate | 30 fps minimum | Sub-second event timing |
| Duration | 20-60 sec (full sequence) | Capture all 7 pMDI steps |
| Angle | **Frontal preferred (≤15° lateral allowed)** | PARK: lateral angle → face landmark detection failure |
| Grip | **Canister-top + index finger visible** | PARK: two-hand cupping → occlusion |
| Audio | Built-in mic, no ambient music | librosa dB extraction |
| Lighting | Indoor ≥200 lux | Vision landmark confidence |

**Camera placement guide** (separate Korean patient handout):
1. Place phone on stable surface at chest height
2. Stand 1-1.5 m from camera
3. Both hands and face must be in frame
4. Avoid backlight (no window behind)
5. **Full sequence demonstration** — include pre-inhalation prep (shake → cap → exhale)

### 4.2 Privacy and De-identification (CRITICAL)

- **MediaPipe Face Mesh upper-face anonymization** — **on-device, applied before any cloud upload**
  - Preserved: mouth, chin, mouthpiece interaction (required for clinical seal assessment)
  - Blocked: eyes, nose, identifiable facial regions
  - Implementation: `assets/scripts/anonymize_video.py` (shipping in v0.3.0)
- **Audio de-identification**: speech silenced via spectral subtraction; inhaler / breath audio preserved
- **Cloud upload region**: Vertex AI Seoul region only (PIPA-compliant, no cross-border transfer)
- **On-premise-only arm option**: Ollama backend (gemma3:27b + qwen2.5vl:32b) — supports cloud-0% cases

### 4.3 Expert Clinician Gold Standard

Each video is independently scored by:
- **Reviewer 1** (PI): M-G Kang, MD — board-certified allergist
- **Reviewer 2**: Senior clinical pharmacist (≥10 years respiratory experience)
- **Adjudicator** (for disagreements): External pulmonologist (blinded to AI output)

Disagreements between Reviewers 1 and 2 of ≥1 level → adjudicator decision. The resulting human gold standard is compared against AI consensus.

---

## 5. Statistical Analysis Plan (refined in v2.0)

### 5.1 Primary Analysis — Inter-Rater Reliability

**AI Evaluator A vs AI Evaluator B** (model + persona dual diversity):
- **Cohen's κ_linear** (Landis & Koch 1977 thresholds): per-step and overall
- **Critical-error agreement**: separate computation (target ≥0.90)
- **Bootstrap 95% CI** (1,000 iterations, BCa method)
- **Per-device subgroup**: pMDI vs pMDI-spacer vs AIM simulator
- **Per-age subgroup**: ≥65 vs <65 years
- **Per-recording-quality subgroup**: 1080p vs 720p, frontal vs lateral

**AI Consensus vs Human Gold Standard**:
- Pairwise weighted κ (both linear and quadratic)
- Per critical-error type: sensitivity / specificity / PPV / NPV
- ROC curve for overall verdict (FAIL / non-FAIL)

### 5.2 Secondary Analysis — Telemetry Layer Impact (Pre-Registered)

**Each video is analyzed twice**:
1. **VLM-only mode** (v0.1.0 equivalent — telemetry layer disabled)
2. **Telemetry-augmented mode** (v0.3.0 — full MediaPipe + librosa)

**Pre-specified hypothesis**: The telemetry layer increases CRIT-pMDI-04 (coordination) detection sensitivity by an **absolute ≥15%** (the anchor-confidence gap was sizeable in the n=2 internal data).

**Comparison metrics**:
- κ pre- vs post-telemetry
- Critical-error sensitivity change
- Per-step evaluator confidence (self-reported)
- Cost (cloud API token consumption) — telemetry adds +0% (runs on-device)

### 5.3 Tertiary Analysis — κ as a Video-Quality Proxy (prospective verification of n=2 finding)

**Pre-specified hypothesis** (from the KIM vs PARK paired case):

> *"Even at the same verdict (ADEQUATE_WITH_EDUCATION, 10/12), κ varies from 0.0 to 0.71 depending on acquisition quality. κ itself therefore behaves as a video-quality + technique-clarity proxy."*

**Verification approach**:
- Analyze the (verdict, κ) pair for all 30 cases
- Within a cohort of identical verdicts (e.g., ADEQUATE_WITH_EDUCATION), measure κ IQR
- Regression model: video acquisition variables (resolution, angle, grip occlusion) → κ
- Sensitivity/specificity of κ-based clinician review priority (κ<0.6 → high priority)

**Expected impact**: If the hypothesis is confirmed, clinical deployment must report **both** "verdict + κ" as the standard.

### 5.4 Quality Metrics

- **Tie-breaker invocation rate**: target 15-30% (persona calibration validation)
- **Clinician review flag accuracy**: % of flagged cases where a human reviewer found a real issue
- **Telemetry availability rate**: % of cases where both MediaPipe and audio succeed

### 5.5 Pre-Specified Subgroup Analyses

- **Real pMDI vs AIM simulator**: audio threshold calibration → update DEVICE_AUDIO_PROFILES dict
- **Healthy vs asthma**: technique error rate
- **Age (≥65 vs <65)**: error type distribution
- **First-time vs experienced users**: most prevalent errors

---

## 6. Data Management

### 6.1 Storage

| Data type | Location | Retention |
|---|---|---|
| Raw videos | CBNUH secure on-premise NAS | 5 years post-publication |
| Anonymized videos | Local + Vertex AI Seoul (encrypted at rest) | Same |
| Telemetry JSON | `logs/{case_id}/01b_*`, `01c_*` | Same |
| Evaluator outputs | `logs/{case_id}/04_*`, `05_*`, `04_*_with_telemetry` | Same |
| Adjudication + consensus | `logs/{case_id}/06_*`, `07_*` | Same |
| Master CSV aggregates | Single Excel file at CBNUH | Same |
| API call log (cost / token) | Separate billing log | 2 years |

### 6.2 Data Export

Every case follows the CAMCA standard schema (camca-py package output). Master CSV columns include:
- Per-evaluator score + critical-error count
- Per-stage model used + duration
- κ (unweighted / linear / quadratic)
- Tie-breaker invocation + outcome
- Clinician review priority
- Telemetry availability (vision / audio / both)
- **NEW v2.0**: VLM↔Telemetry reconciliation outcome (Agree / VLM_wins / Telemetry_wins / Conflict_flagged)

### 6.3 Reproducibility

- Every deterministic computation (κ, scoring) produces a `sha256:` signature
- Same input → same signature → bit-identical output guaranteed
- Software versions logged in `00_pipeline_metadata.json.pipeline_version`
- Model versions logged per stage in `00_pipeline_metadata.json.stages[*].model_used`

---

## 7. Ethical Considerations (expanded in v2.0)

### 7.1 IRB Submission

- CBNUH IRB approval before enrollment
- MGH / HMS reciprocal notification as collaborating institution
- Annual continuing review

### 7.2 Informed Consent (Korean + English dual)

**Explicit consent points**:
- Video recording of face, hands, and inhaler interaction
- On-device facial anonymization (before any cloud upload)
- Cloud analysis via Vertex AI Seoul (PIPA-compliant)
- On-premise-only mode option (Ollama backend — patient's choice)
- 5-year retention post-publication
- Right to withdraw at any time, including deletion of all materials
- Separate consent for use of anonymized videos in future publications

### 7.3 Regulatory Compliance — Korea + US dual track

#### 7.3.1 Korean PIPA (Personal Information Protection Act)

- **No cross-border data transfer**: Vertex AI Seoul region (domestic processing only)
- **Data minimization**: On-device anonymization blocks identifying information (eyes / nose blurred); only mouth and hands — required for clinical assessment — are preserved
- **Explicit separate consent**: Patient's choice between cloud upload arm vs on-premise-only arm is formally documented
- **Right to be forgotten**: Upon withdrawal, all storage (NAS + Vertex AI + local backups) is purged within 7 days

#### 7.3.2 MFDS (Ministry of Food and Drug Safety, Korea) SaMD Classification

- **Current status**: Research prototype — not subject to Software as a Medical Device (SaMD) classification
- **Post-pilot path to clinical deployment**:
  - **Class II SaMD** candidate (clinician decision support, not autonomous diagnosis)
  - Compliance plan with MFDS "AI-based SaMD Approval Review Guidelines" (2023)
  - Pre-submission consultation requested after pilot completion
- **Post-market surveillance** (post-deploy): Quarterly reporting of clinician review-flag rate, false-FAIL rate, and patient complaint logs

#### 7.3.3 FDA (US)

- Not classified as a device within the current research scope (IRB-approved research only)
- For US clinical deployment, a separate 510(k) or De Novo path will be evaluated

#### 7.3.4 Bias Mitigation

- Multi-vendor backend (Claude + Gemini + Ollama) reduces single-vendor lock-in bias
- Persona diversity (GINA-strict vs pragmatic) reduces single-perspective bias
- Comparison against human gold standard detects algorithmic miscalibration

### 7.4 AI Failure-Mode Catalog (v2.0, evidence-based)

Eight failure modes identified during n=2 internal validation, with resolution status:

| # | Failure mode | Discovery case | Verified resolution | Clinical risk |
|---|---|---|---|---|
| L1 | Breath-hold detector false positive (quiet audio) | KIM-001 | ✅ v0.2.1 — min_peak_db_for_detection=55 | Wrong verdict (Level 1→3 inflation) |
| L2 | Finger acceleration threshold too low (8 px/s²) | KIM-001 | ✅ v0.2.1 — 100 px/s² + 3-frame MA | False CRIT-pMDI-04 flag |
| L3 | Head pitch coordinate-transform bug | KIM-001 | ✅ v0.2.1 — calibrated atan2 | S4 posture mis-rated |
| L4 | AIM simulator audio threshold mismatch | PARK+KIM | ✅ v0.2.1 — DEVICE_AUDIO_PROFILES dict | S5 / S7 anchor failure |
| L5 | No policy for VLM↔Telemetry conflict | KIM-001 (Algo 11.3s vs VLM 3s) | ✅ v0.2.1 — reconciliation.py | Lower auto-verdict confidence |
| L6 | Camera-angle dependence (lateral → MediaPipe failure) | PARK-001 | 🔜 v0.3.0 — view_angle field | S4 / S5 accuracy variance |
| L7 | VLM frame-sampling limit (1 fps) | KIM-001 S7 | 🔜 v0.3.0 — 2-4 fps + step-aware | Temporal metric underestimation |
| L8 | Inhalation inference impossible without audio peak | PARK+KIM | 🔜 v0.4.0 — vision-only inhalation | Affects all AIM cases |

### 7.5 AI Failure Mitigation — Patient-Facing Safety Net

- **Mandatory disclaimer in patient PDF**: *"This evaluation is the output of AI video analysis and does not fully replace direct evaluation by a clinician."*
- **Clinician review flag** (3 levels):
  - **None**: κ ≥ 0.8 and critical-error agreement
  - **Moderate**: 0.6 ≤ κ < 0.8 OR video acquisition warning
  - **High**: κ < 0.6 OR critical-error disagreement OR reconciliation conflict → **mandatory direct clinician review within 24 h**
- **Tie-breaker auto-invocation**: triggered automatically when κ < 0.6 (3rd evaluator + 2/3 majority vote)
- **Hard fail-safe**: any critical error reported by either evaluator → automatic FAIL verdict regardless of score

---

## 8. Study Timeline (Updated)

| Phase | Duration | Activities |
|---|---|---|
| **Phase 0 — Validation complete** | ✅ Done (2026-05-21) | n=2 internal validation (PARK, KIM), L1-L5 resolved, v0.3.0 released |
| Phase 1 — Setup | 2 months | IRB submission, equipment procurement, clinician training |
| Phase 2 — Enrollment | 3 months | n=30 enrollment + video collection |
| Phase 3 — Analysis | 2 months | Dual-mode evaluation + human gold-standard scoring |
| Phase 4 — Reporting | 2 months | Statistical analysis + manuscript drafting |
| **Total (Phase 1-4)** | **9 months** | |

---

## 9. Expected Outcomes and Publication Strategy

### 9.1 Primary Publication

**Target journal**: *J Allergy Clin Immunol: In Practice* (CRITIKAL precedent) or *NPJ Digital Medicine*
**Tentative title**: *"Multi-agent VLM with Quantitative Telemetry for Automated Inhaler Technique Assessment: A Pilot Study (n=30)"*

### 9.2 Companion Publications

- **Methods paper**: CAMCA architecture open-source release (Plugin + Python pkg) — *Software Impacts* or *Journal of Open Source Software*
- **Korean clinical brief**: Chungbuk National University College of Medicine journal
- **Cross-model validation**: GPT-5 vs Claude vs Gemini for medical video analysis — *NPJ Digital Medicine* methods

### 9.3 Open Source Release

- Plugin (`camca-inhaler-eval.plugin`) + Python package (`camca` on PyPI)
- All skills and rubrics under MIT license
- Bundled clinical reference tables (XLSX + Markdown) — available for educator use

---

## 10. Funding and Conflicts of Interest

- **Funding**: TBD (CBNUH internal seed grant + parallel government R&D application under consideration)
- **Cloud costs (estimated)**: USD 50-150 for the n=30 pilot (Claude Opus + Gemini Pro full-grade run)
- **Conflicts of interest**: None. No industry sponsorship of CAMCA development.

---

## 11. Appendices

### Appendix A — Telemetry Layer Specification (v0.3.0 verified values)

```python
# camca/telemetry/thresholds.py
DEVICE_AUDIO_PROFILES = {
    "pMDI":                {"baseline_db": 35, "inhalation_min_db": 50, "min_peak_db_for_detection": 55},
    "pMDI-AIM-simulator":  {"baseline_db": 35, "inhalation_min_db": 42, "min_peak_db_for_detection": 45},
    "pMDI-spacer":         {"baseline_db": 35, "inhalation_min_db": 48, "min_peak_db_for_detection": 53},
    "DPI-turbuhaler":      {"baseline_db": 35, "inhalation_min_db": 55, "min_peak_db_for_detection": 60},
}

INDEX_FINGER_ACTUATION_ACCEL_THRESHOLD = 100.0  # px/s² (was 8 in v0.1)
INDEX_FINGER_ACTUATION_MIN_DURATION_MS = 50
INDEX_FINGER_SMOOTHING_WINDOW = 3                # 3-frame moving average
INHALATION_OPTIMAL_DURATION_MS = {"pMDI": 3000, "pMDI-AIM-simulator": 3000, "DPI-turbuhaler": 2000}
```

### Appendix B — Reference Materials (Bundled)

- `assets/reference/inhaler_reference_tables.xlsx` — 6-sheet comprehensive rubric
- `assets/static/patient_guide_pmdi_ko.pdf` — 4-page Korean patient guide
- `assets/static/patient_guide_pmdi_en.pdf` — 5-page English guide
- `assets/static/patient_guide_turbuhaler_ko.pdf` — Phase 2

### Appendix C — Software Versions (locked for pilot)

- **camca v0.3.0** (Python package, frozen for pilot)
- **camca-inhaler-eval v0.4.0** (Claude plugin)
- **Claude API**: claude-opus-4-7, claude-sonnet-4-6
- **Gemini API**: gemini-2.5-pro, gemini-2.5-flash
- **Ollama models** (on-premise fallback): gemma3:27b, qwen2.5vl:32b
- **MediaPipe** ≥0.10, **librosa** ≥0.10, **reportlab** ≥4.0, **pypdf** ≥3.0

### Appendix D — Pilot Case Schema (per case, v2.0 expanded)

```
logs/CAMCA-PILOT-{NNN}/
├── 00_pipeline_metadata.json          (all stages: model · timing · sha256)
├── 01_input.json                       (patient metadata, age, group)
├── 01b_telemetry_stream.json           (0.1s × 6 indicators)
├── 01b_telemetry_full_audit.json       (audio actual + vision observed split) ⭐NEW v2.0
├── 01c_telemetry_summary.json          (clinical anchors)
├── 01d_telemetry_schema.md             (meaning of the 6 metrics) ⭐NEW v2.0
├── 02_device_id.json                   (+ device sub-type)
├── 03_segments.json
├── 04_evaluator_a.json                 (VLM-only mode)
├── 04_evaluator_a_with_telemetry.json  (telemetry-augmented)
├── 04_evaluator_a_detailed.json        (with reasoning trace) ⭐NEW v2.0
├── 05_evaluator_b.json
├── 05_evaluator_b_with_telemetry.json
├── 05_evaluator_b_detailed.json        ⭐NEW v2.0
├── 06_adjudication.json
├── 06b_kappa_stats.json
├── 06c_tie_breaker.json                (if needed)
├── 06d_reconciliation_log.json         (VLM↔Telemetry) ⭐NEW v2.0
├── 07_final_score.json
├── 08_patient_report_ko.pdf
├── 08_patient_report_en.pdf
├── 08_clinician_report_ko.pdf
├── 09_research_export.json
├── 09_research_export.csv
├── 10_human_gold_standard.json         (Reviewer 1 + 2 + adjudicator)
└── 11_comparison_AI_vs_human.json       (computed post-hoc)
```

### Appendix E — Pilot Budget (USD, estimated)

| Item | Unit cost | Quantity | Subtotal |
|---|---|---|---|
| Cloud API (Claude Opus + Gemini Pro, n=30 dual-mode = 60 runs) | $1.50 / run | 60 | $90 |
| Telemetry compute (on-device, free) | $0 | 30 | $0 |
| Ollama tie-breaker (on-premise GPU time) | $0 (sunk) | 30 | $0 |
| Storage (encrypted NAS, 1 year) | flat | — | $50 |
| Statistical software (R, free) | $0 | — | $0 |
| **Estimated total** | | | **USD 140** |

→ Exceptionally low cash cost. The dominant expense is clinician time + IRB administration.

### Appendix F — Preliminary Internal Validation Summary (n=2)

**Validation case 1: CAMCA-PARK-001** (pharmacy student, pMDI demo)
- Evaluator A (Opus + GINA strict): 6/12 (50%)
- Evaluator B (Sonnet + pragmatic): 10/12 (83%)
- κ_linear = 0.0 → tie-breaker invoked 4 times, all in favor of B
- Final consensus: ADEQUATE_WITH_EDUCATION (10/12, 83%)
- Critical errors: 0
- Data quality flag: PARTIAL_DATA (video starts mid-inhalation → S1-S3 unobservable)
- Note: lateral angle + two-hand cupping → MediaPipe occlusion

**Validation case 2: CAMCA-KIM-001** (pharmacy student, 1080p frontal)
- Evaluator A: 9/12 (75%)
- Evaluator B: 10/12 (83%)
- κ_linear = 0.71 → substantial agreement, no tie-breaker
- Final consensus: ADEQUATE_WITH_EDUCATION (10/12, 83%)
- Critical errors: 0
- Note: 1080p + frontal + one-hand standard grip → 100% vision-telemetry detection success

**Key paired finding (KIM vs PARK)**:

| Item | KIM-001 | PARK-001 |
|---|---|---|
| Consensus score | **10/12 (identical)** | **10/12 (identical)** |
| Verdict | **ADEQUATE_WITH_EDUCATION (identical)** | **ADEQUATE_WITH_EDUCATION (identical)** |
| **κ_linear** | **0.71** | **0.0** |
| Tie-breaker | ❌ not needed | ✅ invoked |
| Clinician review priority | low | moderate |

→ **Identical verdict, yet a 5-fold difference in system confidence**. This paired case is the empirical anchor for the prospective §5.3 hypothesis ("κ as a video-quality proxy") in the n=30 pilot.

---

**Document control**:
- v1.0 (2026-05-21): Initial IRB draft
- **v2.0 (2026-05-21)**: Incorporates n=2 internal validation, reflects L1-L5 resolution, refines SAP, expands regulatory compliance
- v2.1 (planned): Post-IRB-committee feedback
- v3.0 (planned): Post-enrollment — empirical SAP update based on actual data

Generated as part of the CAMCA v0.4.0 (plugin) / v0.3.0 (Python package) release.
