#!/usr/bin/env python3
"""Refdes SET parity across every representation of the board (canon S-COUNT).

Motivating incident (2026-07-21, clean-room usb-pwr-hub-3s): `tsci build`
silently DROPPED all four USB connectors — 48/52 components, ERC still 0
errors — because tscircuit rejects alphanumeric pad ids without failing the
build. Only the agent's hand count caught it. A green that was never counted
is a claim, not a gate.

Sources compared (any that exist in the project):
  manifest      03_tscircuit/manifest.yaml `components:` list — the AUTHOR'S
                declared intent, written when the tsx is authored. This is the
                source that catches a silent drop (all generated artifacts
                agree with each other after a drop; only intent disagrees).
  circuit.json  03_tscircuit/build/circuit.json source_component names
  kicad_sch     03_tscircuit/kicad/*.kicad_sch symbol Reference properties
  board         04_kicad/*.kicad_pcb footprint refs
  netlist       06_build/netlists/*.net or 06_build/*.net (comp (ref X))

Excluded everywhere: refs starting with `H` (mounting holes), `#` (power
symbols), `FID` (fiducials), `LOGO`.

Exit 1 on any pairwise mismatch, printing the SYMMETRIC DIFFERENCE — the
missing part is named, not just counted.

usage: count_parity.py PROJECT_DIR
"""
import glob
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SKIP = re.compile(r"^(H\d|#|FID|LOGO)")


def keep(refs):
    return {r for r in refs if r and not SKIP.match(r)}


def main():
    proj = Path(sys.argv[1]).resolve()
    ts = proj / "03_tscircuit"
    sources = {}

    mp = ts / "manifest.yaml"
    if mp.exists() and yaml:
        y = yaml.safe_load(mp.read_text()) or {}
        comps = y.get("components") or []
        sources["manifest"] = keep({str(c) for c in comps})

    for cj in [ts / "build" / "circuit.json",
               *glob.glob(str(ts / "dist" / "**" / "circuit.json"),
                          recursive=True)]:
        if Path(cj).exists():
            d = json.loads(Path(cj).read_text())
            sources["circuit.json"] = keep(
                {e.get("name") for e in d if e.get("type") == "source_component"})
            break

    schs = glob.glob(str(ts / "kicad" / "*.kicad_sch"))
    if schs:
        txt = Path(schs[0]).read_text()
        refs = set()
        for m in re.finditer(
                r'\(symbol \(lib_id[^\n]*\n.{0,1200}?\(property "Reference" "([^"]+)"',
                txt, re.S):
            refs.add(m.group(1))
        sources["kicad_sch"] = keep(refs)

    boards = glob.glob(str(proj / "04_kicad" / "*.kicad_pcb"))
    if boards:
        txt = Path(boards[0]).read_text(errors="replace")
        refs = set(re.findall(
            r'\(property "Reference" "([^"]+)"', txt))
        sources["board"] = keep(refs)

    nets = (glob.glob(str(proj / "06_build" / "netlists" / "*.net"))
            + glob.glob(str(proj / "06_build" / "*.net")))
    if nets:
        txt = Path(nets[0]).read_text(errors="replace")
        sources["netlist"] = keep(set(re.findall(
            r'\(comp\s+\(ref "?([^")\s]+)', txt)))

    if len(sources) < 2:
        print(f"S-COUNT: N-A — fewer than 2 refdes sources found in {proj.name}")
        sys.exit(0)

    names = sorted(sources)
    base_name = "manifest" if "manifest" in sources else names[0]
    base = sources[base_name]
    bad = 0
    for n in names:
        if n == base_name:
            continue
        missing = sorted(base - sources[n])
        extra = sorted(sources[n] - base)
        if missing or extra:
            bad += 1
            print(f"FAIL S-COUNT {n} vs {base_name}: "
                  f"missing {missing[:8] or '[]'} extra {extra[:8] or '[]'}")
        else:
            print(f"ok   {n} == {base_name} ({len(base)} components)")
    if "manifest" not in sources:
        print("note: no 03_tscircuit/manifest.yaml — generated artifacts can "
              "agree with each other after a silent drop; declare intent")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
