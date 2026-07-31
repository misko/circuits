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


@test("kicad_sch_parity FAILS when NEITHER side parses a single net",
      kind="known_bad")
def t_sch_parity_zero_denominator():
    """G-COVER, canon M-COVER (2026-07-27). Two sides that each parse to zero
    nets agree perfectly, and the gate printed
    `REAL DISCREPANCIES: 0  ->  PARITY 0 (PASS)` and exited 0 — a parity proof
    over nothing. That is not hypothetical here: the `Device:U_chip` collision
    (2026-07-19) was a parser that silently stopped matching and truncated
    many-pin chips to 2 pins, and the same class taken one step further lands
    exactly on this line.
    RED-VERIFIED against pre-fix code (git show 5054b07:...kicad_sch_parity
    .py): it exits 0 printing PARITY 0 (PASS)."""
    d = tmpdir("schpz_")
    empty_net = d / "empty.net"
    empty_net.write_text("(export (version \"E\") (nets ))\n")
    empty_pcb = d / "empty.kicad_pcb"
    empty_pcb.write_text('(kicad_pcb (version 20240108) (generator "test")\n'
                         '  (general (thickness 1.6))\n'
                         '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))\n)\n')
    rr = run(["/usr/bin/python3", SCRIPTS / "kicad_sch_parity.py", "emptyboard",
              empty_net, empty_pcb])
    check(rr.rc != 0,
          f"kicad_sch_parity exited 0 comparing two EMPTY sides — a zero "
          f"denominator is a FAIL, never a pass:\n{rr.out[-1500:]}")
    contains(rr.out, "0/0 nets", "reports the zero denominator explicitly")


@test("kicad_sch_parity survives a raw parity_padmap.txt as --padmap (cooksense/crow crash)")
def t_sch_parity_padmap_file():
    """2026-07-23 incident, BOTH active boards: gen_tscircuit.sh passes the
    ENTIRE parity_padmap.txt file text as --padmap, but the script only parsed
    the legacy inline 'U2:4=2,...' form — any comment line or tsx_preflight-only
    token crashed it with `ValueError: not enough values to unpack` at
    `tok.split("=")` (cooksense journal ~L416; crow-rv2 routing.md M-REPRO
    entry). The gate must DEGRADE (skip undecodable tokens with a note), never
    traceback. RED-verified test-first: this test was written against the
    pre-fix script and FAILED with the exact ValueError traceback before the
    tolerant parser landed (swap-back procedure per tests/README.md)."""
    padmap = "\n".join([
        "# parity_padmap.txt — comment line, no '=' anywhere",
        "",
        "J2  pin1=A1    # crow per-line form: <ref>  pin<N>=<realpad>",
        "SM05B-GHS-TB MP GND   # cooksense tsx_preflight-only triple (no '=')",
        "J5: A1 A4 A5          # usb-hub positional form (no '=')",
    ])
    board = ROOT / "archived_projects" / "cook-loadcell" / "04_kicad" / "cook_loadcell.kicad_pcb"
    rr = run(["/usr/bin/python3", SCRIPTS / "kicad_sch_parity.py", "padmapfixture",
              "/dev/null", board, "--padmap", padmap])
    check("ValueError" not in rr.out and "Traceback" not in rr.out,
          f"kicad_sch_parity CRASHED on real-world padmap file text:\n{rr.out[-1500:]}")
    contains(rr.out, "REAL DISCREPANCIES", "parity report (must still run to a verdict)")


