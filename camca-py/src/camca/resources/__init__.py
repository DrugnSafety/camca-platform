"""Bundled resources loader for the CAMCA package.

Uses importlib.resources to access package-bundled assets:
  - Korean fonts (NanumGothic TTF)
  - Skill markdown files (checklists, rubric, CRITIKAL)
  - Static patient guide PDFs
  - Reference tables (XLSX, MD)

All accessors return Path-like objects compatible with file APIs.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Use importlib.resources for both Python <3.9 fallback and >=3.9 path API
if sys.version_info >= (3, 9):
    from importlib import resources as _resources
else:
    import importlib_resources as _resources  # type: ignore

_PACKAGE = "camca.resources"


def _resource_path(subdir: str, filename: str) -> Path:
    """Return absolute Path to a bundled resource."""
    try:
        # Python 3.9+
        with _resources.as_file(_resources.files(_PACKAGE) / subdir / filename) as p:
            return Path(p)
    except (FileNotFoundError, ModuleNotFoundError):
        raise FileNotFoundError(f"Bundled resource not found: {subdir}/{filename}")


def font_path(family: str = "NanumGothic", weight: str = "Regular") -> Path:
    """Return path to a bundled font TTF.

    Args:
        family: "NanumGothic" (default; bundled)
        weight: "Regular" or "Bold"
    """
    return _resource_path("fonts", f"{family}-{weight}.ttf")


def skill_text(skill_name: str) -> str:
    """Return the markdown content of a bundled skill.

    Examples:
        skill_text("inhaler-checklist-pmdi")
        skill_text("critical-errors-critikal")
        skill_text("proficiency-rubric-levels")
    """
    path = _resource_path("skills", f"{skill_name}.md")
    return path.read_text(encoding="utf-8")


def static_guide_path(device: str = "pmdi", lang: str = "ko") -> Path:
    """Return path to a bundled static patient guide PDF."""
    return _resource_path("static", f"patient_guide_{device}_{lang}.pdf")


def reference_path(filename: str) -> Path:
    """Return path to a bundled reference table (XLSX or MD)."""
    return _resource_path("reference", filename)


def available_skills() -> list[str]:
    """List skill markdown files bundled in the package."""
    try:
        files = _resources.files(_PACKAGE) / "skills"
        return sorted(
            p.name.removesuffix(".md")
            for p in files.iterdir()
            if p.name.endswith(".md")
        )
    except (FileNotFoundError, ModuleNotFoundError):
        return []
