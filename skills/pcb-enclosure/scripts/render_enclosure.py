#!/usr/bin/env python3
"""Render a generated enclosure assembly with a deterministic camera."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


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
    if executable is None or not args.source.is_file():
        print(f"ENCLOSURE RENDER ERROR — input: {args.source}: executable/source missing",
              file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = [executable, "-o", str(args.output), "--imgsize", args.size,
               "--viewall", "--autocenter", "--projection", "ortho",
               "--colorscheme", "Tomorrow Night", "-D", 'part="assembly"',
               "-D", "show_reference_board=true", str(args.source)]
    if not os.environ.get("DISPLAY") and shutil.which("xvfb-run"):
        command = [shutil.which("xvfb-run"), "-a", *command]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    if result.returncode or not args.output.is_file() or args.output.stat().st_size == 0:
        print(f"ENCLOSURE RENDER ERROR — input: {args.source}:\n{result.stdout[-4000:]}",
              file=sys.stderr)
        return 1
    print(f"ENCLOSURE RENDERED — input: {args.source} — 1/1 image")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
