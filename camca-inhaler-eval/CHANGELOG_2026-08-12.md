# camca-inhaler-eval 플러그인 패치 v2 (2026-08-12)

이번 세션에서 만든 플러그인 변경분 전체입니다. 로컬 플러그인 소스(`천식 흡입제 사용법 evaluation 시스템 개발/camca-inhaler-eval/`)의 같은 경로에 덮어쓰면 반영됩니다.

## 1. 신규 체크리스트 스킬 9종 (`skills/`)

기존 플러그인은 pMDI / Turbuhaler 2종만 지원해서, 수집한 82개 영상 중 57개가 "체크리스트 없음"으로 파이프라인이 아예 돌지 않았습니다. 이를 해소하는 신규 스킬입니다.

| 스킬 폴더 | 대상 디바이스 | 단계 ID | Critical Error ID |
|---|---|---|---|
| `inhaler-checklist-pmdi-spacer` | pMDI + 스페이서 (마우스피스형 / 안면마스크형) | S1–S7 + S8 | CRIT-SPC-01~07 |
| `inhaler-checklist-diskus` | Diskus, Accuhaler, Wixela Inhub | D1–D7 + D8,D9 | CRIT-DSK-01~14 |
| `inhaler-checklist-ellipta` | Relvar/Breo, Trelegy, Anoro, Incruse, Arnuity Ellipta | E1–E7 + E8,E9 | CRIT-ELP-01~09 |
| `inhaler-checklist-genuair` | Genuair / Pressair (Eklira, Duaklir, Brimica) | G1–G7 + G8,G9 | CRIT-GEN-01~10 |
| `inhaler-checklist-respimat` | Respimat SMI (Spiriva, Spiolto, Striverdi, Combivent) | R1–R7 + R8,R9 | CRIT-RSM-01~09 |
| `inhaler-checklist-capsule-dpi` | HandiHaler, Breezhaler, Neohaler (캡슐형) | C1–C7 + C8,C9,C10 | CRIT-CAP-01~14 |
| `inhaler-checklist-nexthaler` | NEXThaler (Foster/Trimbow), RediHaler | N1–N7 + N8,N9 | CRIT-NXT-01~13 |
| `inhaler-checklist-dpi-generic` | Spiromax, RespiClick, Flexhaler, Twisthaler, Easyhaler, Forspiro 등 전용 스킬 없는 다회용 DPI | P1–P7 + P8,P9 | CRIT-DPI-01~13 |
| `inhaler-checklist-nebulizer` | 제트/컴프레서·메쉬 네뷸라이저 (마우스피스/안면마스크) | B1–B7 + B8,B9 | CRIT-NEB-01~14 |

모든 스킬은 기존 `inhaler-checklist-turbuhaler`와 동일한 구조입니다: Scope + 형제 스킬 라우팅 → 개념적 차이 → 평가 프레임워크 → 단계별 Level 0–3 루브릭 → Critical Error 요약표 → 판정 로직 의사코드 → VLM 관찰 가이드 → 디바이스 전환 환자 주의사항 → 참고문헌(GINA 2024, CRITIKAL 2017, Sanchis 2016, Plaza 2018, Laube 2011 등 — 임의 인용 없음).

점수 체계는 전부 통일: **core 7단계 × 0–3점 = 21점 만점**, PROFICIENT ≥86% / ADEQUATE_WITH_EDUCATION ≥67% / NEEDS_INTENSIVE_TRAINING ≥48% / 그 외 FAIL, **critical error 1건이라도 있으면 무조건 FAIL**.

### 디바이스별로 특히 주의한 임상적 차이

