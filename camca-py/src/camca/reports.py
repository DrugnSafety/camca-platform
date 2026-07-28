"""Bilingual (KO + EN) PDF report generation for CAMCA evaluations.

Two report types:
  - patient: comprehensive (dynamic per-case + static guide append)
  - clinician: brief, 1-page, results-focused

Uses bundled NanumGothic font from camca.resources.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from .resources import font_path, static_guide_path


def _ensure_reportlab():
    try:
        global reportlab_modules
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
        )
        return {
            "A4": A4, "ParagraphStyle": ParagraphStyle, "mm": mm, "colors": colors,
            "pdfmetrics": pdfmetrics, "TTFont": TTFont,
            "SimpleDocTemplate": SimpleDocTemplate, "Paragraph": Paragraph,
            "Spacer": Spacer, "Table": Table, "TableStyle": TableStyle, "PageBreak": PageBreak,
        }
    except ImportError:
        raise ImportError("reportlab required. Install: pip install reportlab")


def _ensure_pypdf():
    try:
        from pypdf import PdfWriter, PdfReader
        return PdfWriter, PdfReader
    except ImportError:
        raise ImportError("pypdf required. Install: pip install pypdf")


def _register_fonts(rl) -> tuple[str, str]:
    """Register bundled NanumGothic. Returns (regular_name, bold_name)."""
    try:
        rl["pdfmetrics"].registerFont(rl["TTFont"]("NanumGothic", str(font_path("NanumGothic", "Regular"))))
        rl["pdfmetrics"].registerFont(rl["TTFont"]("NanumGothic-Bold", str(font_path("NanumGothic", "Bold"))))
        return "NanumGothic", "NanumGothic-Bold"
    except Exception as e:
        print(f"WARNING: NanumGothic registration failed ({e}); Korean may not render.")
        return "Helvetica", "Helvetica-Bold"


# Colors (consistent with plugin)
def _colors(rl):
    return {
        "PRIMARY": rl["colors"].HexColor("#1976D2"),
        "SUCCESS": rl["colors"].HexColor("#388E3C"),
        "WARNING": rl["colors"].HexColor("#F57C00"),
        "CRITICAL": rl["colors"].HexColor("#D32F2F"),
        "TEXT": rl["colors"].HexColor("#212121"),
        "MUTED": rl["colors"].HexColor("#666666"),
        "BG_LIGHT": rl["colors"].HexColor("#F5F5F5"),
        "BG_BLUE": rl["colors"].HexColor("#E3F2FD"),
    }


# I18N labels (same as plugin)
I18N = {
    "ko": {
        "report_title_patient": "흡입기 사용법 평가 — 환자 안내서",
        "report_title_clinician": "흡입기 기술 평가 — 결과 요약",
        "case_id": "케이스 ID", "eval_date": "평가 일시", "device": "장치",
        "verdict": "종합 평가", "score": "점수",
        "verdict_label": {
            "PROFICIENT": "흡입기 사용법을 잘 익히셨습니다",
            "ADEQUATE_WITH_EDUCATION": "사용법이 대체로 잘 되고 있습니다",
            "NEEDS_INTENSIVE_TRAINING": "사용 방법을 좀 더 익히실 필요가 있습니다",
            "FAIL": "사용법에 중요한 개선이 필요합니다",
        },
        "critical_section": "🔴 꼭 개선이 필요한 부분",
        "strengths_section": "✅ 잘하신 점",
        "improvements_section": "📝 다음에 시도해 보실 점",
        "followup_section": "📅 재평가 권장",
        "footer_disclaimer": "본 평가는 AI 영상 분석 결과이며, 의료진의 직접 평가를 완전히 대체하지 않습니다. 궁금한 점은 다음 진료 시 의료진과 상의해 주세요.",
        "kappa_label": "AI 평가 신뢰도",
        "metric_metric": "지표", "metric_value": "값",
        "step_label": "단계", "step_consensus": "Consensus", "step_agreement": "평가 일치도",
        "critical_errors": "치명적 오류", "review_priority": "임상의 검토 우선순위",
        "stage_table_title": "단계별 평가",
        "metadata_title": "평가 메타데이터", "stage_durations": "단계별 소요시간",
        "models_used": "사용 모델", "none": "없음",
    },
    "en": {
        "report_title_patient": "Inhaler Technique Evaluation — Patient Guide",
        "report_title_clinician": "Inhaler Technique Evaluation — Results Summary",
        "case_id": "Case ID", "eval_date": "Evaluation date", "device": "Device",
        "verdict": "Overall verdict", "score": "Score",
        "verdict_label": {
            "PROFICIENT": "Your inhaler technique is excellent",
            "ADEQUATE_WITH_EDUCATION": "Your technique is generally adequate",
            "NEEDS_INTENSIVE_TRAINING": "Your technique needs more training",
            "FAIL": "Your technique requires important improvement",
        },
        "critical_section": "🔴 Critical points to improve",
        "strengths_section": "✅ What you did well",
        "improvements_section": "📝 Try these next time",
        "followup_section": "📅 Follow-up recommendation",
        "footer_disclaimer": "This evaluation was produced by AI video analysis. It does NOT replace direct evaluation by your healthcare team.",
        "kappa_label": "AI evaluation reliability",
        "metric_metric": "Metric", "metric_value": "Value",
        "step_label": "Step", "step_consensus": "Consensus", "step_agreement": "Inter-rater agreement",
        "critical_errors": "Critical errors", "review_priority": "Clinician review priority",
        "stage_table_title": "Per-Step Evaluation",
        "metadata_title": "Evaluation Metadata", "stage_durations": "Stage durations",
        "models_used": "Models used", "none": "None",
    },
}


def _build_patient_dynamic(content: dict, lang: str, buf: BytesIO) -> None:
    rl = _ensure_reportlab()
    C = _colors(rl)
    regular, bold = _register_fonts(rl)
    L = I18N[lang]

    doc = rl["SimpleDocTemplate"](
        buf, pagesize=rl["A4"],
        topMargin=12 * rl["mm"], bottomMargin=12 * rl["mm"],
        leftMargin=18 * rl["mm"], rightMargin=18 * rl["mm"],
    )
    PS = rl["ParagraphStyle"]
    h1 = PS("H1", fontName=bold, fontSize=18, alignment=1,
            textColor=C["PRIMARY"], spaceAfter=4 * rl["mm"], leading=24)
    meta = PS("Meta", fontName=regular, fontSize=9, alignment=1,
              textColor=C["MUTED"], leading=12)
    h2 = PS("H2", fontName=bold, fontSize=13, textColor=C["TEXT"],
            spaceBefore=4 * rl["mm"], spaceAfter=2 * rl["mm"], leading=18)
    body = PS("Body", fontName=regular, fontSize=11, textColor=C["TEXT"],
              leading=17, spaceAfter=2 * rl["mm"])
    critical = PS("Critical", fontName=bold, fontSize=11, textColor=C["CRITICAL"],
                  leading=16, spaceAfter=2 * rl["mm"])
    success = PS("Success", fontName=regular, fontSize=11, textColor=C["SUCCESS"],
                 leading=16, spaceAfter=2 * rl["mm"])
    footer = PS("Footer", fontName=regular, fontSize=8, textColor=C["MUTED"],
                leading=11, alignment=1)

    def loc(key: str, default=None):
        return content.get(f"{key}_{lang}", content.get(key, default))

    story = []
    story.append(rl["Paragraph"](L["report_title_patient"], h1))
    story.append(rl["Paragraph"](
        f"{L['case_id']}: {content['case_id']}　|　{L['eval_date']}: {content['evaluation_date']}　|　{L['device']}: {content['device_type']}",
        meta,
    ))
    story.append(rl["Spacer"](1, 4 * rl["mm"]))

    verdict = content["final_verdict"].split(" ")[0]
    verdict_text = L["verdict_label"].get(verdict, content["final_verdict"])
    vcolor = (C["CRITICAL"] if verdict == "FAIL" else
              C["WARNING"] if verdict == "NEEDS_INTENSIVE_TRAINING" else C["SUCCESS"])

    t = rl["Table"]([
        [rl["Paragraph"](f"<b>{L['verdict']}</b>", body),
         rl["Paragraph"](f"<font color='{vcolor.hexval()}'><b>{verdict_text}</b></font>", body)],
        [rl["Paragraph"](f"<b>{L['score']}</b>", body),
         rl["Paragraph"](f"{content['core_score']} / {content['core_max']} ({content['core_percent']}%)", body)],
    ], colWidths=[40 * rl["mm"], 130 * rl["mm"]])
    t.setStyle(rl["TableStyle"]([
        ("BACKGROUND", (0, 0), (-1, -1), C["BG_LIGHT"]),
        ("BOX", (0, 0), (-1, -1), 0.5, C["MUTED"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(rl["Spacer"](1, 4 * rl["mm"]))

    for key, header_key, style in [
        ("critical_errors_patient_friendly", "critical_section", critical),
        ("strengths", "strengths_section", success),
        ("improvements", "improvements_section", body),
    ]:
        items = loc(key, [])
        if items:
            story.append(rl["Paragraph"](L[header_key], h2))
            for it in items[:2 if key == "improvements" else None]:
                story.append(rl["Paragraph"](f"• {it}", style))
            story.append(rl["Spacer"](1, 2 * rl["mm"]))

    fu = loc("followup_recommendation")
    if fu:
        story.append(rl["Paragraph"](L["followup_section"], h2))
        story.append(rl["Paragraph"](fu, body))

    story.append(rl["Spacer"](1, 6 * rl["mm"]))
    if content.get("kappa") is not None:
        kappa_interp = content.get(f"kappa_interpretation_{lang}",
                                    content.get("kappa_interpretation_ko", ""))
        story.append(rl["Paragraph"](
            f"{L['kappa_label']}: κ = {content.get('kappa')} ({kappa_interp})", footer))
    story.append(rl["Paragraph"](L["footer_disclaimer"], footer))

    doc.build(story)


def build_patient_pdf(content: dict, output_path: Path, lang: str = "ko",
                      device: str = "pmdi", append_static: bool = True) -> Path:
    """Build patient PDF (dynamic page + optional static guide append)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    buf = BytesIO()
    _build_patient_dynamic(content, lang, buf)
    buf.seek(0)

    if not append_static:
        output_path.write_bytes(buf.read())
        return output_path

    PdfWriter, PdfReader = _ensure_pypdf()
    writer = PdfWriter()
    for page in PdfReader(buf).pages:
        writer.add_page(page)
    try:
        sg = static_guide_path(device=device.lower(), lang=lang)
        for page in PdfReader(str(sg)).pages:
            writer.add_page(page)
    except FileNotFoundError:
        pass  # No static guide; dynamic only

    with open(output_path, "wb") as f:
        writer.write(f)
    return output_path


