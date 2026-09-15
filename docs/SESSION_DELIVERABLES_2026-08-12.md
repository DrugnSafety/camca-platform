# CAMCA 세션 산출물 종합 정리 (2026-07-29 ~ 2026-08-12)

이 문서는 이번 작업 세션에서 만들어진 **모든 파일**과 그 용도를 정리한 것입니다. 각 파일이 무엇이고, 왜 만들었고, 어떻게 쓰는지를 담았습니다.

---

## 1. 한눈에 보기

| 구분 | 내용 |
|---|---|
| 처리 완료 영상 | **18건** (1차 3건 + 2차 7건 + 3차 8건) |
| 남은 영상 | 64건 (전부 처리 가능한 상태로 정비 완료) |
| 신규 작성 체크리스트 스킬 | **9종** (지원 디바이스 2종 → 11종) |
| 추출 프레임 | **4,650장** (0.25초 간격, 단계 라벨 부착) |
| 수정한 버그 | scoring_engine 분모 오류 1건 + 신규 디바이스 9종 등록 |
| 발견·기록한 미수정 이슈 | 6건 |

**가장 중요한 성과**: 시작 시점에는 수집한 82개 영상 중 **57개가 체크리스트 부재로 파이프라인이 아예 돌지 않는 상태**였습니다. 체크리스트 9종을 새로 작성해 이 병목을 제거했고, 8개 신규 디바이스 전부에 대해 실제 영상으로 end-to-end 검증까지 마쳤습니다.

---

## 2. 전달된 파일 목록

### 2-1. 플러그인 패치

**`camca-plugin-patch-v2.zip`** ← **이것만 적용하면 플러그인 업데이트 완료**

```
plugin_patch_v2/
├── README_PATCH.md          # 변경 내역 + 적용 방법 + 남은 이슈
├── scripts/
│   └── scoring_engine.py    # 수정본
└── skills/
    ├── inhaler-checklist-pmdi-spacer/SKILL.md
    ├── inhaler-checklist-diskus/SKILL.md
    ├── inhaler-checklist-ellipta/SKILL.md
    ├── inhaler-checklist-genuair/SKILL.md
    ├── inhaler-checklist-respimat/SKILL.md
    ├── inhaler-checklist-capsule-dpi/SKILL.md
    ├── inhaler-checklist-nexthaler/SKILL.md
    ├── inhaler-checklist-dpi-generic/SKILL.md
    └── inhaler-checklist-nebulizer/SKILL.md
```

적용: 로컬 `camca-inhaler-eval/` 의 같은 경로에 덮어쓰기 → git commit → 플러그인 재로드.

(이전에 보낸 `camca-plugin-patch.zip`(v1)은 v2에 모두 포함되어 있으므로 **v2만 쓰면 됩니다.**)

### 2-2. 라벨링 결과

| 파일 | 내용 |
|---|---|
| `timestamp_labeling_ALL.md` | 18건 전체의 단계별 시작–종료 시각 표 + AI 판정 요약 |
| `frame_step_mapping_ALL.csv` | 프레임 파일명 ↔ case_id / step_id / 타임스탬프 매핑 (4,650행) |
| `frames_PILOT-*.zip` (18개, 큰 것은 분할) | 케이스별 0.25초 간격 프레임 이미지 |

프레임 파일명 규칙: `{step_id}_t{초.소수2자리}s.jpg`
예: `S5_t0014.25s.jpg` = S5 단계, 영상 시작 후 14.25초 지점.

### 2-3. 평가 리포트

| 파일 | 내용 |
|---|---|
| `reports_batch3.zip` | 신규 8건의 환자용/임상의용 PDF + `07_final_score.json` + `09_research_export.json/csv` + `03_segments.json` |
| (이전 전달) `pilot7_reports.zip` | 2차 7건 리포트 |
| (이전 전달) 개별 PDF 4개 | 1차 IPCRG-03 / KAPARD-02 리포트 |

검증하실 때는 **`08_clinician_report.pdf`** 를 보시면 됩니다 — 단계별 점수와 그 근거가 적혀 있습니다.

### 2-4. 다음 세션용 도구

| 파일 | 내용 |
|---|---|
| `run_remaining.md` | 남은 64건 처리 절차서 (분류 기준, 입력 JSON 양식, 에이전트 프롬프트 템플릿, 주의점) |
| `extract_frames.py` | 프레임 추출 CLI. `--cases`, `--interval` 인자. HH:MM:SS / MM:SS 양쪽 파싱 지원 |

---

## 3. 처리한 영상 18건 결과

### 1차 — 사전 trim된 클립 (전부 공식 레퍼런스)

| Case | 디바이스 | 판정 | 점수 |
|---|---|---|---|
| PILOT-KR-AMC-02 | Turbuhaler | PROFICIENT | 100% |
| PILOT-INT-IPCRG-03 | pMDI+스페이서(마우스피스) | PROFICIENT | 100% |
| PILOT-KR-KAPARD-02 | pMDI+스페이서(안면마스크/소아) | PROFICIENT | 100% |

### 2차 — 전체 원본 영상

