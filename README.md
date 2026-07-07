# CAMCA — Camera-based Automated Multi-agent Clinical Assessment of Inhaler Technique

흡입제 사용 영상을 **이중 평가자 + Cohen's κ 검증** 방식으로 자동 평가하는 종합 시스템입니다. 동일 평가 엔진을 **두 가지 형태**로 배포합니다.

> 🆕 **v0.2.0 (2026-05-21)** — Google Gemini CDSS 접근법을 반영한 **하이브리드 정량 + VLM 아키텍처**로 진화. MediaPipe + librosa telemetry layer 추가, audio-based breath-hold detector, Pydantic schema enforcement, Gemini Native Video API 지원. 자세한 내용은 [`camca-py/README.md`](camca-py/README.md) 참고.

---

## 📦 배포 산출물 — 한눈에 보기 (v0.2.0)

| # | 파일 | 크기 | 형식 | 누구를 위한 것인가 |
|---|---|---|---|---|
| 1 | [`camca-inhaler-eval.plugin`](camca-inhaler-eval.plugin) | 1.8 MB | Claude plugin (ZIP) | **Claude Cowork·Code 사용자** — slash command로 평가 |
| 2 | [`camca-0.2.0-py3-none-any.whl`](camca-0.2.0-py3-none-any.whl) | 1.7 MB | Python wheel | **외부 Python 환경** — 즉시 `pip install` |
| 3 | [`camca-0.2.0.tar.gz`](camca-0.2.0.tar.gz) | 1.7 MB | Python sdist | **PyPI 업로드용** 표준 source 배포 |
| 4 | [`camca-py-0.2.0-source.tar.gz`](camca-py-0.2.0-source.tar.gz) | 1.7 MB | 개발자용 압축 | **코드 수정·examples 포함** (editable 설치) |

### v0.1.0 → v0.2.0 핵심 변화

| Layer | v0.1.0 | v0.2.0 |
|---|---|---|
| **0. 정량 측정** | — | **MediaPipe + librosa** → 0.1초 telemetry (6 지표) |
| **1. VLM 관찰** | Frames만 입력 | Frames + telemetry 동시 입력 (VLM은 측정값 해석에 집중) |
| **2. Adjudication** | Cohen's κ | 동일 |
| **3. Scoring** | Deterministic Python | 동일 |
| **Output strict** | JSON instruction | **Pydantic schema 강제** (Gemini response_schema + Claude tool_use) |
| **Gemini Video** | Frame 추출 | **Native Video API** 옵션 추가 |

---

## 🎯 의사결정 흐름도

```
사용자가 누구인가?
│
├── Claude Cowork·Code 사용자
│   └─→ 1. camca-inhaler-eval.plugin (drag & drop 설치, slash command 사용)
│
└── Python 환경 (외부 서버, 노트북, 사내 인프라, CI)
    │
    ├── 그냥 쓰고 싶다 → 2. camca-0.1.0-py3-none-any.whl (wheel, 가장 빠른 설치)
    │
    ├── PyPI에 올릴 거다 → 3. camca-0.1.0.tar.gz (sdist 같이 업로드)
    │
    └── 코드를 보고·수정·예시까지 → 4. camca-py-0.1.0-source.tar.gz
```

---

## 📂 디렉토리 구조

```
천식 흡입제 사용법 evaluation 시스템 개발/
├── README.md                                # ← 이 파일
│
├── camca-inhaler-eval/                      # Claude 플러그인 소스
│   ├── README.md                            # 플러그인 상세 가이드
│   ├── .claude-plugin/plugin.json
│   ├── agents/                              # 10개 agent
│   ├── skills/                              # 8개 skill
│   ├── commands/                            # 3개 slash command
│   ├── scripts/                             # deterministic + multimodel
│   ├── assets/
│   │   ├── fonts/                           # NanumGothic TTF
│   │   ├── static/                          # 환자 가이드 PDF (KO+EN)
│   │   └── reference/                       # 흡입제 reference 테이블 (XLSX+MD)
│   └── logs/                                # 케이스별 분석 결과
│
├── camca-py/                                # Python 패키지 소스
│   ├── README.md                            # 패키지 상세 가이드
│   ├── pyproject.toml
│   ├── LICENSE
│   ├── src/camca/                           # 7개 모듈 + 번들 리소스
│   └── examples/                            # 4개 사용 예시
│
├── camca-inhaler-eval.plugin                # ← deliverable 1
├── camca-0.1.0-py3-none-any.whl             # ← deliverable 2
├── camca-0.1.0.tar.gz                       # ← deliverable 3
└── camca-py-0.1.0-source.tar.gz             # ← deliverable 4
```

