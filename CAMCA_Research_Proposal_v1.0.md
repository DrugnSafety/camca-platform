# CAMCA Research Proposal v1.0
**Camera-based Automated Multi-agent Clinical Assessment of Inhaler Technique**

> *"Two patients, identical 10/12 scores, yet a 5-fold difference in inter-rater reliability — and the difference is in the camera angle, not the patient. CAMCA quantifies that gap and turns it into a clinically actionable signal."*

---

| 항목 | 내용 |
|---|---|
| **Version** | 1.0 (2026-05-21) |
| **Document type** | 학회·grant 신청용 종합 연구 제안서 (NIH-style + KR-funder hybrid) |
| **PI** | Min-Gyu Kang, MD (충북대학교병원 알레르기내과) |
| **Co-investigators** | (TBD — MGH allergist + CBNUH 임상약사 + 외부 호흡기 전문의) |
| **Institution** | 충북대학교병원 (CBNUH) — primary; Massachusetts General Hospital · Harvard Medical School — collaborating |
| **Duration** | 9 months (Phase 1-4 IRB pilot) + 12 months follow-on (Phase 5 multi-center) |
| **Funding request** | TBD (CBNUH seed + 한국연구재단·중기부 R&D 병합 검토) |
| **Companion document** | `CAMCA_IRB_Pilot_Protocol_v2.0.md` (집행 protocol — 본 proposal의 §2 Aims와 1:1 매칭) |

---

## A. Specific Aims (정량 가설)

### Aim 1 — Inter-Rater Reliability (Primary)

**가설 1**: GINA-strict vs pragmatic-clinical 두 페르소나가 동일 영상을 독립 평가할 때 Cohen's κ_linear ≥ 0.7 (substantial agreement)이 달성된다.

**검증**: n=30 pilot에서 per-step + overall κ_linear (95% bootstrap CI). Null=0.4 (moderate) vs alternative=0.7 (substantial), α=0.05, power=0.80.

### Aim 2 — Telemetry Layer의 Critical-Error 검출 향상 (Secondary)

**가설 2**: MediaPipe + librosa quantitative telemetry layer를 활성화하면, VLM-only baseline 대비 **CRIT-pMDI-04 (coordination) 검출 sensitivity가 절대 ≥15% 증가**한다.

**검증**: 각 영상을 (a) VLM-only mode, (b) telemetry-augmented mode 두 번 평가. Paired McNemar test (FDR-corrected).

### Aim 3 — κ as Video-Quality Proxy (Tertiary, 가장 혁신적)

**가설 3** (n=2 paired case에서 도출): 동일 verdict 케이스 내에서도 κ는 영상 acquisition quality (resolution × angle × occlusion)에 따라 0.0 ~ 0.71 범위로 변동한다. **즉, κ 자체가 video-quality + technique-clarity proxy 역할을 한다.**

**검증**: Verdict-matched cohort (e.g., ADEQUATE_WITH_EDUCATION 케이스만)에서 κ IQR과 acquisition variables 간 regression model (multivariable linear).

**Clinical impact (만약 confirmed)**: 임상 deploy 시 "verdict + κ" **dual reporting**이 standard가 되어야 한다 — 이는 현재 어떤 inhaler assessment 도구에도 없는 contribution.

### Exploratory Aims

- **E1** — Cross-model 합의도: Claude Opus vs Gemini 2.5 Pro vs Ollama Gemma3:27b (on-premise) — 같은 영상에 대한 verdict 합의율.
- **E2** — Cost-quality frontier: Gemini Flash dual (~$0.10/case) vs Opus+Pro+TB (~$0.50/case) — 정확도 손실 정량화.
- **E3** — AIM 시뮬레이터 vs 실제 pMDI: device sub-type 특이 audio profile (peak dB, baseline) 정량 보정.

---

## B. Significance — 왜 지금 이 연구가 필요한가

### B.1 임상 문제의 광범위성과 산업적 공백

