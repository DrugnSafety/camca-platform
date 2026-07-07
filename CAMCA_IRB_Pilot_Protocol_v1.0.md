# CAMCA Pilot Study Protocol (n=30)
**Camera-based Automated Multi-agent Clinical Assessment of Inhaler Technique**

**Version**: 1.0 (2026-05-21)
**PI**: Min-Gyu Kang, MD (충북대학교병원 알레르기내과)
**Institution**: Chungbuk National University Hospital (CBNUH)
**Collaboration**: Massachusetts General Hospital · Harvard Medical School
**Contact**: drugnsafety@gmail.com

---

## 1. Background and Rationale

### 1.1 Clinical Problem

- Up to 70-80% of asthma and COPD patients use inhalers incorrectly (Sanchis 2016, CRITIKAL 2017).
- Health professionals themselves frequently demonstrate incorrect technique (Plaza 2018).
- The CRITIKAL study identified specific errors associated with worse asthma outcomes:
  - pMDI coordination failure (45% prevalence; aOR 1.45 for uncontrolled asthma)
  - Inadequate inspiratory effort (DPI, 38% prevalence)
  - Inadequate breath-hold (38% prevalence)
- No published computer-vision-based automated scoring system exists (PubMed-confirmed gap).
- Sole commercial competitor (Kata® by VisionHealth) uses 2017-era technology; major digital inhaler companies exited the market in 2024.

### 1.2 Solution Architecture

CAMCA introduces a **4-layer hybrid evaluation system**:

| Layer | Function | Component |
|---|---|---|
| 0 — Quantitative measurement | Deterministic physical metrics (0.1s resolution) | MediaPipe vision + librosa audio DSP |
| 1 — Probabilistic observation | VLM cross-validation with telemetry as anchor | Dual-agent (Claude Opus + Gemini Pro) |
| 2 — IRR adjudication | Inter-rater reliability via Cohen's κ | Deterministic Python script |
| 3 — Final scoring | Verdict with critical-error override | Deterministic Python script |

This separation addresses:
- Hallucination (single VLM unreliable)
- Black-box bias (no audit trail)
- Cross-vendor lock-in (multi-vendor backends supported)

---

## 2. Study Aims

### Primary Aim
Establish **inter-rater reliability** between two independent VLM evaluator personas (strict GINA vs pragmatic clinical) on standardized inhaler-technique videos, with and without quantitative telemetry augmentation.

### Secondary Aims
1. Quantify **agreement between AI consensus and expert clinician evaluation** (gold standard).
2. Assess **impact of MediaPipe + librosa telemetry layer** on critical-error detection sensitivity for S5 coordination (CRIT-pMDI-04) and S7 breath-hold (CRIT-pMDI-08).
3. Document **device sub-type telemetry profile** (real pMDI vs AIM training simulator).
4. Establish **clinician review flag calibration** (κ threshold and priority levels).

### Exploratory Aims
- Cross-model validation: Claude vs Gemini vs local Gemma (on-premise Ollama).
- Cost-quality tradeoff: cheap (Gemini Flash dual) vs research-grade (Opus+Pro+TB).

---

## 3. Study Design

### 3.1 Type
- Prospective single-center observational study with cross-sectional video assessment.

### 3.2 Setting
- Outpatient allergy clinic + Pulmonary Function Lab at CBNUH.

### 3.3 Sample Size and Composition

| Group | n | Inclusion |
|---|---|---|
| Healthy volunteers | 15 | Age ≥19, no chronic respiratory disease, informed consent |
| Asthma patients | 15 | Age ≥19, physician-diagnosed asthma, on inhaled therapy ≥3 months |
| **Total** | **30** | |

**Inclusion criteria** (both groups):
- Capable of providing informed consent in Korean or English
- Owns or can access a pMDI inhaler (will be provided AIM-equivalent placebo if needed)

