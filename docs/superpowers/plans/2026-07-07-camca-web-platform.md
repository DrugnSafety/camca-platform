# CAMCA Web Platform Implementation Plan (Plan 2 of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 동영상 업로드 → 자동 분석 → 의사용+환자용 이중 리포트 자동 발행 → 의사 사후 모니터링(대시보드 + 타임라인 리뷰)까지 수행하는 FastAPI 모놀리스 `camca-web`을 구축한다.

**Architecture:** 모듈형 모놀리스 (spec §2) — `web/`(HTMX 서버 렌더), `pipeline/`(DB-backed 잡 큐 + 백그라운드 워커), `anonymizer/`(PIPA 경계), `quality_gate/`, `reports/`(기존 PDF 재사용), `auth/`(스태프 세션 + 환자 서명 링크). 분석 로직은 camca-py의 `MultiModelPipeline`(+ Plan 1의 `use_phase_engine`)을 그대로 사용하고, 플랫폼은 워크플로우 레이어만 새로 만든다.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (테스트 SQLite / 운영 Postgres), Jinja2 + HTMX(로컬 번들), itsdangerous(서명 링크), pytest + httpx TestClient. camca-py를 로컬 경로 의존성으로 재사용.

**Working directory:** `camca-web/` (신규 — 모든 경로는 이 디렉토리 기준. camca-py와 형제 디렉토리)

## Global Constraints

- **PIPA 경계 (spec §2)**: 원본 영상은 로컬 스토리지에만. 클라우드 VLM에는 **익명화 산출물만** 전달 — runner는 반드시 anonymized video 경로를 파이프라인에 넘긴다.
- **자동 발행 원칙 (spec §4)**: NEEDS_ATTENTION은 발행을 막지 않는다 — 배지만 단다.
- **환자 인증 (spec 결정표)**: 회원가입 없음. 연구코드 + 만료되는 서명 링크 + 생년월일 확인.
- **상태 머신 (spec §4)**: `UPLOADED → QUALITY_CHECK → ANALYZING → SCORED → REPORT_ISSUED`, 분기 `RETAKE_REQUESTED`, `FAILED`(원클릭 재실행).
- **NEEDS_ATTENTION 4조건 (spec §4)**: ① critical error ≥ 1 ② `conflict_flagged` 세그먼트 존재 ③ PARTIAL_DATA(미관측 단계 ≥ 5/9) ④ κ_linear < 0.6.
- **연구 데이터 우선 (spec §3)**: `evaluations` 원시 JSON과 `segments_corrected`는 그대로 Step 2 / Phase 2 연구 export가 되도록 저장.
- **audit_log (spec §6)**: 클라우드 전송·리포트 열람·경계 수정 등 전 이벤트 기록.
- **외부 CDN 금지**: htmx는 로컬 static 파일로 번들 (병원망 오프라인 대비).
- 모든 신규 코드는 TDD — 실패 테스트 → 구현 → 통과 → 커밋.

**사전 확인 사항 (계획 작성 시 실측):**
- `MultiModelPipeline.run_from_video(video_path, case_id, fps=1.0, ...) -> PipelineResult` — 필드: `device_id, segments, evaluator_a, evaluator_b, tie_breaker, kappa_stats, final_score, metadata` (camca-py `pipeline.py:33`)
- `PersonaConfig(name, persona_label, backend)` (camca-py `pipeline.py:22`)
- `build_bilingual_reports(patient_content=, clinician_content=, output_dir=, case_id=, device=) -> dict[str, Path]` (camca-py `reports.py:355`)
- `_build_patient_content(result)/_build_clinician_content(result)` — PipelineResult→PDF content 매핑이 camca-py `cli.py:162,187`에 이미 존재 → import 재사용
- `classify_view_angle(telemetry_stream) -> ViewAngleClassification(primary_view, confidence, yaw_estimate_deg, face_detection_rate, recommendation)` (camca-py `telemetry/view_angle.py:53`)
- `extract_telemetry(video_path)` (camca-py `telemetry/pipeline.py:52`)

---

## File Structure

```
camca-web/
├── pyproject.toml
├── src/camca_web/
│   ├── __init__.py
│   ├── config.py            # Settings: DB URL, storage 경로, SECRET_KEY, 링크 만료
│   ├── db.py                # engine/session + 모델 9종 + write_audit()
│   ├── state.py             # 상태 상수 + can_transition + needs_attention_reasons (순수)
│   ├── auth.py              # 스태프 세션 쿠키 + 환자 서명 링크 토큰 (순수 함수 중심)
│   ├── jobs.py              # DB-backed 잡 큐: enqueue / run_pending_once / worker thread
│   ├── quality_gate.py      # evaluate_quality (telemetry → pass/retake, 순수)
│   ├── anonymizer.py        # MediaPipe 얼굴 블러 (detector 주입 가능)
│   ├── runner.py            # process_case — 케이스 1건 상태 머신 구동 (전 의존성 주입)
│   ├── reports_web.py       # PipelineResult→발행 + 수정본 재발행 diff
│   ├── app.py               # create_app() 팩토리 + 라우터/템플릿/worker 배선
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── staff.py         # 로그인, 업로드, 재실행
│   │   ├── dashboard.py     # 대시보드, 케이스 상세(타임라인), 경계 수정 저장
│   │   └── patient.py       # /r/{token} 생년월일 확인 → 리포트 열람
│   ├── templates/           # base/login/upload/dashboard/case_detail/patient_*.html
│   └── static/htmx.min.js
└── tests/
    ├── conftest.py          # in-memory DB, TestClient, 시드 헬퍼
    ├── test_app.py …        # 태스크별 테스트 파일 (아래 각 태스크에 명시)
```

각 파일 책임: `state.py`/`auth.py`/`quality_gate.py`는 DB를 모르는 순수 로직, `runner.py`만이 상태 전이+저장을 조립, `routes/`는 HTTP↔서비스 변환만. VLM/MediaPipe 의존은 전부 주입 가능해 CI는 mock으로 전 구간 커버.

---

### Task 0: 프로젝트 스캐폴드 + FastAPI 앱 팩토리

**Files:**
- Create: `pyproject.toml`, `src/camca_web/__init__.py`, `src/camca_web/config.py`, `src/camca_web/app.py`
- Create: `tests/conftest.py`, `tests/test_app.py`
- Create: `src/camca_web/static/htmx.min.js` (다운로드)

**Interfaces:**
- Produces: `create_app(settings: Settings) -> FastAPI`, `Settings(db_url, storage_root, secret_key, patient_link_max_age_sec)` — 이후 모든 태스크가 이 팩토리에 라우터를 추가한다.

- [ ] **Step 1: 프로젝트 파일 작성**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "camca-web"
version = "0.1.0"
description = "CAMCA web platform — upload, auto-analysis, dual report issuance, monitoring"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn>=0.29",
    "sqlalchemy>=2.0",
    "jinja2>=3.1",
    "python-multipart>=0.0.9",
    "itsdangerous>=2.1",
]

