# camca (v0.2.0)

**CAMCA — Camera-based Automated Multi-agent Clinical Assessment of Inhaler Technique**

A standalone Python package for video-based inhaler technique evaluation using
multi-model VLM (Claude / Gemini / local Ollama) dual-agent comparison with
**MediaPipe + librosa quantitative telemetry layer**, Cohen's kappa inter-rater
reliability scoring, Pydantic schema enforcement, and bilingual KO+EN PDF reports.

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🆕 v0.2.0 — Hybrid Quantitative + VLM Architecture

v0.2.0는 Google Gemini CDSS 접근법을 반영한 **4-layer 하이브리드** 구조로 진화했습니다.

| Layer | 이전 (v0.1.0) | 신규 (v0.2.0) |
|---|---|---|
| 0. 정량 측정 | — | **MediaPipe Vision + librosa Audio** → 0.1초 telemetry |
| 1. VLM 관찰 | Frame만 입력 | Frame **+ 정량 측정값** 동시 입력 |
| 2. Adjudication | Cohen's κ + tie-breaker | 동일 (보존) |
| 3. Scoring | Deterministic Python | 동일 (보존) |

### v0.2.0 주요 변경

- **`camca.telemetry` 모듈** — MediaPipe(입술·고개·검지·손목·흉부) + librosa(audio dB) 6개 지표를 0.1초 단위 추출
- **Audio-based breath-hold detector** — `audio_energy_db` 급감 패턴으로 S7 숨참기를 결정론적으로 감지 (chest expansion plateau 문제 해결)
- **Telemetry-augmented evaluator prompts** — VLM이 추정하던 timing·duration을 측정값에서 직접 인용
- **Pydantic schema enforcement** — Gemini `response_schema` + Claude `tool_use`로 VLM 출력 strict 강제
- **Gemini Native Video API** — `GeminiBackend(use_native_video=True)` → ffmpeg frame 추출 우회, sub-second timing 보존

> 🔗 **Claude Cowork/Code 사용자**라면 자매 배포 [**camca-inhaler-eval plugin**](../camca-inhaler-eval/) 을 참고하세요. 동일한 평가 엔진을 채팅 인터페이스의 slash command (`/evaluate-dual`)로 사용할 수 있습니다.

---

## 두 가지 배포 방식 비교

| 항목 | `camca` Python 패키지 (이 패키지) | `camca-inhaler-eval.plugin` |
|---|---|---|
| **실행 환경** | 외부 Python 환경 (서버·노트북·CI) | Claude Cowork / Claude Code |
| **사용 방법** | `from camca import ...` 또는 `camca` CLI | `/evaluate-dual video.mp4` slash command |
| **설치** | `pip install camca-0.1.0-py3-none-any.whl[all]` | `.plugin` 파일을 채팅에 drag & drop |
| **VLM 호출** | 사용자가 직접 API 키로 호출 | Claude Cowork agent가 자동 호출 |
| **평가 엔진** | 동일 (skill·rubric·CRITIKAL·scoring) | 동일 |
| **출력 호환성** | 같은 JSON schema | 같은 JSON schema |
| **사용 시나리오** | 연구·배치·on-premise 배포 | 임상의 대화형 평가 |

---

## 어떤 파일을 선택해야 하나요? — 3종 distribution

워크스페이스 루트에 3개의 `camca` Python 배포 파일이 있습니다:

| 파일 | 형식 | 용도 |
|---|---|---|
| **`camca-0.1.0-py3-none-any.whl`** | PEP 427 wheel | **일반 사용자** — 가장 빠른 설치 |
| **`camca-0.1.0.tar.gz`** | PEP 517/518 sdist | PyPI 업로드용 백업, 빌드 재현성 |
| **`camca-py-0.1.0-source.tar.gz`** | 개발자용 압축본 | 코드 수정·examples 포함 (editable 설치) |

### 세 파일의 차이