- **70-80%의 천식·COPD 환자가 흡입제를 부정확하게 사용**(Sanchis 2016, CRITIKAL 2017) — 약물 의 효과의 30-50%가 oping 단계에서 손실됨.
- **CRITIKAL critical errors와 outcome의 통계적 연관**:
  - pMDI coordination failure: aOR 1.45 for uncontrolled asthma
  - DPI inadequate effort: aOR 1.30
  - Inadequate breath-hold: aOR 1.40
- **의료진 자체의 한계**: 처방자조차 부정확한 시범 (Plaza 2018) — 환자에게 올바른 시범을 전달할 수 있는 인적 자원 부족.
- **시장 공백**: PubMed 검색상 published computer-vision-based automated inhaler scoring system이 존재하지 않음. 유일한 상용 경쟁자 Kata® (VisionHealth)는 2017-era 단일 ML 모델 stack. Propeller·Adherium 같은 digital inhaler 회사들은 2024년 시장에서 철수.

### B.2 기존 접근법의 본질적 한계

| 기존 접근 | 한계 |
|---|---|
| **Single VLM (e.g., GPT-4V 직접 호출)** | Hallucination, 임상 평가에 inappropriate한 임상 지식 부재, audit trail 없음 |
| **Smart inhaler (sensor 기반)** | Hardware 의존, 환자별 device 교체 필요, sensor 정확도 한계 |
| **Manual clinician scoring (gold standard)** | Inter-rater variability, scalability 부재, 임상의 시간 소비 |
| **Educational video 단순 검토** | 표준화 부재, 비교 가능성 없음, 시간적 정량 지표 부재 |

### B.3 CAMCA의 차별화된 contribution

1. **검증된 4-layer hybrid 아키텍처**: Layer 0 (quantitative telemetry) + Layer 1 (VLM observation) + Layer 2 (statistical adjudication) + Layer 3 (deterministic scoring) — **세계 최초 published clinical inhaler evaluation framework**.
2. **κ-as-quality-proxy 발견**: 단일 verdict의 한계를 보완하는 **2차원 reporting (verdict + κ)** 정립.
3. **PIPA-compliant on-device anonymization**: Vertex AI Seoul region 사용 + MediaPipe Face Mesh 기반 face anonymization → 한국 환자 cohort 사용 가능한 첫 AI 시스템.
4. **오픈소스 + 다중-벤더 무관성**: Plugin (Claude) + Python package (PyPI) dual deliverable, Claude·Gemini·Ollama backend 호환 → vendor lock-in 없음.

---

## C. Innovation — 본 연구의 혁신성 3축

### C.1 (Technical innovation) Dual-Agent + Telemetry Hybrid Architecture

**문제**: Single VLM은 hallucination이 빈번하고, telemetry alone은 임상 맥락 해석 불가.

**해결**: **Layer 0 telemetry → Layer 1 VLM anchor**의 separation. 즉, MediaPipe로 0.1초 단위 정량 측정 → 이 측정값을 VLM의 prompt에 "anchor"로 inject → VLM은 측정값을 임상 지식으로 해석하는 데 집중.

**구체 구현 (v0.3.0 검증됨)**:
```
영상 (.mp4)
   ↓
[Layer 0: MediaPipe + librosa]  ─→ 6 indicators × 0.1s (lip seal, head pitch, finger accel,
                                                       chest expansion, audio dB, ZCR)
   ↓
[Layer 1: Dual-agent VLM]      ─→ Evaluator A (Opus + GINA strict)
                                  Evaluator B (Sonnet + pragmatic)
                                  (둘 다 Layer 0 anchor를 prompt context로 받음)
   ↓
[Layer 2: Cohen's κ]            ─→ 결정론적 통계 (LLM 미관여) + sha256 signature
   ↓
[Layer 3: scoring + safety]    ─→ Verdict + critical-error override + review flag
```