[project.optional-dependencies]
dev = ["pytest>=8", "httpx>=0.27"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```python
# src/camca_web/config.py
"""플랫폼 설정 — 환경변수 우선, 테스트에서는 Settings 직접 생성."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    db_url: str = field(default_factory=lambda: os.environ.get(
        "CAMCA_DB_URL", "sqlite:///./camca_web.db"))
    storage_root: Path = field(default_factory=lambda: Path(os.environ.get(
        "CAMCA_STORAGE_ROOT", "./storage")))
    secret_key: str = field(default_factory=lambda: os.environ.get(
        "CAMCA_SECRET_KEY", "dev-only-change-me"))
    patient_link_max_age_sec: int = 7 * 24 * 3600  # 서명 링크 만료 7일
```

```python
# src/camca_web/app.py
"""FastAPI 앱 팩토리 — 모든 배선은 여기서만."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import Settings

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATE_DIR = Path(__file__).parent / "templates"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="CAMCA Web")
    app.state.settings = settings
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app
```

```python
# tests/conftest.py
"""공용 fixture — in-memory 설정 + TestClient."""
import pytest
from fastapi.testclient import TestClient

from camca_web.config import Settings
from camca_web.app import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(
        db_url="sqlite://",              # in-memory
        storage_root=tmp_path / "storage",
        secret_key="test-secret",
    )


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))
```

```python
# tests/test_app.py
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **Step 2: 설치 + htmx 번들 + 빈 패키지 파일**

```bash
mkdir -p camca-web/src/camca_web/{routes,templates,static} camca-web/tests
touch camca-web/src/camca_web/__init__.py camca-web/src/camca_web/routes/__init__.py
cd camca-web
curl -sL https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js -o src/camca_web/static/htmx.min.js
python -m venv .venv && .venv/bin/pip install -e '.[dev]' -e ../camca-py
```

- [ ] **Step 3: 테스트 통과 확인**

Run: `cd camca-web && .venv/bin/python -m pytest tests/test_app.py -v`
Expected: PASS (1 passed)

- [ ] **Step 4: Commit**

```bash
git add camca-web/
git commit -m "feat(web): scaffold camca-web FastAPI monolith with app factory"
```

---

### Task 1: DB 모델 + audit 헬퍼

**Files:**
- Create: `src/camca_web/db.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Produces: `Base`, `make_engine(db_url)`, `make_session_factory(engine)`, `init_db(engine)`; 모델 `Participant, Case, Segmentation, SegmentsCorrected, Evaluation, Score, Report, Job, AuditLog`; `write_audit(session, event, case_id=None, detail=None)`.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_db.py
"""spec §3 데이터 모델 — 테이블 생성과 관계, audit 기록."""
import pytest
from camca_web.db import (
    make_engine, make_session_factory, init_db, write_audit,
    Participant, Case, Segmentation, Evaluation, Score, Report, Job, AuditLog,
)


@pytest.fixture
def session():
    engine = make_engine("sqlite://")
    init_db(engine)
    return make_session_factory(engine)()


def test_participant_case_relationship(session):
    p = Participant(research_code="RC-001", dob="1980-01-01")
    session.add(p)
    session.flush()
    c = Case(participant_id=p.id, video_path="v.mp4", device_type="pMDI",
             source="clinic", status="UPLOADED")
    session.add(c)
    session.commit()
    assert c.id is not None
    assert session.get(Participant, p.id).cases[0].id == c.id


def test_case_children(session):
    p = Participant(research_code="RC-002", dob="1990-02-02")
    session.add(p); session.flush()
    c = Case(participant_id=p.id, video_path="v.mp4", device_type="pMDI",
             source="clinic", status="SCORED")
    session.add(c); session.flush()
    session.add_all([
        Segmentation(case_id=c.id, segments=[{"step_id": "S1"}], events=[], engine="telemetry-anchored-v1"),
        Evaluation(case_id=c.id, evaluator="A", raw={"per_step": []}),
        Score(case_id=c.id, final_score={"final_verdict": "PASS"}, kappa={"linear_weighted": 0.8}, verdict="PASS"),
        Report(case_id=c.id, kind="patient_ko", pdf_path="r.pdf", revision=1),
        Job(case_id=c.id, status="pending"),
    ])
    session.commit()
    assert session.query(Segmentation).filter_by(case_id=c.id).count() == 1


def test_write_audit(session):
    write_audit(session, "cloud_upload", detail={"frames": 12})
    session.commit()
    row = session.query(AuditLog).one()
    assert row.event == "cloud_upload"
    assert row.detail["frames"] == 12
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'camca_web.db'`

- [ ] **Step 3: db.py 구현**

```python
# src/camca_web/db.py
"""spec §3 Postgres 스키마 — SQLAlchemy 2.0 (테스트는 SQLite, JSON 타입 공용)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, DateTime, ForeignKey, Integer,
                        String, create_engine)
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship, sessionmaker)


def _now():
    return datetime.now(timezone.utc)


def _uuid():
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class Participant(Base):
    __tablename__ = "participants"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    research_code: Mapped[str] = mapped_column(String, unique=True)
    dob: Mapped[str] = mapped_column(String)  # YYYY-MM-DD — 링크 열람 본인확인용
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    cases: Mapped[list["Case"]] = relationship(back_populates="participant")


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    participant_id: Mapped[str] = mapped_column(ForeignKey("participants.id"))
    video_path: Mapped[str] = mapped_column(String)
    anonymized_path: Mapped[str | None] = mapped_column(String, nullable=True)
    device_type: Mapped[str] = mapped_column(String, default="pMDI")
    source: Mapped[str] = mapped_column(String, default="clinic")  # clinic|home
    view_angle: Mapped[str | None] = mapped_column(String, nullable=True)
    quality_flag: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="UPLOADED")
    needs_attention: Mapped[bool] = mapped_column(Boolean, default=False)
    attention_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    participant: Mapped[Participant] = relationship(back_populates="cases")


class Segmentation(Base):
    __tablename__ = "segmentations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    segments: Mapped[list] = mapped_column(JSON)
    events: Mapped[list] = mapped_column(JSON)
    engine: Mapped[str] = mapped_column(String, default="vlm-prompt")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class SegmentsCorrected(Base):
    """의사 수정 경계 — flywheel 학습 라벨 (spec §3, §5.3-1)."""
    __tablename__ = "segments_corrected"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    corrected_by: Mapped[str] = mapped_column(String)
    segments: Mapped[list] = mapped_column(JSON)
    diff: Mapped[list] = mapped_column(JSON)       # [{step_id, field, before, after}]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Evaluation(Base):
    """evaluator A/B/TB 원시 JSON — Step 2·3 연구 export (spec §3)."""
    __tablename__ = "evaluations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    evaluator: Mapped[str] = mapped_column(String)  # A|B|TB
    raw: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Score(Base):
    __tablename__ = "scores"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    final_score: Mapped[dict] = mapped_column(JSON)
    kappa: Mapped[dict] = mapped_column(JSON)
    verdict: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    kind: Mapped[str] = mapped_column(String)   # patient_ko|patient_en|clinician_ko|clinician_en
    pdf_path: Mapped[str] = mapped_column(String)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Job(Base):
    """pipeline/ 잡 큐 — 추후 독립 워커 분리 경계 (spec §2)."""
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id"))
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|running|done|failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    case_id: Mapped[str | None] = mapped_column(String, nullable=True)
    event: Mapped[str] = mapped_column(String)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


def make_engine(db_url: str):
    # sqlite in-memory는 커넥션 간 상태 공유를 위해 StaticPool 사용
    if db_url in ("sqlite://", "sqlite:///:memory:"):
        from sqlalchemy.pool import StaticPool
        return create_engine(db_url, connect_args={"check_same_thread": False},
                             poolclass=StaticPool)
    return create_engine(db_url)


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def write_audit(session, event: str, case_id: str | None = None,
                detail: dict | None = None) -> None:
    session.add(AuditLog(case_id=case_id, event=event, detail=detail))
```

- [ ] **Step 4: 테스트 통과 확인 + 앱 팩토리에 DB 배선**

Run: `.venv/bin/python -m pytest tests/test_db.py -v` → PASS (3 passed)

`src/camca_web/app.py`의 `create_app`에 추가 (health 엔드포인트 위):

```python
    from .db import make_engine, make_session_factory, init_db
    engine = make_engine(settings.db_url)
    init_db(engine)
    app.state.session_factory = make_session_factory(engine)
```

Run: `.venv/bin/python -m pytest tests/ -v` → 전체 PASS

- [ ] **Step 5: Commit**

```bash
git add camca-web/src/camca_web/db.py camca-web/src/camca_web/app.py camca-web/tests/test_db.py
git commit -m "feat(web): SQLAlchemy models for spec §3 schema + audit helper"
```

---

### Task 2: 케이스 상태 머신 + NEEDS_ATTENTION 규칙

**Files:**
- Create: `src/camca_web/state.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Produces: 상태 상수 `UPLOADED, QUALITY_CHECK, RETAKE_REQUESTED, ANALYZING, SCORED, REPORT_ISSUED, FAILED`; `can_transition(cur: str, new: str) -> bool`; `needs_attention_reasons(final_score: dict, kappa_stats: dict, segments: list[dict]) -> list[str]` (빈 리스트 = 정상).

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_state.py
"""spec §4 상태 머신 + NEEDS_ATTENTION 4조건 (순수 함수)."""
from camca_web.state import (
    UPLOADED, QUALITY_CHECK, RETAKE_REQUESTED, ANALYZING, SCORED,
    REPORT_ISSUED, FAILED, can_transition, needs_attention_reasons,
)

OK_SCORE = {"critical_error_override": {"critical_errors": []}}
OK_KAPPA = {"kappa": {"linear_weighted": 0.8}}
OK_SEGS = [{"step_id": f"S{i}", "observable": i in (1, 4, 5, 6, 7)} for i in range(1, 10)]


def test_happy_path_transitions():
    for a, b in [(UPLOADED, QUALITY_CHECK), (QUALITY_CHECK, ANALYZING),
                 (ANALYZING, SCORED), (SCORED, REPORT_ISSUED)]:
        assert can_transition(a, b)


def test_branch_transitions():
    assert can_transition(QUALITY_CHECK, RETAKE_REQUESTED)
    assert can_transition(ANALYZING, FAILED)
    assert can_transition(FAILED, ANALYZING)          # 원클릭 재실행
    assert not can_transition(UPLOADED, SCORED)       # 단계 건너뛰기 금지
    assert not can_transition(REPORT_ISSUED, UPLOADED)


def test_no_attention_when_all_ok():
    assert needs_attention_reasons(OK_SCORE, OK_KAPPA, OK_SEGS) == []


def test_attention_critical_error():
    score = {"critical_error_override": {"critical_errors": ["no_breath_hold"]}}
    assert "critical_error" in needs_attention_reasons(score, OK_KAPPA, OK_SEGS)


def test_attention_conflict_flag():
    segs = OK_SEGS[:4] + [dict(OK_SEGS[4], conflict_flagged=True)] + OK_SEGS[5:]
    assert "conflict_flagged" in needs_attention_reasons(OK_SCORE, OK_KAPPA, segs)


def test_attention_partial_data():
    segs = [{"step_id": f"S{i}", "observable": i == 5} for i in range(1, 10)]  # 8/9 미관측
    assert "partial_data" in needs_attention_reasons(OK_SCORE, OK_KAPPA, segs)


def test_attention_low_kappa():
    kappa = {"kappa": {"linear_weighted": 0.45}}
    assert "low_kappa" in needs_attention_reasons(OK_SCORE, kappa, OK_SEGS)
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: state.py 구현**

```python
# src/camca_web/state.py
"""spec §4 — 케이스 상태 머신과 NEEDS_ATTENTION 규칙. DB 미의존 순수 로직."""
from __future__ import annotations

UPLOADED = "UPLOADED"
QUALITY_CHECK = "QUALITY_CHECK"
RETAKE_REQUESTED = "RETAKE_REQUESTED"
ANALYZING = "ANALYZING"
SCORED = "SCORED"
REPORT_ISSUED = "REPORT_ISSUED"
FAILED = "FAILED"

_TRANSITIONS: dict[str, set[str]] = {
    UPLOADED: {QUALITY_CHECK},
    QUALITY_CHECK: {ANALYZING, RETAKE_REQUESTED},
    ANALYZING: {SCORED, FAILED},
    SCORED: {REPORT_ISSUED},
    FAILED: {ANALYZING},            # 스태프 원클릭 재실행
    RETAKE_REQUESTED: set(),        # 재촬영은 새 케이스로 업로드
    REPORT_ISSUED: set(),
}

KAPPA_ATTENTION_THRESHOLD = 0.6
PARTIAL_DATA_MIN_UNOBSERVED = 5     # 9단계 중 미관측 ≥ 5 → PARTIAL_DATA


def can_transition(cur: str, new: str) -> bool:
    return new in _TRANSITIONS.get(cur, set())


def needs_attention_reasons(final_score: dict, kappa_stats: dict,
                            segments: list[dict]) -> list[str]:
    """spec §4의 4조건 검사. 발행은 막지 않고 배지 사유만 반환."""
    reasons: list[str] = []
    crit = (final_score.get("critical_error_override") or {}).get("critical_errors") or []
    if len(crit) >= 1:
        reasons.append("critical_error")
    if any(s.get("conflict_flagged") for s in segments):
        reasons.append("conflict_flagged")
    unobserved = sum(1 for s in segments if not s.get("observable"))
    if unobserved >= PARTIAL_DATA_MIN_UNOBSERVED:
        reasons.append("partial_data")
    kappa = (kappa_stats.get("kappa") or {}).get("linear_weighted")
    if kappa is not None and kappa < KAPPA_ATTENTION_THRESHOLD:
        reasons.append("low_kappa")
    return reasons
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_state.py -v` → PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add camca-web/src/camca_web/state.py camca-web/tests/test_state.py
git commit -m "feat(web): case state machine + NEEDS_ATTENTION rules (spec §4)"
```

---

### Task 3: 인증 — 스태프 세션 + 환자 서명 링크

**Files:**
- Create: `src/camca_web/auth.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Produces: `hash_password(pw) -> str`, `verify_password(pw, hashed) -> bool`, `make_session_cookie(username, secret) -> str`, `read_session_cookie(value, secret) -> str | None`, `make_patient_token(case_id, secret) -> str`, `read_patient_token(token, secret, max_age_sec) -> str | None`(만료/변조 시 None), `dob_matches(input_dob, stored_dob) -> bool`.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_auth.py
"""스태프 계정(간단) + 환자 연구코드/서명링크/생년월일 (spec 결정표)."""
import time
import pytest
from camca_web.auth import (
    hash_password, verify_password, make_session_cookie, read_session_cookie,
    make_patient_token, read_patient_token, dob_matches,
)

SECRET = "test-secret"


def test_password_roundtrip():
    h = hash_password("s3cret")
    assert h != "s3cret"
    assert verify_password("s3cret", h)
    assert not verify_password("wrong", h)


def test_session_cookie_roundtrip_and_tamper():
    c = make_session_cookie("dr.kang", SECRET)
    assert read_session_cookie(c, SECRET) == "dr.kang"
    assert read_session_cookie(c + "x", SECRET) is None
    assert read_session_cookie(c, "other-secret") is None


def test_patient_token_roundtrip():
    t = make_patient_token("case-abc", SECRET)
    assert read_patient_token(t, SECRET, max_age_sec=60) == "case-abc"


def test_patient_token_expiry():
    t = make_patient_token("case-abc", SECRET)
    time.sleep(1.1)
    assert read_patient_token(t, SECRET, max_age_sec=1) is None


def test_dob_matches_formats():
    assert dob_matches("1980-01-01", "1980-01-01")
    assert dob_matches("19800101", "1980-01-01")   # 숫자만 입력해도 허용
    assert not dob_matches("1980-01-02", "1980-01-01")
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_auth.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: auth.py 구현**

```python
# src/camca_web/auth.py
"""인증 — 스태프: 서명 세션 쿠키. 환자: 만료되는 서명 링크 + 생년월일 확인.

회원가입 없음(spec). 외부 의존은 itsdangerous 하나로 최소화.
"""
from __future__ import annotations

import hashlib
import hmac
import os

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

_PBKDF2_ITER = 200_000


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, _PBKDF2_ITER)
    return salt.hex() + ":" + dk.hex()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        salt_hex, dk_hex = hashed.split(":")
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt_hex), _PBKDF2_ITER)
    return hmac.compare_digest(dk.hex(), dk_hex)


def _serializer(secret: str, salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret, salt=salt)


def make_session_cookie(username: str, secret: str) -> str:
    return _serializer(secret, "staff-session").dumps(username)


def read_session_cookie(value: str, secret: str,
                        max_age_sec: int = 12 * 3600) -> str | None:
    try:
        return _serializer(secret, "staff-session").loads(value, max_age=max_age_sec)
    except (BadSignature, SignatureExpired):
        return None


def make_patient_token(case_id: str, secret: str) -> str:
    return _serializer(secret, "patient-link").dumps(case_id)


def read_patient_token(token: str, secret: str, max_age_sec: int) -> str | None:
    try:
        return _serializer(secret, "patient-link").loads(token, max_age=max_age_sec)
    except (BadSignature, SignatureExpired):
        return None


def dob_matches(input_dob: str, stored_dob: str) -> bool:
    """입력 유연화: 숫자만 남겨 비교 (1980-01-01 == 19800101)."""
    digits = lambda s: "".join(ch for ch in s if ch.isdigit())
    return digits(input_dob) == digits(stored_dob) and len(digits(input_dob)) == 8
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_auth.py -v` → PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add camca-web/src/camca_web/auth.py camca-web/tests/test_auth.py
git commit -m "feat(web): staff session + expiring signed patient links + DOB check"
```

---

### Task 4: 스태프 업로드 라우트 (케이스 생성 + 잡 등록)

**Files:**
- Create: `src/camca_web/routes/staff.py`, `src/camca_web/templates/base.html`, `src/camca_web/templates/login.html`, `src/camca_web/templates/upload.html`
- Modify: `src/camca_web/app.py` (라우터/템플릿 배선)
- Test: `tests/test_upload.py`

**Interfaces:**
- Consumes: Task 1 모델, Task 3 `read_session_cookie/verify_password`.
- Produces: `POST /login`, `POST /upload` (multipart: video, research_code, dob, device_type, source) → Case(UPLOADED) + Job(pending) 생성, 파일은 `storage_root/cases/<case_id>/original.mp4`. `require_staff(request) -> str` 의존성.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_upload.py
"""업로드 → 케이스 생성 + 잡 등록 + 원본이 로컬 스토리지에만 저장."""
import io
from camca_web.db import Participant, Case, Job
from camca_web.auth import hash_password


def _login(client, settings):
    # 테스트용 스태프 계정을 앱 상태에 시드
    client.app.state.staff_accounts = {"staff": hash_password("pw")}
    r = client.post("/login", data={"username": "staff", "password": "pw"},
                    follow_redirects=False)
    assert r.status_code in (302, 303)
    return r.cookies


def test_upload_requires_login(client):
    r = client.post("/upload", files={"video": ("v.mp4", b"xx", "video/mp4")},
                    data={"research_code": "RC-1", "dob": "1980-01-01"},
                    follow_redirects=False)
    assert r.status_code in (302, 303, 401)


def test_upload_creates_case_and_job(client, settings):
    cookies = _login(client, settings)
    r = client.post(
        "/upload",
        files={"video": ("v.mp4", io.BytesIO(b"fake-mp4-bytes"), "video/mp4")},
        data={"research_code": "RC-1", "dob": "1980-01-01",
              "device_type": "pMDI", "source": "clinic"},
        cookies=cookies,
    )
    assert r.status_code == 200
    with client.app.state.session_factory() as s:
        case = s.query(Case).one()
        assert case.status == "UPLOADED"
        job = s.query(Job).filter_by(case_id=case.id).one()
        assert job.status == "pending"
        p = s.query(Participant).filter_by(research_code="RC-1").one()
        assert case.participant_id == p.id
    saved = settings.storage_root / "cases" / case.id / "original.mp4"
    assert saved.read_bytes() == b"fake-mp4-bytes"


def test_upload_reuses_existing_participant(client, settings):
    cookies = _login(client, settings)
    for _ in range(2):
        client.post(
            "/upload",
            files={"video": ("v.mp4", io.BytesIO(b"x"), "video/mp4")},
            data={"research_code": "RC-9", "dob": "1990-09-09"},
            cookies=cookies,
        )
    with client.app.state.session_factory() as s:
        assert s.query(Participant).filter_by(research_code="RC-9").count() == 1
        assert s.query(Case).count() == 2
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_upload.py -v`
Expected: FAIL — 404 (라우트 없음)

- [ ] **Step 3: 템플릿 + 라우트 구현**

```html
<!-- src/camca_web/templates/base.html -->
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1"><!-- 모바일 우선 (spec §7) -->
  <title>{% block title %}CAMCA{% endblock %}</title>
  <script src="/static/htmx.min.js"></script>
  <style>
    body{font-family:sans-serif;max-width:960px;margin:0 auto;padding:1rem}
    .badge{background:#c0392b;color:#fff;border-radius:4px;padding:2px 6px;font-size:.8em}
    table{border-collapse:collapse;width:100%} td,th{border:1px solid #ccc;padding:6px}
  </style>
</head>
<body>{% block content %}{% endblock %}</body>
</html>
```

```html
<!-- src/camca_web/templates/login.html -->
{% extends "base.html" %}
{% block content %}
<h1>CAMCA 스태프 로그인</h1>
<form method="post" action="/login">
  <input name="username" placeholder="아이디" required>
  <input name="password" type="password" placeholder="비밀번호" required>
  <button>로그인</button>
</form>
{% endblock %}
```

```html
<!-- src/camca_web/templates/upload.html -->
{% extends "base.html" %}
{% block content %}
<h1>영상 업로드</h1>
{% if case_id %}<p>업로드 완료 — 케이스 <code>{{ case_id }}</code> 분석 대기열에 등록됨.</p>{% endif %}
<form method="post" action="/upload" enctype="multipart/form-data">
  <input name="research_code" placeholder="연구코드 (예: RC-001)" required>
  <input name="dob" placeholder="생년월일 YYYY-MM-DD" required>
  <select name="device_type">
    <option>pMDI</option><option>pMDI-AIM-simulator</option>
    <option>pMDI-spacer</option><option>DPI-turbuhaler</option>
  </select>
  <select name="source"><option>clinic</option><option>home</option></select>
  <input name="video" type="file" accept="video/*" required>
  <button>업로드</button>
</form>
{% endblock %}
```

```python
# src/camca_web/routes/staff.py
"""스태프용 라우트 — 로그인, 업로드 (원본은 로컬 스토리지에만 저장)."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse

from ..auth import make_session_cookie, read_session_cookie, verify_password
from ..db import Case, Job, Participant, write_audit

router = APIRouter()


def require_staff(request: Request) -> str:
    user = read_session_cookie(request.cookies.get("camca_session", ""),
                               request.app.state.settings.secret_key)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


@router.get("/login")
def login_form(request: Request):
    return request.app.state.templates.TemplateResponse(
        request, "login.html", {})


@router.post("/login")
def login(request: Request, username: str = Form(), password: str = Form()):
    accounts = getattr(request.app.state, "staff_accounts", {})
    hashed = accounts.get(username)
    if not hashed or not verify_password(password, hashed):
        raise HTTPException(status_code=401, detail="invalid credentials")
    resp = RedirectResponse("/upload", status_code=303)
    resp.set_cookie("camca_session",
                    make_session_cookie(username, request.app.state.settings.secret_key),
                    httponly=True)
    return resp


@router.get("/upload")
def upload_form(request: Request):
    require_staff(request)
    return request.app.state.templates.TemplateResponse(
        request, "upload.html", {"case_id": None})


@router.post("/upload")
async def upload(request: Request, video: UploadFile,
                 research_code: str = Form(), dob: str = Form(),
                 device_type: str = Form("pMDI"), source: str = Form("clinic")):
    user = require_staff(request)
    settings = request.app.state.settings
    with request.app.state.session_factory() as s:
        participant = s.query(Participant).filter_by(research_code=research_code).first()
        if participant is None:
            participant = Participant(research_code=research_code, dob=dob)
            s.add(participant)
            s.flush()
        case = Case(participant_id=participant.id, video_path="", 
                    device_type=device_type, source=source, status="UPLOADED")
        s.add(case)
        s.flush()
        case_dir = Path(settings.storage_root) / "cases" / case.id
        case_dir.mkdir(parents=True, exist_ok=True)
        dest = case_dir / "original.mp4"
        dest.write_bytes(await video.read())
        case.video_path = str(dest)
        s.add(Job(case_id=case.id, status="pending"))
        write_audit(s, "case_uploaded", case_id=case.id,
                    detail={"by": user, "source": source})
        s.commit()
        case_id = case.id
    return request.app.state.templates.TemplateResponse(
        request, "upload.html", {"case_id": case_id})
```

`src/camca_web/app.py`의 `create_app`에 배선 추가 (session_factory 아래):

```python
    from fastapi.templating import Jinja2Templates
    app.state.templates = Jinja2Templates(directory=TEMPLATE_DIR)
    app.state.staff_accounts = {}   # 운영: 환경변수/CLI로 시드. 테스트: 직접 주입.

    from .routes.staff import router as staff_router
    app.include_router(staff_router)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_upload.py tests/ -v` → 전체 PASS

- [ ] **Step 5: Commit**

```bash
git add camca-web/src/camca_web/ camca-web/tests/test_upload.py
git commit -m "feat(web): staff login + video upload creating case and pipeline job"
```

---

### Task 5: 잡 큐 + 백그라운드 워커 + FAILED 재실행

**Files:**
- Create: `src/camca_web/jobs.py`
- Modify: `src/camca_web/routes/staff.py` (재실행 라우트)
- Test: `tests/test_jobs.py`

**Interfaces:**
- Consumes: Task 1 `Job`, Task 2 상태 상수.
- Produces: `run_pending_once(session_factory, processor: Callable[[str], None], max_attempts=3) -> int`(처리 건수), `start_worker(session_factory, processor, interval_sec=2.0) -> threading.Thread`, `POST /cases/{case_id}/rerun`. `processor(case_id)`는 Task 8의 `process_case`가 담당 — 여기서는 주입만.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_jobs.py
"""DB-backed 잡 큐 — 실행/실패 기록/재시도 상한/원클릭 재실행."""
import pytest
from camca_web.db import (make_engine, make_session_factory, init_db,
                          Participant, Case, Job)
from camca_web.jobs import run_pending_once


@pytest.fixture
def sf():
    engine = make_engine("sqlite://")
    init_db(engine)
    factory = make_session_factory(engine)
    with factory() as s:
        p = Participant(research_code="RC-J", dob="1980-01-01")
        s.add(p); s.flush()
        c = Case(id="case-j", participant_id=p.id, video_path="v.mp4",
                 device_type="pMDI", source="clinic", status="UPLOADED")
        s.add(c)
        s.add(Job(id="job-1", case_id="case-j", status="pending"))
        s.commit()
    return factory


def test_run_pending_calls_processor_and_marks_done(sf):
    seen = []
    n = run_pending_once(sf, processor=seen.append)
    assert n == 1
    assert seen == ["case-j"]
    with sf() as s:
        assert s.get(Job, "job-1").status == "done"


def test_processor_error_marks_failed_and_records_error(sf):
    def boom(case_id):
        raise RuntimeError("pipeline exploded")
    run_pending_once(sf, processor=boom)
    with sf() as s:
        job = s.get(Job, "job-1")
        assert job.status == "failed"
        assert "pipeline exploded" in job.error
        assert job.attempts == 1


def test_failed_job_not_retried_automatically(sf):
    def boom(case_id):
        raise RuntimeError("x")
    run_pending_once(sf, processor=boom)
    assert run_pending_once(sf, processor=boom) == 0   # failed는 자동 재시도 안 함


def test_rerun_endpoint_requeues(client, settings):
    from camca_web.auth import hash_password
    client.app.state.staff_accounts = {"staff": hash_password("pw")}
    cookies = client.post("/login", data={"username": "staff", "password": "pw"},
                          follow_redirects=False).cookies
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-R", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-r", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="FAILED"))
        s.add(Job(id="job-r", case_id="case-r", status="failed", attempts=1, error="x"))
        s.commit()
    r = client.post("/cases/case-r/rerun", cookies=cookies)
    assert r.status_code == 200
    with client.app.state.session_factory() as s:
        assert s.get(Job, "job-r").status == "pending"
        assert s.get(Case, "case-r").status == "ANALYZING"
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_jobs.py -v`
Expected: FAIL — `ModuleNotFoundError` / 404

- [ ] **Step 3: jobs.py 구현**

```python
# src/camca_web/jobs.py
"""pipeline/ 잡 큐 — DB polling 워커. 추후 독립 워커 프로세스로 분리 가능한 경계.

자동 재시도는 하지 않는다: FAILED는 스태프 원클릭 재실행(spec §4)으로만 재개.
"""
from __future__ import annotations

import threading
import time
import traceback
from typing import Callable

from .db import Job, write_audit


def run_pending_once(session_factory, processor: Callable[[str], None],
                     max_attempts: int = 3) -> int:
    """pending 잡을 순서대로 1패스 처리. 처리한 잡 수를 반환 (테스트/워커 공용)."""
    processed = 0
    with session_factory() as s:
        pending = (s.query(Job).filter_by(status="pending")
                   .order_by(Job.created_at).all())
        job_ids = [j.id for j in pending]
    for job_id in job_ids:
        with session_factory() as s:
            job = s.get(Job, job_id)
            if job is None or job.status != "pending" or job.attempts >= max_attempts:
                continue
            job.status = "running"
            job.attempts += 1
            s.commit()
            case_id = job.case_id
        try:
            processor(case_id)
        except Exception as e:
            with session_factory() as s:
                job = s.get(Job, job_id)
                job.status = "failed"
                job.error = f"{e}\n{traceback.format_exc()[-1500:]}"
                write_audit(s, "job_failed", case_id=case_id, detail={"error": str(e)})
                s.commit()
        else:
            with session_factory() as s:
                job = s.get(Job, job_id)
                job.status = "done"
                s.commit()
        processed += 1
    return processed


def start_worker(session_factory, processor: Callable[[str], None],
                 interval_sec: float = 2.0) -> threading.Thread:
    """백그라운드 폴링 워커 (daemon). 운영 진입점에서만 시작 — 테스트는 run_pending_once."""
    def loop():
        while True:
            try:
                run_pending_once(session_factory, processor)
            except Exception:
                traceback.print_exc()
            time.sleep(interval_sec)

    t = threading.Thread(target=loop, daemon=True, name="camca-job-worker")
    t.start()
    return t
```

`src/camca_web/routes/staff.py` 끝에 재실행 라우트 추가:

```python
@router.post("/cases/{case_id}/rerun")
def rerun(request: Request, case_id: str):
    user = require_staff(request)
    with request.app.state.session_factory() as s:
        case = s.get(Case, case_id)
        if case is None:
            raise HTTPException(404)
        job = (s.query(Job).filter_by(case_id=case_id)
               .order_by(Job.created_at.desc()).first())
        if job is None:
            job = Job(case_id=case_id)
            s.add(job)
        job.status = "pending"
        job.error = None
        case.status = "ANALYZING" if case.status == "FAILED" else case.status
        write_audit(s, "case_rerun", case_id=case_id, detail={"by": user})
        s.commit()
    return {"ok": True, "case_id": case_id}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_jobs.py tests/ -v` → 전체 PASS

- [ ] **Step 5: Commit**

```bash
git add camca-web/src/camca_web/jobs.py camca-web/src/camca_web/routes/staff.py camca-web/tests/test_jobs.py
git commit -m "feat(web): DB-backed job queue with worker thread and one-click rerun"
```

---

### Task 6: Quality gate — 사전검사 (L6 차단)

**Files:**
- Create: `src/camca_web/quality_gate.py`
- Test: `tests/test_quality_gate.py`

**Interfaces:**
- Consumes: camca-py `classify_view_angle(telemetry_stream)`.
- Produces: `QualityResult(passed: bool, view: str, face_detection_rate: float, vlm_weight_up: bool, reasons: list[str])`, `evaluate_quality(telemetry_stream: list[dict]) -> QualityResult` (순수 — telemetry는 호출자가 추출).

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_quality_gate.py
"""업로드 직후 사전검사 — 부적합 즉시 재촬영 안내 (spec §2 quality_gate)."""
from camca_web.quality_gate import evaluate_quality


def _stream(n, lip=20.0, face_detected=True):
    """합성 telemetry — lip_distance_px>0이면 얼굴 검출로 간주."""
    return [{"timestamp_ms": i * 100,
             "lip_distance_px": lip if face_detected else 0.0,
             "head_pitch_deg": 0.0} for i in range(n)]


def test_frontal_video_passes():
    r = evaluate_quality(_stream(100))
    assert r.passed is True
    assert r.reasons == []


def test_no_face_fails_with_reason():
    r = evaluate_quality(_stream(100, face_detected=False))
    assert r.passed is False
    assert "face_not_detected" in r.reasons


def test_empty_telemetry_fails():
    r = evaluate_quality([])
    assert r.passed is False
    assert "no_telemetry" in r.reasons


def test_partial_detection_passes_with_vlm_weight_up():
    """측면 등 검출률 낮음 → 차단하지 않되 Stage 2 VLM 가중 상향 (spec §5.3-2)."""
    stream = _stream(60) + _stream(40, face_detected=False)
    r = evaluate_quality(stream)
    assert r.passed is True
    assert r.vlm_weight_up is True
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_quality_gate.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: quality_gate.py 구현**

```python
# src/camca_web/quality_gate.py
"""업로드 직후 사전검사 — camca-py view_angle 분류를 재사용해 L6를 촬영 시점에 차단.

정책:
  - face_detection_rate < 0.3 또는 back_or_unknown → 재촬영 (passed=False)
  - 0.3 ≤ rate < 0.8 (oblique/lateral) → 통과하되 vlm_weight_up=True (spec §5.3-2)
  - 그 외 → 통과
"""
from __future__ import annotations

from dataclasses import dataclass, field

from camca.telemetry.view_angle import classify_view_angle

FACE_RATE_FAIL_BELOW = 0.3
FACE_RATE_VLM_WEIGHT_BELOW = 0.8


@dataclass
class QualityResult:
    passed: bool
    view: str
    face_detection_rate: float
    vlm_weight_up: bool = False
    reasons: list[str] = field(default_factory=list)


def evaluate_quality(telemetry_stream: list[dict]) -> QualityResult:
    if not telemetry_stream:
        return QualityResult(passed=False, view="unknown", face_detection_rate=0.0,
                             reasons=["no_telemetry"])
    cls = classify_view_angle(telemetry_stream)
    reasons: list[str] = []
    if cls.face_detection_rate < FACE_RATE_FAIL_BELOW or \
            cls.primary_view == "back_or_unknown":
        reasons.append("face_not_detected")
        return QualityResult(passed=False, view=cls.primary_view,
                             face_detection_rate=cls.face_detection_rate,
                             reasons=reasons)
    weight_up = cls.face_detection_rate < FACE_RATE_VLM_WEIGHT_BELOW
    return QualityResult(passed=True, view=cls.primary_view,
                         face_detection_rate=cls.face_detection_rate,
                         vlm_weight_up=weight_up, reasons=reasons)
```

**주의**: `classify_view_angle`은 `lip_distance_px == 0.0`을 얼굴 미검출로 계산한다 — 합성 테스트가 실패하면 camca-py의 실제 판정 로직(`view_angle.py:53` docstring의 휴리스틱)에 맞게 **테스트 합성 데이터 쪽**을 조정한다 (분류기 로직은 camca-py 소관이므로 여기서 고치지 않는다).

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_quality_gate.py -v` → PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add camca-web/src/camca_web/quality_gate.py camca-web/tests/test_quality_gate.py
git commit -m "feat(web): pre-analysis quality gate reusing view-angle classifier"
```

---

### Task 7: Anonymizer — 얼굴 블러 (PIPA 경계)

**Files:**
- Create: `src/camca_web/anonymizer.py`
- Test: `tests/test_anonymizer.py`

**Interfaces:**
- Produces: `AnonymizeResult(output_path: Path, total_frames: int, blurred_frames: int)`, `anonymize_video(src: Path, dst: Path, face_detector=None) -> AnonymizeResult`. `face_detector(frame_rgb) -> list[tuple[x, y, w, h]]` 시그니처로 주입 가능 (기본: MediaPipe FaceDetection).

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_anonymizer.py
"""클라우드 전송 전 얼굴 블러 — detector 주입으로 mediapipe 없이 검증."""
import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")
from camca_web.anonymizer import anonymize_video


@pytest.fixture
def tiny_video(tmp_path):
    """8프레임 64x64 합성 영상 — 중앙에 밝은 사각형(가짜 얼굴)."""
    path = tmp_path / "src.mp4"
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 4, (64, 64))
    for _ in range(8):
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        frame[16:48, 16:48] = 255
        w.write(frame)
    w.release()
    return path


