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

G-INPUT / G-COVER (canon M-COVER, 2026-07-27). Three defects, all the same
shape — a verdict that did not say what it had looked at:

  * it named the SOURCE KIND ("board", "netlist") but never the PATH, so a
    reader could not tell which of several `.kicad_pcb` files was globbed, nor
    a sealed board from a `06_build` reconstruction (canon M-SHIP);
  * it printed no `N/M` denominator, so a project where two sources each
    carried ONE refdes read exactly like one where they carried two hundred;
  * `missing[:8]` TRUNCATED the finding SILENTLY. A campaign report quoted
    "8 refs" from this line when the real symmetric difference was 12. The
    truncated list is retained (a 200-ref dump helps nobody) but it now states
    the full count beside it.

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


def listing(items, cap=8):
    """A truncated sample that DECLARES its truncation and its full count.
    `missing[:8]` reported 8 of 12 refs as though 8 were the answer."""
    items = sorted(items)
    if not items:
        return "[]"
    if len(items) <= cap:
        return f"{items} ({len(items)})"
    return f"{items[:cap]} ... +{len(items) - cap} more, {len(items)} TOTAL"


def pick(paths, want, kind):
    """Choose ONE artifact, and refuse to guess on a multi-board project.

    THE DEFECT THIS REPLACES (measured 2026-07-28, smc0985-cooksense): every
    caller site did `paths[0]` on an UNSORTED glob. On the fleet's one
    multi-board project that silently graded `interposer.kicad_pcb`,
    `interposer.kicad_sch` and `interposer.net` against COOKSENSE's manifest and
    reported `S-COUNT FAIL: 0/4` — 3 of the 4 "disagreements" were the tool
    reading a different board, not the board disagreeing with itself. `--board`
    was accepted on the command line and silently ignored, because this script
    never parsed anything past argv[1].

    Silence is the part that had to go. An unsorted `[0]` is not even
    deterministic between runs, so a green result could not be trusted either.
    """
    paths = sorted(paths)
    if not paths:
        return None
    if want:
        hit = [p for p in paths if Path(p).stem == want]
        if not hit:
            sys.exit(f"count_parity: --board {want!r} matches no {kind}; "
                     f"have {[Path(p).stem for p in paths]}")
        return hit[0]
    if len(paths) > 1:
        sys.exit(f"count_parity: {len(paths)} {kind} artifacts and no --board: "
                 f"{[Path(p).stem for p in paths]}. This project builds more "
                 f"than one board; name the one to grade with --board <stem>. "
                 f"(Refusing to pick one silently — that is the defect this "
                 f"check exists to catch.)")
    return paths[0]


def main():
    proj = Path(sys.argv[1]).resolve()
    want = ""
    if "--board" in sys.argv:
        i = sys.argv.index("--board")
        if i + 1 >= len(sys.argv):
            sys.exit("count_parity: --board needs a board stem")
        want = sys.argv[i + 1]
    ts = proj / "03_tscircuit"
    sources = {}
    origin = {}          # source kind -> the PATH it was actually read from

    mp = ts / "manifest.yaml"
    if mp.exists() and yaml:
        y = yaml.safe_load(mp.read_text(encoding="utf-8-sig")) or {}
        comps = y.get("components") or []
        sources["manifest"] = keep({str(c) for c in comps})
        origin["manifest"] = str(mp)

    for cj in [ts / "build" / "circuit.json",
               *glob.glob(str(ts / "dist" / "**" / "circuit.json"),
                          recursive=True)]:
        if Path(cj).exists():
            d = json.loads(Path(cj).read_text(encoding="utf-8-sig"))
            sources["circuit.json"] = keep(
                {e.get("name") for e in d if e.get("type") == "source_component"})
            origin["circuit.json"] = str(cj)
            break

    sch = pick(glob.glob(str(ts / "kicad" / "*.kicad_sch")), want, "kicad_sch")
    if sch:
        txt = Path(sch).read_text(encoding="utf-8-sig")
        refs = set()
        for m in re.finditer(
                r'\(symbol \(lib_id[^\n]*\n.{0,1200}?\(property "Reference" "([^"]+)"',
                txt, re.S):
            refs.add(m.group(1))
        sources["kicad_sch"] = keep(refs)
        origin["kicad_sch"] = sch

    board = pick(glob.glob(str(proj / "04_kicad" / "*.kicad_pcb")), want, "board")
    if board:
        txt = Path(board).read_text(errors="replace")
        refs = set(re.findall(
            r'\(property "Reference" "([^"]+)"', txt))
        sources["board"] = keep(refs)
        origin["board"] = board

    net = pick(glob.glob(str(proj / "06_build" / "netlists" / "*.net"))
               + glob.glob(str(proj / "06_build" / "*.net")), want, "netlist")
    if net:
        txt = Path(net).read_text(errors="replace")
        sources["netlist"] = keep(set(re.findall(
            r'\(comp\s+\(ref "?([^")\s]+)', txt)))
        origin["netlist"] = net

    # G-INPUT: name every artifact actually read, by PATH. A glob that picked
    # the wrong one of several files is invisible otherwise.
    print(f"input: project = {proj}")
    for n in sorted(origin):
        print(f"input: {n:<12} = {origin[n]}  ({len(sources[n])} refdes)")

    if len(sources) < 2:
        print(f"S-COUNT: N-A — {len(sources)}/2 refdes sources found in "
              f"{proj.name}; parity needs two representations to compare")
        sys.exit(0)

    names = sorted(sources)
    base_name = "manifest" if "manifest" in sources else names[0]
    base = sources[base_name]

    # G-COVER: a zero denominator is a FAIL. Two sources that each contain no
    # refdes agree perfectly and prove nothing — and a silent `tsci build`
    # drop of EVERY component is exactly the incident this gate exists for.
    if not base:
        print(f"FAIL S-COUNT: 0 refdes in the base source {base_name!r} "
              f"({origin.get(base_name)}) — every comparison would be "
              f"vacuously equal. A zero denominator is a FAIL, never a pass "
              f"(canon M-COVER)")
        sys.exit(1)

    bad = 0
    pairs = len(names) - 1
    for n in names:
        if n == base_name:
            continue
        missing = base - sources[n]
        extra = sources[n] - base
        if missing or extra:
            bad += 1
            print(f"FAIL S-COUNT {n} vs {base_name}: "
                  f"{len(base & sources[n])}/{len(base | sources[n])} refdes "
                  f"agree; missing {listing(missing)} extra {listing(extra)}")
        else:
            print(f"ok   {n} == {base_name} "
                  f"({len(base)}/{len(base)} components)")
    if "manifest" not in sources:
        print("note: no 03_tscircuit/manifest.yaml — generated artifacts can "
              "agree with each other after a silent drop; declare intent")
    if bad:
        print(f"S-COUNT FAIL: {pairs - bad}/{pairs} source pair(s) agree with "
              f"{base_name} over {len(base)} refdes")
        sys.exit(1)
    print(f"S-COUNT PASS: {pairs}/{pairs} source pair(s) agree with "
          f"{base_name} over {len(base)} refdes")
    sys.exit(0)


if __name__ == "__main__":
    main()
