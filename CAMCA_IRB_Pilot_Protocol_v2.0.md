# CAMCA Pilot Study Protocol (n=30) — v2.0
**Camera-based Automated Multi-agent Clinical Assessment of Inhaler Technique**

**Version**: 2.0 (2026-05-21)
**Status**: IRB-ready (post n=2 internal validation)
**PI**: Min-Gyu Kang, MD (충북대학교병원 알레르기내과)
**Institution**: Chungbuk National University Hospital (CBNUH)
**Collaboration**: Massachusetts General Hospital · Harvard Medical School
**Contact**: drugnsafety@gmail.com

---

## 0. 개정 이력 (v1.0 → v2.0)

| 변경 영역 | v1.0 (2026-05-21 초안) | **v2.0 (2026-05-21 개정)** |
|---|---|---|
| **Preliminary data** | 없음 | **n=2 internal validation (PARK·KIM) — κ_linear 0.0 vs 0.71 paired case** 추가 |
| **시스템 아키텍처** | 4-layer hybrid (개념) | **검증된 v0.3.0 stack** — L1~L5 한계 해결 + L6~L8 prospective 검증 plan |
| **SAP (Statistical Analysis Plan)** | 1-page | **§5 정교화** — 1차 IRR, 2차 telemetry impact, 3차 κ-as-quality-proxy, 사전 정의된 power calculation |
| **PIPA·MFDS·IRB 컴플라이언스** | §7 요약 | **§7 확장** — Vertex AI Seoul, on-device anonymization 알고리즘 spec, MFDS SaMD class 2 후속 경로 |
| **AI failure-mode catalog** | 일반론 | **검증 기반 8개 실패 모드 매트릭스** (L1-L8) |
| **부록 D — schema** | 21 파일 | **24 파일** (telemetry audit, vlm reasoning trace, reconciliation log 추가) |
| **Budget appendix** | 없음 | **부록 E — 예산 표** 추가 |

> ✅ v2.0의 핵심 차별점은 "**가설→검증된 데이터** 전환"입니다. v1.0이 prospective protocol이었다면, v2.0은 n=2 internal validation 결과 + 5개 시스템 한계의 정량 해결 → IRB 위원회가 평가할 수 있는 **재현 가능한 evidence base**를 갖춥니다.

---

## 1. Background and Rationale

### 1.1 Clinical Problem

- **흡입제 오용의 광범위성**: 천식·COPD 환자의 70-80%가 흡입제를 부정확하게 사용함 (Sanchis 2016, CRITIKAL 2017).
- **의료진 자체의 한계**: 처방자조차 부정확한 시범을 보이는 경우가 빈번함 (Plaza 2018).
- **CRITIKAL 연구의 critical errors 정의** — 임상 outcome 악화와 통계적으로 연관된 오류:
  - pMDI coordination failure (유병률 45%, aOR 1.45 for uncontrolled asthma)
  - DPI inadequate inspiratory effort (38%)
  - Inadequate breath-hold (38%)
- **자동 평가 시스템의 부재**: PubMed 검색상 published computer-vision-based automated scoring system은 존재하지 않음. 유일한 상용 경쟁자(Kata® by VisionHealth)는 2017년 기술 stack에 머물러 있고, 주요 digital inhaler 회사들은 2024년 시장에서 철수.

### 1.2 Solution Architecture — v0.3.0 기준 검증된 4-Layer Hybrid

| Layer | 기능 | 컴포넌트 | v0.3.0 검증 상태 |
|---|---|---|---|
| **0 — Quantitative measurement** | 0.1초 해상도 결정론적 물리 측정 | MediaPipe Pose+FaceMesh + librosa DSP | ✅ n=2 검증 (L1-L5 해결) |
| **1 — Probabilistic observation** | VLM이 telemetry를 anchor로 활용 | Dual-agent (Claude Opus + Gemini Pro) | ✅ Pydantic schema 강제 |
| **2 — IRR adjudication** | Cohen's κ 산출 + 결정론적 통계 | `kappa_calculator.py` (sha256 signature) | ✅ KIM κ=0.71 / PARK κ=0.0 |
| **3 — Final scoring** | Verdict + critical-error override | `scoring_engine.py` | ✅ 100% deterministic 재현 |