def fake_detector(frame_rgb):
    return [(16, 16, 32, 32)]


def test_anonymize_blurs_face_region(tiny_video, tmp_path):
    dst = tmp_path / "anon.mp4"
    result = anonymize_video(tiny_video, dst, face_detector=fake_detector)
    assert dst.exists()
    assert result.total_frames == 8
    assert result.blurred_frames == 8
    cap = cv2.VideoCapture(str(dst))
    ok, frame = cap.read()
    cap.release()
    assert ok
    # 블러 후 얼굴 영역은 원본(전부 255)보다 분산이 생기고 경계가 흐려짐
    face = frame[20:44, 20:44]
    assert float(face.std()) > 0.0 or int(face.mean()) < 255


def test_no_detection_counts_zero_blur(tiny_video, tmp_path):
    result = anonymize_video(tiny_video, tmp_path / "anon2.mp4",
                             face_detector=lambda f: [])
    assert result.total_frames == 8
    assert result.blurred_frames == 0
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_anonymizer.py -v`
Expected: FAIL — `ModuleNotFoundError` (cv2 미설치 환경이면 SKIP — 그 경우 `pip install opencv-python` 후 재실행)

- [ ] **Step 3: anonymizer.py 구현**

```python
# src/camca_web/anonymizer.py
"""PIPA 방어 경계 — 원본은 로컬에만, 클라우드에는 이 모듈의 산출물만 나간다.

MediaPipe FaceDetection으로 얼굴 bbox를 찾아 가우시안 블러. detector는
주입 가능해 CI에서는 mediapipe 없이 fake detector로 검증한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

Detector = Callable[["object"], list[tuple[int, int, int, int]]]


@dataclass
class AnonymizeResult:
    output_path: Path
    total_frames: int
    blurred_frames: int


def _mediapipe_detector() -> Detector:
    import mediapipe as mp
    fd = mp.solutions.face_detection.FaceDetection(model_selection=1,
                                                   min_detection_confidence=0.4)

    def detect(frame_rgb):
        res = fd.process(frame_rgb)
        boxes = []
        if res.detections:
            h, w = frame_rgb.shape[:2]
            for d in res.detections:
                bb = d.location_data.relative_bounding_box
                boxes.append((int(bb.xmin * w), int(bb.ymin * h),
                              int(bb.width * w), int(bb.height * h)))
        return boxes

    return detect


def anonymize_video(src: Path | str, dst: Path | str,
                    face_detector: Detector | None = None) -> AnonymizeResult:
    import cv2

    detector = face_detector or _mediapipe_detector()
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    out = cv2.VideoWriter(str(dst), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    total = blurred = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        total += 1
        boxes = detector(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if boxes:
            blurred += 1
            for (x, y, bw, bh) in boxes:
                # 여유 마진 20% — bbox가 얼굴보다 작게 잡히는 경우 대비
                mx, my = int(bw * 0.2), int(bh * 0.2)
                x0, y0 = max(0, x - mx), max(0, y - my)
                x1, y1 = min(w, x + bw + mx), min(h, y + bh + my)
                if x1 > x0 and y1 > y0:
                    roi = frame[y0:y1, x0:x1]
                    frame[y0:y1, x0:x1] = cv2.GaussianBlur(roi, (51, 51), 30)
        out.write(frame)
    cap.release()
    out.release()
    return AnonymizeResult(output_path=Path(dst), total_frames=total,
                           blurred_frames=blurred)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_anonymizer.py -v` → PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add camca-web/src/camca_web/anonymizer.py camca-web/tests/test_anonymizer.py
git commit -m "feat(web): face-blur anonymizer as PIPA boundary (injectable detector)"
```

---

### Task 8: Runner — 케이스 1건 처리 오케스트레이션

**Files:**
- Create: `src/camca_web/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: Task 1 모델/`write_audit`, Task 2 상태·`needs_attention_reasons`, Task 6 `evaluate_quality`, Task 7 `anonymize_video`, Task 9의 `issue_reports`(이 태스크에서는 주입된 no-op).
- Produces: `RunnerDeps(telemetry_fn, quality_fn, anonymize_fn, pipeline_factory, issue_fn)`, `process_case(case_id: str, session_factory, settings, deps: RunnerDeps) -> None`. `pipeline_factory(case_dir, use_phase_engine) -> pipeline` 이고 pipeline은 `run_from_video(video_path, case_id) -> PipelineResult` 인터페이스만 요구.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_runner.py
"""process_case — 상태 전이·산출물 저장·NEEDS_ATTENTION·클라우드 경계를 mock으로 검증."""
from types import SimpleNamespace
import pytest

from camca_web.config import Settings
from camca_web.db import (make_engine, make_session_factory, init_db, AuditLog,
                          Participant, Case, Segmentation, Evaluation, Score)
from camca_web.quality_gate import QualityResult
from camca_web.runner import RunnerDeps, process_case


@pytest.fixture
def env(tmp_path):
    engine = make_engine("sqlite://")
    init_db(engine)
    sf = make_session_factory(engine)
    video = tmp_path / "original.mp4"
    video.write_bytes(b"fake")
    with sf() as s:
        p = Participant(research_code="RC-P", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-p", participant_id=p.id, video_path=str(video),
                   device_type="pMDI", source="clinic", status="UPLOADED"))
        s.commit()
    return sf, Settings(db_url="sqlite://", storage_root=tmp_path, secret_key="t")


def _fake_result(critical=(), kappa=0.8, conflict=False):
    segs = [{"step_id": f"S{i}", "observable": True,
             **({"conflict_flagged": True} if conflict and i == 5 else {})}
            for i in range(1, 10)]
    return SimpleNamespace(
        device_id={"device_type": "pMDI"},
        segments={"segments": segs, "events": [], "engine": "telemetry-anchored-v1"},
        evaluator_a={"per_step": ["a"]}, evaluator_b={"per_step": ["b"]},
        tie_breaker=None,
        kappa_stats={"kappa": {"linear_weighted": kappa}},
        final_score={"final_verdict": "PASS",
                     "critical_error_override": {"critical_errors": list(critical)}},
        metadata={},
    )


def _deps(result, quality=None, issued=None, anonymized_calls=None):
    def pipeline_factory(case_dir, use_phase_engine):
        return SimpleNamespace(run_from_video=lambda video_path, case_id: result)
    return RunnerDeps(
        telemetry_fn=lambda video_path: [{"timestamp_ms": 0, "lip_distance_px": 20.0}],
        quality_fn=lambda stream: quality or QualityResult(
            passed=True, view="frontal", face_detection_rate=0.95),
        anonymize_fn=lambda src, dst: (anonymized_calls is not None
                                        and anonymized_calls.append((src, dst))) or
                                       SimpleNamespace(output_path=dst,
                                                       total_frames=1, blurred_frames=1),
        pipeline_factory=pipeline_factory,
        issue_fn=lambda session, case, result_dict, settings: (issued is not None
                                                               and issued.append(case.id)),
    )


def test_happy_path_reaches_report_issued(env):
    sf, settings = env
    issued = []
    process_case("case-p", sf, settings, _deps(_fake_result(), issued=issued))
    with sf() as s:
        case = s.get(Case, "case-p")
        assert case.status == "REPORT_ISSUED"
        assert case.needs_attention is False
        assert s.query(Segmentation).filter_by(case_id="case-p").count() == 1
        assert s.query(Evaluation).filter_by(case_id="case-p").count() == 2  # A, B
        assert s.query(Score).filter_by(case_id="case-p").count() == 1
    assert issued == ["case-p"]


def test_pipeline_receives_anonymized_video_not_original(env):
    """PIPA 경계: 파이프라인 입력은 익명화 산출물이어야 한다."""
    sf, settings = env
    calls = []
    seen_paths = []
    deps = _deps(_fake_result(), anonymized_calls=calls)
    orig_factory = deps.pipeline_factory
    def spy_factory(case_dir, use_phase_engine):
        p = orig_factory(case_dir, use_phase_engine)
        inner = p.run_from_video
        p.run_from_video = lambda video_path, case_id: (
            seen_paths.append(str(video_path)) or inner(video_path, case_id))
        return p
    deps.pipeline_factory = spy_factory
    process_case("case-p", sf, settings, deps)
    assert len(calls) == 1                       # 익명화 1회 수행
    assert "anonymized" in seen_paths[0]         # 원본이 아닌 익명화본 전달
    with sf() as s:                              # 클라우드 전송 audit 기록
        events = [a.event for a in s.query(AuditLog).all()]
        assert "cloud_dispatch" in events


def test_quality_fail_stops_at_retake(env):
    sf, settings = env
    bad = QualityResult(passed=False, view="back_or_unknown",
                        face_detection_rate=0.1, reasons=["face_not_detected"])
    issued = []
    process_case("case-p", sf, settings, _deps(_fake_result(), quality=bad, issued=issued))
    with sf() as s:
        case = s.get(Case, "case-p")
        assert case.status == "RETAKE_REQUESTED"
        assert case.quality_flag == "face_not_detected"
    assert issued == []                          # 발행 안 함


def test_needs_attention_badge_does_not_block_issue(env):
    """spec §4: critical error가 있어도 발행은 진행 + 배지."""
    sf, settings = env
    issued = []
    process_case("case-p", sf, settings,
                 _deps(_fake_result(critical=["no_breath_hold"], kappa=0.4),
                       issued=issued))
    with sf() as s:
        case = s.get(Case, "case-p")
        assert case.status == "REPORT_ISSUED"
        assert case.needs_attention is True
        assert set(case.attention_reasons) >= {"critical_error", "low_kappa"}
    assert issued == ["case-p"]
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_runner.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: runner.py 구현**

```python
# src/camca_web/runner.py
"""케이스 1건 처리 — 상태 머신을 구동하는 유일한 곳.