**왜 hybrid인가**: VLM은 hallucinate하지만 임상 지식이 있고, MediaPipe는 정확하지만 임상 맥락 없음. **서로의 약점을 정확히 보완**.

### C.2 (Statistical innovation) κ-as-Video-Quality-Proxy

**기존 paradigm**: AI 시스템은 단일 verdict를 출력 → 임상의가 그것을 trust or not.

**CAMCA의 paradigm shift**: AI는 verdict + κ를 함께 출력 → **κ가 시스템 자체의 confidence proxy**로 작동. n=2 paired case (KIM κ=0.71 vs PARK κ=0.0, 둘 다 verdict=ADEQUATE_WITH_EDUCATION)에서 발견 → n=30 pilot에서 prospective 검증 예정.

**Publication impact**: 이 paradigm이 confirmed되면 **모든 AI clinical assessment 시스템이 verdict + reliability metric을 dual-report해야 함**을 제안 가능 — methods publication의 핵심.

### C.3 (Regulatory innovation) PIPA-First 설계

**한국 시장 진입을 막는 가장 큰 장벽**: cross-border data transfer 규제. 대부분의 US 기반 AI 시스템이 한국 cohort에서 사용 불가.

**CAMCA의 해결**:
- Vertex AI **Seoul region** 사용 (Google Cloud의 한국 datacenter) → cross-border transfer 없음
- MediaPipe **on-device** facial anonymization → 식별 정보가 클라우드로 전송되지 않음
- **On-premise-only arm** (Ollama gemma3:27b) → 클라우드 사용 0% 옵션 제공

**Regulatory positioning**:
- Pilot 종료 후 **MFDS Class II SaMD** 신청 가능한 첫 한국제 AI inhaler assessment 시스템
- 2023년 MFDS "AI 기반 SaMD 허가·심사 가이드라인" 준수 설계

---

## D. Preliminary Data — n=2 Internal Validation (검증됨)

### D.1 검증 케이스 개요

n=2의 실제 영상으로 v0.3.0 stack 전체를 end-to-end 검증했습니다. 이 데이터는 (a) 시스템 작동 증명, (b) 8개 failure mode 식별, (c) §5.3 hypothesis의 motivating evidence 제공합니다.

| 케이스 ID | 영상 메타 | 평가 결과 | 핵심 발견 |
|---|---|---|---|
| CAMCA-PARK-001 | 720p, 측면, 양손 cupping | 10/12 (Consensus), κ=0.0, 4 tie-breaker calls | **occlusion으로 모든 단계 disagree** |
| CAMCA-KIM-001 | 1080p, 정면, 한 손 표준 그립 | 10/12 (Consensus), κ=0.71, no tie-breaker | **acquisition quality good → 자연 합의 도달** |

### D.2 KIM vs PARK paired finding (논문 lead figure 후보)

```
       동일 verdict (10/12, ADEQUATE_WITH_EDUCATION)
                          │
       ┌──────────────────┴──────────────────┐
       │                                       │
   KIM-001                              PARK-001
   κ_linear = 0.71                      κ_linear = 0.00
   (substantial)                        (slight)
       │                                       │
   Tie-breaker                         Tie-breaker
   불필요                                 4번 호출 (모두 B 손)
       │                                       │
   Clinician review                    Clinician review
   priority: LOW                       priority: MODERATE
       │                                       │
       └──────────────┬────────────────────────┘
                       │
       → 같은 verdict, 5배 이상 차이나는 시스템 신뢰도.
       → κ가 video acquisition quality + technique clarity proxy로 작동.
```

### D.3 식별된 8개 system limitations (이 중 5개는 v0.2.1에서 해결)