이 4-layer separation은 다음의 fundamental 문제를 해결합니다:

1. **Hallucination** — single VLM의 신뢰도 부족 → Layer 0 telemetry가 anchor로 grounding
2. **Black-box bias** — auditability 부재 → Layer 1 VLM reasoning trace + Layer 2/3 deterministic
3. **Cross-vendor lock-in** — single vendor risk → Claude / Gemini / Ollama 3-way 호환

---

## 2. Study Aims (정교화 v2.0)

### 2.1 Primary Aim

**Establish inter-rater reliability** between two independent VLM evaluator personas (GINA-strict vs pragmatic-clinical) on standardized inhaler-technique videos, **with and without quantitative telemetry augmentation**.

**Primary endpoint**: Cohen's κ_linear (overall, per-step, per-critical-error) — bootstrap 95% CI.

**Sample size justification**: n=30 yields ≥80% power to detect κ ≥ 0.7 (substantial agreement) vs null of κ=0.4 (moderate agreement) at α=0.05, based on Fleiss-Cohen sample size table for ordinal κ with 7 steps × 4 levels.

### 2.2 Secondary Aims

1. **Telemetry impact on critical-error detection**: 정량적으로 telemetry layer 적용 전후의 CRIT-pMDI-04 (coordination), CRIT-pMDI-08 (breath-hold) 검출 sensitivity 변화 측정.
2. **AI vs human gold standard agreement**: AI consensus vs (PI + senior pharmacist + adjudicator) gold standard의 pairwise weighted κ.
3. **Device sub-type telemetry profile**: 실제 pMDI vs AIM training simulator의 audio profile (peak dB, baseline dB, inhalation onset detection rate) 정량화.
4. **Clinician review flag calibration**: κ threshold (0.6) + critical-error 불일치 → review priority (none/moderate/high) 자동 부여 시스템의 sensitivity/specificity.

### 2.3 Exploratory Aims

- **Cross-model validation**: Claude Opus vs Gemini 2.5 Pro vs 로컬 Gemma3:27b (on-premise Ollama) → 같은 영상에 대한 합의도.
- **Cost-quality tradeoff**: 저비용 (Gemini Flash dual) vs research-grade (Opus + Gemini Pro + tie-breaker).
- **κ as video-quality proxy** (n=2 발견): 영상 acquisition quality (resolution, angle, occlusion)가 동일한 verdict에서도 κ를 5배 이상 변동시키는 현상의 prospective 검증.

---

## 3. Study Design

### 3.1 Type

Prospective single-center observational study with cross-sectional video assessment.

### 3.2 Setting

- 충북대학교병원 알레르기내과 외래 + 호흡기 검사실 (Pulmonary Function Lab)
- 영상 촬영: 진료실 내 표준화된 brackets (벽 마운트 + 1.5m 거리)
- 분석: 사내 보안 NAS + Vertex AI Seoul (PIPA region)

### 3.3 Sample Size and Composition

| Group | n | 포함 기준 |
|---|---|---|
| Healthy volunteers | 15 | 만 19세 이상, 만성 호흡기 질환 없음, 동의서 작성 가능 |
| Asthma patients | 15 | 만 19세 이상, 의사 진단 천식, 흡입 치료 ≥3개월 |
| **Total** | **30** | |

**Inclusion criteria** (공통):
- 한국어 또는 영어로 동의서 작성 가능
- pMDI 흡입제 소유 또는 AIM-equivalent placebo 제공 수용

**Exclusion criteria**:
- 인지·신체적 장애로 흡입 동작 불가
- enrollment 시점 active 호흡기 감염
- 영상 촬영 거부
- 다른 CAMCA validation study 참여 이력

### 3.4 Device Coverage

| Device | n (예상) | Phase |
|---|---|---|
| pMDI standalone | 20 | MVP (이번 IRB) |
| pMDI + Spacer | 5-8 | Secondary subgroup |
| AIM training simulator | 30 (전원 — 교육용 비교) | 동일 IRB 내 |
| DPI-Turbuhaler | — | Phase 2 별도 IRB |