QUALITY_CHECK → (부적합) RETAKE_REQUESTED
             → 익명화 → ANALYZING(파이프라인) → 저장 → SCORED → 발행 → REPORT_ISSUED
예외는 잡 큐(jobs.py)가 받아 FAILED 처리하므로 여기서는 그대로 올린다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .config import Settings
from .db import Case, Evaluation, Score, Segmentation, write_audit
from .quality_gate import QualityResult
from .state import (ANALYZING, QUALITY_CHECK, REPORT_ISSUED, RETAKE_REQUESTED,
                    SCORED, needs_attention_reasons)


@dataclass
class RunnerDeps:
    """전 외부 의존 주입점 — CI는 전부 mock, 운영은 build_default_deps()."""
    telemetry_fn: Callable[[str], list[dict]]
    quality_fn: Callable[[list[dict]], QualityResult]
    anonymize_fn: Callable[[Path, Path], Any]
    pipeline_factory: Callable[[Path, bool], Any]   # (case_dir, use_phase_engine)
    issue_fn: Callable[..., Any]                     # (session, case, result_dict, settings)


def process_case(case_id: str, session_factory, settings: Settings,
                 deps: RunnerDeps) -> None:
    with session_factory() as s:
        case = s.get(Case, case_id)
        if case is None:
            raise ValueError(f"unknown case: {case_id}")
        case.status = QUALITY_CHECK
        s.commit()
        video_path = case.video_path
        device_type = case.device_type

    # 1) Quality gate (spec §2 quality_gate — L6 차단)
    telemetry = deps.telemetry_fn(video_path)
    quality = deps.quality_fn(telemetry)
    with session_factory() as s:
        case = s.get(Case, case_id)
        case.view_angle = quality.view
        if not quality.passed:
            case.status = RETAKE_REQUESTED
            case.quality_flag = ",".join(quality.reasons)
            write_audit(s, "retake_requested", case_id=case_id,
                        detail={"reasons": quality.reasons})
            s.commit()
            return
        if quality.vlm_weight_up:
            case.quality_flag = "vlm_weight_up"
        s.commit()

    # 2) 익명화 — 클라우드로 나가는 유일한 산출물 (PIPA 경계)
    case_dir = Path(settings.storage_root) / "cases" / case_id
    anon_path = case_dir / "anonymized.mp4"
    deps.anonymize_fn(Path(video_path), anon_path)
    with session_factory() as s:
        case = s.get(Case, case_id)
        case.anonymized_path = str(anon_path)
        case.status = ANALYZING
        write_audit(s, "cloud_dispatch", case_id=case_id,
                    detail={"artifact": str(anon_path)})
        s.commit()

    # 3) camca-py 파이프라인 (익명화본만 전달)
    pipeline = deps.pipeline_factory(case_dir, True)
    result = pipeline.run_from_video(anon_path, case_id=case_id)

    # 4) 산출물 저장 + NEEDS_ATTENTION 판정 (spec §3, §4)
    segments = (result.segments or {}).get("segments", [])
    reasons = needs_attention_reasons(result.final_score, result.kappa_stats, segments)
    with session_factory() as s:
        case = s.get(Case, case_id)
        s.add(Segmentation(case_id=case_id, segments=segments,
                           events=(result.segments or {}).get("events", []),
                           engine=(result.segments or {}).get("engine", "vlm-prompt")))
        s.add(Evaluation(case_id=case_id, evaluator="A", raw=result.evaluator_a))
        s.add(Evaluation(case_id=case_id, evaluator="B", raw=result.evaluator_b))
        if result.tie_breaker:
            s.add(Evaluation(case_id=case_id, evaluator="TB", raw=result.tie_breaker))
        s.add(Score(case_id=case_id, final_score=result.final_score,
                    kappa=result.kappa_stats,
                    verdict=result.final_score.get("final_verdict", "UNKNOWN")))
        case.status = SCORED
        case.needs_attention = bool(reasons)
        case.attention_reasons = reasons
        s.commit()

    # 5) 자동 발행 — NEEDS_ATTENTION이어도 막지 않는다 (spec §4)
    with session_factory() as s:
        case = s.get(Case, case_id)
        deps.issue_fn(s, case, result, settings)
        case.status = REPORT_ISSUED
        write_audit(s, "report_issued", case_id=case_id,
                    detail={"needs_attention": case.needs_attention})
        s.commit()


