#!/usr/bin/env python3
"""Render a saved KiCad board with the exact model-resolution environment.

Raw ``kicad-cli pcb render`` does not necessarily inherit the fallback model
directories used by pcbnew or the GUI.  This wrapper first runs the same saved-
board resolver as P-MODEL, then passes every referenced model-directory token
to the renderer with ``-D``.  A successful image therefore cannot lose all
stock KiCad bodies merely because the shell lacks KICAD10_3DMODEL_DIR.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from model_coverage_check import inspect, kicad_env


TOKEN = re.compile(r"\$\{([^}]+)\}|\$\(([^)]+)\)")


def required_defines(board_path: Path, rows):
    env = kicad_env(board_path)
    names = set()
    for row in rows:
        for model in row["models"]:
            for match in TOKEN.finditer(model["declared"]):
                name = match.group(1) or match.group(2)
                if name != "KIPRJMOD":
                    names.add(name)
    missing = sorted(name for name in names if not env.get(name))
    if missing:
        raise ValueError(f"model variables have no renderer value: {missing}")
    return {name: env[name] for name in sorted(names)}


def command(args, board_path: Path, output: Path, defines):
    result = ["kicad-cli", "pcb", "render"]
    for name, value in defines.items():
        result += ["-D", f"{name}={value}"]
    result += [
        "--width", str(args.width), "--height", str(args.height),
        "--quality", args.quality, "--side", args.side,
        "--background", args.background,
    ]
    if args.floor:
        result.append("--floor")
    if args.perspective:
        result.append("--perspective")
    if args.rotate:
        result += ["--rotate", args.rotate]
    result += ["-o", str(output), str(board_path)]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("board")
    parser.add_argument("output")
    parser.add_argument("--side", choices=["top", "bottom", "left", "right",
                                            "front", "back"], default="top")
    parser.add_argument("--width", type=int, default=2400)
    parser.add_argument("--height", type=int, default=1400)
    parser.add_argument("--quality", choices=["basic", "high", "user",
                                               "job_settings"], default="high")
    parser.add_argument("--background", choices=["default", "transparent",
                                                  "opaque"], default="opaque")
    parser.add_argument("--floor", action="store_true")
    parser.add_argument("--perspective", action="store_true")
    parser.add_argument("--rotate")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    board_path = Path(args.board).resolve()
    output = Path(args.output).resolve()
    if not board_path.is_file():
        raise SystemExit(f"P-RENDER-ENV board does not exist: {board_path}")
    if args.width < 64 or args.height < 64:
        raise SystemExit("P-RENDER-ENV width and height must both be >= 64")

    rows = inspect(board_path)
    missing = [row for row in rows if not row["resolved"]]
    if missing or not rows:
        refs = [row["ref"] for row in missing]
        raise SystemExit(
            f"P-RENDER-ENV model coverage {len(rows)-len(missing)}/{len(rows)}; "
            f"unresolved refs: {refs}")
    try:
        defines = required_defines(board_path, rows)
    except ValueError as exc:
        raise SystemExit(f"P-RENDER-ENV {exc}")
    invocation = command(args, board_path, output, defines)
    if args.dry_run:
        print(json.dumps({"board": str(board_path), "output": str(output),
                          "coverage": [len(rows), len(rows)],
                          "defines": defines, "command": invocation},
                         indent=2, sort_keys=True))
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    before = output.stat().st_mtime_ns if output.exists() else None
    result = subprocess.run(invocation)
    if result.returncode:
        return result.returncode
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit(f"P-RENDER-ENV renderer produced no image: {output}")
    if before is not None and output.stat().st_mtime_ns == before:
        raise SystemExit(f"P-RENDER-ENV output was not refreshed: {output}")
    print(f"P-RENDER-ENV PASS: {len(rows)}/{len(rows)} model paths; "
          f"{len(defines)} renderer define(s) -> {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
