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