def build_default_deps() -> RunnerDeps:
    """운영 배선 — VLM/MediaPipe 실의존. 테스트에서는 사용하지 않는다."""
    from camca.backends import create_backend
    from camca.pipeline import MultiModelPipeline, PersonaConfig
    from camca.telemetry import extract_telemetry
    from .anonymizer import anonymize_video
    from .quality_gate import evaluate_quality
    from .reports_web import issue_reports

    def pipeline_factory(case_dir: Path, use_phase_engine: bool):
        return MultiModelPipeline(
            device_id_backend=create_backend("claude:sonnet"),
            segmenter_backend=create_backend("claude:sonnet"),
            evaluator_a=PersonaConfig("evaluator-a", "GINA-strict",
                                      create_backend("claude:opus")),
            evaluator_b=PersonaConfig("evaluator-b", "real-world-pragmatic",
                                      create_backend("gemini:pro")),
            case_dir=case_dir,
            use_phase_engine=use_phase_engine,
        )

    return RunnerDeps(
        telemetry_fn=extract_telemetry,
        quality_fn=evaluate_quality,
        anonymize_fn=anonymize_video,
        pipeline_factory=pipeline_factory,
        issue_fn=issue_reports,
    )
```

**주의**: 이 시점에는 `reports_web.issue_reports`가 아직 없다(Task 9). `build_default_deps`는 함수 내부 지연 import이므로 테스트 수집은 통과한다 — Task 9 완료 전에 운영 배선을 호출하지 말 것.

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_runner.py tests/ -v` → 전체 PASS

