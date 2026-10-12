#!/usr/bin/env python3
"""Start complete Prompt/Response capture for one Litex problem.

The capture engine stays in ``temp/imo_litex_log.py``. This wrapper is kept
with the Litex memory tools and resolves every path from its own location, so
it can be launched from any working directory.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
AGENT_ROOT = SCRIPT_DIR.parents[1]
CAPTURE_SCRIPT = AGENT_ROOT / "temp" / "imo_litex_log.py"
DEFAULT_RESPONSES_DIR = AGENT_ROOT / "temp" / "model_responses"
DEFAULT_ARCHIVE_ROOT = AGENT_ROOT.parent / "LItex_vs_Lean_new-2" / "IMO" / "solutions"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture the complete agent Prompt/Response stream for a Litex problem."
    )
    parser.add_argument("problem_id", type=int, help="problem number, for example 4")
    parser.add_argument(
        "--responses-dir",
        type=Path,
        default=DEFAULT_RESPONSES_DIR,
        help=f"model response directory (default: {DEFAULT_RESPONSES_DIR})",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=DEFAULT_ARCHIVE_ROOT,
        help=f"parent directory for problem_<id> (default: {DEFAULT_ARCHIVE_ROOT})",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="capture one explicit model_responses_*.txt file",
    )
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument(
        "--append",
        action="store_true",
        help="resume capture into an existing agent_session.log",
    )
    output_mode.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing agent_session.log",
    )
    parser.add_argument(
        "--no-follow",
        action="store_true",
        help="copy the current response file and exit",
    )
    parser.add_argument(
        "--from-start",
        action="store_true",
        help="capture the selected response file from byte zero; default is only new output",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.problem_id < 0:
        raise SystemExit("problem_id must be a non-negative integer")
    if not CAPTURE_SCRIPT.is_file():
        raise SystemExit(f"capture engine not found: {CAPTURE_SCRIPT}")

    command = [
        sys.executable,
        str(CAPTURE_SCRIPT),
        "capture",
        "--problem-id",
        str(args.problem_id),
        "--responses-dir",
        str(args.responses_dir.expanduser().resolve()),
        "--archive-root",
        str(args.archive_root.expanduser().resolve()),
        "--quiet",
    ]
    if args.source is not None:
        command.extend(["--source", str(args.source.expanduser().resolve())])
    if not args.from_start and not args.append:
        command.append("--from-end")
    if args.append:
        command.append("--append")
    if args.overwrite:
        command.append("--overwrite")
    if args.no_follow:
        command.append("--no-follow")

    output = args.archive_root.expanduser().resolve() / f"problem_{args.problem_id}" / "agent_session.log"
    print(f"Capture output: {output}")
    print("Press Ctrl+C in this terminal when the problem-solving session is complete.")
    return subprocess.call(command, cwd=AGENT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