---

## 4. Data Collection Procedures

### 4.1 Video Recording Specification (v2.0 강화)

| Parameter | Specification | Rationale |
|---|---|---|
| Camera | 스마트폰 (환자 본인 또는 제공된 iPhone 14/Galaxy S24) | Real-world 일반화 |
| Resolution | **≥1080p (1920×1080)** | KIM(1080p) vs PARK(720p) 결과 → MediaPipe landmark 정확도 차이 발견 |
| Frame rate | 30 fps minimum | Sub-second event timing |
| Duration | 20-60초 (전체 시퀀스) | 7-step pMDI 전체 capture |
| Angle | **정면 우선 (≤15° 측면 허용)** | PARK case: 측면 영상 → 측면 face landmark 검출 실패 |
| Grip | **canister top + 검지 시각화 권장** | PARK case: 양손 cupping → occlusion |
| Audio | Built-in microphone, ambient music 제거 | librosa dB 추출 |
| Lighting | 실내 ≥200 lux | Vision landmark confidence |

**Camera placement 가이드 (환자용 한국어 handout 별도 제공)**:
1. 흉부 높이의 안정된 표면에 스마트폰 거치
2. 카메라로부터 1-1.5m 거리에 직립
3. 양 손과 얼굴이 모두 화면 안에 들어오도록
4. 후방 광원 (역광) 피하기
5. **전체 시퀀스 시범** — pre-inhalation prep (shake → cap → exhale) 포함

### 4.2 Privacy and De-identification (CRITICAL)

- **MediaPipe Face Mesh upper-face anonymization** — **on-device, cloud 업로드 이전 적용**
  - 보존: 입, 턱, mouthpiece interaction (clinical seal assessment 필수)
  - 차단: 눈, 코, 식별 가능 facial 영역
  - 구현: `assets/scripts/anonymize_video.py` (v0.3.0 포함 예정)
- **Audio de-identification**: speech은 spectral subtraction으로 silenced, inhaler/breath audio는 보존
- **Cloud upload region**: Vertex AI Seoul region only (PIPA 준수, cross-border transfer 없음)
- **On-premise-only arm 옵션**: Ollama backend (gemma3:27b + qwen2.5vl:32b) — 클라우드 0% 케이스 가능

### 4.3 Expert Clinician Gold Standard

각 영상은 다음 3명에 의해 독립적으로 평가됨:
- **Reviewer 1** (PI): M-G Kang, MD — 알레르기 전문의 (board-certified)
- **Reviewer 2**: 호흡기 임상약사 (≥10년 경력)
- **Adjudicator** (불일치 시): 외부 호흡기내과 전문의 (AI 출력 blinded)

Reviewer 1·2 간 ≥1 level 차이 → adjudicator 결정. 이 human gold standard가 AI consensus와 비교 대상.

---

## 5. Statistical Analysis Plan (v2.0 정교화)

### 5.1 Primary Analysis — Inter-Rater Reliability

**AI Evaluator A vs AI Evaluator B** (model + persona dual diversity):
- **Cohen's κ_linear** (Landis & Koch 1977 thresholds): per step + overall
- **Critical-error agreement**: 별도 계산 (target ≥0.90)
- **Bootstrap 95% CI** (1,000 iterations, BCa method)
- **Per-device subgroup**: pMDI vs pMDI-spacer vs AIM simulator
- **Per-age subgroup**: ≥65 vs <65세
- **Per-recording-quality subgroup**: 1080p vs 720p, 정면 vs 측면

**AI Consensus vs Human Gold Standard**:
- Pairwise weighted κ (linear + quadratic 둘 다)
- Per critical-error type: sensitivity / specificity / PPV / NPV
- 전체 verdict (FAIL / non-FAIL)에 대한 ROC curve

### 5.2 Secondary Analysis — Telemetry Layer Impact (Pre-registered)

**각 영상을 두 번 분석**:
1. **VLM-only mode** (v0.1.0 equivalent — telemetry layer 비활성화)
2. **Telemetry-augmented mode** (v0.3.0 — full MediaPipe + librosa)

