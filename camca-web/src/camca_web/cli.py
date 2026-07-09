"""camca-web CLI — 운영 보조 커맨드.

현재 서브커맨드:
  create-staff   스태프 계정 시드/갱신 (회원가입 없는 설계에서 유일한 생성 경로)

사용 예:
  camca-web create-staff --username dr-kang            # 비밀번호는 프롬프트
  CAMCA_DB_URL=postgresql://... camca-web create-staff --username nurse-a
"""
from __future__ import annotations

import argparse
import getpass
import sys

from .auth import hash_password
from .config import Settings
from .db import Staff, init_db, make_engine, make_session_factory, write_audit


def _cmd_create_staff(args: argparse.Namespace) -> int:
    password = args.password
    if password is None:
        password = getpass.getpass("새 비밀번호: ")
        confirm = getpass.getpass("비밀번호 확인: ")
        if password != confirm:
            print("오류: 비밀번호가 일치하지 않습니다.", file=sys.stderr)
            return 1
    if not password:
        print("오류: 빈 비밀번호는 사용할 수 없습니다.", file=sys.stderr)
        return 1

    db_url = args.db_url or Settings().db_url
    engine = make_engine(db_url)
    init_db(engine)   # 파일럿은 create_all — Alembic은 계획서상 후속 (Plan 2)
    with make_session_factory(engine)() as s:
        row = s.query(Staff).filter_by(username=args.username).first()
        action = "updated" if row else "created"
        if row is None:
            row = Staff(username=args.username,
                        password_hash=hash_password(password))
            s.add(row)
        else:
            row.password_hash = hash_password(password)
        write_audit(s, "staff_account_seeded",
                    detail={"username": args.username, "action": action})
        s.commit()
    print(f"스태프 계정 {action}: {args.username} ({db_url})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="camca-web")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create-staff", help="스태프 계정 시드/갱신")
    p.add_argument("--username", required=True)
    p.add_argument("--password", default=None,
                   help="생략하면 안전한 프롬프트로 입력받는다")
    p.add_argument("--db-url", default=None,
                   help="생략하면 CAMCA_DB_URL 환경변수/기본값 사용")
    p.set_defaults(func=_cmd_create_staff)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