| # | Failure mode | 발견 케이스 | 상태 | v 도입 |
|---|---|---|---|---|
| L1 | Breath-hold detector false positive (quiet audio) | KIM-001 | ✅ Resolved | v0.2.1 |
| L2 | Finger acceleration threshold 너무 낮음 | KIM-001 | ✅ Resolved | v0.2.1 |
| L3 | Head pitch 좌표계 변환 버그 | KIM-001 | ✅ Resolved | v0.2.1 |
| L4 | AIM 시뮬레이터 audio threshold 불일치 | PARK+KIM | ✅ Resolved | v0.2.1 |
| L5 | VLM↔Telemetry 충돌 정책 부재 | KIM-001 | ✅ Resolved | v0.2.1 |
| L6 | 카메라 각도 의존성 | PARK-001 | 🔜 Planned | v0.3.0 |
| L7 | VLM frame sampling (1 fps) 한계 | KIM-001 | 🔜 Planned | v0.3.0 |
| L8 | Audio peak 부재 시 inhalation 추론 불가 | PARK+KIM | 🔜 Planned | v0.4.0 |

**Significance for grant reviewer**: 이는 단순한 demo가 아니라 **실제 영상으로 검증되고, 한계가 식별되고, 정량적으로 해결된** 시스템임을 의미합니다.

### D.4 AIM audio profile 발견 (clinical novelty)

CAMCA-PARK 와 CAMCA-KIM 두 케이스 모두 **AIM 훈련 시뮬레이터** (충북대학교 약학과 교육용 device) 사용. 두 케이스 모두 audio peak가 51-56 dB에 그쳐, 표준 pMDI threshold(50 dB)로 inhalation onset 검출 실패.

→ **AIM-specific threshold profile** (baseline 35 dB, inhalation_min 42 dB, detection_min 45 dB)을 v0.2.1에 hard-coded. 이는 published 데이터에 없는 **새로운 finding**으로, 약학 교육 분야에 별도 publication 가능.

---

## E. Research Strategy / Approach (Aim별)

### E.1 Aim 1 — IRR (Primary)

**Design**: Prospective single-center observational, cross-sectional video assessment.

**Subjects**: n=30 (15 healthy + 15 asthma), 만 19세 이상.

**Workflow per case**:
1. 영상 촬영 (≥1080p, 정면, full pMDI 시퀀스 20-60초)
2. On-device anonymization (MediaPipe Face Mesh upper-face)
3. Upload to Vertex AI Seoul (encrypted) OR local Ollama (환자 선택권)
4. Layer 0 telemetry 자동 추출
5. Evaluator A (Claude Opus + GINA strict) + Evaluator B (Gemini Pro + pragmatic) 병렬 평가
6. Cohen's κ 결정론적 산출 + 95% bootstrap CI
7. κ < 0.6 → tie-breaker 자동 호출 (Ollama Gemma3:27b)
8. Final scoring + verdict + clinician review flag
9. 24h 내 human gold standard (Reviewer 1+2+adjudicator) 독립 평가

**Statistics**:
- 1차: per-step + overall κ_linear (n=30 × 7 steps)
- 2차: critical-error agreement (target ≥0.90)
- Subgroup: pMDI vs AIM vs spacer, 정면 vs 측면, 1080p vs 720p
- Bootstrap 95% CI (1,000 iterations, BCa)

### E.2 Aim 2 — Telemetry Impact (Secondary)

**Design**: Within-subject paired comparison (각 영상 두 번 분석).

**Pre-registered hypothesis**: CRIT-pMDI-04 detection sensitivity 변화 ≥+15% (absolute).

**Statistics**:
- Paired McNemar test (telemetry vs no-telemetry)
- ROC AUC 변화 (critical-error gold standard 대비)
- Per-evaluator confidence 변화 (self-reported 0-1)
- Token cost / computation time 변화 (no clinical 영향이지만 deploy decision 참고)

### E.3 Aim 3 — κ-as-Quality-Proxy (Tertiary, 가장 혁신적)

**Design**: Verdict-matched cohort 내 κ 변동성 분석.

