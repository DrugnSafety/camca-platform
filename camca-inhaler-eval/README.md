# camca-inhaler-eval

**CAMCA: Camera-based Automated Multi-agent Clinical Assessment of Inhaler Technique**

천식·만성폐쇄성폐질환 환자의 흡입제 사용 영상을 **이중 평가자 + Cohen's κ 검증** 방식으로 자동 평가하는 Claude 플러그인입니다.

> 🔗 **Python에서 외부 환경 사용**을 원하시면 자매 패키지 [**`camca`** (PyPI-style)](../camca-py/) 를 참고하세요. 동일한 평가 엔진을 standalone Python으로 제공합니다.

---

## 두 가지 배포 방식 한눈에 비교

| 항목 | `camca-inhaler-eval.plugin` (이 패키지) | `camca` Python 패키지 |
|---|---|---|
| **실행 환경** | Claude Cowork / Claude Code 데스크탑 앱 | 외부 Python 환경 (서버, Jupyter, CI) |
| **사용 방법** | `/evaluate-dual video.mp4` slash command | `from camca import ...` 또는 `camca` CLI |
| **설치** | `.plugin` 파일을 채팅에 drag & drop | `pip install camca-0.1.0-py3-none-any.whl[all]` |
| **VLM 호출 주체** | Claude Cowork 내 agents | 사용자가 직접 API 키로 호출 (Claude/Gemini/Ollama) |
| **평가 엔진** | 동일 (skill·rubric·CRITIKAL·scoring) | 동일 (skill·rubric·CRITIKAL·scoring) |
| **출력 호환성** | 같은 JSON schema | 같은 JSON schema |
| **권장 시나리오** | 임상의가 대화형으로 평가 진행 | 연구·배치 처리·on-premise 배포 |

---

## 핵심 설계 원칙

CAMCA는 임상 평가 시스템에서 흔히 발생하는 hallucination·bias 문제를 **separation of concerns + dual-agent independence**로 해결합니다.

- **Probabilistic observation** (VLM): 영상에서 행동을 관찰
- **Deterministic scoring** (Python rule engine): 관찰 결과를 점수로 변환 — LLM 미관여
- **Natural language explanation** (LLM): 환자용 피드백 생성
- **Independent dual evaluation**: 두 평가자가 독립적으로 평가 후 reconcile

## 3-Layer 아키텍처

### Layer 1: Orchestration
- `orchestrator-agent`: 전체 파이프라인 조정 (10단계)

### Layer 2: 평가 Agents (10개)
| Agent | 역할 | Model |
|---|---|---|
| `device-id` | 흡입제 종류 식별 | Sonnet |
| `video-segmenter` | 평가 단계별 영상 분할 | Sonnet |
| `evaluator-a` | **Primary reviewer** — GINA 2024 엄격 평가자 페르소나 | **Opus** |
| `evaluator-b` | **Independent reviewer** — 실용주의 임상 평가자 페르소나 | **Sonnet** |
| `critical-error-detector` | CRITIKAL 기반 효과 무효화 오류 감지 | Sonnet |
| `adjudicator` | A·B 결과 비교, Kappa 계산, consensus 도출 | Opus |
| `tie-breaker` | κ < 0.6 시 3차 평가자 (자동 호출) | Opus |
| `scoring-engine` | 결정론적 점수 변환 (Python invoke) | — |
| `report-generator` | 환자용 한국어/영어 PDF 보고서 | Sonnet |
| `orchestrator` | 전체 흐름 조정 | Sonnet |

### Layer 3: Skills (정적 지식)
- `inhaler-checklist-pmdi` — pMDI 7단계 체크리스트 + Levels 0-3 rubric
- `inhaler-checklist-turbuhaler` — Turbuhaler 체크리스트
- `critical-errors-critikal` — CRITIKAL study 기반 critical vs non-critical 분류
- `proficiency-rubric-levels` — Levels 0-3 정의 + 페르소나 tie-break 규칙
- `gina-2024-reference` — GINA 2024 흡입제 기술 챕터 요약
- `vlm-prompt-library` — Device-ID·Segmentation·Step Eval VLM 프롬프트
- `patient-feedback-templates-ko` — 한국어 환자용 피드백 문구
- `adjudicator-comparison-template` — A vs B 비교 보고서 schema

## 이중 평가 다이버시티 전략

**Model + Persona Dual Diversity** — 두 축의 독립성을 동시에 확보

| Axis | Evaluator A | Evaluator B |
|---|---|---|
| Model | Claude Opus | Claude Sonnet |
| Persona | GINA 2024 엄격 평가자 | 실용주의 임상 평가자 |
| Tolerance | 작은 결함도 감점 | 임상 효과 영향만 감점 |
| Reference | GINA 원문 + German Airway League | CRITIKAL critical-first |

**Why this matters**: 두 평가자가 모델·관점 두 축에서 독립적이므로 IRR 검증의 외적 타당도가 강합니다. 논문에 *"We employed model and perspective diversity in dual-agent evaluation, achieving κ = X.XX"* 형태로 보고 가능.

## Workflow