**Pre-specified hypothesis**: Telemetry layer는 CRIT-pMDI-04 (coordination) 검출 sensitivity를 **절대 ≥15%** 증가시킬 것이다 (n=2 internal data에서 anchor confidence 차이가 컸음).

**비교 지표**:
- κ pre vs post telemetry
- Critical-error sensitivity 변화
- 단계별 evaluator confidence (self-report)
- Cost (cloud API token consumption) — telemetry는 +0% (on-device)

### 5.3 Tertiary Analysis — κ-as-Video-Quality-Proxy (n=2 발견의 prospective 검증)

**Pre-specified hypothesis** (from KIM vs PARK paired case):

> *"같은 verdict (ADEQUATE_WITH_EDUCATION, 10/12점)에서도 영상 acquisition quality에 따라 κ가 0.0 ~ 0.71로 변동한다. 따라서 κ 자체가 video-quality + technique-clarity proxy로 작동한다."*

**검증 방법**:
- 모든 30 케이스에서 (verdict, κ) pair를 분석
- Verdict 동일 (e.g., ADEQUATE_WITH_EDUCATION) cohort 내에서 κ의 IQR 측정
- 영상 acquisition variables (resolution, angle, grip occlusion) → κ regression model
- κ-based clinician review priority의 sensitivity/specificity (κ<0.6 → review priority high)

**Expected impact**: 만약 hypothesis가 confirmed되면, 임상 deploy시 "verdict + κ"를 **함께** 보고하는 것이 표준이 되어야 함.

### 5.4 Quality Metrics

- **Tie-breaker invocation rate**: target 15-30% (persona calibration validation)
- **Clinician review flag accuracy**: % of flagged cases where human reviewer found a real issue
- **Telemetry availability rate**: % of cases where MediaPipe + audio 둘 다 성공

### 5.5 Pre-specified Subgroup Analyses

- **Real pMDI vs AIM simulator**: audio threshold calibration → DEVICE_AUDIO_PROFILES dictionary 업데이트
- **Healthy vs asthma**: technique error rate
- **Age (≥65 vs <65)**: error type distribution
- **First-time vs experienced users**: 가장 빈번한 error 유형

---

## 6. Data Management

### 6.1 Storage

| Data type | Location | Retention |
|---|---|---|
| Raw videos | CBNUH 사내 보안 NAS | publication 후 5년 |
| Anonymized videos | Local + Vertex AI Seoul (encrypted at rest) | 동일 |
| Telemetry JSON | `logs/{case_id}/01b_*`, `01c_*` | 동일 |
| Evaluator outputs | `logs/{case_id}/04_*`, `05_*`, `04_*_with_telemetry` | 동일 |
| Adjudication + consensus | `logs/{case_id}/06_*`, `07_*` | 동일 |
| Master CSV aggregates | CBNUH 단일 Excel 파일 | 동일 |
| API call log (cost·token) | 별도 billing log | 2년 |

### 6.2 Data Export

모든 케이스는 CAMCA standard schema (camca-py 패키지 output) 준수. Master CSV 컬럼 포함:
- Per-evaluator score + critical-error count
- Per-stage model used + duration
- κ (unweighted/linear/quadratic)
- Tie-breaker invocation + outcome
- Clinician review priority
- Telemetry availability (vision/audio/both)
- **NEW v2.0**: VLM↔Telemetry reconciliation outcome (Agree / VLM_wins / Telemetry_wins / Conflict_flagged)

### 6.3 Reproducibility

- 모든 deterministic computation (kappa, scoring)은 `sha256:` signature 생성
- 동일 입력 → 동일 signature → bit-identical output 보장
- Software 버전 log: `00_pipeline_metadata.json.pipeline_version`
- 모델 버전 log per stage: `00_pipeline_metadata.json.stages[*].model_used`

---

## 7. Ethical Considerations (v2.0 확장)

### 7.1 IRB Submission

- CBNUH IRB 승인 후 enrollment 개시
- MGH/HMS 협력기관 reciprocal notification
- Annual continuing review

### 7.2 Informed Consent (한국어 + 영어 dual)