- **Wheel (`.whl`)**: 미리 빌드된 binary 배포. `pip`이 그대로 설치 → 가장 빠르고 안전. 코드 수정 불가.
- **Sdist (`.tar.gz`)**: PyPI 표준 source distribution. 사용자 측에서 wheel을 다시 빌드 후 설치. PyPI 표준이라 GitHub Release/사내 PyPI 미러에 함께 올리기 적합.
- **Source archive (`-source.tar.gz`)**: PyPI 표준이 **아닌** 개발자 친화적 압축본. `examples/` 폴더와 README 포함, `pip install -e .` (editable) 가능. GitHub clone과 같은 경험.

---

## What It Does

1. Identifies the inhaler type from a video (pMDI / Turbuhaler / spacer)
2. Segments the video into canonical evaluation steps
3. Runs **two independent VLM evaluators** with different personas (strict vs pragmatic)
4. Computes **Cohen's kappa** inter-rater reliability deterministically
5. Optionally invokes a **third evaluator** as tie-breaker when agreement is low
6. Produces a **deterministic final verdict** (PROFICIENT / ADEQUATE / NEEDS TRAINING / FAIL)
7. Generates **bilingual Korean + English PDF reports** (patient guide + clinician summary)

## Installation

```bash
# Option 1: Install from local wheel (fastest, recommended)
pip install camca-0.1.0-py3-none-any.whl[all]

# Option 2: Install from sdist (slower; builds wheel locally)
pip install camca-0.1.0.tar.gz[all]

# Option 3: Editable install from extracted source (for development)
tar -xzf camca-py-0.1.0-source.tar.gz
cd camca-py-0.1.0
pip install -e ".[all]"
```

### Optional extras

```bash
pip install camca                     # 핵심만 (Ollama 사용 가능)
pip install "camca[claude]"           # + Anthropic SDK
pip install "camca[gemini]"           # + Google GenAI SDK
pip install "camca[telemetry]"        # + MediaPipe + librosa (정량 telemetry)
pip install "camca[all]"              # 모든 cloud 백엔드 + telemetry
```

**중요**: `[telemetry]` 옵션이 없으면 v0.2.0의 핵심 가치인 정량 측정 layer가 비활성화됩니다. VLM-only 평가로 자동 fallback 됩니다 (v0.1.0과 동일 동작).

External dependencies (가상환경 외부):
- **ffmpeg** must be in PATH (영상 frame 추출용)
- **Ollama** (optional, 로컬 모델 서빙용)

## Quick Start

### Python API — v0.2.0 (telemetry + schema 강제 활성화)

```python
from camca import (
    create_backend, PersonaConfig, MultiModelPipeline,
)

pipeline = MultiModelPipeline(
    device_id_backend=create_backend("claude:sonnet"),
    segmenter_backend=create_backend("gemini:flash"),
    evaluator_a=PersonaConfig(
        "evaluator-a", "GINA-strict",
        create_backend("claude:opus"),
    ),
    evaluator_b=PersonaConfig(
        "evaluator-b", "real-world-pragmatic",
        create_backend("gemini:pro"),
    ),
    tie_breaker=PersonaConfig(
        "tie-breaker", "clinical-pharmacy-educator",
        create_backend("ollama:gemma3:27b"),
    ),
    case_dir="./logs/CASE-001",
    enable_telemetry=True,        # v0.2.0 신규: MediaPipe+librosa 측정 layer
    use_pydantic_schema=True,     # v0.2.0 신규: VLM 출력 schema 강제
)

result = pipeline.run_from_video(
    "patient_inhaler.mp4",
    case_id="CASE-001",
    fps=1.0,
)

print(f"Verdict: {result.final_score['final_verdict']}")
print(f"Kappa: {result.kappa_stats['kappa']['linear_weighted']}")
```

### Telemetry layer 단독 사용

```python
from camca.telemetry import extract_telemetry, detect_breath_hold, compute_telemetry_summary

# 0.1초 단위 6개 지표 추출
stream = extract_telemetry("patient.mp4")

# Audio dB 급감 패턴으로 숨참기 자동 감지
bh = detect_breath_hold(stream)
print(f"Breath-hold: {bh.duration_ms}ms (adequate per GINA: {bh.is_adequate})")

# VLM prompt 주입용 임상 요약
summary = compute_telemetry_summary(stream)
print(summary["clinical_anchors"]["S5_coordination_check"])
# → {"actuation_ms": 250, "inhalation_onset_ms": 280, "gap_ms": 30,
#    "interpretation": "OPTIMAL — actuation and inhalation within 300ms"}
```

