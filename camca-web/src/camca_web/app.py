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

    from .db import make_engine, make_session_factory, init_db
    engine = make_engine(settings.db_url)
    init_db(engine)
    app.state.session_factory = make_session_factory(engine)

    from fastapi.templating import Jinja2Templates
    app.state.templates = Jinja2Templates(directory=TEMPLATE_DIR)
    app.state.staff_accounts = {}   # 운영: 환경변수/CLI로 시드. 테스트: 직접 주입.

    from .routes.staff import router as staff_router
    app.include_router(staff_router)

    from .routes.patient import router as patient_router
    app.include_router(patient_router)

    from .routes.dashboard import router as dashboard_router
    app.include_router(dashboard_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    # 운영 전용 백그라운드 워커 — 테스트에서는 환경변수 미설정으로 비활성.
    import os
    if os.environ.get("CAMCA_START_WORKER") == "1":
        from .jobs import start_worker
        from .runner import build_default_deps, process_case
        deps = build_default_deps()
        start_worker(app.state.session_factory,
                     lambda cid: process_case(cid, app.state.session_factory,
                                              settings, deps))

    return app