@test("kicad_sch_parity padmap parser: legacy inline + per-line forms both apply")
def t_sch_parity_padmap_parse():
    """PROPERTY test on the parser itself (imported, no board needed): the
    legacy 'U2:4=2,U9:5=3' inline form and the documented per-line
    '<ref>  pin<N>=<pad>' file form must BOTH land in the mapping; 'pinN' is
    aliased to bare 'N' because tsx portHints are numeric in the netlist."""
    r = run(["/usr/bin/python3", "-c", (
        "import sys; sys.path.insert(0, r'%s');\n"
        "import kicad_sch_parity as m\n"
        "pm = m.parse_padmap('U2:4=2,U9:5=3')\n"
        "assert pm[('U2','4')]=='2' and pm[('U9','5')]=='3', pm\n"
        "pm = m.parse_padmap('# hdr\\nJ2  pin1=A1  # GND\\nBADLINE NO EQUALS\\n')\n"
        "assert pm[('J2','1')]=='A1' and pm[('J2','pin1')]=='A1', pm\n"
        "print('PARSE-OK')\n") % SCRIPTS])
    contains(rr_out := r.out, "PARSE-OK", "padmap parser check")
    check(r.rc == 0, f"parser property check failed:\n{r.out[-1500:]}")


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


# ============ the LABEL-ON-WIRE merge the pin guard cannot see (2026-07-28) ==
def _label(name, x, y, i):
    return {"type": "schematic_net_label", "schematic_net_label_id": f"lbl_{i}",
            "text": name, "anchor_position": {"x": x, "y": y},
            "center": {"x": x, "y": y}, "anchor_side": "left"}


def _layout_with(extra_labels):
    """The `rotated_placement` t0 fixture plus extra net labels, run through
    `convert_layout`. Returns the LayoutFallback message, or None on success.

    The fixture's one wire runs (0.5, 0) -> (1.5, 0) on net `k_mid`, so a
    label placed anywhere strictly between those points is MID-SEGMENT — the
    exact geometry of the incident."""
    import json
    import tempfile
    sys.path.insert(0, str(SCRIPTS))
    from circuit_json_to_kicad_sch import (LayoutFallback,  # noqa: E402
                                           convert_layout)
    base = json.load(open(FIXTURES / "t0" / "rotated_placement"
                          / "circuit.json"))
    p = tempfile.mktemp(suffix=".json")
    json.dump(base + extra_labels, open(p, "w"))
    try:
        convert_layout(p, "p", "t", "r", "d")
        return None
    except LayoutFallback as e:
        return str(e)


@test("convert_layout FALLS BACK when one wire root carries two different "
      "LABEL NAMES — the merge happens on labels, not on pins",
      kind="known_bad")
def t_label_on_wire_merge():
    """THE INCIDENT (2026-07-28, smc0985-cooksense rebuild). The converter's
    cross-net guard asked whether a wire root joins two different PIN nets —
    the short a human would draw. `kicad-cli sch export netlist` does not care:
    two global labels on ONE electrical root merge their nets whether or not a
    second pin is involved.

    MEASURED: tscircuit's auto-layout put the `3V3_ANALOG` global label at
    (275.59, 365.76), MID-SEGMENT on a `3V3` wire running (275.59, 401.32) to
    (275.59, 355.60). One root, two label names, ONE pin net. The pin guard saw
    nothing; the converter dropped 3 segments, DECLARED SUCCESS, and the
    exported netlist had 191 nets with no `3V3_ANALOG` anywhere. That would
    have re-merged the analog rail into the digital one and silently undone the
    v1.3 P1-1 fix. It was caught only because `net_label_survival.py` reported
    161/162 and a human read the number.

    TWO defects, both fixed here. A mid-segment label was a SINGLETON root in
    the union-find — it was never joined to the wire it sits on — so even a
    label-name guard could not have seen the merge; and there was no
    label-name guard. The pin-tip half of the mid-segment rule already existed
    (`_on_segment` in the segment-drop pass); the label half is the one that
    shipped a defect.

    RED-VERIFIED 2026-07-28 (git-swap, tests/README step 3): with git HEAD's
    circuit_json_to_kicad_sch.py swapped back in, `convert_layout` returns
    successfully on the two-label fixture and this fails with `a root carrying
    two different label names was imported without complaint`.
    """
    msg = _layout_with([_label("MID_A", 0.75, 0.0, 9),
                        _label("MID_B", 1.25, 0.0, 10)])
    check(msg, "a root carrying two different label names was imported "
               "without complaint — the netlist would merge them at export")
    contains(msg, "LABEL merge", "the fallback names the class")
    contains(msg, "MID_A", "names the first label")
    contains(msg, "MID_B", "names the second label")