- [ ] **Step 5: Commit**

```bash
git add camca-web/src/camca_web/runner.py camca-web/tests/test_runner.py
git commit -m "feat(web): process_case orchestration with PIPA boundary and auto-issue"
```

---

### Task 9: 리포트 발행 + 환자 열람 페이지

**Files:**
- Create: `src/camca_web/reports_web.py`, `src/camca_web/routes/patient.py`
- Create: `src/camca_web/templates/patient_verify.html`, `src/camca_web/templates/patient_report.html`
- Modify: `src/camca_web/app.py` (patient 라우터 배선)
- Test: `tests/test_reports_web.py`

**Interfaces:**
- Consumes: camca-py `build_bilingual_reports`, `cli._build_patient_content/_build_clinician_content`; Task 3 `make_patient_token/read_patient_token/dob_matches`.
- Produces: `issue_reports(session, case, result, settings, revision=1) -> list[Report]`; `patient_link(case_id, settings) -> str` ("/r/{token}"); 라우트 `GET /r/{token}`(생년월일 폼) / `POST /r/{token}`(확인 후 리포트 뷰 + 열람 audit) / `GET /r/{token}/pdf/{kind}`.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_reports_web.py
"""자동 발행(PDF 4종 + reports 행) + 서명 링크 열람 (생년월일 확인, 열람 로그)."""
from types import SimpleNamespace
import pytest

from camca_web.auth import make_patient_token
from camca_web.db import Participant, Case, Report, AuditLog


def _result():
    return SimpleNamespace(
        device_id={"device_type": "pMDI"},
        segments={"segments": [], "events": []},
        evaluator_a={}, evaluator_b={}, tie_breaker=None,
        kappa_stats={"kappa": {"linear_weighted": 0.8,
                               "interpretation_linear": "substantial"},
                     "critical_error_consensus": {"both_flagged": []},
                     "per_step_agreement": []},
        final_score={"final_verdict": "PASS",
                     "per_step_levels": {},
                     "score_components": {"core_steps_total": 8, "core_steps_max": 10,
                                          "core_steps_percent": 80.0},
                     "critical_error_override": {"critical_errors": []}},
        metadata={"started_at": "2026-07-07T00:00:00", "stages": []},
    )


@pytest.fixture
def seeded_case(client, settings):
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-PT", dob="1980-01-01")
        s.add(p); s.flush()
        c = Case(id="case-pt", participant_id=p.id, video_path="v.mp4",
                 device_type="pMDI", source="clinic", status="SCORED")
        s.add(c); s.commit()
    return "case-pt"


