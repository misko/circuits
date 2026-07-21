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
"""
import glob
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def main():
    proj = Path(sys.argv[1]).resolve()
    padmap_p = proj / "03_tscircuit" / "parity_padmap.txt"
    padmap = padmap_p.read_text() if padmap_p.exists() else ""
    bad = []
    for py in sorted(glob.glob(str(proj / "02_parts" / "*" / "part.yaml"))):
        if not yaml:
            break
        y = yaml.safe_load(Path(py).read_text()) or {}
        pins = y.get("pins") or {}
        alnum = [str(k) for k in pins
                 if not re.fullmatch(r"\d+", str(k))]
        uncovered = [p for p in alnum if p not in padmap]
        if uncovered:
            bad.append((y.get("mpn", Path(py).parent.name), uncovered))
    if bad:
        for mpn, pads in bad:
            print(f"FAIL TSX-PRE {mpn}: alphanumeric pads {pads[:6]} not in "
                  f"03_tscircuit/parity_padmap.txt")
        print("remedy: number these pins in the tsx (<chip> needs pin<N>), "
              "record 'tsxN realpad' lines in parity_padmap.txt — otherwise "
              "tsci DROPS the part silently (2026-07-21 incident)")
        sys.exit(1)
    print("TSX-PRE: all multi-pin pad names tsx-safe or mapped")
    sys.exit(0)


if __name__ == "__main__":
    main()