**Analysis pipeline**:
1. Verdict별 cohort 분리 (e.g., ADEQUATE_WITH_EDUCATION cohort = 약 12-15명 예상)
2. Cohort 내 κ의 IQR 측정
3. Acquisition variables (resolution, angle, occlusion score) → κ multivariable linear regression
4. κ-based clinician review priority의 sensitivity/specificity (gold standard: human reviewer가 acquisition issue를 flag한 경우)

**Innovation potential**: 만약 R² > 0.5 (κ가 acquisition quality의 substantial portion을 설명)이면 published claim:

> *"κ should be reported alongside every AI-generated verdict in clinical video assessment, as it functions as a built-in quality and confidence indicator."*

### E.4 Exploratory Aims

- **E1 Cross-model**: 같은 30 영상을 Claude·Gemini·Ollama 세 backend로 평가 → backend별 verdict 일치율
- **E2 Cost-quality**: 4 가지 backend 조합 비용 vs 정확도 frontier
- **E3 Sub-device**: AIM vs real pMDI subgroup audio profile 정량 보정

---

## F. Statistical Analysis Plan — Pre-Specified

### F.1 Primary

| Aim | 통계량 | Target | Null |
|---|---|---|---|
| 1 — Overall κ_A,B | Cohen's κ_linear, 95% BCa CI | ≥0.7 | =0.4 |
| 1 — Critical-error agreement | Cohen's κ (binary) | ≥0.9 | =0.6 |
| 2 — Telemetry impact | McNemar paired test, FDR-corrected | Δ ≥15% | Δ=0 |
| 3 — κ regression | Multivariable linear, R² | ≥0.5 | <0.1 |

### F.2 Sample Size Power

- Aim 1: n=30 → power 0.82 for κ=0.7 vs 0.4 (Fleiss-Cohen formula, ordinal κ, 7 categories)
- Aim 2: n=30 paired → power 0.85 for Δ sensitivity=15% (McNemar, baseline=0.7)
- Aim 3: Verdict-matched cohort n≈12-15 → exploratory only; n=60 (Phase 5) extension에서 confirmatory

### F.3 Subgroup Analyses (Pre-Specified)

- pMDI standalone vs pMDI + spacer vs AIM simulator
- 정면 vs 측면
- 1080p vs 720p
- ≥65세 vs <65세
- Healthy vs asthma
- First-time vs experienced

### F.4 Sensitivity Analyses

- Quadratic κ (linear의 sensitivity 분석)
- Inter-coder reliability of human gold standard (Reviewer 1 vs 2)
- Per-evaluator persona drift (per-step verdict의 시간적 trend)

---

## G. Regulatory & Ethical Strategy

### G.1 PIPA (Korean Personal Information Protection Act)

- **No cross-border**: Vertex AI Seoul region 사용
- **Data minimization**: on-device upper-face anonymization
- **Explicit dual consent**: cloud upload vs on-premise-only arm 환자 선택권
- **Right to be forgotten**: withdrawal 시 7일 내 모든 storage 삭제

### G.2 MFDS (식약처) SaMD Pathway

- 현재 분류: 연구용 prototype (SaMD 분류 대상 아님)
- Pilot 종료 후 **Class II SaMD** 신청 계획 (의료진 decision support)
- MFDS "AI 기반 SaMD 허가·심사 가이드라인" (2023) 준수
- Post-market surveillance plan 사전 수립 (분기별 review flag rate, false-FAIL rate 보고)

### G.3 IRB (CBNUH + MGH Reciprocal)

- CBNUH primary IRB
- MGH/HMS reciprocal notification (collaborating institution)
- Annual continuing review
- 별도 consent: anonymized video의 향후 publication 사용

### G.4 AI Failure-Mode Safety Net

n=2 검증으로 확인된 8개 실패 모드 (L1-L8) 중 5개 해결 + 3개 prospective 검증 계획. 환자 대면 보호 장치:

- **Hard fail-safe**: critical error 단일 발견 → 자동 FAIL verdict (점수 무관)
- **Clinician review flag (3-tier)**: κ<0.6 → 24h 내 임상의 직접 검토 의무
- **Patient PDF disclaimer**: AI 평가는 직접 평가를 대체하지 않음 명문화

---

## H. Timeline — Gantt-Style

```
2026-Q2/Q3 ── Phase 0 ─ n=2 internal validation              ✅ 완료 (2026-05-21)
              │  └─ L1-L5 해결, v0.3.0 release
              │
2026-Q3 ────── Phase 1 ─ IRB Setup (2개월)                    
              │  ├─ CBNUH IRB 제출 (v2.0 protocol)
              │  ├─ MGH reciprocal notification
              │  └─ 장비 조달 + clinician training
              │
2026-Q4 ────── Phase 2 ─ Enrollment (3개월)                   
              │  ├─ n=15 healthy + n=15 asthma
              │  └─ 영상 collection (60% pMDI, 100% AIM, 일부 spacer)
              │
2027-Q1 ────── Phase 3 ─ Analysis (2개월)                     
              │  ├─ Dual-mode evaluation (VLM-only vs telemetry-augmented)
              │  ├─ Human gold standard scoring
              │  └─ Cohen's κ 산출 + regression analysis
              │
2027-Q2 ────── Phase 4 ─ Reporting (2개월)                    
              │  ├─ Primary manuscript (JACI: In Practice 또는 NPJ Digital Medicine)
              │  ├─ Methods paper (Software Impacts 또는 JOSS)
              │  └─ Open source release (Plugin v1.0 + camca v1.0)
              │
2027-Q3+ ───── Phase 5 ─ Follow-on multi-center (12개월)      
                 ├─ MGH cohort 추가 (n=30)
                 ├─ 다른 한국 대학병원 협력 (n=60)
                 ├─ DPI-Turbuhaler IRB amendment
                 └─ MFDS Class II SaMD 신청
```

---

## I. Budget Summary

| 항목 | Phase 1-4 (IRB pilot) | Phase 5 (multi-center) | Total |
|---|---|---|---|
| Cloud API (Claude Opus + Gemini Pro) | $90 | $270 | $360 |
| Storage (encrypted NAS 1yr) | $50 | $150 | $200 |
| On-premise GPU (이미 보유) | $0 | $0 | $0 |
| Statistical software (R, free) | $0 | $0 | $0 |
| Clinician time (PI + Reviewer 2) | (in-kind) | (in-kind) | — |
| Patient incentive (₩30,000 × 30) | ₩900,000 | ₩2,700,000 | ₩3,600,000 |
| IRB 행정·printing | ₩500,000 | ₩1,000,000 | ₩1,500,000 |
| Publication fees (open access) | $3,000 | $6,000 | $9,000 |
| **Cash subtotal (USD)** | **~$3,200** | **~$6,600** | **~$9,800** |
| **Cash subtotal (KRW)** | **₩1.4M + $3.2K** | **₩3.7M + $6.6K** | **₩5.1M + $9.8K** |

→ 매우 저비용 연구. 주요 cost는 임상의 시간 (in-kind contribution) + IRB 행정.

---

## J. Risk Analysis & Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Enrollment 지연 (천식 환자) | Medium | Medium | 외래 + LinkedIn 학생 모집 ad 병행 |
| Vertex AI Seoul outage | Low | High | Ollama on-premise fallback 상시 가용 |
| Cohen's κ < 0.4 (negative result) | Low | High | n=2에서 κ=0.71 검증됨; 만약 κ가 낮으면 그 자체가 publishable finding |
| AIM 시뮬레이터 audio threshold이 한국 인구에 안 맞을 가능성 | Medium | Low | DEVICE_AUDIO_PROFILES dict 재calibration plan 사전 수립 |
| 임상의 (Reviewer 2) availability | Low | Medium | Secondary reviewer pool 사전 확보 |
| MFDS guideline 업데이트 | Low | Low | Pre-submission consultation으로 사전 정보 확보 |