---

## ⚡ 5분 시작 가이드

### A. Claude Cowork에서 사용

```
1. camca-inhaler-eval.plugin 파일을 Claude 채팅에 drag & drop
2. 미리보기 카드의 "Accept" 버튼 클릭
3. 평가 실행: /evaluate-dual /path/to/video.mp4
```

### B. Python으로 사용 (v0.2.0)

```bash
# 1) 가상환경 + 설치
python3 -m venv camca-env
source camca-env/bin/activate
pip install camca-0.2.0-py3-none-any.whl[all]   # [all] = cloud 백엔드 + telemetry

# 2) API 키 설정
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."

# 3) CLI 분석 실행
camca analyze --video patient.mp4 --case-id CASE-001 \
  --evaluator-a claude:opus --evaluator-b gemini:pro \
  --tie-breaker ollama:gemma3:27b

# 또는 Python에서:
python -c "
from camca import create_backend, PersonaConfig, MultiModelPipeline
pipeline = MultiModelPipeline(
    device_id_backend=create_backend('claude:sonnet'),
    segmenter_backend=create_backend('claude:sonnet'),
    evaluator_a=PersonaConfig('A', 'GINA-strict', create_backend('claude:opus')),
    evaluator_b=PersonaConfig('B', 'real-world-pragmatic', create_backend('gemini:pro')),
    case_dir='./logs/DEMO-001',
)
result = pipeline.run_from_video('patient.mp4', case_id='DEMO-001')
print(result.final_score['final_verdict'])
"
```

---

## 🔬 핵심 설계 원칙

CAMCA는 임상 평가 시스템에서 흔히 발생하는 hallucination·bias 문제를 **separation of concerns + dual-agent independence**로 해결합니다.

- **Probabilistic observation** (VLM): 영상에서 행동을 관찰
- **Deterministic scoring** (Python rule engine): 관찰 결과를 점수로 변환 — LLM 미관여
- **Natural language explanation** (LLM): 환자용 피드백 생성
- **Independent dual evaluation**: 두 평가자가 독립적으로 평가 후 reconcile

## 📊 이중 평가 다이버시티 전략

**Model + Persona Dual Diversity** — 두 축의 독립성을 동시에 확보

| Axis | Evaluator A | Evaluator B |
|---|---|---|
| Model | Claude Opus | Claude Sonnet (또는 Gemini Pro) |
| Persona | GINA 2024 엄격 평가자 | 실용주의 임상 평가자 |
| Tolerance | 작은 결함도 감점 | 임상 효과 영향만 감점 |
| Reference | GINA 원문 + German Airway League | CRITIKAL critical-first |

논문 reporting: *"We employed model and perspective diversity in dual-agent evaluation, achieving κ_linear = X.XX with critical-error consensus of Y%"*

## 🔄 Workflow (양쪽 deliverable 공통)

```
[영상 입력 .mp4]
    ↓
device-id → 흡입제 종류 식별
    ↓
video-segmenter → 평가 단계별 분할
    ↓
┌──────────────┬──────────────┐
│ Evaluator A  │ Evaluator B  │  (병렬 실행, 독립)
│ (Opus+GINA)  │ (Sonnet+prag)│
└──────┬───────┴──────┬───────┘
       ↓              ↓
       kappa_calculator.py    ← deterministic (LLM 미사용)
              ↓
         κ < 0.6?
              ↓
       tie-breaker            ← 자동 호출 (있을 때)
              ↓
       scoring_engine.py      ← deterministic
              ↓
       한국어 + 영어 PDF 보고서  ← 환자용(5쪽) + 임상의용(1쪽)
              ↓
       JSON + CSV export      ← IRB·연구용
```