@test("convert_layout still imports a layout whose labels do NOT merge — the "
      "guard is not a blanket refusal of mid-segment labels")
def t_label_on_wire_adjacent_property():
    """The adjacent-property red-verify, re-measured every run. tscircuit
    routinely places a net's OWN label part-way along its wire, and a guard
    that refused those would send every board to `--mode grid` and cost the
    layout import entirely. Three cases that must all still import:
      * the untouched fixture;
      * ONE extra mid-segment label (root carries one name);
      * TWO mid-segment labels with the SAME name (no merge — same net).
    """
    check(_layout_with([]) is None, "the untouched t0 fixture no longer imports")
    check(_layout_with([_label("MID_ANALOG", 1.0, 0.0, 9)]) is None,
          "a single mid-segment label was refused")
    check(_layout_with([_label("MID_A", 0.75, 0.0, 9),
                        _label("MID_A", 1.25, 0.0, 10)]) is None,
          "two labels of the SAME net were treated as a merge")


# ==================================================== label plate DIRECTION
# THE DEFECT (2026-07-31, fleet-wide, every layout-mode board). The converter
# handed tscircuit's `anchor_side` straight into its (angle, justify) table.
# `anchor_side` names the EDGE OF THE LABEL PLATE that the anchor sits on,
# which is the REVERSE of the direction the plate reaches, so every label fired
# back across the body it hangs off. On a HORIZONTALLY placed 2-pin part both
# plates fire INWARD and collide with each other and with the symbol: a
# 7.62 mm pin span cannot hold two (len+2)*1.05 mm plates at ANY placement, on
# ANY board, so it was never fixable by moving parts.
#
# MEASURED over all 7 live projects: 1504 of 1504 `schematic_net_label`
# entries have `anchor_side` exactly opposite `center - anchor_position`, in
# all four orientations, 0 missing `center`, 0 degenerate. Fixing it moves
# 620 of 1501 emitted labels and 174 of 706 GND power symbols fleet-wide (the
# two boards at 0 are the ones already falling back to `--mode grid`), and
# drops pluto-rx2-8way-v2's plate-vs-body collisions from 40 to 3 — the 3
# survivors being tscircuit's OWN two label overlaps, which its own render
# has too, plus one body-box artefact.
#
# NOTHING KEYED TO CONNECTIVITY COULD EVER HAVE SEEN IT. The label ANCHOR
# never moves — only the angle and justification — so the exported netlist is
# node-for-node identical before and after on all 8 fleet sheets (2749 nodes,
# symmetric difference 0), and ERC reports 0 errors on both. That is asserted
# inline in the known-bad fixtures below, and it is why every semantic gate in
# the stack reported green on a schematic that drew the 3V3 rail on top of an
# RF port.
#
# GIT-SWAP RED-VERIFIED 2026-07-31 against the REAL pre-fix file
# (`git show HEAD:skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py`
# swapped in, suite rerun, file restored — tests/README.md §3): **19 passed /
# 5 failed**, exactly the five fixtures below and nothing else; restored
# **24 / 0 / 8 known-bad**. The sixth new test
# (`t_label_fixtures_are_discriminating`) stays GREEN on purpose — it grades
# the FIXTURE's discriminating power, not the fix, so a red there would mean
# the fixture had changed.

# the two fixture nets: NET_L rides the LEFT (horizontal) / UPPER (vertical)
# pin, NET_R the RIGHT / LOWER one.
NET_L, NET_R = "TAP_MID_LONG_NAME", "OUT_MID_LONG_NAME"

# The (angle, justify) -> direction truth table, MEASURED from kicad-cli
# 10.0.4 rendered SVG ink, not derived. `t_kicad_direction_table_is_measured`
# below re-measures it every run against KiCad itself (canon M1: the emitter
# must not grade its own angles).
PLATE_DIR = {(0, "left"): (1, 0), (180, "left"): (1, 0),
             (0, "right"): (-1, 0), (180, "right"): (-1, 0),
             (90, "left"): (0, -1), (270, "left"): (0, -1),
             (90, "right"): (0, 1), (270, "right"): (0, 1)}
