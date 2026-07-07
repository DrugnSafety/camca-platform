"""camca segment 서브커맨드 — argparse 배선만 검증 (실제 영상 처리 없음)."""
from camca.cli import build_parser


def test_segment_subcommand_exists():
    parser = build_parser()
    args = parser.parse_args([
        "segment", "--video", "demo.mp4", "--device", "pMDI",
        "--case-id", "X-001", "--out", "seg.json", "--no-vlm",
    ])
    assert args.cmd == "segment"
    assert args.video == "demo.mp4"
    assert args.no_vlm is True


def test_segment_defaults():
    parser = build_parser()
    args = parser.parse_args(["segment", "--video", "v.mp4", "--case-id", "C-1"])
    assert args.device == "pMDI"
    assert args.out is None
    assert args.vlm is None
    assert args.no_vlm is False


def test_existing_analyze_command_unchanged():
    parser = build_parser()
    args = parser.parse_args(["analyze", "--video", "v.mp4", "--case-id", "C-1"])
    assert args.cmd == "analyze"