### Gemini Native Video (P5)

```python
from camca import create_backend

# Frame 추출 우회 — 영상 직접 업로드
gemini_native = create_backend("gemini:pro")
gemini_native.use_native_video = True

result = gemini_native.analyze_video(
    prompt="Evaluate this inhaler technique...",
    video_path="patient.mp4",
    response_schema=VLMClinicalReport,  # Pydantic 강제
)
```

### CLI

```bash
# Full analysis with PDF reports
camca analyze \
    --video patient.mp4 \
    --case-id CASE-001 \
    --evaluator-a claude:opus \
    --evaluator-b gemini:pro \
    --tie-breaker ollama:gemma3:27b

# Show bundled resources + backend availability
camca info

# Show version
camca version
```

### Phase Recognition Engine (v0.4.0)

telemetry-anchored 하이브리드 세그멘테이션 (spec: docs/superpowers/specs/2026-07-07-camca-platform-design.md §5):

```bash
# telemetry-only (무비용, CI용)
camca segment --video patient.mp4 --device pMDI --case-id X-001 --no-vlm --out seg.json

# 하이브리드 (VLM 경계 정밀화)
camca segment --video patient.mp4 --device pMDI --case-id X-001 --vlm claude:sonnet
```

`MultiModelPipeline(use_phase_engine=True)`로 전체 파이프라인에서도 opt-in 사용 가능
(telemetry 추출이 활성화된 경우 기존 VLM-프롬프트 세그멘테이션을 대체).

**검증 게이트 (Step 1 데이터 12영상 확보 시 실행):**
- mean_absolute_boundary_error_sec < 0.5 (human 경계 라벨 대비)
- overlap_violations == 0 (구조 불변조건)
- KIM-001/PARK-001에서 기존 consensus score 재현

## Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."           # Claude
export GOOGLE_API_KEY="AIza..."                 # Gemini (or GEMINI_API_KEY)
export OLLAMA_HOST="http://localhost:11434"     # Ollama (optional)
```

## Backend Specifications

| Provider | Spec example | Notes |
|---|---|---|
| Claude | `claude:opus`, `claude:sonnet`, `claude:haiku` | Vision; cost varies by model |
| Gemini | `gemini:pro`, `gemini:flash`, `gemini:1.5-pro` | Vision + audio; 1M context |
| Ollama | `ollama:gemma3:4b`, `ollama:gemma3:12b`, `ollama:gemma3:27b`, `ollama:llava:13b`, `ollama:qwen2.5vl:32b` | Local; free; needs GPU |

## Cost & Latency Estimates

For a typical 13-second pMDI demonstration video (~13 frames):

| Configuration | Cost | Latency |
|---|---|---|
| All Claude Sonnet | ~$0.30 | ~60s |
| Claude Opus + Gemini Pro | ~$0.50 | ~80s |
| All Gemini Flash | ~$0.05 | ~30s |
| All Ollama (local) | $0 (GPU required) | ~120s |

## Telemetry Layer (v0.2.0) — 6개 핵심 지표

| 지표 | 추출 도구 | 임상 의미 | 어떤 평가에 사용 |
|---|---|---|---|
| `audio_energy_db` | librosa RMS | 흡입음 강도 + **숨참기 시작점** | S5, S6, S7 |
| `lip_distance_px` | MediaPipe FaceMesh | 입술 밀착 (mouth seal) | S4 |
| `head_pitch_deg` | MediaPipe FaceMesh | 기도 확보 각도 | S4, S5 |
| `index_finger_acceleration` | MediaPipe Hands | **Actuation 정확 시점** | S5 (CRIT-pMDI-04) |
| `wrist_zero_crossing_rate` | MediaPipe Hands | **진짜 흔들기 vs 이동** | S1 (CRIT-pMDI-01) |
| `chest_expansion_ratio` | MediaPipe Pose | 흡입 깊이 | S6 |

각 지표는 `camca.telemetry.thresholds`에 임상 기준값이 정의되어 있어, pilot 데이터로 calibration 가능합니다.

## Bundled Resources

The package includes:
- 8 clinical skill markdown files (pMDI/Turbuhaler checklists, CRITIKAL errors, GINA reference, etc.)
- 2 Korean fonts (NanumGothic Regular + Bold, SIL OFL licensed)
- 2 static patient education guides (pMDI in KO + EN)
- 1 comprehensive reference table (XLSX + Markdown)

Access programmatically:

```python
from camca.resources import skill_text, font_path, static_guide_path, available_skills