def test_issue_reports_creates_pdfs_and_rows(client, settings, seeded_case):
    pytest.importorskip("reportlab")
    from camca_web.reports_web import issue_reports
    with client.app.state.session_factory() as s:
        case = s.get(Case, seeded_case)
        rows = issue_reports(s, case, _result(), settings)
        s.commit()
    assert {r.kind for r in rows} == {"patient_ko", "patient_en",
                                      "clinician_ko", "clinician_en"}
    with client.app.state.session_factory() as s:
        for r in s.query(Report).all():
            from pathlib import Path
            assert Path(r.pdf_path).exists()


def test_patient_link_flow(client, settings, seeded_case):
    token = make_patient_token(seeded_case, settings.secret_key)
    r = client.get(f"/r/{token}")
    assert r.status_code == 200
    assert "생년월일" in r.text                      # 확인 폼
    r = client.post(f"/r/{token}", data={"dob": "1980-01-01"})
    assert r.status_code == 200
    with client.app.state.session_factory() as s:   # 열람 로그
        events = [a.event for a in s.query(AuditLog).all()]
        assert "report_viewed" in events


def test_patient_link_wrong_dob_rejected(client, settings, seeded_case):
    token = make_patient_token(seeded_case, settings.secret_key)
    r = client.post(f"/r/{token}", data={"dob": "1999-12-31"})
    assert r.status_code == 403


def test_patient_link_tampered_token_404(client, settings, seeded_case):
    r = client.get("/r/not-a-real-token")
    assert r.status_code == 404
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_reports_web.py -v`
Expected: FAIL — `ModuleNotFoundError` / 404

- [ ] **Step 3: reports_web.py + patient 라우트 구현**

```python
# src/camca_web/reports_web.py
"""리포트 발행 — camca-py PDF 생성기 재사용. 수정본 재발행은 revision 증가."""
from __future__ import annotations

from pathlib import Path

from camca.cli import _build_clinician_content, _build_patient_content
from camca.reports import build_bilingual_reports

from .auth import make_patient_token
from .config import Settings
from .db import Case, Report


def issue_reports(session, case: Case, result, settings: Settings,
                  revision: int = 1) -> list[Report]:
    out_dir = Path(settings.storage_root) / "cases" / case.id / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    device = (result.device_id.get("device_type", "pmdi")
              .lower().replace("-", "_"))
    paths = build_bilingual_reports(
        patient_content=_build_patient_content(result),
        clinician_content=_build_clinician_content(result),
        output_dir=out_dir,
        case_id=case.id,
        device=device,
    )
    rows = []
    for kind, path in paths.items():
        row = Report(case_id=case.id, kind=kind, pdf_path=str(path),
                     revision=revision)
        session.add(row)
        rows.append(row)
    return rows


def patient_link(case_id: str, settings: Settings) -> str:
    return f"/r/{make_patient_token(case_id, settings.secret_key)}"
```

**주의**: `_build_patient_content(result)`는 `result.case_id`/`result.kappa_stats`/`result.final_score`/`result.metadata`/`result.device_id`를 사용한다 (camca-py `cli.py:162-230` 실측). mock `SimpleNamespace`에 `case_id` 필드가 없으면 테스트가 `AttributeError`로 실패한다 — 그 경우 테스트 `_result()`에 `case_id="case-pt"`를 추가한다.

```python
# src/camca_web/routes/patient.py
"""환자용 — 서명 링크 + 생년월일 확인 후 리포트 열람 (회원가입 없음)."""
from __future__ import annotations

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse

from ..auth import dob_matches, read_patient_token
from ..db import Case, Participant, Report, write_audit

router = APIRouter()


def _resolve_case(request: Request, token: str):
    settings = request.app.state.settings
    case_id = read_patient_token(token, settings.secret_key,
                                 settings.patient_link_max_age_sec)
    if case_id is None:
        raise HTTPException(404)
    with request.app.state.session_factory() as s:
        case = s.get(Case, case_id)
        if case is None:
            raise HTTPException(404)
        participant = s.get(Participant, case.participant_id)
        reports = s.query(Report).filter_by(case_id=case_id).all()
    return case, participant, reports


@router.get("/r/{token}")
def verify_form(request: Request, token: str):
    _resolve_case(request, token)   # 토큰 유효성만 먼저 확인
    return request.app.state.templates.TemplateResponse(
        request, "patient_verify.html", {"token": token, "error": None})


@router.post("/r/{token}")
def view_report(request: Request, token: str, dob: str = Form()):
    case, participant, reports = _resolve_case(request, token)
    if not dob_matches(dob, participant.dob):
        raise HTTPException(403, detail="생년월일이 일치하지 않습니다.")
    with request.app.state.session_factory() as s:
        write_audit(s, "report_viewed", case_id=case.id, detail={"channel": "link"})
        s.commit()
    return request.app.state.templates.TemplateResponse(
        request, "patient_report.html",
        {"token": token, "case": case, "reports": reports})


@router.get("/r/{token}/pdf/{kind}")
def download_pdf(request: Request, token: str, kind: str):
    case, _, reports = _resolve_case(request, token)
    match = [r for r in reports if r.kind == kind and r.kind.startswith("patient")]
    if not match:
        raise HTTPException(404)
    return FileResponse(match[-1].pdf_path, media_type="application/pdf")
```

```html
<!-- src/camca_web/templates/patient_verify.html -->
{% extends "base.html" %}
{% block content %}
<h1>본인 확인</h1>
<p>리포트 열람을 위해 생년월일을 입력해 주세요.</p>
<form method="post" action="/r/{{ token }}">
  <input name="dob" placeholder="생년월일 YYYY-MM-DD" required>
  <button>확인</button>
</form>
{% endblock %}
```

```html
<!-- src/camca_web/templates/patient_report.html -->
{% extends "base.html" %}
{% block content %}
<h1>흡입제 사용 평가 리포트</h1>
{% if case.quality_flag %}
<p><em>영상 품질 안내: 일부 단계는 평가에서 제외되었을 수 있습니다.</em></p>
{% endif %}
<ul>
{% for r in reports if r.kind.startswith("patient") %}
  <li><a href="/r/{{ token }}/pdf/{{ r.kind }}">{{ r.kind }} (rev {{ r.revision }})</a></li>
{% endfor %}
</ul>
{% endblock %}
```

`src/camca_web/app.py`에 배선 추가:

```python
    from .routes.patient import router as patient_router
    app.include_router(patient_router)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_reports_web.py tests/ -v` → 전체 PASS
(reportlab 미설치 시 발행 테스트만 SKIP — `.venv/bin/pip install reportlab pypdf` 후 재실행 권장)

- [ ] **Step 5: Commit**

```bash
git add camca-web/src/camca_web/ camca-web/tests/test_reports_web.py
git commit -m "feat(web): auto report issuance + signed patient link viewing with DOB check"
```

---

### Task 10: 대시보드 + 타임라인 리뷰 UI + segments_corrected

**Files:**
- Create: `src/camca_web/routes/dashboard.py`
- Create: `src/camca_web/templates/dashboard.html`, `src/camca_web/templates/case_detail.html`
- Modify: `src/camca_web/app.py` (dashboard 라우터 배선)
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: Task 1 모델, Task 4 `require_staff`, Task 2 상태 상수.
- Produces: `GET /dashboard`(케이스 목록 + NEEDS_ATTENTION 배지 + 재실행 버튼), `GET /cases/{id}`(타임라인 리뷰), `POST /cases/{id}/segments`(경계 수정 → `segments_corrected` + diff + audit — flywheel 라벨 입구, spec §5.3-1).

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_dashboard.py
"""대시보드 목록/배지 + 타임라인 경계 수정 → segments_corrected + diff."""
import pytest
from camca_web.auth import hash_password
from camca_web.db import (Participant, Case, Segmentation, SegmentsCorrected,
                          AuditLog)


@pytest.fixture
def staff(client):
    client.app.state.staff_accounts = {"staff": hash_password("pw")}
    return client.post("/login", data={"username": "staff", "password": "pw"},
                       follow_redirects=False).cookies


@pytest.fixture
def seeded(client):
    with client.app.state.session_factory() as s:
        p = Participant(research_code="RC-D", dob="1980-01-01")
        s.add(p); s.flush()
        s.add(Case(id="case-ok", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="REPORT_ISSUED"))
        s.add(Case(id="case-warn", participant_id=p.id, video_path="v.mp4",
                   device_type="pMDI", source="clinic", status="REPORT_ISSUED",
                   needs_attention=True, attention_reasons=["critical_error"]))
        s.add(Segmentation(case_id="case-warn", engine="telemetry-anchored-v1",
                           events=[],
                           segments=[{"step_id": "S5", "observable": True,
                                      "t_start_ms": 6000, "t_end_ms": 9000}]))
        s.commit()


def test_dashboard_requires_login(client, seeded):
    r = client.get("/dashboard", follow_redirects=False)
    assert r.status_code in (302, 303)


def test_dashboard_lists_cases_with_badge(client, staff, seeded):
    r = client.get("/dashboard", cookies=staff)
    assert r.status_code == 200
    assert "case-ok" in r.text and "case-warn" in r.text
    assert "NEEDS_ATTENTION" in r.text


def test_case_detail_renders_timeline(client, staff, seeded):
    r = client.get("/cases/case-warn", cookies=staff)
    assert r.status_code == 200
    assert "S5" in r.text
    assert "timeline" in r.text        # 타임라인 컨테이너 존재


def test_segment_correction_saved_with_diff(client, staff, seeded):
    r = client.post("/cases/case-warn/segments", cookies=staff, json={
        "segments": [{"step_id": "S5", "observable": True,
                      "t_start_ms": 6200, "t_end_ms": 9000}],
    })
    assert r.status_code == 200
    with client.app.state.session_factory() as s:
        row = s.query(SegmentsCorrected).one()
        assert row.case_id == "case-warn"
        assert row.diff == [{"step_id": "S5", "field": "t_start_ms",
                             "before": 6000, "after": 6200}]
        events = [a.event for a in s.query(AuditLog).all()]
        assert "segments_corrected" in events
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/test_dashboard.py -v`
Expected: FAIL — 404

- [ ] **Step 3: 라우트 + 템플릿 구현**