CH_W, CH_H = 1.05, 2.2          # the converter's own plate model


def plates_and_body(sheet):
    """(plate boxes, body box) for a one-component fixture sheet, in mm."""
    txt = sheet.read_text()
    plates = {}
    for m in re.finditer(r'\(global_label "([^"]+)" \(shape passive\) '
                         r'\(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(justify (\w+)\)',
                         txt):
        name, x, y, ang, just = (m.group(1), float(m.group(2)), float(m.group(3)),
                                 int(m.group(4)), m.group(5))
        check((ang, just) in PLATE_DIR,
              f"label {name}: unrepresentable (angle {ang}, justify {just})")
        ux, uy = PLATE_DIR[(ang, just)]
        reach = (len(name) + 2) * CH_W
        if ux:
            box = (min(x, x + ux * reach), y - CH_H / 2,
                   max(x, x + ux * reach), y + CH_H / 2)
        else:
            box = (x - CH_H / 2, min(y, y + uy * reach),
                   x + CH_H / 2, max(y, y + uy * reach))
        plates[name] = box
    im = re.search(r'\(symbol \(lib_id "elt:(SYM_\w+)"\) \(at ([-\d.]+) ([-\d.]+)', txt)
    check(im is not None, "no placed symbol instance in the sheet")
    ix, iy = float(im.group(2)), float(im.group(3))
    rm = re.search(r'\(rectangle \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)',
                   txt)
    check(rm is not None, "no body rectangle in the lib_symbol")
    x0, y0, x1, y1 = (float(rm.group(i)) for i in (1, 2, 3, 4))
    body = (ix + min(x0, x1), iy - max(y0, y1), ix + max(x0, x1), iy - min(y0, y1))
    return plates, body


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def label_collisions(sheet):
    """Every plate-vs-body and plate-vs-plate overlap on a fixture sheet."""
    plates, body = plates_and_body(sheet)
    bad = []
    names = sorted(plates)
    for n in names:
        if overlaps(plates[n], body):
            bad.append(f"{n} x BODY")
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if overlaps(plates[names[i]], plates[names[j]]):
                bad.append(f"{names[i]} x {names[j]}")
    return bad, plates, body


# The pre-fix converter, restored as a 4-line monkeypatch on the two constants
# the fix introduced, so the RED side is RE-MEASURED on every run instead of
# living in a docstring. Verified equivalent to the real pre-fix file
# (`git show HEAD~:skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py`,
# run 2026-07-31): identical angle/justify on both fixtures.
PREFIX_SHIM = '''import sys
sys.path.insert(0, {scripts!r})
import circuit_json_to_kicad_sch as C
# PRE-FIX: the side handed to the table was tscircuit's `anchor_side`
# verbatim, and the table's 'bottom' row was (270, 'left') -- which KiCad
# renders reaching UP, not down.
C.label_plate_side = lambda n, pin_reach=None: (n.get("anchor_side") or "left")
C.LABEL_ANG_JUST = {{"left": (180, "right"), "right": (0, "left"),
                    "top": (90, "left"), "bottom": (270, "left")}}
C.main()
'''


def convert_prefix(fixture):
    """Convert a t0 fixture with the PRE-FIX side derivation restored."""
    d = tmpdir("convpre_")
    shim = d / "prefix_conv.py"
    shim.write_text(PREFIX_SHIM.format(scripts=str(SCRIPTS)))
    out = d / f"{fixture}_prefix.kicad_sch"
    must_pass(run([PY, shim, T0 / fixture / "circuit.json", "-o", out,
                   "--project", fixture]), f"pre-fix convert {fixture}")
    return d, out


@test("converter: a HORIZONTALLY placed 2-pin part's label plates reach "
      "OUTWARD, clear of the body and of each other")