**Exclusion criteria**:
- Inability to perform inhalation maneuver due to cognitive/physical impairment
- Active respiratory infection at enrollment
- Refusal of video recording
- Prior participation in another CAMCA validation study

### 3.4 Device Coverage
- pMDI (standalone) — Primary MVP scope (n=30)
- pMDI + Spacer — secondary subgroup (anticipated 5-8 cases)
- DPI-Turbuhaler — Phase 2 follow-up study (separate IRB submission)

---

## 4. Data Collection Procedures

### 4.1 Video Recording Specification

| Parameter | Specification | Rationale |
|---|---|---|
| Camera | Smartphone (patient's own or provided iPhone/Android) | Real-world generalizability |
| Resolution | ≥720p (1280×720) | MediaPipe landmark accuracy |
| Frame rate | 30 fps minimum | Sub-second event timing |
| Duration | 20-60 sec (full demonstration) | Capture all 7 pMDI steps |
| Angle | Frontal + slight 30° lateral | Allow canister-top visibility for S5 |
| Audio | Built-in microphone, no ambient music | librosa dB extraction |
| Lighting | Adequate indoor (>200 lux) | Vision landmark confidence |

**Camera placement instructions to subjects** (Korean handout provided):
1. Place phone on stable surface at chest height
2. Stand 1-1.5 m from camera
3. Ensure both hands and face are in frame
4. Avoid backlight (window behind you)
5. Demonstrate the FULL sequence including pre-inhalation prep (shake, cap, exhale)

### 4.2 Privacy and De-identification (CRITICAL)

- **MediaPipe Face Mesh upper-face anonymization** applied **on-device before any cloud upload**
- Preserves mouth, chin, and inhaler mouthpiece interaction for clinical seal assessment
- Blurs eyes, nose bridge, and identifiable facial regions
- Implementation: `assets/scripts/anonymize_video.py` (to be added in v0.5.0)
- **No personally identifiable audio** retained: speech is muted via spectral subtraction; inhaler/breath audio preserved
- All cloud uploads use Vertex AI Seoul region (PIPA-compliant, no cross-border transfer)
- Local Ollama backend available for on-premise-only analysis arm (no cloud at all)

### 4.3 Expert Clinician Gold Standard

Each video is independently scored by:
- **Reviewer 1**: PI (M-G Kang, board-certified allergist)
- **Reviewer 2**: Senior clinical pharmacist with ≥10 years respiratory experience
- **Adjudicator (for disagreements)**: External pulmonologist (blinded to AI output)

Disagreements between Reviewers 1 and 2 of ≥1 level → adjudicator decision. This human gold standard is compared to AI consensus.

---

## 5. Statistical Analysis Plan

### 5.1 Primary Analysis — Inter-Rater Reliability

**AI Evaluator A vs AI Evaluator B**:
- **Cohen's κ** (linear weighted), reported per step and overall
- Landis & Koch 1977 interpretation thresholds
- **Critical-error agreement**: separate calculation (target ≥0.90)
- Bootstrap 95% CI (1000 iterations)

**AI Consensus vs Human Gold Standard**:
- Pairwise weighted κ
- Sensitivity / specificity / positive predictive value for each critical error type
- ROC curve for overall verdict (FAIL/non-FAIL)

### 5.2 Secondary Analysis — Telemetry Impact

Each video evaluated twice:
1. **VLM-only mode** (v0.1.0 equivalent — no telemetry layer)
2. **Telemetry-augmented mode** (v0.2.0+ — full MediaPipe + librosa)

Compared:
- κ change: pre- vs post-telemetry
- Critical-error detection sensitivity change
- Evaluation duration (computation time)
- Cost (cloud API token consumption)

**Hypothesis**: Telemetry layer increases CRIT-pMDI-04 (coordination) detection sensitivity by ≥15% absolute.

### 5.3 Subgroup Analyses

- Real pMDI vs AIM simulator: audio threshold calibration
- Healthy vs asthma: technique error rate
- Age (≥65 vs <65): error type distribution
- First-time vs experienced users: which errors most prevalent

### 5.4 Quality Metrics

- **Tie-breaker invocation rate**: target 15-30% (validates persona calibration)
- **Clinician review flag accuracy**: % of flagged cases where human reviewer found a real issue
- **Telemetry availability rate**: % of cases where MediaPipe + audio both succeed

---

## 6. Data Management

### 6.1 Storage

| Data type | Location | Retention |
|---|---|---|
| Raw videos | CBNUH secure on-premise NAS | 5 years post-publication |
| Anonymized videos | Local + Vertex AI Seoul (encrypted) | Same |
| Telemetry JSONs | `logs/{case_id}/01b_*`, `01c_*` | Same |
| Evaluator outputs | `logs/{case_id}/04_*`, `05_*` | Same |
| Adjudication + consensus | `logs/{case_id}/06_*`, `07_*` | Same |
| Master CSV aggregates | Single Excel file at CBNUH | Same |
| API call logs (cost) | Separate billing log | 2 years |

### 6.2 Data Export

All cases follow the CAMCA standard schema (see `camca-py` package output structure). Master CSV columns include:
- Per-evaluator score and critical-error count
- Per-stage model used and duration
- κ (unweighted/linear/quadratic)
- Tie-breaker invocation and outcome
- Clinician review priority
- Telemetry availability (vision/audio/both)

### 6.3 Reproducibility

- All deterministic computations (kappa, scoring) produce `sha256:` signature
- Same input → same signature → bit-identical output guaranteed
- Software versions logged: `00_pipeline_metadata.json.pipeline_version`
- Model versions logged per stage: `00_pipeline_metadata.json.stages[*].model_used`

---

## 7. Ethical Considerations

### 7.1 IRB Submission
- CBNUH IRB approval to be obtained before enrollment
- Reciprocal IRB notification to MGH/HMS as collaborating institution
- Annual continuing review

### 7.2 Informed Consent
- Written consent in Korean (with English version for international patients)
- Explicit consent points:
  - Video recording of face, hands, and inhaler interaction
  - On-device face anonymization performed before any cloud upload
  - Cloud analysis via Vertex AI Seoul region (PIPA-compliant)
  - Optional on-premise-only mode available (Ollama backend) — patient's choice
  - Data retention for 5 years post-publication
  - Right to withdraw at any time with deletion of all materials
- Separate consent for use of anonymized videos in future publications

### 7.3 Regulatory Compliance

- **Korean PIPA**: Vertex AI Seoul region eliminates cross-border transfer requirements
- **MFDS classification**: This is a research prototype — not yet a Software as a Medical Device (SaMD); classification will be sought post-pilot if clinical deployment is pursued
- **FDA**: Not regulated as device in current research-only scope
- **Bias mitigation**: Multi-vendor backend (Claude + Gemini + Ollama) reduces single-vendor lock-in bias

### 7.4 AI Failure Mitigation

- **Patient PDF report** includes prominent disclaimer: "본 평가는 AI 영상 분석 결과이며, 의료진의 직접 평가를 완전히 대체하지 않습니다"
- **Clinician review flag** at three levels (none / moderate / high) — high priority cases manually reviewed within 24h
- **Tie-breaker auto-invocation** when κ < 0.6
- **Hard fail-safe**: any critical error → FAIL verdict regardless of score

---

## 8. Study Timeline

| Phase | Duration | Activities |
|---|---|---|
| Phase 1 — Setup | 2 months | IRB submission, equipment procurement, training |
| Phase 2 — Enrollment | 3 months | n=30 enrollment + video collection |
| Phase 3 — Analysis | 2 months | Dual-mode evaluation + human gold standard scoring |
| Phase 4 — Reporting | 2 months | Statistical analysis + manuscript drafting |
| **Total** | **9 months** | |

---

## 9. Expected Outcomes and Publication Strategy

### 9.1 Primary Publication
Target journal: *J Allergy Clin Immunol: In Practice* (CRITIKAL precedent) or *NPJ Digital Medicine*
Title: *"Multi-agent VLM with Quantitative Telemetry for Automated Inhaler Technique Assessment: A Pilot Study"*

### 9.2 Companion Publications
- Methods paper: CAMCA architecture (open-source release)
- Korean-language clinical brief: 충북대 의과대학 학술지
- Comparative validation: GPT-5 vs Claude vs Gemini for medical video analysis

### 9.3 Open Source Release
- Plugin (`camca-inhaler-eval.plugin`) + Python package (`camca` on PyPI)
- All skills and rubrics under MIT license
- Bundled clinical reference tables (XLSX + Markdown) for educator use

---

## 10. Funding and Conflicts of Interest

- **Funding**: TBD (likely CBNUH internal seed grant)
- **Cloud costs**: Estimated $50-150 USD for n=30 pilot (Claude Opus + Gemini Pro)
- **Conflicts of interest**: None to declare. No industry sponsorship of CAMCA development.

---

## 11. Appendices

### Appendix A — Telemetry Layer Specification
See `camca-py/src/camca/telemetry/thresholds.py` for clinical thresholds.

Per-device threshold profile (v0.3.0 forward — pending pilot data):

| Threshold | Real pMDI | AIM Simulator | DPI-Turbuhaler |
|---|---|---|---|
| `AUDIO_INHALATION_MIN_DB` | 50.0 | TBD (estimated 45.0) | 55.0 |
| `AUDIO_BREATH_HOLD_THRESHOLD_DB` | 40.0 | TBD (estimated 41.0) | 40.0 |
| `INHALATION_OPTIMAL_DURATION_MS` | 3000 | 3000 | 2000 (fast inhale) |

### Appendix B — Reference Materials Bundled
- `assets/reference/inhaler_reference_tables.xlsx` — 6-sheet comprehensive rubric
- `assets/static/patient_guide_pmdi_ko.pdf` — 4-page patient guide
- `assets/static/patient_guide_pmdi_en.pdf` — 5-page English version

### Appendix C — Software Versions (Locked for Pilot)
- camca v0.2.0 (Python package, frozen for pilot)
- camca-inhaler-eval v0.4.0 (Claude plugin)
- Claude API: claude-opus-4-7, claude-sonnet-4-6
- Gemini API: gemini-2.5-pro, gemini-2.5-flash
- Ollama models: gemma3:27b, qwen2.5vl:32b (on-premise fallback)
- MediaPipe ≥0.10, librosa ≥0.10, reportlab ≥4.0, pypdf ≥3.0

### Appendix D — Pilot Case Schema (per case)

```
logs/CAMCA-PILOT-{NNN}/
├── 00_pipeline_metadata.json
├── 01_input.json                  (patient metadata, age, group)
├── 01b_telemetry_stream.json      (0.1s × 6 indicators)
├── 01c_telemetry_summary.json     (clinical anchors)
├── 02_device_id.json
├── 03_segments.json
├── 04_evaluator_a.json            (VLM-only mode)
├── 04_evaluator_a_with_telemetry.json
├── 05_evaluator_b.json            (VLM-only mode)
├── 05_evaluator_b_with_telemetry.json
├── 06_adjudication.json
├── 06b_kappa_stats.json
├── 06c_tie_breaker.json           (if needed)
├── 07_final_score.json
├── 08_patient_report_ko.pdf
├── 08_patient_report_en.pdf
├── 08_clinician_report_ko.pdf
├── 09_research_export.json
├── 09_research_export.csv
├── 10_human_gold_standard.json    (Reviewer 1 + 2 + adjudicator)
└── 11_comparison_AI_vs_human.json (computed post-hoc)
```

---

**Document control**:
- v1.0 (2026-05-21): Initial draft for IRB submission
- v1.1 (TBD): Post-IRB-feedback revision

Generated as part of the CAMCA v0.4.0 (plugin) / v0.2.0 (Python package) release.