```python
# src/camca_web/routes/dashboard.py
"""의사용 대시보드 — 사후 모니터링 + 타임라인 경계 수정 (flywheel 라벨 입구)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..db import Case, Segmentation, SegmentsCorrected, write_audit
from .staff import require_staff

router = APIRouter()


@router.get("/dashboard")
def dashboard(request: Request):
    require_staff(request)
    with request.app.state.session_factory() as s:
        cases = s.query(Case).order_by(Case.uploaded_at.desc()).all()
    return request.app.state.templates.TemplateResponse(
        request, "dashboard.html", {"cases": cases})


@router.get("/cases/{case_id}")
def case_detail(request: Request, case_id: str):
    require_staff(request)
    with request.app.state.session_factory() as s:
        case = s.get(Case, case_id)
        if case is None:
            raise HTTPException(404)
        seg = (s.query(Segmentation).filter_by(case_id=case_id)
               .order_by(Segmentation.created_at.desc()).first())
    segments = seg.segments if seg else []
    duration = max((x.get("t_end_ms") or 0) for x in segments) if segments else 1
    return request.app.state.templates.TemplateResponse(
        request, "case_detail.html",
        {"case": case, "segments": segments, "duration_ms": max(duration, 1)})


class CorrectionPayload(BaseModel):
    segments: list[dict]


def _diff_segments(before: list[dict], after: list[dict]) -> list[dict]:
    """step_id 기준으로 t_start_ms/t_end_ms/observable 변경만 추출."""
    by_id = {x["step_id"]: x for x in before}
    diffs = []
    for seg in after:
        old = by_id.get(seg["step_id"])
        if not old:
            continue
        for field in ("t_start_ms", "t_end_ms", "observable"):
            if field in seg and seg.get(field) != old.get(field):
                diffs.append({"step_id": seg["step_id"], "field": field,
                              "before": old.get(field), "after": seg.get(field)})
    return diffs


@router.post("/cases/{case_id}/segments")
def correct_segments(request: Request, case_id: str, payload: CorrectionPayload):
    user = require_staff(request)
    with request.app.state.session_factory() as s:
        seg = (s.query(Segmentation).filter_by(case_id=case_id)
               .order_by(Segmentation.created_at.desc()).first())
        if seg is None:
            raise HTTPException(404)
        diff = _diff_segments(seg.segments, payload.segments)
        s.add(SegmentsCorrected(case_id=case_id, corrected_by=user,
                                segments=payload.segments, diff=diff))
        write_audit(s, "segments_corrected", case_id=case_id,
                    detail={"by": user, "n_changes": len(diff)})
        s.commit()
    return {"ok": True, "n_changes": len(diff)}
```

```html
<!-- src/camca_web/templates/dashboard.html -->
{% extends "base.html" %}
{% block content %}
<h1>CAMCA 대시보드</h1>
<table>
  <tr><th>케이스</th><th>기기</th><th>상태</th><th>업로드</th><th></th></tr>
  {% for c in cases %}
  <tr>
    <td><a href="/cases/{{ c.id }}">{{ c.id }}</a>
        {% if c.needs_attention %}<span class="badge">NEEDS_ATTENTION</span>
        {{ c.attention_reasons | join(", ") }}{% endif %}</td>
    <td>{{ c.device_type }}</td>
    <td>{{ c.status }}</td>
    <td>{{ c.uploaded_at }}</td>
    <td>{% if c.status == "FAILED" %}
        <button hx-post="/cases/{{ c.id }}/rerun" hx-swap="none">재실행</button>
        {% endif %}</td>
  </tr>
  {% endfor %}
</table>
{% endblock %}
```

```html
<!-- src/camca_web/templates/case_detail.html -->
{% extends "base.html" %}
{% block content %}
<h1>케이스 {{ case.id }} <small>({{ case.status }})</small></h1>
{% if case.needs_attention %}
<p><span class="badge">NEEDS_ATTENTION</span> {{ case.attention_reasons | join(", ") }}</p>
{% endif %}

<video id="player" controls width="100%" src="/static/placeholder.mp4"></video>

<div id="timeline" style="position:relative;height:48px;background:#eee;margin:8px 0"
     data-duration="{{ duration_ms }}">
  {% for s in segments if s.observable %}
  <div class="band" data-step="{{ s.step_id }}"
       data-start="{{ s.t_start_ms }}" data-end="{{ s.t_end_ms }}"
       style="position:absolute;top:4px;bottom:4px;background:hsl({{ loop.index0 * 40 }},70%,60%);
              left:{{ 100 * s.t_start_ms / duration_ms }}%;
              width:{{ 100 * (s.t_end_ms - s.t_start_ms) / duration_ms }}%">
    <span style="font-size:.7em">{{ s.step_id }}</span>
    <div class="handle" style="position:absolute;right:-4px;top:0;bottom:0;width:8px;cursor:ew-resize"></div>
  </div>
  {% endfor %}
</div>

<table id="segTable">
  <tr><th>단계</th><th>시작(ms)</th><th>끝(ms)</th></tr>
  {% for s in segments %}
  <tr data-step="{{ s.step_id }}">
    <td>{{ s.step_id }}</td>
    <td><input type="number" name="start" value="{{ s.t_start_ms if s.t_start_ms is not none else '' }}"></td>
    <td><input type="number" name="end" value="{{ s.t_end_ms if s.t_end_ms is not none else '' }}"></td>
  </tr>
  {% endfor %}
</table>
<button id="saveBtn">경계 수정 저장</button>
<p id="saveMsg"></p>

<script>
// 드래그: 밴드 우측 핸들을 잡아 끝 경계를 조정 → 표의 입력값 동기화
const tl = document.getElementById("timeline");
const duration = parseInt(tl.dataset.duration, 10);
tl.querySelectorAll(".band .handle").forEach(h => {
  h.addEventListener("pointerdown", e => {
    e.preventDefault();
    const band = h.parentElement;
    const move = ev => {
      const rect = tl.getBoundingClientRect();
      const ms = Math.round((ev.clientX - rect.left) / rect.width * duration);
      const start = parseInt(band.dataset.start, 10);
      if (ms > start) {
        band.dataset.end = ms;
        band.style.width = (100 * (ms - start) / duration) + "%";
        const row = document.querySelector(`#segTable tr[data-step="${band.dataset.step}"]`);
        if (row) row.querySelector('input[name="end"]').value = ms;
      }
    };
    const up = () => { window.removeEventListener("pointermove", move);
                       window.removeEventListener("pointerup", up); };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  });
});

document.getElementById("saveBtn").addEventListener("click", async () => {
  const segments = [...document.querySelectorAll("#segTable tr[data-step]")].map(tr => {
    const start = tr.querySelector('input[name="start"]').value;
    const end = tr.querySelector('input[name="end"]').value;
    return {step_id: tr.dataset.step,
            observable: start !== "" && end !== "",
            t_start_ms: start === "" ? null : parseInt(start, 10),
            t_end_ms: end === "" ? null : parseInt(end, 10)};
  });
  const r = await fetch(`/cases/{{ case.id }}/segments`, {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({segments}),
  });
  const j = await r.json();
  document.getElementById("saveMsg").textContent =
    r.ok ? `저장됨 — 변경 ${j.n_changes}건 (flywheel 라벨로 축적)` : "저장 실패";
});
</script>
{% endblock %}
```

`src/camca_web/app.py`에 배선 추가:

```python
    from .routes.dashboard import router as dashboard_router
    app.include_router(dashboard_router)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.venv/bin/python -m pytest tests/test_dashboard.py tests/ -v` → 전체 PASS

- [ ] **Step 5: 운영 진입점 확인 (수동)**

`create_app` 마지막에 워커 배선(운영에서만, `CAMCA_START_WORKER=1`일 때):

```python
    import os
    if os.environ.get("CAMCA_START_WORKER") == "1":
        from .jobs import start_worker
        from .runner import build_default_deps, process_case
        deps = build_default_deps()
        start_worker(app.state.session_factory,
                     lambda cid: process_case(cid, app.state.session_factory,
                                              settings, deps))
```

Run: `.venv/bin/python -m pytest tests/ -v` → 전체 PASS (워커는 테스트에서 비활성)

- [ ] **Step 6: Commit**

```bash
git add camca-web/src/camca_web/ camca-web/tests/test_dashboard.py
git commit -m "feat(web): dashboard with attention badges + timeline review saving corrected segments"
```

---

## Self-Review 결과 (계획 작성 시 수행)

1. **Spec coverage**: §2 모듈 경계→Task 0/4/5/6/7/9/10, §3 스키마 9테이블→Task 1 (열람 로그는 audit_log로 통합, `reports.열람 로그` 요건 충족), §4 상태 머신+NEEDS_ATTENTION+재실행→Task 2/5/8, §5.3-1 타임라인 리뷰+segments_corrected→Task 10, §5.3-2 quality gate VLM 가중→Task 6 (`vlm_weight_up` 플래그; Stage 2 가중 반영 자체는 Plan 1 엔진 파라미터화 후속), §6 에러 처리→Task 5(FAILED/재실행)+지수 백오프는 camca-py 백엔드 소관, data quality 환자 언어 안내→Task 9 템플릿, §7 재택 대비→`cases.source` 필드+모바일 viewport, §8 테스트 전략→전 태스크 mock 기반. **의사 점수 수정→재발행 diff**는 경계 수정(Task 10)으로 flywheel 입구를 구현하고, 점수 수정 UI는 후속 작업으로 명시(아래).
2. **Placeholder scan**: 통과 — 전 스텝 실행 가능한 코드/커맨드 포함. Task 9의 `_build_patient_content` mock 필드 불일치 가능성은 주의 블록으로 명기.
3. **Type consistency**: `Settings(db_url, storage_root, secret_key, patient_link_max_age_sec)`, `QualityResult(passed, view, face_detection_rate, vlm_weight_up, reasons)`, `RunnerDeps(telemetry_fn, quality_fn, anonymize_fn, pipeline_factory, issue_fn)`, `issue_fn(session, case, result, settings)` 시그니처가 Task 8 테스트/구현/Task 9 `issue_reports`에서 일치함을 확인.

**알려진 후속 작업 (이 계획 범위 밖):**
- 의사 점수(레벨) 수정 UI + 수정본 리포트 재발행 diff (경계 수정 flywheel과 동일 패턴으로 확장)
- Postgres 마이그레이션 도구(Alembic) — 파일럿은 create_all로 충분
- 리포트 golden file 비교 테스트 (spec §8 — PDF 생성기 자체는 camca-py에서 검증됨)
- quality gate `vlm_weight_up` → Plan 1 엔진의 Stage 2 가중 파라미터 연결
- 스태프 계정 시드 CLI (`camca-web create-staff`)
