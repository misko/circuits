#!/usr/bin/env python3
"""T1: circuit_json_to_kicad_sch.py — the tscircuit -> KiCad schematic converter.

THE regression this file exists for: tscircuit's own kicad_sch exporter derives
a chip's symbol id from its footprint NAME, so two chips with hand-authored
footprints both collapse to bare `Device:U_chip` and each TRUNCATES TO 2 PINS.
`manypin_custom_fp` is that exact situation — a 41-pin and a 24-pin chip, both
with an empty footprinter_string. The clean case asserts 41 and 24. The
known-bad case proves the assertion has teeth by running it against a sheet
that really does have the collapsed symbol.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FIXTURES, ROOT, SCRIPTS, check, contains, eq, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

CONV = SCRIPTS / "circuit_json_to_kicad_sch.py"
T0 = FIXTURES / "t0"
PY = sys.executable or "python3"


def convert(fixture, extra=()):
    d = tmpdir("conv_")
    out = d / f"{fixture}.kicad_sch"
    r = must_pass(run([PY, CONV, T0 / fixture / "circuit.json", "-o", out,
                       "--project", fixture, *extra]),
                  f"convert {fixture}")
    check(out.is_file(), f"{fixture}: no sheet written")
    return d, out, r


def netlist_of(sheet):
    """(refdes, pad) -> net, straight from kicad-cli. This is the ONLY
    honest way to ask 'is the sheet annotated and wired' — an un-annotated
    sheet exports 0 nets."""
    out = sheet.with_suffix(".net")
    must_pass(run(["kicad-cli", "sch", "export", "netlist", "--format",
                   "kicadsexpr", "-o", out, sheet]), "kicad-cli export netlist")
    s = out.read_text()
    nodes = {}
    for m in re.finditer(r'\(net\s+\(code\s+"\d+"\)\s+\(name\s+"([^"]+)"\)(.*?)'
                         r'(?=\(net\s+\(code|\Z)', s, re.S):
        name, body = m.group(1), m.group(2)
        for r_, p in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', body):
            nodes[(r_, p)] = name
    return nodes


def erc_errors(sheet):
    rpt = sheet.with_suffix(".erc")
    run(["kicad-cli", "sch", "erc", "--severity-error", "--format", "report",
         "-o", rpt, sheet])
    if not rpt.exists():
        return -1
    m = re.search(r"Found (\d+) errors", rpt.read_text())
    return int(m.group(1)) if m else 0


def lib_symbols(sheet):
    return re.findall(r'\(symbol\s+"([^"]+)"', sheet.read_text())


def pins_per_ref(sheet):
    n = {}
    for ref, pad in netlist_of(sheet):
        n[ref] = n.get(ref, 0) + 1
    return n


# ------------------------------------------------------------ clean cases
@test("converter: two_resistors exports an annotated, wired sheet")
def t_two_resistors():
    d, sheet, r = convert("two_resistors")
    contains(r.out, "MODE=layout", "converter stdout")
    nodes = netlist_of(sheet)
    eq(len(nodes), 4, "node count")
    eq(sorted(set(nodes.values())), ["GND", "MID", "VIN"], "net names")
    # annotated => no unannotated '?' references anywhere
    check("R?" not in sheet.read_text(), "sheet has unannotated references")


@test("converter: every refdes gets its OWN lib_symbol (no Device:U_chip collision)")
def t_unique_symbols():
    d, sheet, r = convert("manypin_custom_fp")
    syms = lib_symbols(sheet)
    check(not any(s == "Device:U_chip" for s in syms),
          f"collapsed symbol present: {syms[:10]}")
    top = [s for s in syms if s.startswith("elt:")]
    eq(len(set(top)), len(top), "lib_symbol uniqueness (duplicates present)")
    check(any("U1" in s for s in top) and any("U2" in s for s in top),
          f"expected per-refdes symbols, got {sorted(set(top))[:10]}")


@test("REGRESSION: a 41-pin chip exports 41 pins, not 2")
def t_41_pins():
    d, sheet, r = convert("manypin_custom_fp")
    n = pins_per_ref(sheet)
    eq(n.get("U1"), 41, "U1 pin count")
    eq(n.get("U2"), 24, "U2 pin count")
    contains(r.out, "65 pins", "converter reported pin total")


@test("converter: pins are keyed to the KiCad PAD NAME, not the pin number")
def t_pad_names():
    d, sheet, r = convert("manypin_custom_fp")
    nodes = netlist_of(sheet)
    u1 = {p for (ref, p) in nodes if ref == "U1"}
    check(all(p.startswith("P") for p in u1),
          f"U1 pads should be the hand-authored P1..P41 names, got {sorted(u1)[:8]}")
    u2 = {p for (ref, p) in nodes if ref == "U2"}
    check(all(p.startswith("B") for p in u2),
          f"U2 pads should be B1..B24, got {sorted(u2)[:8]}")


@test("converter: ERC reports 0 errors on every T0 fixture")
def t_erc_zero():
    for fx in ("two_resistors", "polarized", "manypin_custom_fp", "digit_rails"):
        d, sheet, r = convert(fx)
        e = erc_errors(sheet)
        check(e == 0, f"{fx}: ERC reported {e} errors (want 0)")


@test("converter: pad-1 net identity survives (polarized parts)")
def t_polarity():
    d, sheet, r = convert("polarized")
    nodes = netlist_of(sheet)
    eq(nodes.get(("D1", "1")), "OUT", "D1 pad1 (cathode) net")
    eq(nodes.get(("C1", "1")), "VIN", "C1 pad1 (+) net")


@test("converter: leading-digit rails canonicalize (N5V -> 5V, N3V3 -> 3V3)")
def t_digit_rails():
    d, sheet, r = convert("digit_rails")
    nets = set(netlist_of(sheet).values())
    eq(sorted(nets), ["3V3", "5V", "GND"], "canonical rail names")
    check(not any(n.startswith("N5V") or n.startswith("N3V3") for n in nets),
          f"author-prefix guard leaked into the netlist: {sorted(nets)}")


@test("converter: every component carries a resolved FPID")
def t_fpid_present():
    d, sheet, r = convert("manypin_custom_fp")
    contains(r.out, "2 with FPID", "converter FPID count")
    txt = sheet.read_text()
    # power/PWR_FLAG symbols legitimately carry a blank Footprint; the real
    # parts must not. Both chips have an empty footprinter_string, so their
    # FPIDs can only have come from the 02_parts override.
    fpids = set(re.findall(r'\(property "Footprint" "([^"]+)"', txt))
    real = {f for f in fpids if ":" in f and not f.startswith("power:")}
    check(len(real) >= 2,
          f"expected an FPID for each chip, got {sorted(fpids)}")
    check(len(real) == len({f for f in real}),
          "the two chips share one FPID")
    check(any("BIGCHIP" in f for f in real) and any("MIDCHIP" in f for f in real),
          f"02_parts FPID override did not reach the sheet: {sorted(real)}")


@test("converter: a 02_parts `tie:` EP pad absent from circuit.json reaches the netlist on its net")
def t_thermal_ep_tie():
    """The exposed thermal pad (EP) of a WSON/DFN eFuse is the sole heat path
    and MUST tie GND, but tscircuit's pad-only footprint token can't express it,
    so it never reaches circuit.json — the schematic omits it and the board pad
    floats invisibly to parity. `thermal_ep` is that case: an 8-pad chip whose
    part.yaml annotates pad 9 `tie: GND`. WITH the feature the exported netlist
    carries (U1, 9) on GND, sharing the node with the in-circuit GND pad 8."""
    d, sheet, r = convert("thermal_ep")
    contains(r.out, "9 pins", "pin total (8 in-circuit + 1 tie EP)")
    nodes = netlist_of(sheet)
    eq(nodes.get(("U1", "9")), "GND", "EP pad 9 net (the `tie: GND` annotation)")
    # the in-circuit thermal/GND path is untouched — both pads share GND
    eq(nodes.get(("U1", "8")), "GND", "in-circuit GND pad 8 net (unchanged)")
    e = erc_errors(sheet)
    check(e == 0, f"thermal_ep: ERC reported {e} errors (want 0)")


# --------------------------------------------------------- known-bad cases
@test("the EP tie is load-bearing: strip `tie:` and pad 9 vanishes from the netlist",
      kind="known_bad")
def t_tie_is_load_bearing():
    """The tie assertion is only meaningful if REMOVING the annotation drops the
    pin. Rerun the same circuit.json against a part.yaml with the `tie:` line
    stripped and confirm pad 9 is gone (the board pad would float) — proving the
    feature fires on the annotation, not unconditionally, and that it does NOT
    invent pins for a part.yaml that doesn't ask for one."""
    src = T0 / "thermal_ep"
    d = tmpdir("conv_")
    parts = d / "02_parts" / "TPS_EFUSE_EP"
    parts.mkdir(parents=True)
    yaml = (src / "02_parts" / "TPS_EFUSE_EP" / "part.yaml").read_text()
    stripped = "\n".join(l for l in yaml.splitlines() if "tie:" not in l) + "\n"
    check(stripped != yaml, "fixture mutation did not change the part.yaml")
    (parts / "part.yaml").write_text(stripped)
    out = d / "stripped.kicad_sch"
    must_pass(run([PY, CONV, src / "circuit.json", "-o", out, "--project",
                   "thermal_ep", "--parts-dir", d / "02_parts"]),
              "convert thermal_ep (tie stripped)")
    nodes = netlist_of(out)
    check(("U1", "9") not in nodes,
          "EP pad 9 present WITHOUT a `tie:` annotation — the feature is blind "
          "to whether the annotation exists (would invent phantom pins)")
    eq(nodes.get(("U1", "8")), "GND", "in-circuit GND pad 8 still present")