def build_clinician_pdf(content: dict, output_path: Path, lang: str = "ko") -> Path:
    """Build single-page clinician brief PDF."""
    rl = _ensure_reportlab()
    C = _colors(rl)
    regular, bold = _register_fonts(rl)
    L = I18N[lang]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = rl["SimpleDocTemplate"](
        str(output_path), pagesize=rl["A4"],
        topMargin=12 * rl["mm"], bottomMargin=12 * rl["mm"],
        leftMargin=15 * rl["mm"], rightMargin=15 * rl["mm"],
    )
    PS = rl["ParagraphStyle"]
    h1 = PS("H1", fontName=bold, fontSize=14, alignment=1,
            textColor=C["PRIMARY"], spaceAfter=2 * rl["mm"], leading=18)
    meta = PS("Meta", fontName=regular, fontSize=8, alignment=1,
              textColor=C["MUTED"], leading=10, spaceAfter=4 * rl["mm"])
    h2 = PS("H2", fontName=bold, fontSize=10, textColor=C["TEXT"],
            spaceBefore=3 * rl["mm"], spaceAfter=1 * rl["mm"], leading=14)
    footer = PS("Footer", fontName=regular, fontSize=7, textColor=C["MUTED"],
                leading=9, alignment=1)

    story = []
    story.append(rl["Paragraph"](L["report_title_clinician"], h1))
    story.append(rl["Paragraph"](
        f"{L['case_id']}: {content['case_id']}　|　{L['eval_date']}: {content['evaluation_date']}　|　{L['device']}: {content['device_type']}",
        meta,
    ))

    crit_count = len(content.get("critical_errors", []))
    crit_display = ", ".join(content.get("critical_errors", [])) or L["none"]
    rows = [
        [L["metric_metric"], L["metric_value"]],
        [L["verdict"], content["final_verdict"]],
        [L["score"], f"{content['core_score']} / {content['core_max']} ({content['core_percent']}%)"],
        [L["critical_errors"], f"{crit_count} ({crit_display})"],
        ["κ (linear)", f"{content.get('kappa', 'N/A')} — {content.get(f'kappa_interpretation_{lang}', '')}"],
        [L["review_priority"], content.get("clinician_review_priority", "none")],
    ]
    t = rl["Table"](rows, colWidths=[55 * rl["mm"], 125 * rl["mm"]])
    t.setStyle(rl["TableStyle"]([
        ("FONT", (0, 0), (-1, -1), regular, 9),
        ("FONT", (0, 0), (-1, 0), bold, 9),
        ("BACKGROUND", (0, 0), (-1, 0), C["BG_BLUE"]),
        ("BACKGROUND", (0, 1), (0, -1), C["BG_LIGHT"]),
        ("BOX", (0, 0), (-1, -1), 0.4, C["MUTED"]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, C["MUTED"]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(rl["Spacer"](1, 4 * rl["mm"]))

    # Per-step table
    if content.get("per_step_breakdown"):
        story.append(rl["Paragraph"](L["stage_table_title"], h2))
        step_rows = [[L["step_label"], "A", "B", "TB", L["step_consensus"], L["step_agreement"]]]
        for s in content["per_step_breakdown"]:
            step_rows.append([s["step_id"], str(s["a_level"]), str(s["b_level"]),
                              str(s.get("tb_level", "-")), str(s["consensus_level"]),
                              s["agreement_label"]])
        t2 = rl["Table"](step_rows, colWidths=[35 * rl["mm"], 10 * rl["mm"], 10 * rl["mm"],
                                                10 * rl["mm"], 25 * rl["mm"], 90 * rl["mm"]])
        t2.setStyle(rl["TableStyle"]([
            ("FONT", (0, 0), (-1, -1), regular, 8),
            ("FONT", (0, 0), (-1, 0), bold, 8),
            ("BACKGROUND", (0, 0), (-1, 0), C["BG_LIGHT"]),
            ("GRID", (0, 0), (-1, -1), 0.3, C["MUTED"]),
            ("ALIGN", (1, 0), (4, -1), "CENTER"),
        ]))
        story.append(t2)

    # Metadata
    md = content.get("metadata", {})
    if md:
        story.append(rl["Spacer"](1, 3 * rl["mm"]))
        story.append(rl["Paragraph"](L["metadata_title"], h2))
        md_rows = [[L["metric_metric"], L["metric_value"]]]
        if md.get("models_used"):
            md_rows.append([L["models_used"],
                            "; ".join(f"{k}: {v}" for k, v in md["models_used"].items())])
        if md.get("stage_durations_ms"):
            durs = md["stage_durations_ms"]
            total = sum(durs.values())
            md_rows.append([L["stage_durations"],
                            f"Total {total/1000:.1f}s — " + ", ".join(f"{k}={v}ms" for k, v in durs.items())])
        if md.get("started_at"):
            md_rows.append(["Pipeline started", md["started_at"]])
        t3 = rl["Table"](md_rows, colWidths=[55 * rl["mm"], 125 * rl["mm"]])
        t3.setStyle(rl["TableStyle"]([
            ("FONT", (0, 0), (-1, -1), regular, 7),
            ("FONT", (0, 0), (-1, 0), bold, 7),
            ("BACKGROUND", (0, 0), (-1, 0), C["BG_LIGHT"]),
            ("GRID", (0, 0), (-1, -1), 0.3, C["MUTED"]),
        ]))
        story.append(t3)

    story.append(rl["Spacer"](1, 4 * rl["mm"]))
    story.append(rl["Paragraph"](L["footer_disclaimer"], footer))
    story.append(rl["Paragraph"](
        f"CAMCA v0.1.0 · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC", footer))

    doc.build(story)
    return output_path


def build_bilingual_reports(
    patient_content: dict | None = None,
    clinician_content: dict | None = None,
    output_dir: Path | str = ".",
    case_id: str = "CASE-001",
    device: str = "pmdi",
    languages: tuple[str, ...] = ("ko", "en"),
) -> dict[str, Path]:
    """Convenience: build patient (KO+EN) + clinician (KO+EN) reports together."""
    output_dir = Path(output_dir)
    out_paths = {}
    for lang in languages:
        if patient_content:
            p = output_dir / f"{case_id}_patient_{lang}.pdf"
            build_patient_pdf(patient_content, p, lang=lang, device=device)
            out_paths[f"patient_{lang}"] = p
        if clinician_content:
            p = output_dir / f"{case_id}_clinician_{lang}.pdf"
            build_clinician_pdf(clinician_content, p, lang=lang)
            out_paths[f"clinician_{lang}"] = p
    return out_paths