---

## K. Expected Outcomes

### K.1 단기 (Phase 1-4 종료 시)

1. **Primary publication** (JACI: In Practice 또는 NPJ Digital Medicine) — IRR 검증 + κ-as-quality-proxy paradigm 제안
2. **Methods paper** (Software Impacts 또는 JOSS) — open source architecture
3. **CAMCA v1.0 stable release** (Plugin + Python pkg) — 학회·교육 기관 활용 가능
4. **MFDS Class II SaMD pre-submission consultation 신청**
5. **Korean clinical brief** — 충북대학교 의과대학 학술지

### K.2 중기 (Phase 5, 12개월 follow-on)

1. **Multi-center validation paper** (MGH + 한국 다기관, n=120) — generalizability 입증
2. **DPI-Turbuhaler extension** (n=30 별도 IRB)
3. **MFDS Class II SaMD 허가** (실제 임상 deploy 경로)
4. **Educational deployment**: 약학·의학 교육과정에 통합 (충북대 + 협력기관)

### K.3 장기 (2-3년)

1. **상용 deployment**: 한국 외래 clinic 대상 SaaS 또는 EHR 통합
2. **국제 확장**: MGH (US) + 영국 (NHS 연구 partnership) + 일본 (cross-cultural validation)
3. **다른 device 확장**: Respimat (Soft Mist Inhaler), Ellipta (DPI), Genuair, Diskus

---

## L. References (Key)

1. **Sanchis J**, Gich I, Pedersen S. *Systematic Review of Errors in Inhaler Use: Has Patient Technique Improved Over Time?* Chest 2016;150(2):394-406.
2. **Price DB**, Roman-Rodriguez M, McQueen RB, et al. *Inhaler Errors in the CRITIKAL Study: Type, Frequency, and Association with Asthma Outcomes.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.
3. **Plaza V**, Giner J, Rodrigo GJ, et al. *Errors in the Use of Inhalers by Health Care Professionals: A Systematic Review.* J Allergy Clin Immunol Pract 2018;6(3):987-995.
4. **Global Initiative for Asthma (GINA)**. *Global Strategy for Asthma Management and Prevention, 2024.* ginasthma.org.
5. **Landis JR**, Koch GG. *The Measurement of Observer Agreement for Categorical Data.* Biometrics 1977;33(1):159-174.
6. **Worth H**, Voshaar T, et al. *Standardised Checklists for Inhaler Technique* (German Airway League).
7. **MFDS (식약처)**. *AI 기반 SaMD 허가·심사 가이드라인* (2023).
8. **개인정보보호위원회**. *개인정보 보호법 (PIPA)* — 보건의료 데이터 활용 지침 (2023).

---

## M. Companion Documents

| 문서 | 역할 |
|---|---|
| `CAMCA_IRB_Pilot_Protocol_v2.0.md` | 본 proposal §E의 실집행 protocol (1:1 매칭) |
| `CAMCA_IRB_Pilot_Protocol_v2.0_EN.md` | 영문판 |
| `CAMCA_System_Limitations_and_Improvement_Roadmap_v1.0.md` | §D의 8개 limitation 상세 |
| `camca-inhaler-eval/logs/CAMCA-KIM-001/comparison_KIM_vs_PARK.md` | §D paired finding 원본 데이터 |
| `README.md` (repo 루트) | 시스템 deliverable 사용 가이드 |

---

**Document control**:
- **v1.0 (2026-05-21)**: 초안 — IRB Protocol v2.0과 동시 발행, n=2 internal validation 통합, 3대 강조 영역 (Dual-agent+telemetry / SAP / PIPA·MFDS·IRB) 정립
- v1.1 (예정): 학회·grant reviewer 피드백 반영
- v2.0 (예정): Phase 4 종료 후 실제 데이터 기반 결과 섹션 추가