print(available_skills())
# ['adjudicator-comparison-template', 'critical-errors-critikal', ...]

pmdi_checklist = skill_text("inhaler-checklist-pmdi")
font = font_path("NanumGothic", "Bold")
guide = static_guide_path("pmdi", "ko")
```

## Output Structure

After running `pipeline.run_from_video(...)`, the case directory contains:

```
{case_dir}/
├── 00_pipeline_metadata.json     # Stage timing, models, timestamps
├── 02_device_id.json             # Device identification result
├── 03_segments.json              # Video segmentation
├── 04_evaluator_a.json           # Evaluator A output
├── 05_evaluator_b.json           # Evaluator B output
├── 06b_kappa_stats.json          # Cohen's kappa statistics
├── 06c_tie_breaker.json          # Tie-breaker (if invoked)
├── 07_final_score.json           # Deterministic final verdict
├── {case_id}_patient_ko.pdf      # Patient PDF (Korean, comprehensive)
├── {case_id}_patient_en.pdf      # Patient PDF (English)
├── {case_id}_clinician_ko.pdf    # Clinician PDF (Korean, 1 page)
├── {case_id}_clinician_en.pdf    # Clinician PDF (English)
└── frames/                       # Extracted video frames
```

These JSON outputs are **byte-identical schema** to those produced by the `camca-inhaler-eval` Claude plugin → 두 deliverable이 같은 데이터로 상호운용됩니다.

## Examples

See [examples/](examples/) directory:
- `basic_analysis.py` — Minimal Claude-only example
- `cross_vendor.py` — Claude + Gemini + Ollama tie-breaker (research-grade)
- `local_only.py` — All-Ollama for privacy-sensitive cases
- `use_scoring_only.py` — Use kappa+verdict layer with pre-existing JSON inputs

## Architecture (v0.2.0 — 4 layers)

```
Video (.mp4)
    │
    ├─→ [ffmpeg] → Frames (.jpg)
    │
    └─→ [MediaPipe + librosa]  ← NEW (Layer 0)
              ↓
       0.1초 telemetry stream (6 지표)
              ↓
       compute_telemetry_summary
              ↓
       {S5 coordination, S7 breath-hold, ...}
              ↓
                  ↓ (frames + telemetry 동시)
device-id backend ──→ Device type
    ↓
segmenter backend ──→ Per-step segments
    ↓
┌─────────────────────────────┐
│  Evaluator A   Evaluator B   │  (parallel; frames + telemetry 입력)
│  (Opus+GINA)   (Gemini+prag) │  + Pydantic schema enforcement (P4)
└─────────────┬───────────────┘
              ↓
       [kappa_calculator]     ← deterministic-python
              ↓
          κ<0.6?
              ↓
       [Tie-Breaker]           ← optional
              ↓
       [scoring_engine]        ← deterministic-python
              ↓
       Final verdict
              ↓
       [bilingual PDFs]        ← KO + EN, patient + clinician
```

## Citation

> Kang MG. *CAMCA: Camera-based Automated Multi-agent Clinical Assessment of
> Inhaler Technique.* v0.1.0, 2026. https://github.com/drugnsafety/camca

## References

- GINA 2024 — Global Initiative for Asthma Strategy
- Price DB et al. *CRITIKAL study.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.
- Sanchis J et al. *Systematic Review of Errors in Inhaler Use.* Chest 2016;150(2):394-406.
- Landis JR, Koch GG. *The measurement of observer agreement for categorical data.* Biometrics 1977;33:159-174.

## License

MIT (see [LICENSE](LICENSE)). Bundled NanumGothic font is licensed under SIL OFL 1.1.