---

## 📈 검증된 동작 (예시: CAMCA-PARK-001)

박상이 학생 (충북대 약학과 2023, 2-4조)의 pMDI 시범 영상으로 end-to-end 테스트 완료:
- Device 인식: pMDI (Vitalograph AIM 훈련 시뮬레이터)
- Evaluator A (Opus + GINA strict): 6/12 (50%)
- Evaluator B (Sonnet + pragmatic): 10/12 (83%)
- **κ_linear = 0.0** (체계적 +1 편차 → tie-breaker 자동 호출)
- Tie-breaker 4건 모두 B 손 → Consensus: ADEQUATE_WITH_EDUCATION (10/12 = 83%)
- Critical errors: 0 (직접 확인 footage 기준)
- Data quality flag: PARTIAL_DATA (영상이 흡입 동작부터 시작 → S1-S3 미관측)

→ 자세한 결과는 [logs/CAMCA-PARK-001/](camca-inhaler-eval/logs/CAMCA-PARK-001/) 폴더 참고.

---

## 🌐 외부 환경 사용 가이드 (Python 패키지)

### 백엔드 조합 시나리오 (4가지)

| Config | A | B | TB | 비용/케이스 | 권장 용도 |
|---|---|---|---|---|---|
| **Cross-vendor (논문급)** | Claude Opus | Gemini Pro | Ollama Gemma3:27b | ~$0.50 | IRB·publication |
| **Same-vendor** | Claude Opus | Claude Sonnet | — | ~$0.30 | 모델 크기 다이버시티 |
| **Local-only (PIPA)** | Ollama Gemma3:27b | Qwen2.5VL:32b | Ollama Gemma3:27b | $0 (로컬 GPU) | on-premise, 클라우드 0% |
| **Cost-optimized** | Gemini Flash | Claude Sonnet | Claude Opus | ~$0.10 | 대규모 스크리닝 |

자세한 코드 예시는 [`camca-py/examples/`](camca-py/examples/)를 참고하세요.

### API 키 설정

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."  
export OLLAMA_HOST="http://localhost:11434"  # 선택
```

---

## 📚 References

- **GINA 2024** — Global Initiative for Asthma. *Global Strategy for Asthma Management and Prevention*, 2024.
- **CRITIKAL** — Price DB, Roman-Rodriguez M, McQueen RB, et al. *Inhaler errors in the CRITIKAL study.* J Allergy Clin Immunol Pract 2017;5(4):1071-1081.
- **ADMIT** — Sanchis J, Gich I, Pedersen S. *Systematic Review of Errors in Inhaler Use.* Chest 2016;150(2):394-406.
- **German Airway League** — Worth H, Voshaar T, et al. Standardized inhaler technique checklist.
- **Kappa** — Landis JR, Koch GG. *The measurement of observer agreement for categorical data.* Biometrics 1977;33:159-174.

## 🏥 연구 컨텍스트

이 시스템은 **Min-Gyu Kang, MD** (충북대학교병원 알레르기내과 · 하버드 MGH 방문연구원)의 **CAMCA 연구 프레임워크** 일부입니다.

- **MVP scope**: pMDI + DPI(Turbuhaler)
- **Pilot study**: n=30 (15 healthy + 15 asthma) @ CBNUH, IRB 승인 후 실시
- **Phase 3**: Cross-model validation (Claude vs Gemini vs Qwen) — 본 multi-model 러너로 가능

## 📄 License

MIT (전체 시스템). 번들 NanumGothic 폰트는 SIL OFL 1.1.

---

## 📞 문의

- **Email**: drugnsafety@gmail.com
- **소속**: 충북대학교병원 알레르기내과
- **Visit**: Massachusetts General Hospital / Harvard Medical School

자세한 사용 가이드는 각 deliverable별 README를 참고하세요:
- [Plugin 가이드 → camca-inhaler-eval/README.md](camca-inhaler-eval/README.md)
- [Python 패키지 가이드 → camca-py/README.md](camca-py/README.md)
