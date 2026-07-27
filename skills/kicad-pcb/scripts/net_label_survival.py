#!/usr/bin/env python3
"""net_label_survival.py — the schematic NET-MERGE gate (candidate S-NETMERGE).

THE CLASS (crow-recorder-central-v2, 2026-07-23, two DO-NOT-ORDER defects on
one board, red-team P0): `kicad-cli sch export netlist` CONNECTS wires whose
endpoint touches another wire (T-junction) or that overlap collinearly. A
schematic net label silently merges into a foreign net at export:

  1. P5VA_4 -> AUDIO4M: a vertical P5VA_4 wire passed exactly through the
     AUDIO4M wires' junction — the merged net took the name AUDIO4M, port 4's
     +5V-audio pins landed on the ch4 balanced-minus into the ADC.
  2. MID2P -> 5V: the 5V trunk ran collinear-overlapping the MID2P wire —
     the ch2 RC mid-node DC-shorted to the 5V rail.

Every downstream gate stayed green (ERC 0, DRC 0/0, count_parity 194==194)
because they are all SELF-consistent with the merged netlist; nothing compared
LABEL INTENT vs exported net membership. This gate does (canon M1: the labels
are authored intent, the netlist is the exporter's output — different methods).

TWO CHECKS, both against the exported netlist:

  1. LABEL SURVIVAL (generic, always on, zero config): every global_label
     name in the schematic must exist as a net name in the exported netlist.
     A label swallowed by a geometric merge disappears from the netlist while
     remaining in the schematic text — this is the check that found MID2P.

  2. PIN MAP (config-driven, board-specific): pin-for-pin net assertions from
     the OPTIONAL `label_survival:` block in
     03_src/rules/electrical_invariants.yaml — the generalization of the
     crow-recorder 8-port RJ45 map. Schema (all keys optional):

       label_survival:
         exempt:                       # labels ALLOWED to be absent — each
           - {label: NAME, why: "…"}   #   needs evidence (canon M4)
         pin_map:
           - refs: [J3, J4, …]         # each ref checked; {n} in a net
             n_start: 1                #   pattern = n_start + position
             pins: {"1": "AUDIO{n}P", "4": "P5VA_{n}", "5": GND}
             unconnected: ["9", "10"]  # pins that must NOT carry a real net

USAGE
-----
  net_label_survival.py PROJECT_DIR
      Auto-locates: schematic = 03_tscircuit/kicad/*.kicad_sch (the committed
      pinned artifact) else 04_kicad/*.kicad_sch; netlist =
      06_build/netlists/*.net else 06_build/*.net; config = the
      `label_survival:` block of 03_src/rules/electrical_invariants.yaml
      (absent block -> check 1 still runs, check 2 is N-A).
  --schematic / --netlist / --config PATH   override auto-location.

Exit 0 = pass, 1 = findings (LABEL-LOST / PIN-MAP), 2 = load/config error.
No pcbnew import — runs on any python3 (PyYAML only needed for the config).
"""
import argparse
import glob
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:      # config block then unavailable; check 1 still runs
    yaml = None


class LoadError(Exception):
    """A config/input problem — distinct from a gate finding."""


def parse_netlist(text):
    """(netnames set, {(ref, pin): netname}) from an exported .net."""
    flat = re.sub(r"\s+", " ", text)
    nets = re.findall(
        r'\(net \(code "[^"]*"\) \(name "([^"]+)"\)(.*?)(?=\(net \(code|\Z)',
        flat)
    pad2net = {}
    for name, body in nets:
        for r, p in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)',
                               body):
            pad2net[(r, p)] = name
    return {n for n, _ in nets}, pad2net


def schematic_labels(text):
    return set(re.findall(r'\(global_label "([^"]+)"', text))


def load_config(path):
    """The validated `label_survival:` block, or {} when absent. Raises
    LoadError on schema problems (an exempt entry without evidence, a pin_map
    entry without refs/pins)."""
    p = Path(path)
    if not p.is_file():
        return {}
    if yaml is None:
        raise LoadError("PyYAML unavailable but a config file exists")
    data = yaml.safe_load(p.read_text()) or {}
    blk = data.get("label_survival") if isinstance(data, dict) else None
    if blk is None:
        return {}
    if not isinstance(blk, dict):
        raise LoadError("label_survival: must be a mapping")
    for i, ex in enumerate(blk.get("exempt") or []):
        if not isinstance(ex, dict) or not ex.get("label"):
            raise LoadError(f"label_survival.exempt[{i}] needs 'label:'")
        if len(str(ex.get("why", "")).strip()) < 5:
            raise LoadError(
                f"label_survival.exempt[{i}] ({ex['label']}) is missing a "
                f"substantive 'why:' — an exemption without evidence is "
                f"itself a defect (canon M4)")
    for i, pm in enumerate(blk.get("pin_map") or []):
        if not isinstance(pm, dict) or not pm.get("refs") \
                or not isinstance(pm.get("pins"), dict):
            raise LoadError(f"label_survival.pin_map[{i}] needs 'refs:' "
                            f"(list) and 'pins:' (pin -> net pattern map)")
    return blk