**Explicit consent points**:
- 얼굴, 손, 흡입제 interaction의 영상 녹화
- On-device facial anonymization (cloud 업로드 이전)
- Cloud 분석 via Vertex AI Seoul (PIPA 준수)
- On-premise-only mode 옵션 (Ollama backend — 환자 선택권)
- Publication 후 5년 보관
- 언제든 철회 + 모든 자료 삭제 권리
- Anonymized video의 향후 publication 사용 별도 동의

### 7.3 Regulatory Compliance — 한국·미국 dual track

#### 7.3.1 Korean PIPA (Personal Information Protection Act)

- **Cross-border data transfer 없음**: Vertex AI Seoul region 사용 (한국 내 처리)
- **Data minimization**: On-device anonymization으로 식별 정보 차단 (eyes/nose blurred), 임상 평가에 필수인 mouth/hands만 보존
- **명시적 별도 동의**: Cloud upload arm vs on-premise-only arm 환자 선택권 명문화
- **삭제권 (Right to be forgotten)**: 환자가 철회 시 7일 내 모든 storage에서 삭제 (NAS + Vertex AI + local backup)

#### 7.3.2 MFDS (식품의약품안전처) SaMD Classification

- **현재 분류**: 연구용 prototype — Software as a Medical Device (SaMD) 분류 대상 아님
- **임상 deploy 전 후속 경로**:
  - **Class II SaMD** 후보 (의료진 의사결정 지원, 자동 진단 아님)
  - MFDS "인공지능 기반 SaMD 허가·심사 가이드라인" (2023) 준수 계획
  - Pilot 종료 후 별도 회의 신청
- **Post-market surveillance** (deploy 후): clinician review flag rate, false-FAIL rate, patient complaint log 분기별 보고

#### 7.3.3 FDA (US)

- 현 연구 범위에서는 device로 분류되지 않음 (research only, IRB-approved)
- 미국 임상 deploy 추진 시 별도 510(k) 또는 De Novo path 검토

#### 7.3.4 Bias Mitigation

- Multi-vendor backend (Claude + Gemini + Ollama) → single-vendor lock-in bias 감소
- Persona diversity (GINA strict vs pragmatic) → single-perspective bias 감소
- Human gold standard 비교 → algorithmic miscalibration 검출

### 7.4 AI Failure-Mode Catalog (v2.0 검증 기반)

n=2 internal validation으로 검출된 **8개 실패 모드**와 해결 상태:

| # | Failure mode | 발견 케이스 | 검증된 해결 | 임상 risk |
|---|---|---|---|---|
| L1 | Breath-hold detector false positive (조용한 audio) | KIM-001 | ✅ v0.2.1 — min_peak_db_for_detection=55 | 잘못된 verdict (Level 1→3 inflation) |
| L2 | Finger acceleration threshold 너무 낮음 (8 px/s²) | KIM-001 | ✅ v0.2.1 — 100 px/s² + 3-frame MA | False CRIT-pMDI-04 flag |
| L3 | Head pitch 좌표계 변환 버그 | KIM-001 | ✅ v0.2.1 — calibrated atan2 | S4 자세 평가 부정확 |
| L4 | AIM 시뮬레이터 audio threshold 불일치 | PARK+KIM | ✅ v0.2.1 — DEVICE_AUDIO_PROFILES dict | S5/S7 anchor 실패 |
| L5 | VLM↔Telemetry 충돌 시 정책 부재 | KIM-001 (Algo 11.3s vs VLM 3s) | ✅ v0.2.1 — reconciliation.py | 자동 verdict 신뢰도 낮음 |
| L6 | 카메라 각도 의존성 (측면→MediaPipe 검출 실패) | PARK-001 | 🔜 v0.3.0 — view_angle field | S4·S5 정확도 변동 |
| L7 | VLM frame sampling (1 fps) 한계 | KIM-001 S7 | 🔜 v0.3.0 — 2-4 fps + step-aware | 시간적 지표 과소평가 |
| L8 | Audio peak 부재 시 inhalation 추론 불가 | PARK+KIM | 🔜 v0.4.0 — vision-only inhalation | AIM class 전체 영향 |

### 7.5 AI Failure Mitigation — 환자 대면 안전망