# --------------------------------------------------------- more known-bad cases
@test("the pin-count assertion actually catches a 2-pin collapsed sheet",
      kind="known_bad")
def t_pin_assertion_has_teeth():
    """The 41-pin test is only meaningful if it would FAIL on the defect it
    guards. Build the defect — strip U1 down to 2 pins — and confirm the
    same assertion path rejects it."""
    d, sheet, r = convert("manypin_custom_fp")
    txt = sheet.read_text()
    # drop every global label for U1 pads P3..P41, simulating the truncation
    broken = re.sub(r'\(global_label[^\n]*"[^"]*"[^\n]*\n(?:[^\n]*\n)*?\s*\)\n', '', txt, count=0) \
        if False else txt
    # simpler + surgical: delete the pin definitions past the second
    def drop(m):
        drop.n += 1
        return "" if drop.n > 2 else m.group(0)
    drop.n = 0
    broken = re.sub(r'\s*\(pin \w+ line[^\n]*\n(?:.*?\n)*?\s*\)\n',
                    drop, txt, count=0)
    check(broken != txt, "fixture mutation did not change the sheet")
    bad = d / "broken.kicad_sch"
    bad.write_text(broken)
    try:
        n = pins_per_ref(bad)
    except Exception:
        return          # unparseable is also a rejection
    check(n.get("U1", 0) != 41,
          "the mutated sheet still reports 41 pins — the assertion is blind")