def t_label_sides_horizontal():
    d, sheet, r = convert("label_sides_h")
    contains(r.out, "MODE=layout", "converter stdout")
    bad, plates, body = label_collisions(sheet)
    check(not bad, f"label plates collide: {bad}\nplates={plates}\nbody={body}")
    # and they reach the correct WAY, not merely clear of things: the plate on
    # the left-hand pin must end LEFT of the body, the right-hand one RIGHT.
    check(plates[NET_L][0] < body[0], f"{NET_L} does not reach left of the body")
    check(plates[NET_R][2] > body[2], f"{NET_R} does not reach right of the body")


@test("converter: a VERTICALLY placed 2-pin part's label plates reach "
      "OUTWARD — the orientation the horizontal fixture cannot discriminate")
def t_label_sides_vertical():
    """A fix proven on one axis is not proven. The vertical case is also where
    the SECOND defect lived: LABEL_ANG_JUST['bottom'] was (270, 'left'), which
    KiCad renders reaching UP. Pre-fix the two bugs CANCELLED on
    `anchor_side: bottom` labels (~155 across the fleet) and did not on
    `anchor_side: top` ones, which is why both had to move together."""
    d, sheet, r = convert("label_sides_v")
    contains(r.out, "MODE=layout", "converter stdout")
    bad, plates, body = label_collisions(sheet)
    check(not bad, f"label plates collide: {bad}\nplates={plates}\nbody={body}")
    # KiCad sheets are y-DOWN: the upper pin's plate ends ABOVE the body.
    check(plates[NET_L][1] < body[1], f"{NET_L} does not reach above the body")
    check(plates[NET_R][3] > body[3], f"{NET_R} does not reach below the body")


@test("the (angle, justify) -> plate-direction table is MEASURED from KiCad, "
      "not assumed — and every GND rotation points the symbol OUTWARD")
