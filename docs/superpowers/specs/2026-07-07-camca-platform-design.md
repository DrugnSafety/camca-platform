# CAMCA Platform 설계 문서

- **날짜**: 2026-07-07
- **작성**: 브레인스토밍 세션 (Min-Gyu Kang, MD + Claude)
- **상태**: 설계 승인 완료, 구현 계획 대기
- **관련 문서**: `CAMCA_Research_Proposal_v1.1.md`, `CAMCA_System_Limitations_and_Improvement_Roadmap_v1.0.md`, `method/` 6개 문서

---

## 1. 목적과 범위

**CAMCA Web** — 천식 흡입제 사용 동영상을 업로드하면 자동 분석 후 **의사용 리포트(1쪽) + 환자용 리포트(5쪽)를 자동 발행**하고, 의사가 대시보드에서 사후 모니터링하는 반응형 웹 플랫폼.

분석 로직은 기존 camca-py 평가 엔진(`MultiModelPipeline`)을 그대로 사용한다. 플랫폼이 새로 만드는 것은 두 가지다:

1. **워크플로우 레이어** — 업로드 → 파이프라인 → 발행 → 모니터링
2. **Phase Recognition Engine** — telemetry-anchored 하이브리드 세그멘테이션 (본 설계의 핵심, §5)

### 확정된 핵심 결정

| 결정 사항 | 선택 | 근거 |
|---|---|---|
| 1차 사용자·리뷰 의미 | 동영상 분석 → 의사용 + 환자용 이중 리포트 생성 | 사용자 확정 |
| 발행 워크플로우 | **자동 발행 + 사후 모니터링** (의사 사전 승인 없음) | 초기에는 연구용 도구 포지셔닝, SaMD는 후속 단계 |
| 촬영 환경 | 외래·교육실 우선, 재택 확장 대비 | IRB 파일럿(n=30)과 동일 워크플로우 |
| 플랫폼 형태 | 반응형 웹앱 (PC 대시보드 + 스마트폰 촬영·업로드) | 앱스토어 심사 없이 빠른 배포·수정 |
| 분석 백엔드 | 하이브리드: 서버 익명화 후 클라우드 VLM | PIPA 방어 + 논문급 cross-vendor 이중평가 (~$0.5/케이스) |
| 환자 식별 | 연구코드 + 서명된 접근링크 (+생년월일 확인), 회원가입 없음 | 개인정보 최소 수집, IRB 부담 최소화 |
| 아키텍처 | 모듈형 모놀리스 (FastAPI + HTMX) | 4-6주 파일럿 투입, 워커·스토리지 경계 분리로 확장 대비 |
| Phase recognition | **Telemetry-anchored 하이브리드** (1안) + flywheel 데이터 축적 | ms급 정밀도, 설명가능, L6·L7·L8 완화 |

---

## 2. 시스템 아키텍처

```
[스마트폰/PC 브라우저]
   │ 업로드/열람 (HTMX)
   ▼
┌ FastAPI 모놀리스 ──────────────────────────┐
│ web/          업로드·리포트 열람·대시보드    │
│ pipeline/     백그라운드 잡 큐              │
│   └ anonymizer → segmentation(신규 코어)   │
│     → 이중평가(camca-py) → κ/tie-break     │
│     → scoring → 리포트 생성 → 발행          │
│ quality_gate/ 업로드 직후 사전검사          │
│ reports/      PDF(기존 재사용) + HTML 뷰    │
│ auth/         스태프 계정 + 환자 서명 링크   │
└──┬─────────────────────────────────────────┘
   ▼
Postgres + 병원 내 스토리지 (원본 영상)
클라우드 VLM ← 익명화 프레임 + 오디오 특징만
```

### 모듈 경계 (모놀리스 내부)

| 모듈 | 역할 | 비고 |
|---|---|---|
| `web/` | ① 스태프용 업로드 ② 환자용 리포트 열람(링크) ③ 의사용 대시보드 | Jinja2 + HTMX 서버 렌더 |
| `pipeline/` | 백그라운드 잡 큐 — 케이스 상태 머신 구동 | 추후 독립 워커로 분리 가능한 경계 유지 |
| `anonymizer/` | MediaPipe 얼굴 블러. 원본은 병원 스토리지에만, 클라우드에는 익명화 산출물만 전송 | PIPA 방어의 핵심 경계 |
| `quality_gate/` | 얼굴/손 랜드마크 검출률, view_angle 분류 → 부적합 시 즉시 재촬영 안내 | L6를 촬영 시점에 차단 |
| `reports/` | 기존 PDF 생성기 재사용 + HTML 웹 뷰 | 한/영 |
| `auth/` | 스태프: 간단 계정. 환자: 연구코드 + 만료되는 서명 링크 + 생년월일 확인 | 회원가입 없음 |

