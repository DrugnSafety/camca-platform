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