- **환자용 PDF report 의무 disclaimer**: *"본 평가는 AI 영상 분석 결과이며, 의료진의 직접 평가를 완전히 대체하지 않습니다"*
- **Clinician review flag** 3단계:
  - **None**: κ ≥ 0.8 + critical-error 일치
  - **Moderate**: 0.6 ≤ κ < 0.8 OR 영상 acquisition warning
  - **High**: κ < 0.6 OR critical-error 불일치 OR reconciliation conflict → **24h 내 임상의 직접 검토 의무**
- **Tie-breaker auto-invocation**: κ < 0.6 시 자동 호출 (3rd evaluator + 2/3 majority vote)
- **Hard fail-safe**: 어느 evaluator든 critical error 단일 발견 → 자동 FAIL verdict (점수 무관)

---

## 8. Study Timeline (Updated)

| Phase | 기간 | 활동 |
|---|---|---|
| **Phase 0 — 검증 완료** | ✅ 완료 (2026-05-21) | n=2 internal validation (PARK, KIM), L1-L5 해결, v0.3.0 release |
| Phase 1 — Setup | 2개월 | IRB 제출, 장비 조달, 임상의 training |
| Phase 2 — Enrollment | 3개월 | n=30 enrollment + 영상 collection |
| Phase 3 — Analysis | 2개월 | Dual-mode evaluation + human gold standard scoring |
| Phase 4 — Reporting | 2개월 | 통계 분석 + manuscript drafting |
| **Total (Phase 1-4)** | **9개월** | |

---

## 9. Expected Outcomes and Publication Strategy

### 9.1 Primary Publication

**Target journal**: *J Allergy Clin Immunol: In Practice* (CRITIKAL 출간지) 또는 *NPJ Digital Medicine*
**Tentative title**: *"Multi-agent VLM with Quantitative Telemetry for Automated Inhaler Technique Assessment: A Pilot Study (n=30)"*

### 9.2 Companion Publications

- **Methods paper**: CAMCA 아키텍처 오픈소스 release (Plugin + Python pkg) — *Software Impacts* 또는 *Journal of Open Source Software*
- **한국어 임상 brief**: 충북대학교 의과대학 학술지
- **Cross-model validation**: GPT-5 vs Claude vs Gemini for medical video analysis — *NPJ Digital Medicine* methods

### 9.3 Open Source Release

- Plugin (`camca-inhaler-eval.plugin`) + Python package (`camca` on PyPI)
- 모든 skill과 rubric은 MIT license
- 번들 clinical reference 테이블 (XLSX + Markdown) — educator 활용 가능

---

## 10. Funding and Conflicts of Interest

- **Funding**: TBD (CBNUH internal seed grant 신청 예정 + 정부 R&D 과제 병행 신청 검토)
- **Cloud costs (estimated)**: $50-150 USD for n=30 pilot (Claude Opus + Gemini Pro full-grade run)
- **Conflicts of interest**: 없음. CAMCA 개발에 산업 후원 없음.

---

## 11. Appendices

### Appendix A — Telemetry Layer Specification (v0.3.0 검증된 값)

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

- `assets/reference/inhaler_reference_tables.xlsx` — 6-sheet 종합 rubric
- `assets/static/patient_guide_pmdi_ko.pdf` — 4-page 환자 가이드 (한국어)
- `assets/static/patient_guide_pmdi_en.pdf` — 5-page (영문)
- `assets/static/patient_guide_turbuhaler_ko.pdf` — Phase 2

### Appendix C — Software Versions (Pilot용 Lock)

- **camca v0.3.0** (Python package, frozen for pilot)
- **camca-inhaler-eval v0.4.0** (Claude plugin)
- **Claude API**: claude-opus-4-7, claude-sonnet-4-6
- **Gemini API**: gemini-2.5-pro, gemini-2.5-flash
- **Ollama models** (on-premise fallback): gemma3:27b, qwen2.5vl:32b
- **MediaPipe** ≥0.10, **librosa** ≥0.10, **reportlab** ≥4.0, **pypdf** ≥3.0

### Appendix D — Pilot Case Schema (per case, v2.0 확장)

