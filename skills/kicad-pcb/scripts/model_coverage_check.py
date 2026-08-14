#!/usr/bin/env python3
"""Fail when a fitted board footprint has no renderer-resolvable 3D body.

KiCad deliberately treats a missing 3D model as non-fatal, so a successful
headless render is not evidence that every fitted component was drawn.  This
gate walks the independent saved-board state and resolves model paths in the
same environment in which the renderer will run.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import pcbnew


def kicad_env(board_path):
    """Return the renderer's practical ${VAR} substitution table."""
    env = {}
    for ver in ("10.0", "9.0", "8.0", "7.0"):
        cfg = Path.home() / ".config" / "kicad" / ver / "kicad_common.json"
        if not cfg.is_file():
            continue
        try:
            values = ((json.loads(cfg.read_text(encoding="utf-8-sig"))
                       .get("environment") or {}).get("vars") or {})
            env.update({str(k): str(v) for k, v in values.items()})
        except (OSError, ValueError, TypeError):
            pass
    env.update({k: v for k, v in os.environ.items() if k.startswith("KICAD")})
    user_3d = Path.home() / ".local" / "share" / "kicad" / "10.0" / "3dmodels"
    system_3d = Path("/usr/share/kicad/3dmodels")
    default_3d = str(user_3d if user_3d.is_dir() else system_3d)
    for name, default in (("KICAD10_3DMODEL_DIR", default_3d),
                          ("KICAD9_3DMODEL_DIR", str(system_3d)),
                          ("KICAD8_3DMODEL_DIR", str(system_3d)),
                          ("KISYS3DMOD", default_3d)):
        env.setdefault(name, default)
    env["KIPRJMOD"] = str(Path(board_path).resolve().parent)
    return env


def resolve_model(filename, env, base):
    value = str(filename)
    for _ in range(4):
        before = value
        for key, replacement in env.items():
            value = value.replace("${%s}" % key, replacement)
            value = value.replace("$(%s)" % key, replacement)
        if value == before:
            break
    if "${" in value or "$(" in value:
        return None
    path = Path(os.path.expanduser(value))
    candidates = [path] if path.is_absolute() else [Path(base) / path, path]
    for candidate in candidates:
        try:
            if candidate.is_file() and candidate.stat().st_size > 0:
                return str(candidate.resolve())
        except OSError:
            pass
    return None


def fitted(fp):
    attrs = fp.GetAttributes()
    skip = (getattr(pcbnew, "FP_EXCLUDE_FROM_BOM", 0)
            | getattr(pcbnew, "FP_BOARD_ONLY", 0)
            | getattr(pcbnew, "FP_DNP", 0))
    return not bool(attrs & skip)


def inspect(board_path):
    board_path = Path(board_path).resolve()
    board = pcbnew.LoadBoard(str(board_path))
    env = kicad_env(board_path)
    rows = []
    for fp in sorted((fp for fp in board.GetFootprints() if fitted(fp)),
                     key=lambda item: item.GetReference()):
        entries = []
        for model in fp.Models():
            declared = str(model.m_Filename)
            entries.append({"declared": declared,
                            "resolved": resolve_model(declared, env,
                                                      board_path.parent)})
        rows.append({"ref": fp.GetReference(), "value": fp.GetValue(),
                     "models": entries,
                     "resolved": any(row["resolved"] for row in entries)})
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("board", help="saved .kicad_pcb to inspect")
    parser.add_argument("-o", "--output", help="optional deterministic JSON report")
    args = parser.parse_args(argv)

    print(f"MODEL-COVERAGE input: {Path(args.board).resolve()}")
    rows = inspect(args.board)
    missing = [row for row in rows if not row["resolved"]]
    report = {
        "gate": "MODEL-COVERAGE",
        "board": str(Path(args.board).resolve()),
        "population": "fitted footprints (BOM, non-DNP, non-board-only)",
        "resolved": len(rows) - len(missing),
        "total": len(rows),
        "missing": missing,
        "footprints": rows,
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    for row in missing:
        if row["models"]:
            detail = "; ".join(m["declared"] for m in row["models"])
            print(f"FAIL MODEL-COVERAGE {row['ref']}: unresolved {detail}")
        else:
            print(f"FAIL MODEL-COVERAGE {row['ref']}: no 3D model entry")
    resolved = report["resolved"]
    total = report["total"]
    verdict = "PASS" if not missing and total else "FAIL"
    print(f"{verdict} MODEL-COVERAGE: {resolved}/{total} fitted footprints "
          "have a renderer-resolvable 3D body")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