```
[영상 입력 .mp4]
    │
    ▼
device-id ──→ checklist skill 로드
    │
    ▼
video-segmenter ──→ 단계별 분할
    │
    ├──────────────┬──────────────┐
    ▼              ▼              ▼
evaluator-A   evaluator-B   (병렬 실행)
(Opus+GINA)   (Sonnet+practical)
    │              │
    └──────┬───────┘
           ▼
      adjudicator ──→ kappa_calculator.py
           │
       κ < 0.6?
           │
       ┌───┴───┐
       ▼       ▼
    tie-breaker  consensus
       │       │
       └───┬───┘
           ▼
    scoring-engine.py
           │
           ▼
    report-generator ──→ 한국어 + 영어 PDF (환자 + 임상의)
           │
           ▼
    JSON/CSV export (IRB·연구용)
```

## Commands

- `/evaluate-inhaler <video.mp4>` — 단일 평가 (Evaluator A만, IRR 검증 없음)
- `/evaluate-dual <video.mp4>` — **이중 평가 + Kappa + consensus** (메인 use case)
- `/compare-evaluations <eval_A.json> <eval_B.json>` — 기존 평가 결과 비교

## 번들 리소스

`assets/` 폴더에 다음이 포함되어 있습니다.

- **`fonts/`**: NanumGothic Regular + Bold (SIL OFL, 한국어 PDF 렌더링용)
- **`static/`**: 환자 교육용 PDF 가이드 (pMDI 한국어 4쪽 + 영어 5쪽 — 매 보고서에 자동 첨부)
- **`reference/`**: 종합 reference 테이블 (XLSX 6시트 + Markdown 버전)

## Scripts (deterministic + multi-model)

`scripts/` 폴더 구성:

| 파일 | 역할 |
|---|---|
| `kappa_calculator.py` | Cohen's kappa 계산 (LLM 미사용) |
| `scoring_engine.py` | 최종 점수 결정론적 산출 |
| `bilingual_pdf_generator.py` | 한국어 + 영어 PDF 보고서 생성 |
| `build_static_patient_guide.py` | 정적 환자 가이드 PDF 생성 (1회) |
| `build_reference_tables.py` | XLSX + MD reference 테이블 생성 |
| `research_log_exporter.py` | IRB·연구용 JSON + CSV export |
| `pipeline_metadata.py` | Stage별 모델·duration·timestamp 추적 |
| `multimodel/` | Claude·Gemini·Ollama 멀티 백엔드 러너 (Python 패키지의 핵심) |

## v0.3.0 상태

| 컴포넌트 | 상태 |
|---|---|
| Plugin manifest | ✅ v0.3.0 |
| 모든 Agent (10개) | ✅ 풀 구현 |
| 모든 Skill (8개) | ✅ 풀 구현 |
| 모든 Command (3개) | ✅ 풀 구현 |
| Scripts | ✅ deterministic 7개 + multimodel 4개 |
| 한국어 폰트 번들 | ✅ NanumGothic TTF |
| Static 환자 가이드 | ✅ KO + EN |
| Reference 테이블 | ✅ XLSX 6 시트 + Markdown |
| Multi-model 러너 | ✅ Claude + Gemini + Ollama |
| **Python 패키지 (자매)** | ✅ [`camca-py/`](../camca-py/) **v0.2.0** — telemetry + schema 강제 |

## 🆕 자매 Python 패키지 v0.2.0 — Gemini CDSS 통합

[`camca-py/`](../camca-py/) Python 패키지는 v0.2.0에서 **4-layer 하이브리드** 구조로 진화했습니다 (Gemini CDSS pipeline 통찰 반영).

| 추가 기능 (camca-py v0.2.0) | 임팩트 |
|---|---|
| **`camca.telemetry`** — MediaPipe + librosa 정량 측정 layer | VLM의 timing·duration 추정을 결정론적 측정으로 대체 |
| **Audio-based breath-hold detector** | S7 평가의 chest expansion plateau 문제 해결 (dB drop 직접 감지) |
| **Telemetry-augmented evaluator prompts** | "추정" → "측정값 해석"으로 VLM 역할 변경 |
| **Pydantic schema enforcement** | Gemini `response_schema` + Claude `tool_use`로 출력 strict 강제 |
| **Gemini Native Video API** | ffmpeg frame 추출 우회, sub-second timing 보존 |

플러그인 측에서도 향후 동일 telemetry layer를 통합할 예정 (v0.4.0 로드맵).

## References

- Global Initiative for Asthma. *GINA 2024 Global Strategy.*
- GOLD 2025 *Global Strategy for COPD.*
- Price DB et al. *CRITIKAL study.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.
- Sanchis J et al. *Systematic Review of Errors in Inhaler Use.* Chest 2016;150(2):394-406.
- Worth H et al. *German Airway League standardized inhaler technique checklist.*
- Landis JR, Koch GG. *The measurement of observer agreement for categorical data.* Biometrics 1977;33:159-174.

## 연구 컨텍스트

이 플러그인은 **Min-Gyu Kang, MD (충북대학교병원 알레르기내과, 하버드 MGH 방문연구원)** 의 CAMCA 연구 프레임워크 일부입니다. IRB 승인 후 n=30 pilot study (15 healthy + 15 asthma)에서 검증 예정.

자세한 사용 시나리오 비교는 워크스페이스 루트의 [README.md](../README.md)를 참고하세요.