def survival_findings(labels, netnames, exempt):
    ex = {e["label"] for e in exempt}
    out = []
    for l in sorted(labels - netnames):
        if l in ex:
            continue
        out.append(f"LABEL-LOST: schematic global_label {l!r} is not a net in "
                   f"the netlist — geometric merge/swallow at export (the "
                   f"P5VA_4/MID2P class)")
    return out


def pin_map_findings(pin_map, pad2net):
    out = []
    for pm in pin_map:
        n0 = int(pm.get("n_start", 1))
        for i, ref in enumerate(pm["refs"]):
            n = n0 + i
            for pin, pattern in pm["pins"].items():
                want = str(pattern).format(n=n)
                got = pad2net.get((str(ref), str(pin)))
                if got != want:
                    out.append(f"PIN-MAP: {ref}.{pin} = {got!r}, want {want!r}")
            for pin in pm.get("unconnected") or []:
                got = pad2net.get((str(ref), str(pin)), "")
                if got and not got.startswith("unconnected-"):
                    out.append(f"PIN-MAP: {ref}.{pin} = {got!r}, want "
                               f"unconnected")
    return out


def _first(patterns):
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="label-intent vs exported-netlist gate (candidate "
                    "S-NETMERGE)")
    ap.add_argument("project")
    ap.add_argument("--schematic", default="")
    ap.add_argument("--netlist", default="")
    ap.add_argument("--config", default="")
    a = ap.parse_args(argv)
    proj = Path(a.project).resolve()

    sch = a.schematic or _first([str(proj / "03_tscircuit" / "kicad" / "*.kicad_sch"),
                                 str(proj / "04_kicad" / "*.kicad_sch")])
    net = a.netlist or _first([str(proj / "06_build" / "netlists" / "*.net"),
                               str(proj / "06_build" / "*.net")])
    if not sch or not Path(sch).is_file():
        print(f"S-NETMERGE: LOAD ERROR — no schematic found in {proj}")
        return 2
    if not net or not Path(net).is_file():
        print(f"S-NETMERGE: LOAD ERROR — no exported netlist found in {proj}")
        return 2
    try:
        cfg = load_config(a.config or
                          proj / "03_src" / "rules" / "electrical_invariants.yaml")
    except LoadError as e:
        print(f"S-NETMERGE: LOAD ERROR — {e}")
        return 2

    labels = schematic_labels(Path(sch).read_text())
    netnames, pad2net = parse_netlist(Path(net).read_text())
    if not netnames:
        print(f"S-NETMERGE: LOAD ERROR — netlist {net} parsed 0 nets (format "
              f"change? a parse that yields zero results is an error)")
        return 2

    # G-COVER: a zero LABEL census is a FAIL. `parse 0 nets` was already
    # caught above, but a schematic that yields ZERO global labels — a
    # KiCad format change, a sheet that never got its labels, the wrong file
    # globbed — made `survival_findings` iterate nothing and print
    # "PASS — 0 labels all survive", which is true and worthless. The whole
    # incident this gate pins (P5VA_4 -> AUDIO4M) is a label that vanished.
    if not labels:
        print(f"S-NETMERGE: LOAD ERROR — schematic {sch} parsed 0 global "
              f"labels. Every label trivially survives, so the check would "
              f"pass over nothing; a zero denominator is a FAIL, never a "
              f"skip (canon M-COVER)")
        return 2

    bad = survival_findings(labels, netnames, cfg.get("exempt") or [])
    pm = cfg.get("pin_map") or []
    bad += pin_map_findings(pm, pad2net)
    pins = sum(len(p["pins"]) * len(p["refs"]) for p in pm)

    # G-INPUT: name both artifacts by path (canon M-SHIP — a 06_build netlist
    # is a reconstruction, and a reader must be able to see that it is one).
    print(f"input: schematic = {sch}")
    print(f"input: netlist   = {net}  ({len(netnames)} nets)")

    if bad:
        print(f"net_label_survival: FAIL — {len(labels) - len(bad)}/"
              f"{len(labels)} labels survive, {pins} pin-map assertion(s) "
              f"checked; {len(bad)} finding(s)")
        for m in bad:
            print("  " + m)
        return 1
    print(f"net_label_survival: PASS — {len(labels)}/{len(labels)} labels "
          f"survive to the netlist"
          + (f"; {pins}/{pins} pin-map assertions hold" if pins
             else "; 0 pin_map assertions configured (survival only)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