| Case | 디바이스 | 판정 | 점수 |
|---|---|---|---|
| PILOT-INT-IPCRG-02 | pMDI | PROFICIENT | 90.5% |
| PILOT-PT-AAN-01 | pMDI | **NEEDS_INTENSIVE_TRAINING** | 61.9% |
| PILOT-PT-COPDF-06 | pMDI+스페이서 | ADEQUATE_WITH_EDUCATION | 81.0% |
| PILOT-KR-CMC-03 | Turbuhaler | ADEQUATE_WITH_EDUCATION | 85.7% |
| PILOT-KR-GW-04 | Turbuhaler | ADEQUATE_WITH_EDUCATION | 76.2% |
| PILOT-KR-KAPARD-01 | pMDI (소아) | ADEQUATE_WITH_EDUCATION | 81.0% |
| PILOT-KR-AMC-08 | pMDI (소아) | ADEQUATE_WITH_EDUCATION | 85.7% |

### 3차 — 신규 체크리스트 검증

| Case | 디바이스 | 판정 | 점수 | 검증한 스킬 |
|---|---|---|---|---|
| PILOT-KR-AMC-03 | Diskus | PROFICIENT | 95.2% | `-diskus` |
| PILOT-KR-AMC-04 | Ellipta | ADEQUATE_WITH_EDUCATION | 81.0% | `-ellipta` |
| PILOT-KR-AMC-05 | Genuair | ADEQUATE_WITH_EDUCATION | 71.4% | `-genuair` |
| PILOT-KR-GW-02 | Respimat | PROFICIENT | 95.2% | `-respimat` |
| PILOT-KR-KUG-01 | Breezhaler (캡슐형) | ADEQUATE_WITH_EDUCATION | 81.0% | `-capsule-dpi` |
| PILOT-KR-CMC-05 | NEXThaler | ADEQUATE_WITH_EDUCATION | 71.4% | `-nexthaler` |
| PILOT-PT-COPDF-10 | RespiClick | **NEEDS_INTENSIVE_TRAINING** | 52.4% | `-dpi-generic` |
| PILOT-KR-KAPARD-03 | 네뷸라이저 (소아) | ADEQUATE_WITH_EDUCATION | 76.2% | `-nebulizer` |

**18건 전체에서 critical error 확정 0건.** 공식 교육영상에 대해 오탐(false positive)을 내지 않는다는 점은 일관되게 확인되었습니다.

---

## 4. 사용자 검증이 특히 필요한 케이스

AI 판정을 그대로 신뢰하기 어려운 케이스들입니다. 대부분 **기술이 나빠서가 아니라 영상에서 근거를 확보할 수 없어서** 점수가 낮게 나왔습니다.

| 우선순위 | Case | 확인해야 할 것 |
|---|---|---|
| 1 | **PT-AAN-01** (61.9%) | 실제 사용 시연 구간이 총 7.5초뿐(프레임 28장). S5(협응)·S7(숨참기) critical error 여부가 A/B 평가자 간 미해결. 점수가 낮은 게 기술 문제인지 촬영 문제인지 판단 필요 |
| 2 | **PT-COPDF-10** (52.4%) | 18건 중 최저점. generic DPI 체크리스트의 P2(용량 장전) 문구가 RespiClick 같은 힌지캡 방식에 안 맞아 A/B가 6/8 단계에서 갈림. 스킬 문구 수정이 필요한 사안일 가능성 |
| 3 | **KR-GW-04** (76.2%) | 오디오 소실로 T2(클릭음)·T5(흡입력) 판정 신뢰도 0.5~0.55. 직접 들어보고 판단 필요 |
| 4 | **KR-CMC-05** (71.4%) | 배경음악이 NEXThaler 클릭음을 가림 + "Training Device" 표기 데모라 카운터 전후 비교 불가 |
| 5 | **PT-COPDF-06** (81.0%) | t=90~98초 구간(마우스피스 제거~숨참기 전환)이 샘플링에서 누락되어 CRIT-SPC-06 여부 불명확 |

---

## 5. 진행 중 발견한 시스템 문제

### 이번에 고친 것

1. **`inhaler-checklist-pmdi-spacer` 스킬 부재** — `inhaler-checklist-pmdi/SKILL.md` 13행이 이 스킬을 참조하는데 실제로는 존재하지 않아, spacer 영상이 전부 `unsupported_device` 로 정지. → 신규 작성.
2. **`scoring_engine.py` 분모 오류** — `pMDI-spacer` 가 8단계/24점으로 잘못 설정(실제는 7단계/21점). 21/21=100%가 87.5%로 표기됨. → 정정 후 해당 케이스 재채점.
3. **신규 디바이스 9종 미등록** — `DEVICE_MAX_SCORES` 에 없으면 `--device` 인자가 거부됨. → 등록.

### 아직 안 고친 것 (우선순위 순)

