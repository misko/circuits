#!/usr/bin/env python3
"""Pre-flight for tscircuit authoring: alphanumeric pads must be mapped BEFORE
`tsci build`, or tscircuit drops the part silently (canon S-COUNT's cause).

tscircuit `<chip>` accepts only `pin<number>` pin ids derived from footprint
portHints. A KiCad footprint with alphanumeric pad names — USB-C `A1..B12`,
shield `SH`, some EP conventions — is rejected WITHOUT failing the build
(2026-07-21 incident: 4 USB connectors dropped, ERC still 0).

Rule enforced here: every part.yaml whose `pins:` map contains a
non-numeric pad name must have every such pad covered in
`03_tscircuit/parity_padmap.txt` (the documented tsx-number -> real-pad
mapping consumed by kicad_sch_parity.py). Run before the first tsci build
and in the schematic gate.

usage: tsx_preflight.py PROJECT_DIR      (exit 1 = uncovered alphanumeric pads)

G-INPUT / G-COVER (canon M-COVER, 2026-07-27). Three holes, all the same
shape as the incident this gate exists to prevent:

  * `if not yaml: break` LEFT THE LOOP and fell through to
    "TSX-PRE: all multi-pin pad names tsx-safe or mapped". With PyYAML absent
    the gate graded ZERO parts and printed a pass.
  * a project with no `02_parts/*/part.yaml` — a wrong directory, a stage not
    yet run — printed the same pass.
  * the verdict named neither the project nor the padmap file the whole check
    depends on, and `pads[:6]` truncated the finding silently.

There is nothing subtle here: this is `jlc_twin` exiting 0 on 11 unverified
parts, in a different file.
"""
import argparse
import glob
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def main(argv=None):
    ap = argparse.ArgumentParser(description="TSX-PRE pad-name pre-flight")
    ap.add_argument("project", help="PROJECT_DIR")
    args = ap.parse_args(argv)
    proj = Path(args.project).resolve()

    if yaml is None:
        print("TSX-PRE LOAD ERROR: PyYAML is not available, so 0 part.yaml "
              "could be read. A gate that cannot parse its input FAILS and "
              "says so; it does not fall through to a pass (canon M-COVER)")
        return 2

    padmap_p = proj / "03_tscircuit" / "parity_padmap.txt"
    padmap = padmap_p.read_text(encoding="utf-8-sig") if padmap_p.exists() else ""
    parts = sorted(glob.glob(str(proj / "02_parts" / "*" / "part.yaml")))

    # G-INPUT: name the project, the padmap, and how many parts were in scope.
    print(f"input: project = {proj}")
    print(f"input: padmap  = {padmap_p}"
          f"{'' if padmap_p.exists() else '  (ABSENT — every alphanumeric pad '
                                          'is therefore uncovered)'}")

    # G-COVER: a zero denominator is a FAIL.
    if not parts:
        print(f"TSX-PRE FAIL: 0/0 parts graded — no 02_parts/*/part.yaml under "
              f"{proj}. There is nothing this pre-flight could have checked, "
              f"and a green verdict over zero parts is the silent-drop class "
              f"it exists to catch (canon M-COVER)")
        return 1

    bad, multipin = [], 0
    for py in parts:
        y = yaml.safe_load(Path(py).read_text(encoding="utf-8-sig")) or {}
        pins = y.get("pins") or {}
        if len(pins) > 2:
            multipin += 1
        alnum = [str(k) for k in pins
                 if not re.fullmatch(r"\d+", str(k))]
        uncovered = [p for p in alnum if p not in padmap]
        if uncovered:
            bad.append((y.get("mpn", Path(py).parent.name), uncovered))
    if bad:
        for mpn, pads in bad:
            extra = ("" if len(pads) <= 6 else
                     f" ... +{len(pads) - 6} more, {len(pads)} TOTAL")
            print(f"FAIL TSX-PRE {mpn}: alphanumeric pads {pads[:6]}{extra} "
                  f"not in 03_tscircuit/parity_padmap.txt")
        print("remedy: number these pins in the tsx (<chip> needs pin<N>), "
              "record 'tsxN realpad' lines in parity_padmap.txt — otherwise "
              "tsci DROPS the part silently (2026-07-21 incident)")
        print(f"TSX-PRE FAIL: {len(parts) - len(bad)}/{len(parts)} part.yaml "
              f"tsx-safe or mapped ({multipin} multi-pin)")
        return 1
    print(f"TSX-PRE PASS: {len(parts)}/{len(parts)} part.yaml have all "
          f"multi-pin pad names tsx-safe or mapped ({multipin} multi-pin)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