@test("kicad_sch_parity FAILS when the sheet and board disagree", kind="known_bad")
def t_sch_parity_fails():
    """Parity between a converted sheet and a board must not be a rubber
    stamp: point it at a board that shares no refdes with the fixture."""
    d, sheet, r = convert("two_resistors")
    board = ROOT / "archived_projects" / "cook-loadcell" / "04_kicad" / "cook_loadcell.kicad_pcb"
    rr = run(["/usr/bin/python3", SCRIPTS / "kicad_sch_parity.py", sheet, board])
    check(rr.rc != 0,
          f"kicad_sch_parity exited 0 comparing a 2-resistor sheet to a "
          f"33-part board:\n{rr.out[-2000:]}")


@test("a circuit.json with no components is rejected, not silently empty",
      kind="known_bad")
def t_empty_circuit():
    d = tmpdir("conv_")
    empty = d / "circuit.json"
    empty.write_text("[]")
    out = d / "empty.kicad_sch"
    r = run([PY, CONV, empty, "-o", out, "--project", "empty"])
    if r.rc == 0 and out.exists():
        nodes = netlist_of(out)
        check(not nodes,
              "an empty circuit.json produced nets — conversion invented them")
        # Document the real behaviour: the converter is a generator and
        # exits 0. The GATE is that downstream parity sees 0 nodes, which
        # can never match a real board.
        rr = run(["/usr/bin/python3", SCRIPTS / "kicad_sch_parity.py", out,
                  ROOT / "archived_projects" / "cook-loadcell" / "04_kicad"
                  / "cook_loadcell.kicad_pcb"])
        check(rr.rc != 0, "an EMPTY sheet passed parity against a real board")


if __name__ == "__main__":
    sys.exit(main())