1. **`run_telemetry.py` MediaPipe 오류** ⚠️ **최우선**
   `module 'mediapipe' has no attribute 'solutions'` 로 **모든 케이스에서 텔레메트리가 실패**하고 있습니다. 파이프라인은 VLM-only 축소 모드로 폴백되어 결과 자체는 나오지만, 흡입력·클릭음처럼 오디오 근거가 필요한 단계의 신뢰도가 전반적으로 낮아집니다. **위 "검증 필요 케이스" 5건 중 3건의 근본 원인이 이것입니다.** 남은 64건을 이 상태로 다 돌리면 나중에 재실행해야 할 수 있으므로, 다음 작업 전에 먼저 해결하시길 권합니다.

2. **`kappa_calculator.py` null 처리 크래시**
   단계 레벨이 `null`(관찰 불가)이면 죽습니다. 이 때문에 "관찰 불가 단계에 억지로 점수를 매기는" 잘못된 유인이 생기고, 실제로 1차 실행에서 그 오류가 발생했습니다.

3. **`inhaler-checklist-pmdi-spacer` S4 루브릭 결함**
   Level 2 조건에 "혀 위치 불명확"이 있는데, 마우스피스를 물면 혀는 **항상** 안 보입니다. 즉 Level 3 달성이 구조적으로 불가능합니다. tie-breaker가 이 점을 지적했습니다.

4. **`inhaler-checklist-dpi-generic` P2 문구 모호**
   디바이스 중립적으로 쓰다 보니 실제 채점에 쓰기엔 불충분. RespiClick 실증에서 확인됨.

5. **`research_log_exporter.py` CSV 필드 매핑 불일치**
   `tie_breaker_invoked` / `clinician_review_flag` / `kappa_interpretation` 컬럼이 비어 나옵니다(JSON export는 정상).

6. **`korean_pdf_generator.py` 폰트 경로 하드코딩**
   한글 폰트를 못 찾으면 Helvetica로 조용히 폴백합니다.

### 방법론적으로 중요한 발견 — 평가자 독립성

orchestrator 서브에이전트에는 Task/Agent 디스패치 도구가 없어서, evaluator-A/B를 **진짜 독립 에이전트로 띄우지 못하고 orchestrator가 두 페르소나를 순차적으로 흉내내는** 방식으로 동작했습니다. 이를 검증하기 위해 PILOT-INT-IPCRG-03에 대해 메인 세션에서 **진짜 격리된 Agent 호출**로 재실행한 결과:

| 지표 | 순차 시뮬레이션 | 진짜 독립 dispatch |
|---|---|---|
| 정확 일치율 | 0.75 (6/8) | 0.33 (2/6) |
| 불일치 스텝 | S2, S8 (관찰 불가 형식 단계만) | S1, S4, S6, S7 (실제 시연 단계) |

**즉, 기존 방식은 평가자 간 합의를 인위적으로 부풀리고 있었습니다.** 불일치가 "형식적 단계"에서 "실제 핵심 단계"로 이동했고, 이 과정에서 세그멘테이션 데이터 결함(구간 길이 7.5초인데 서술문은 10초 주장)과 위 3번 루브릭 결함이 새로 드러났습니다.

**논문·IRB 제출용 IRR 통계는 반드시 진짜 dispatch 환경에서 재산출해야 합니다.** 지금까지의 18건 kappa 값은 이 한계를 안고 있습니다.

---

## 6. 다음 단계 권장 순서

1. **`run_telemetry.py` MediaPipe 수정** — 남은 64건 처리 전에 반드시. 안 하면 재작업 위험.
2. **패치 v2 적용 + git commit** — `camca-plugin-patch-v2.zip`
3. **검증 필요 5건 직접 확인** — 프레임 이미지와 clinician PDF로 확인 가능
4. **루브릭 결함 2건 수정** — pmdi-spacer S4, dpi-generic P2
5. **남은 64건 배치 처리** — `run_remaining.md` 절차대로, 세션 나눠서
6. **IRR 재산출** — 진짜 Agent dispatch 환경에서 대표 케이스 재실행

---

## 7. 파일 위치 참고

파이프라인 원자료는 플러그인 디렉터리 안에 케이스별로 남아 있습니다.

```
camca-inhaler-eval/logs/PILOT-{CASE_ID}/
  00_pipeline_metadata.json   # 실행 환경, 폴백 여부, 알려진 편차 기록
  01_input.json               # 입력 정의
  01c_telemetry_summary.json  # 텔레메트리(현재 전부 실패 기록)
  02_device_id.json           # 디바이스 판정 + 신뢰도
  03_segments.json            # ★ 단계별 타임스탬프 (프레임 추출의 입력)
  04_evaluator_a.json         # 평가자 A (GINA 엄격)
  05_evaluator_b.json         # 평가자 B (실무 관용)
  06_adjudication.json        # 합의 + 불일치 분석
  06b_kappa_stats.json        # 카파 통계
  06c_tie_breaker.json        # (κ<0.6 시) 3차 평가자
  07_final_score.json         # ★ 최종 점수·판정 (결정론적)
  08_patient_report.pdf       # 환자용 한국어 리포트
  08_clinician_report.pdf     # ★ 임상의용 리포트 (검증은 이걸 보세요)
  09_research_export.json/csv # 연구용 내보내기
```

`_independent_verify.json` 접미사가 붙은 파일은 위 5절의 독립성 재검증 결과이며, 원본은 대조군으로 보존되어 있습니다.
