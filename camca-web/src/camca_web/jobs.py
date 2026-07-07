"""pipeline/ 잡 큐 — DB polling 워커. 추후 독립 워커 프로세스로 분리 가능한 경계.

자동 재시도는 하지 않는다: FAILED는 스태프 원클릭 재실행(spec §4)으로만 재개.
"""
from __future__ import annotations

import threading
import time
import traceback
from typing import Callable

from sqlalchemy import update

from .db import Job, write_audit


def run_pending_once(session_factory, processor: Callable[[str], None],
                     max_attempts: int = 3) -> int:
    """pending 잡을 순서대로 1패스 처리. 처리한 잡 수를 반환 (테스트/워커 공용).

    claim은 조건부 UPDATE로 원자적으로 수행한다 — SELECT-then-UPDATE는 두
    워커가 동시에 같은 잡을 claim하는 경쟁을 허용하므로, WHERE 절에 상태
    조건을 걸고 rowcount == 1일 때만 claim 성공으로 간주한다.
    """
    processed = 0
    with session_factory() as s:
        pending = (s.query(Job).filter_by(status="pending")
                   .order_by(Job.created_at).all())
        job_ids = [j.id for j in pending]
    for job_id in job_ids:
        with session_factory() as s:
            result = s.execute(
                update(Job)
                .where(Job.id == job_id, Job.status == "pending",
                       Job.attempts < max_attempts)
                .values(status="running", attempts=Job.attempts + 1)
            )
            s.commit()
            if result.rowcount != 1:
                continue
            job = s.get(Job, job_id)
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