---

## 3. 데이터 모델 (Postgres)

```
participants (연구코드, 등록일)
  └ cases (영상 경로, device_type, source[clinic|home], view_angle,
           quality_flag, 상태, 업로드 시각)
      ├ segmentations (segments JSON, events JSON, 경계별 confidence·source)
      ├ segments_corrected (의사 수정 경계 — flywheel 학습 라벨)
      ├ evaluations (evaluator A/B/TB 원시 JSON — Step 2·3 연구 export)
      ├ scores (deterministic scoring 결과, verdict)
      └ reports (PDF 경로, 발행 시각, 열람 로그)
audit_log (클라우드 전송 이력 포함 전체 감사 추적)
```

`evaluations`의 원시 JSON과 `segments_corrected`가 그대로 연구 데이터(Step 2 human-vs-LLM, Phase 2 학습 라벨)가 되도록 설계한다.

---

## 4. 케이스 상태 머신 — 자동 발행 + 사후 모니터링

```
UPLOADED → QUALITY_CHECK → ANALYZING → SCORED → REPORT_ISSUED
                │(부적합)                  │
                └→ RETAKE_REQUESTED        └→ NEEDS_ATTENTION 배지 (병행)
```

- 발행은 막지 않는다(자동 발행 원칙). 단, 다음 조건이면 대시보드에 **NEEDS_ATTENTION 배지** + 선택적 알림:
  1. Critical error ≥ 1
  2. VLM↔telemetry `CONFLICT_FLAGGED`
  3. `PARTIAL_DATA` (관측 불가 단계 다수)
  4. κ < 0.6
- 의사가 사후에 점수를 수정하면 **수정본 리포트 재발행 + 원본 대비 diff 기록** → 이 수정 기록이 Step 2 human-vs-LLM 연구 데이터가 된다.
- 파이프라인 중단 시 `FAILED` 상태 + 스태프 화면에서 원클릭 재실행.

---

## 5. 핵심 모듈: Phase Recognition Engine (`camca/segmentation/`)

### 5.1 문제 정의 — 현재 세그멘테이션의 구조적 약점

현재 구현(VLM-prompt 단독)은 5fps 프레임 + 오디오 envelope를 VLM에 통째로 주고 S1~S9 경계를 추정한다. 실측(PARK 케이스)에서 확인된 약점:

1. **경계 겹침** — S4(0~1.5s), S5(0.5~3.0s), S6(1.5~6.0s)이 상호 중첩
2. **핵심 이벤트(actuation) 미검출** — "exact actuation moment is hard to pinpoint" 자인
3. **흡입 지속 vs 숨참기 구분 불가** — S6/S7 경계가 추정에 그침
4. **telemetry 미활용** — 0.1초 해상도 telemetry가 존재하지만 세그멘테이션에서는 사용되지 않음 (scoring 단계 reconciliation에서만 사용)

### 5.2 설계 — 3단계 하이브리드 파이프라인

**Stage 1 — Deterministic 이벤트 검출** (0.1초 telemetry, LLM 미관여)

기존 telemetry 6지표에 change-point 검출을 적용해 이벤트 후보를 생성한다:

| 이벤트 | 신호 | 대응 단계 |
|---|---|---|
| E1 흔들기 | 손목/디바이스 반복 진동 (주기성) | S1 |
| E2 손→입 접근 | hand-mouth distance 급감 | S4 시작 |
| E3 입술 밀폐 | lip closure ratio 상승 | S4 완료 |
| E4 흡입 개시 | audio onset (device profile 적용) + **chest expansion fallback** | S5 시작 |
| E5 Actuation | finger acceleration spike (v0.2.1 threshold) | S5 핵심 |
| E6 숨참기 | 전 지표 저분산(정지) + 무음 구간 | S7 |
| E7 마우스피스 제거 | hand-mouth distance 증가 | S7 종료 |