```
logs/CAMCA-PILOT-{NNN}/
├── 00_pipeline_metadata.json          (모든 stage 모델·timing·sha256)
├── 01_input.json                       (환자 메타, age, group)
├── 01b_telemetry_stream.json           (0.1s × 6 indicators)
├── 01b_telemetry_full_audit.json       (audio actual + vision observed 분리) ⭐NEW v2.0
├── 01c_telemetry_summary.json          (clinical anchors)
├── 01d_telemetry_schema.md             (6 metric meaning) ⭐NEW v2.0
├── 02_device_id.json                   (+ device sub-type)
├── 03_segments.json
├── 04_evaluator_a.json                 (VLM-only mode)
├── 04_evaluator_a_with_telemetry.json  (telemetry-augmented)
├── 04_evaluator_a_detailed.json        (reasoning trace 포함) ⭐NEW v2.0
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
└── 11_comparison_AI_vs_human.json       (post-hoc computed)
```

### Appendix E — Pilot Budget (USD, 추정)

| 항목 | Unit cost | Quantity | Subtotal |
|---|---|---|---|
| Cloud API (Claude Opus + Gemini Pro, n=30 dual-mode = 60 runs) | $1.50/run | 60 | $90 |
| Telemetry compute (on-device, free) | $0 | 30 | $0 |
| Ollama tie-breaker (on-premise GPU 시간) | $0 (sunk) | 30 | $0 |
| Storage (encrypted NAS, 1 year) | flat | — | $50 |
| Statistical software (R, free) | $0 | — | $0 |
| **Estimated total** | | | **$140 USD** |

→ 예외적으로 저비용. 주요 사업 cost는 임상의 시간 + IRB 행정.

### Appendix F — Preliminary Internal Validation Summary (n=2)

**검증 케이스 1: CAMCA-PARK-001** (박상이 학생, pMDI demo)
- Evaluator A (Opus + GINA strict): 6/12 (50%)
- Evaluator B (Sonnet + pragmatic): 10/12 (83%)
- κ_linear = 0.0 → tie-breaker 4건 호출, 모두 B 손
- 최종 consensus: ADEQUATE_WITH_EDUCATION (10/12, 83%)
- Critical errors: 0
- Data quality flag: PARTIAL_DATA (영상이 흡입부터 시작 → S1-S3 미관측)
- 비고: 측면 각도 + 양손 cupping → MediaPipe occlusion

**검증 케이스 2: CAMCA-KIM-001** (김진수 학생, 1080p 정면)
- Evaluator A: 9/12 (75%)
- Evaluator B: 10/12 (83%)
- κ_linear = 0.71 → substantial agreement, tie-breaker 불필요
- 최종 consensus: ADEQUATE_WITH_EDUCATION (10/12, 83%)
- Critical errors: 0
- 비고: 1080p + 정면 + 한 손 표준 그립 → 모든 vision telemetry 100% 검출 성공

**핵심 발견 (KIM vs PARK paired)**:

| 항목 | KIM-001 | PARK-001 |
|---|---|---|
| Consensus 점수 | **10/12 (동일)** | **10/12 (동일)** |
| Verdict | **ADEQUATE_WITH_EDUCATION (동일)** | **ADEQUATE_WITH_EDUCATION (동일)** |
| **κ_linear** | **0.71** | **0.0** |
| Tie-breaker | ❌ 불필요 | ✅ 호출 |
| Clinician review priority | low | moderate |

→ **동일 verdict이지만 5배 이상 차이나는 시스템 신뢰도**. 이 paired case가 IRB pilot에서 prospective 검증할 §5.3 hypothesis ("κ-as-video-quality-proxy")의 출발점입니다.

---

**문서 control**:
- v1.0 (2026-05-21): 초안 IRB 제출용
- **v2.0 (2026-05-21)**: n=2 internal validation 통합, L1-L5 해결 반영, SAP 정교화, 규제 컴플라이언스 확장
- v2.1 (예정): IRB 위원회 피드백 반영
- v3.0 (예정): Enrollment 종료 후 — 실제 데이터 기반 SAP 사후 보완

Generated as part of the CAMCA v0.4.0 (plugin) / v0.3.0 (Python package) release.
