#!/usr/bin/env python3
"""Render a generated enclosure assembly with a deterministic camera."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    EnclosureError, atomic_output, reject_symlink_path, run_bounded,
)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--openscad", default="openscad")
    parser.add_argument("--size", default="1400,1000")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    executable = shutil.which(args.openscad)
    try:
        source = reject_symlink_path(args.source, "render source")
    except EnclosureError as exc:
        print(f"ENCLOSURE RENDER ERROR — input: {args.source}: {exc}",
              file=sys.stderr)
        return 1
    if executable is None or not source.is_file():
        print(f"ENCLOSURE RENDER ERROR — input: {args.source}: executable/source missing",
              file=sys.stderr)
        return 1
    try:
        with atomic_output(
                args.output, where="enclosure render", root=args.output.parent,
                inputs=[source], temporary_suffix=".png") as (temporary, stream):
            stream.flush()
            command = [executable, "-o", str(temporary), "--imgsize", args.size,
                       "--viewall", "--autocenter", "--projection", "ortho",
                       "--colorscheme", "Tomorrow Night", "-D", 'part="assembly"',
                       "-D", "show_reference_board=true", str(source)]
            if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
                # Debian's xvfb-run trap sends SIGTERM to Xvfb but does not
                # wait for it.  A strict process-group supervisor correctly
                # rejects that still-live descendant.  Keep this bounded
                # wrapper alive briefly after xvfb-run so its cleanup can
                # finish before the supervised group leader exits.
                command = [
                    "/bin/sh", "-c",
                    'xvfb="$1"; shift; "$xvfb" -a "$@"; '
                    'rc=$?; sleep 0.25; exit "$rc"',
                    "pcb-enclosure-headless", shutil.which("xvfb-run"),
                    *command,
                ]
            result = run_bounded(command, timeout_s=300)
            diagnostic = result.stdout + result.stderr
            if result.returncode or "ERROR:" in diagnostic or \
                    not temporary.is_file() or temporary.stat().st_size == 0:
                raise EnclosureError(
                    "OpenSCAD render failed:\n" + diagnostic[-4000:])
    except (OSError, EnclosureError) as exc:
        print(f"ENCLOSURE RENDER ERROR — input: {args.source}: {exc}",
              file=sys.stderr)
        return 1
    print(f"ENCLOSURE RENDERED — input: {args.source} — 1/1 image")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