각 이벤트 출력: `(timestamp, type, confidence)`. E4의 vision fallback은 **L8(AIM 시뮬레이터 audio 부재)을 세그멘테이션 레벨에서 완화**한다.

**Stage 2 — VLM 정밀 라벨링** (경계 주변만)

- 각 후보 경계 ±1초 구간을 dense(4~8fps)로 추출해 VLM에 전달 → 경계 확정 + 동작 라벨링
- 전체 영상 균등 1fps 샘플링을 폐기하고 **경계 집중 샘플링**으로 전환 — L7(1fps 한계) 근본 해결
- telemetry가 볼 수 없는 단계(S2 cap 제거, S3 내쉬기 방향)는 VLM 전체 스캔(sparse) 유지
- Pydantic schema 강제 출력

**Stage 3 — Canonical 정렬**

- 이벤트 시퀀스를 S1~S9 템플릿과 순서 제약 DP alignment (missing·순서 뒤바뀜·반복 허용)
- 출력: **겹침 없는** 세그먼트 + observability + 경계별 confidence + 경계별 근거 출처(`telemetry` / `vlm` / `both`)
- 기존 `segmentation.json` 스키마 하위 호환 — evaluator A/B는 무수정 재사용

### 5.3 플랫폼 통합 포인트

1. **타임라인 리뷰 UI** — 대시보드에 비디오 스크러버 + phase 색 밴드 + 이벤트 마커. 의사가 경계를 드래그로 수정하면 `segments_corrected`로 저장 → **Phase 2 학습형 모델(MS-TCN/ASFormer류)의 라벨 자동 축적** (data flywheel 입구)
2. **Quality gate 연동** — telemetry 검출률이 낮은 영상(측면 등)은 Stage 2 VLM 가중 자동 상향 (L6 완화)
3. **한계 해소 매핑**: L6 → quality_gate + VLM 가중, L7 → 경계 집중 샘플링, L8 → chest expansion fallback

### 5.4 검증 게이트

- KIM-001/PARK-001 regression fixture (기존 검증 점수와 일치 확인)
- 본인 12영상(Step 1 데이터)에 human 경계 라벨 부여 → **mean absolute boundary error < 0.5초**를 pass/fail 게이트로 설정
- 경계 겹침 0건, canonical 순서 위반 0건 (구조적 불변조건)

---

## 6. 에러 처리·운영

- VLM API 실패/rate limit: 지수 백오프 재시도 → 대체 백엔드 폴백 (camca-py `create_backend` 활용)
- 리포트에 data quality flag를 환자용 언어로 명시 (예: "영상 앞부분이 촬영되지 않아 일부 단계는 평가에서 제외되었습니다")
- `audit_log`에 클라우드 전송 이력 포함 전 이벤트 기록

## 7. 재택 확장 대비 (지금 안 만들되 막지 않는 것)

- 업로드 페이지는 모바일 브라우저 우선 설계
- `cases.source` 필드(clinic/home)만 미리 확보, 동일 연구코드로 재업로드
- 실시간 촬영 각도 가이드는 v2 과제로 보류 (quality_gate 사후 검사로 MVP 대체)

## 8. 테스트 전략

- KIM/PARK 케이스 regression fixture 고정
- 파이프라인 e2e는 mock 백엔드, VLM 호출부만 계약 테스트
- 리포트 golden file 비교
- Phase recognition은 §5.4 검증 게이트 별도 적용

## 9. 구현 순서 (제안)

1. **Phase Recognition Engine** (camca-py 신규 모듈, 2-3주) — 플랫폼 없이도 CLI로 검증 가능, 가장 리스크 큰 부분 선행
2. 모놀리스 골격 + 업로드 → 파이프라인 → 리포트 발행 (2주)
3. 대시보드 + 타임라인 리뷰 UI + NEEDS_ATTENTION (1-2주)
4. Quality gate + 익명화 경계 + audit (1주)

## 10. 명시적 비범위 (YAGNI)

- 환자 계정/회원가입 시스템
- 실시간 촬영 각도 가이드 (v2)
- 학습형 세그멘테이션 모델 훈련 (Phase 2 — 라벨 축적 구조만 마련)
- EMR 연동, 다기관 멀티테넌시
- MFDS SaMD 인허가 대응 기능 (연구용 포지셔닝 우선)