def t_kicad_direction_table_is_measured():
    """Canon M1: the emitter must not grade its own angles. Everything above
    rests on one truth table, so that table is re-derived here from
    `kicad-cli sch export svg` INK on a probe sheet KiCad renders itself.

    Two things it pins, both of which were wrong in shipped code until this
    was measured:
      * a global_label's ANGLE selects only the AXIS. KiCad normalises the
        180-degree component away and `justify` ALONE selects the sense — so
        (270, 'left') reaches UP, exactly like (90, 'left'), and the
        converter's 'bottom' row could never have drawn a downward plate.
      * an `elt:GND` body points DOWN at 0, RIGHT at 90, UP at 180, LEFT at
        270 — so the converter's `'top': 0, 'bottom': 180` pointed every
        ground symbol on a top/bottom pin back INTO the body it hangs off.
    """
    sys.path.insert(0, str(SCRIPTS))
    import circuit_json_to_kicad_sch as C          # noqa: E402
    import schwriter2 as SW                        # noqa: E402
    d = tmpdir("dirprobe_")
    libs = SW.power_lib_symbols("elt")
    out = ['(kicad_sch (version 20230121) (generator probe)',
           '  (uuid "00000000-0000-0000-0000-000000000001")',
           '  (paper "User" 420.00 300.00)',
           '  (title_block (title "probe") (date "2026-07-31") (rev "p")', '  )',
           '  (lib_symbols'] + list(libs.values()) + ['  )']
    n = [0]

    def uu():
        n[0] += 1
        return "00000000-0000-0000-0000-%012d" % n[0]

    lab = {}
    for i, (a, j) in enumerate([(a, j) for a in (0, 90, 180, 270)
                                for j in ("left", "right")]):
        x, y = 40 + (i % 4) * 90, 60 + (i // 4) * 80
        name = "L%03d%sAAAA" % (a, j[0].upper())
        lab[name] = (x, y, a, j)
        out.append(f'  (global_label "{name}" (shape passive) (at {x} {y} {a})'
                   f' (fields_autoplaced) (effects (font (size 1.27 1.27))'
                   f' (justify {j})) (uuid "{uu()}"))')
    gnd = {}
    for i, a in enumerate((0, 90, 180, 270)):
        x, y = 40 + i * 90, 230
        gnd[a] = (x, y)
        out += [f'  (symbol (lib_id "elt:GND") (at {x} {y} {a}) (unit 1)'
                f' (in_bom no) (on_board yes) (dnp no) (uuid "{uu()}")',
                f'    (property "Reference" "#PWR{a:03d}" (at {x} {y} 0)'
                f' (effects (font (size 1.27 1.27)) hide))',
                f'    (property "Value" "GND" (at {x} {y} 0)'
                f' (effects (font (size 1.27 1.27)) hide))',
                f'    (pin "1" (uuid "{uu()}"))',
                f'    (instances (project "probe" (path "/00000000-0000-0000-'
                f'0000-000000000001" (reference "#PWR{a:03d}") (unit 1))))', '  )']
    out += ['  (sheet_instances (path "/" (page "1")))', ')']
    sch = d / "probe.kicad_sch"
    sch.write_text("\n".join(out) + "\n")
    svg = d / "probe.svg"
    must_pass(run(["kicad-cli", "sch", "export", "svg", "--no-background-color",
                   "-o", d, sch]), "kicad-cli sch export svg")
    check(svg.is_file(), "probe render produced no probe.svg")
    txt = svg.read_text()

    def pts(s):
        return [(float(m.group(1)), float(m.group(2)))
                for m in re.finditer(r'(-?\d+\.?\d*)[ ,](-?\d+\.?\d*)', s)]

    def unit(dx, dy):
        return (1 if dx > 0 else -1, 0) if abs(dx) > abs(dy) else (0, 1 if dy > 0 else -1)

    seen = 0
    for m in re.finditer(r'<g class="stroked-text"><desc>(L\d{3}[LR]AAAA)</desc>'
                         r'(.*?)</g>', txt, re.S):
        name = m.group(1)
        if name not in lab:
            continue
        p = pts(m.group(2))
        check(p, f"{name}: no ink in the rendered glyph run")
        ax, ay, a, j = lab[name]
        cx = (min(q[0] for q in p) + max(q[0] for q in p)) / 2
        cy = (min(q[1] for q in p) + max(q[1] for q in p)) / 2
        eq(unit(cx - ax, cy - ay), PLATE_DIR[(a, j)],
           f"KiCad renders (angle {a}, justify {j}) reaching")
        seen += 1
    eq(seen, 8, "label combinations measured out of the render")

    # every side name in the converter's own table must reach OUTWARD
    want = {"left": (-1, 0), "right": (1, 0), "top": (0, -1), "bottom": (0, 1)}
    for side, (a, j) in C.LABEL_ANG_JUST.items():
        eq(PLATE_DIR[(a, j)], want[side],
           f"LABEL_ANG_JUST[{side!r}] = {(a, j)} reaches")

    # ...and so must every GND rotation
    paths = [pts(mm.group(1)) for mm in
             re.finditer(r'<(?:path|polyline)[^>]*?(?:\bd|points)="([^"]+)"', txt)]
    measured = {}
    for a, (gx, gy) in gnd.items():
        acc = [q for p in paths if p and min(x for x, _ in p) > gx - 10
               and max(x for x, _ in p) < gx + 10
               and min(y for _, y in p) > gy - 10
               and max(y for _, y in p) < gy + 10 for q in p]
        check(acc, f"GND at angle {a}: no ink found near ({gx}, {gy})")
        measured[a] = unit(sum(q[0] for q in acc) / len(acc) - gx,
                           sum(q[1] for q in acc) / len(acc) - gy)
    eq(measured, {0: (0, 1), 90: (1, 0), 180: (0, -1), 270: (-1, 0)},
       "elt:GND body direction per rotation")
    for side, a in C.GND_ANG.items():
        eq(measured[a], want[side], f"GND_ANG[{side!r}] = {a} points")


@test("PRE-FIX: a horizontally placed 2-pin part's plates both fire INWARD, "
      "across the body and each other", kind="known_bad")
def t_prefix_inverts_horizontal():
    """The shipped defect, re-measured every run. `anchor_side` fed straight
    into the (angle, justify) table inverts both plates of a horizontal part.

    THE ADJACENT PROPERTY, asserted inline, is the reason no gate caught this
    for the life of the layout importer: the pre-fix and post-fix sheets have
    the SAME NETLIST, node for node. The label anchors never move — only the
    angle and the justification — so ERC, `--schematic-parity`, S-NETMERGE and
    every other connectivity-keyed gate are structurally blind to it, and the
    only artefact that carries the defect is the one a human reads."""
    d, bad = convert_prefix("label_sides_h")
    coll, plates, body = label_collisions(bad)
    check(coll, "the PRE-FIX converter produced NO collisions on the "
                "horizontal fixture — the fixture does not reproduce the defect")
    check(f"{NET_L} x BODY" in coll and f"{NET_R} x BODY" in coll,
          f"expected BOTH plates across the body, got {coll}")
    # ...and they reach exactly the WRONG way
    check(plates[NET_L][2] > body[0],
          f"{NET_L} was expected to fire right, into the body")
    check(plates[NET_R][0] < body[2],
          f"{NET_R} was expected to fire left, into the body")
    d2, good, _ = convert("label_sides_h")
    check(not label_collisions(good)[0], "the fixed converter still collides")
    eq(netlist_of(bad), netlist_of(good),
       "netlist of the DEFECTIVE sheet vs the fixed one (blindness proof)")
    eq(erc_errors(bad), 0, "ERC on the DEFECTIVE sheet (blindness proof)")


@test("PRE-FIX: a vertically placed 2-pin part's lower plate fires INWARD — "
      "and the upper one is right only by CANCELLATION", kind="known_bad")
def t_prefix_inverts_vertical():
    """Both halves of the vertical case, which is the one a horizontal-only
    fixture cannot see:
      * `anchor_side: top` (plate truly reaches DOWN) mapped to (90, 'left'),
        which reaches UP — inverted, and it collides with the body.
      * `anchor_side: bottom` (plate truly reaches UP) mapped to (270, 'left'),
        which ALSO reaches UP — accidentally correct, because the inverted side
        and the broken 'bottom' table row cancel.
    That cancellation is why repairing either defect alone would have BROKEN
    the ~155 fleet labels the pair was getting right, and why this fixture
    asserts the cancellation explicitly rather than just "vertical is wrong"."""
    d, bad = convert_prefix("label_sides_v")
    coll, plates, body = label_collisions(bad)
    check(f"{NET_R} x BODY" in coll,
          f"expected the LOWER plate across the body, got {coll}")
    check(plates[NET_R][1] < body[3],
          f"{NET_R} was expected to fire up, into the body")
    # the cancellation: the UPPER plate is correct pre-fix
    check(plates[NET_L][1] < body[1],
          f"{NET_L} pre-fix should already reach above the body (the "
          f"anchor_side-inversion and the (270,'left') row cancel)")
    d2, good, _ = convert("label_sides_v")
    check(not label_collisions(good)[0], "the fixed converter still collides")
    eq(netlist_of(bad), netlist_of(good),
       "netlist of the DEFECTIVE sheet vs the fixed one (blindness proof)")
    eq(erc_errors(bad), 0, "ERC on the DEFECTIVE sheet (blindness proof)")


@test("the two label fixtures are DISCRIMINATING: their plate reach exceeds "
      "the pin span, so no placement could ever separate two inward plates")
def t_label_fixtures_are_discriminating():
    """Canon M-DISC. A fixture whose labels happen to be short enough to fit
    between the pins would pass both before and after the fix and prove
    nothing. Both plates must be longer than the whole pin span, which is what
    makes the defect placement-independent — the claim the brief rests on."""
    for fx in ("label_sides_h", "label_sides_v"):
        d, sheet, r = convert(fx)
        plates, body = plates_and_body(sheet)
        span = max(body[2] - body[0], body[3] - body[1])
        for name, box in plates.items():
            reach = max(box[2] - box[0], box[3] - box[1])
            check(reach > span,
                  f"{fx}/{name}: plate reach {reach:.2f} mm does not exceed "
                  f"the body span {span:.2f} mm — the fixture is not "
                  f"discriminating")


if __name__ == "__main__":
    sys.exit(main())
