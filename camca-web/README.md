# camca-web

CAMCA 흡입제 사용 영상 자동 평가 플랫폼 — 업로드 → 자동 분석(익명화 → 이중 평가자 → 채점) → 의사용/환자용 리포트 자동 발행 → 대시보드 사후 모니터링까지 수행하는 FastAPI 모놀리스입니다.

분석 엔진 자체는 형제 패키지 [`camca-py`](../camca-py)의 `MultiModelPipeline`을 그대로 사용합니다. 이 저장소는 그 위의 워크플로우 레이어(업로드·잡큐·익명화·발행·대시보드)만 구현합니다. 설계 배경은 [`docs/superpowers/specs/2026-07-07-camca-platform-design.md`](../docs/superpowers/specs/2026-07-07-camca-platform-design.md)를 참고하세요.

## 요구사항

- Python 3.11+
- `ffmpeg` (시스템 PATH에 있어야 함 — 프레임 추출·경계 정밀화에 사용)
- `camca-py`가 형제 디렉토리(`../camca-py`)에 있어야 함 (로컬 경로 의존성)
- (선택) 실제 영상 분석을 돌리려면 VLM API 키 — 아래 [환경 변수](#환경-변수) 참고
- (선택) 얼굴 익명화를 실제로 돌리려면 `mediapipe` — `pip install '.[anonymizer]'`

## 빠른 시작

```bash
cd camca-web
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]' -e ../camca-py

# 스태프 계정 생성 (회원가입 없는 설계 — 이 CLI가 유일한 계정 생성 경로)
.venv/bin/camca-web create-staff --username dr-kang
# 비밀번호는 프롬프트로 입력받습니다 (--password로 직접 지정도 가능)

# 개발 서버 실행
.venv/bin/uvicorn --factory camca_web.app:create_app --reload
```

`http://localhost:8000/login` 에서 방금 만든 계정으로 로그인 → `/upload`에서 영상 업로드 → `/dashboard`에서 케이스 확인.

기본 설정은 SQLite(`./camca_web.db`) + 로컬 파일스토리지(`./storage`)를 씁니다. 파일럿/운영 전환 시에는 환경 변수로 Postgres 등을 지정하세요.

### 백그라운드 워커까지 함께 띄우기

업로드된 케이스가 자동으로 분석되게 하려면(익명화 → 파이프라인 → 채점 → 발행) 워커를 켜야 합니다:

```bash
CAMCA_START_WORKER=1 .venv/bin/uvicorn --factory camca_web.app:create_app
```

워커 없이 띄우면 업로드/로그인/대시보드는 동작하지만 잡 큐가 소비되지 않아 케이스가 `UPLOADED` 상태에 머뭅니다.

## 환경 변수

| 변수 | 기본값 | 용도 |
|---|---|---|
| `CAMCA_DB_URL` | `sqlite:///./camca_web.db` | DB 연결 문자열 (운영은 Postgres 권장) |
| `CAMCA_STORAGE_ROOT` | `./storage` | 원본·익명화 영상, 리포트 PDF 저장 경로 (원본 영상은 **여기서 나가지 않음** — PIPA 경계) |
| `CAMCA_SECRET_KEY` | `dev-only-change-me` | 세션 쿠키·환자 서명 링크 서명 키 — **운영 배포 전 반드시 변경** |
| `CAMCA_START_WORKER` | (미설정) | `1`이면 앱 시작 시 백그라운드 워커 스레드 기동 |
| `ANTHROPIC_API_KEY` | — | Evaluator A(GINA-strict, Claude Opus) + device-id/segmenter(Claude Sonnet) 호출에 필요 |
| `GOOGLE_API_KEY` 또는 `GEMINI_API_KEY` | — | Evaluator B(실용주의, Gemini Pro) 호출에 필요 |

`ANTHROPIC_API_KEY`/`GOOGLE_API_KEY`는 **실제 영상 분석을 돌릴 때만** 필요합니다. 테스트 스위트는 전 구간 mock이라 API 키 없이 통과합니다.

## 테스트

```bash
.venv/bin/python -m pytest tests/ -v
```

VLM/MediaPipe 등 외부 의존은 전부 `RunnerDeps`로 주입 가능해 CI는 mock만으로 전 구간을 검증합니다. `reportlab`/`pypdf`가 없으면 리포트 관련 테스트 일부가 자동 SKIP됩니다.

리포트 콘텐츠 매핑이 의도치 않게 바뀌면 `tests/test_reports_golden.py`가 실패합니다. 의도된 변경이면:

```bash
CAMCA_UPDATE_GOLDEN=1 .venv/bin/python -m pytest tests/test_reports_golden.py -q
# 갱신된 tests/golden/*.json diff를 리뷰하고 커밋
```

## 주요 라우트

| 라우트 | 대상 | 설명 |
|---|---|---|
| `GET/POST /login` | 스태프 | 세션 쿠키 로그인 |
| `GET/POST /upload` | 스태프 | 영상 업로드 → 케이스 생성 + 잡 등록 |
| `POST /cases/{id}/rerun` | 스태프 | `FAILED` 케이스 원클릭 재실행 |
| `GET /dashboard` | 스태프 | 케이스 목록 + NEEDS_ATTENTION 배지 |
| `GET /cases/{id}` | 스태프 | 타임라인 리뷰 + 점수 편집 |
| `POST /cases/{id}/segments` | 스태프 | 경계 수정 저장 (flywheel 라벨) |
| `POST /cases/{id}/scores` | 스태프 | 점수 수정 → 재채점 → 리포트 재발행 |
| `GET/POST /r/{token}` | 환자 | 서명 링크 + 생년월일 확인 → 리포트 열람 |
| `GET /health` | — | 헬스체크 |

## 케이스 상태 머신

```
UPLOADED → QUALITY_CHECK → ANALYZING → SCORED → REPORT_ISSUED
                │(부적합)                            │
                └→ RETAKE_REQUESTED      NEEDS_ATTENTION 배지 (발행은 막지 않음)
```

`FAILED` 상태는 `/cases/{id}/rerun`으로 재시도합니다. NEEDS_ATTENTION 4조건, PIPA 익명화 경계 등 상세 규칙은 design spec §4를 참고하세요.

## 더 읽어보기

- 설계 배경: [`docs/superpowers/specs/2026-07-07-camca-platform-design.md`](../docs/superpowers/specs/2026-07-07-camca-platform-design.md)
- 구현 계획(태스크별 근거·self-review): [`docs/superpowers/plans/2026-07-07-camca-web-platform.md`](../docs/superpowers/plans/2026-07-07-camca-web-platform.md)
- 분석 엔진(세그멘테이션·평가·채점) 상세: [`../camca-py/README.md`](../camca-py/README.md)