- **Respimat(SMI)**: 흡입은 **느리고 깊게** — DPI의 "세게 빨아들이기"를 그대로 적용하면 안 됨. 이 혼동 자체를 critical error(CRIT-RSM-03)로 명시.
- **네뷸라이저**: **평상시 호흡(tidal breathing)** 이 정상. 흡입력·숨참기 요구 없음. DPI 기준 적용 금지를 스킬에 명시. 사용 후 세척은 감염관리상 safety-critical로 취급.
- **캡슐형 DPI**: 캡슐을 삼켜버리는 실제 사고, 천공 반복으로 인한 캡슐 파편 흡입 등 다른 디바이스에 없는 실패 모드 포함. 캡슐 회전음(휘파람 소리)이 흡입력의 고신뢰 오디오 근거.
- **Genuair**: 빨강→초록→빨강 창 색 변화가 **시각만으로** 확인 가능 — VLM 평가에 가장 유리한 디바이스.
- **NEXThaler**: 흡입 성공 시에만 카운터가 감소하는 구조라 "복용 여부"를 사후 검증 가능.

## 2. `scripts/scoring_engine.py` 수정

`DEVICE_MAX_SCORES` 테이블 수정:

- **버그 수정**: `pMDI-spacer` 가 `core_max: 24, core_steps: 8` 로 잘못 설정되어 있었음 → 실제 체크리스트는 7단계 21점이라 백분율이 왜곡됨(21/21=100%가 87.5%로 표기). `core_max: 21, conditional_max: 3, core_steps: 7, conditional_steps: 1` 로 정정.
- **신규 디바이스 9종 등록**: `DPI-diskus`, `DPI-ellipta`, `DPI-genuair`, `SMI-respimat`, `DPI-capsule`, `DPI-nexthaler`, `DPI-generic`, `nebulizer` 추가. 미등록 상태면 `--device` 인자가 거부되어 파이프라인이 정지합니다.

## 적용 방법

```bash
cd "천식 흡입제 사용법 evaluation 시스템 개발/camca-inhaler-eval"
# 1) 스킬 9종 복사 (신규 폴더)
cp -R /path/to/patch/skills/inhaler-checklist-* skills/
# 2) 스코어링 엔진 교체
cp /path/to/patch/scripts/scoring_engine.py scripts/
# 3) git 반영
git add skills scripts && git commit -m "feat: add 9 device checklists; fix pMDI-spacer scoring denominator"
```

이후 Claude Code / Cowork 에서 플러그인을 다시 로드하면 다음 세션부터 반영됩니다.

## 남아 있는 알려진 이슈 (미수정)

1. `scripts/research_log_exporter.py` — CSV writer가 `tie_breaker_invoked` / `clinician_review_flag` / `kappa_interpretation` 을 중첩 객체로 기대하나 adjudicator는 top-level scalar로 출력. 해당 CSV 컬럼이 비어 나옴(JSON export는 정상).
2. `scripts/kappa_calculator.py` — 단계 레벨이 `null`(관찰 불가) 이면 크래시. 이 때문에 "관찰 불가 단계에 억지로 점수를 매기는" 잘못된 유인이 생김.
3. `scripts/korean_pdf_generator.py` — 한글 폰트 경로 하드코딩, 미발견 시 Helvetica로 조용히 폴백.
4. `scripts/run_telemetry.py` — MediaPipe API 불일치(`module 'mediapipe' has no attribute 'solutions'`)로 이 환경에서 항상 실패. 파이프라인은 VLM-only 축소 모드로 정상 폴백되지만, **오디오 근거가 필요한 단계(흡입력·클릭음)의 신뢰도가 전반적으로 낮아지는 주된 원인**입니다. 우선순위 높음.
5. `inhaler-checklist-pmdi-spacer` S4 루브릭 결함 — 마우스피스 사용 시 "혀 위치 불명확"이 항상 참이 되어 Level 3 달성이 구조적으로 불가능. 재작성 필요.
6. `inhaler-checklist-dpi-generic` P2(용량 장전) 문구가 실제 채점에 쓰기엔 너무 모호하다는 점이 RespiClick 실증에서 확인됨.
