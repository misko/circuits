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
{extra}C.main()
'''


def convert_prefix(fixture, extra=""):
    """Convert a t0 fixture with the PRE-FIX side derivation restored."""
    d = tmpdir("convpre_")
    shim = d / "prefix_conv.py"
    shim.write_text(PREFIX_SHIM.format(scripts=str(SCRIPTS), extra=extra))
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
    `anchor_side: top` ones, which is why both had to move together.

    WHAT THIS TEST DOES NOT SAY, corrected 2026-07-31. `label_collisions()`
    grades plate-vs-BODY and plate-vs-PLATE only, so for most of its life this
    fixture read as a clean bill on a sheet that was not clean: R1 is placed
    VERTICALLY, its Reference and Value are centred on the same x as both
    plates, and both plates are drawn straight through them. That is
    plate-vs-PROPERTY and nothing here could see it. It is now graded by the
    gate that can — `sch_occlusion.py`, which reads this fixture 2 -> 0 across
    the de-collision pass, fixtured in
    `tests/t1_occlusion.py t_label_sides_v_is_clean_only_because_the_pass_moves_it`
    — and the whole-sheet assertion below is the local half of that."""
    d, sheet, r = convert("label_sides_v")
    contains(r.out, "MODE=layout", "converter stdout")
    bad, plates, body = label_collisions(sheet)
    check(not bad, f"label plates collide: {bad}\nplates={plates}\nbody={body}")
    # KiCad sheets are y-DOWN: the upper pin's plate ends ABOVE the body.
    check(plates[NET_L][1] < body[1], f"{NET_L} does not reach above the body")
    check(plates[NET_R][3] > body[3], f"{NET_R} does not reach below the body")
    # ...and CLEAN means clean against EVERY drawn object, not just the two
    # classes the helper above models.
    sys.path.insert(0, str(SCRIPTS))
    import sch_occlusion as SO                                  # noqa: E402
    occl, unm, graded, total = SO.occlusions(
        sheet.read_text(encoding="utf-8-sig"))
    eq(unm, [], "drawable objects S-OCCL could not place on label_sides_v")
    eq(occl, [], "S-OCCL over the WHOLE emitted sheet — plate-vs-property "
                 "included, which is the class this fixture used to hide")


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


# The label de-collision pass (canon S11) runs AFTER the direction derivation
# and would relocate whatever the two fixtures below emit — so they hold it OFF
# and grade the stage they are about, exactly as the pre-fix converter behaved.
# `_prefix_decollide_masks_the_direction_defect` then measures what happens with
# it ON, and the answer is the reason this shim is not a convenience.
_NO_DECOLLIDE = ('C.place_labels = lambda cands, *a, **k: (cands, [], [], 0)\n')


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
    d, bad = convert_prefix("label_sides_h", _NO_DECOLLIDE)
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
    d, bad = convert_prefix("label_sides_v", _NO_DECOLLIDE)
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


# ============ property text drawn ON the ground glyph of its own pin ========
# THE DEFECT (2026-07-31, fleet-wide, every layout-mode board). `Reference` and
# `Value` were anchored at a BLIND offset from the body edge — literally
#
#     ry = iy - comp["h"] / 2 - 2.2
#     vy = iy + comp["h"] / 2 + 2.2
#
# — which takes no account of what is ALREADY drawn on that side of the symbol.
# A pin whose net is GND carries an `elt:GND` hanging off its TIP in the
# direction that pin REACHES (GND_ANG), and on a VERTICALLY placed 2-pin
# passive that tip sits ON the body edge, so the triangle occupies the strip
# from the edge to 2.54 mm below it — exactly where the Value is written.
#
# MEASURED on pluto-rx2-8way-v2 (scratch conversion, nothing regenerated in
# place): R_PD1's "10kΩ" ink spans x 114.122-118.288 / y 95.507-96.853 and
# #PWR52's lower vertex sits at (116.205, 96.52), inside it. Under the
# direction-aware S-OCCL model (canon S11, `2914dcad`) this ONE class is
# 160 of the fleet's 341 findings — 151 the 2-pin shape, 9 an IC with a
# bottom-side GND pin — and 7 of the 11 findings blocking that board's seal.
#
# THE FIX MOVES EXACTLY THE DEFECT AND NOTHING ELSE: 160 of 2992 fleet property
# anchors move, and they are precisely the 160 that were findings. The 166
# grounded HORIZONTAL passives in the same fleet do not move at all, because a
# left/right pin's triangle hangs sideways from a tip that is already outside
# the body and `prop_rows` skips any glyph whose x-range misses the body. Both
# `--mode grid` boards emit BYTE-IDENTICAL property rows (measured).
#
# GIT-SWAP RED-VERIFIED 2026-07-31 against the real pre-fix file — see
# `t_prefix_value_on_its_own_ground_glyph` for the per-run red side and the
# whole-file swap result.

_PREFIX_PROP_SHIM = '''import sys
sys.path.insert(0, {scripts!r})
import circuit_json_to_kicad_sch as C
# PRE-FIX: the property rows were a blind offset from the body edge, with no
# model of the glyphs hanging off this symbol's own pins.
C.prop_rows = (lambda ix, iy, w, h, boxes, gap_above=2.2, gap_below=None:
               (iy - h / 2 - gap_above,
                iy + h / 2 + (gap_above if gap_below is None else gap_below)))
C.main()
'''


def _gnd_fixture(base, gnd_pin):
    """`label_sides_{h,v}` with ONE pin moved onto GND — a good input broken in
    exactly one way (tests/README). The GND net's `schematic_net_label` is
    dropped because the converter draws a ground SYMBOL for it, which is the
    whole point: that symbol is the thing the property lands on."""
    import json
    import tempfile
    keep = "sn_a" if gnd_pin == 2 else "sn_b"
    out = []
    for e in json.load(open(T0 / base / "circuit.json")):
        if e["type"] == "source_net" and e["source_net_id"] != keep:
            e = dict(e, name="GND")
        if e["type"] == "schematic_net_label" and e["source_net_id"] != keep:
            continue
        out.append(e)
    p = Path(tempfile.mkdtemp(prefix="gndfx_")) / "circuit.json"
    p.write_text(json.dumps(out))
    return p


#: the LABEL DE-COLLISION pass held off — which is exactly what the converter
#: did before `place_labels` existed, so this is the RED side of every
#: de-collision fixture below, re-run on every run rather than asserted in a
#: docstring. Verified equivalent to the real pre-pass file by whole-file git
#: swap; see `t_decollide_horizontal`.
_NO_DECOLLIDE_SHIM = '''import sys
sys.path.insert(0, {scripts!r})
import circuit_json_to_kicad_sch as C
C.place_labels = lambda cands, *a, **k: (cands, [], [], 0)
C.main()
'''


def _convert_json(cj, name, prefix=False, raw=False):
    """Convert an arbitrary circuit.json. `prefix` restores the PRE-FIX
    property rows; `raw` holds the LABEL DE-COLLISION pass off. Either red side
    is RE-RUN every run, never asserted in prose."""
    d = tmpdir("gndconv_")
    out = d / f"{name}.kicad_sch"
    if prefix or raw:
        shim = d / "shim.py"
        shim.write_text((_PREFIX_PROP_SHIM if prefix else _NO_DECOLLIDE_SHIM)
                        .format(scripts=str(SCRIPTS)))
        cmd = [PY, shim, cj, "-o", out, "--project", name]
    else:
        cmd = [PY, CONV, cj, "-o", out, "--project", name]
    r = must_pass(run(cmd), f"convert {name}{' [PRE-FIX]' if prefix else ''}")
    contains(r.out, "MODE=layout", f"{name}: converter stdout")
    return d, out


def _svg_ink(sheet):
    """(text runs, graphic segments) in SHEET MILLIMETRES, straight out of
    `kicad-cli sch export svg`.

    KiCad's schematic SVG viewBox IS the paper in mm, so nothing is scaled:
    what this reads is what the sheet DRAWS. Text is every
    `<g class="stroked-text">` run keyed by its `<desc>`; graphics is every
    `<path>` AND `<rect>` that survives removing those runs — bodies, pin
    lines, wires, label plates and the ground triangle, with no model of any
    of them.

    THREE SHAPES KiCad 10.0.4 REALLY EMITS, each of which silently drops ink
    if only the obvious one is handled, and all three were found by rendering
    a fixture and counting rather than by reading the writer: `d` is NOT always
    the first attribute (a stroked polyline carries `style=` first — and that
    is exactly the form the GROUND TRIANGLE takes, so a `<path d=` matcher
    reads a sheet with no ground symbol on it at all); a filled symbol body is
    a `<rect>` and not a path; and both coordinate syntaxes (`M1.0 2.0 L3.0
    4.0` and `M 1.0,2.0 L 3.0,4.0`) appear on ONE sheet.
    """
    d = sheet.parent
    must_pass(run(["kicad-cli", "sch", "export", "svg",
                   "--no-background-color", "-o", d, sheet]),
              f"kicad-cli sch export svg {sheet.name}")
    svg = d / (sheet.stem + ".svg")
    check(svg.is_file(), f"no {svg.name} rendered")
    txt = svg.read_text()

    def pts(s):
        return [(float(a), float(b)) for a, b in
                re.findall(r"(-?\d+\.?\d*)[\s,]+(-?\d+\.?\d*)", s)]

    runs = {}
    for m in re.finditer(r'<g class="stroked-text"><desc>(.*?)</desc>(.*?)</g>',
                         txt, re.S):
        p = pts(m.group(2))
        if not p:
            continue
        b = (min(q[0] for q in p), min(q[1] for q in p),
             max(q[0] for q in p), max(q[1] for q in p))
        runs.setdefault(m.group(1), []).append(b)
    gtxt = re.sub(r'<g class="stroked-text">.*?</g>', "", txt, flags=re.S)
    graphics = []
    for m in re.finditer(r'<path\b[^>]*?\bd="([^"]+)"', gtxt):
        p = pts(m.group(1))
        for k in range(len(p) - 1):
            graphics.append((p[k], p[k + 1]))
    for m in re.finditer(r'<rect\b[^>]*?\bx="([-\d.]+)"[^>]*?\by="([-\d.]+)"'
                         r'[^>]*?\bwidth="([-\d.]+)"[^>]*?\bheight="([-\d.]+)"',
                         gtxt):
        x, y, w, h = (float(m.group(k)) for k in (1, 2, 3, 4))
        c = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
        graphics += [(c[k], c[k + 1]) for k in range(4)]
    check(graphics, f"{svg.name}: no graphic ink extracted at all")
    return runs, graphics


def _seg_in_box(p, q, box):
    """Length of segment p->q inside an axis-aligned box (Liang-Barsky).

    A LENGTH, not a hit test: a stroke that merely touches a corner is not a
    text drawn on top of something, and every glyph is stroked 0.254 mm wide so
    exact tangency is the normal case."""
    import math
    x0, y0, x1, y1 = box
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]),
                   (-dy, p[1] - y0), (dy, y1 - p[1])):
        if abs(pp) < 1e-12:
            if qq < 0:
                return 0.0
        else:
            r = qq / pp
            if pp < 0:
                if r > t1:
                    return 0.0
                t0 = max(t0, r)
            else:
                if r < t0:
                    return 0.0
                t1 = min(t1, r)
    return max(0.0, t1 - t0) * math.hypot(dx, dy)


def _property_ink_hits(sheet):
    """Every (property, mm of graphic ink drawn through it) on a sheet.

    FALSIFIED IN INK, not against a model. The property strings come from the
    `.kicad_sch`; their extents and the graphics they collide with come from
    KiCad's own render — so neither the converter's geometry nor `S-OCCL`'s is
    an input to this verdict (canon M1)."""
    body = re.sub(r"^  \(lib_symbols.*?^  \)$", "", sheet.read_text(),
                  flags=re.S | re.M)          # prototypes are never rendered
    props = [(m.group(1), m.group(2)) for m in re.finditer(
        r'\(property "(Reference|Value)" "([^"]+)" \(at [-\d. ]+\)\s*'
        r'\(effects \(font \(size [\d.]+ [\d.]+\)\)\)\)', body)]
    check(props, f"{sheet.name}: no VISIBLE Reference/Value property emitted")
    runs, graphics = _svg_ink(sheet)
    hits = []
    for kind, txt in props:
        for box in runs.get(txt, []):
            worst = max([_seg_in_box(p, q, box) for p, q in graphics] + [0.0])
            if worst > 0.05:
                hits.append((f"{kind} {txt}", round(worst, 4), box))
    return hits, props


# the four orientations x directions the fix has to be right in. `gnd_pin` 2 is
# the LOWER pin of the vertical fixture and the RIGHT pin of the horizontal one
# (see `label_sides_*`); 1 is the upper / left one.
_GND_CASES = [("label_sides_v", 2, "vertical, GND on the LOWER pin"),
              ("label_sides_v", 1, "vertical, GND on the UPPER pin"),
              ("label_sides_h", 2, "horizontal, GND on the RIGHT pin"),
              ("label_sides_h", 1, "horizontal, GND on the LEFT pin")]


@test("converter: a 2-pin passive's Reference and Value clear the GROUND GLYPH "
      "on its own pin — all four orientations, verified in RENDERED INK")
def t_property_clears_its_own_ground_glyph():
    """The subject of the fix, graded the only way that cannot be argued with:
    KiCad renders the sheet and NO graphic stroke may pass through the ink of
    a Reference or Value. All four (orientation x grounded pin) cases, because
    a fix proven on one axis is not proven — and because the two directions
    move OPPOSITE properties (a bottom-pin triangle displaces the Value, a
    top-pin one displaces the Reference and the PWR_FLAG above it)."""
    for base, pin, why in _GND_CASES:
        d, sheet = _convert_json(_gnd_fixture(base, pin), f"{base}_g{pin}")
        hits, props = _property_ink_hits(sheet)
        check(len(props) == 2, f"{why}: expected Reference+Value, got {props}")
        check(not hits, f"{why}: property text drawn on graphics: {hits}")


@test("PRE-FIX: the Value is drawn ON the ground triangle of its own lower pin "
      "— re-measured in ink every run", kind="known_bad")
def t_prefix_value_on_its_own_ground_glyph():
    """THE SHIPPED DEFECT. `prop_rows` is replaced by the pre-fix expression it
    was extracted from (`iy +/- h/2 +/- 2.2`, no glyph model) and the fixtures
    are re-converted with it, so the RED side is measured on every run instead
    of living in a docstring.

    MEASURED, and reported honestly rather than tuned into four reds: the two
    VERTICAL cases go red and the two HORIZONTAL ones do NOT, and that is
    arithmetic, not luck. A left/right pin's ground triangle spans only
    +/-1.00 mm ACROSS its axis, while the Value's nearest edge sits
    h/2 + 2.2 - 0.53*1.27 >= 2.797 mm below the centre (h_mm has a 2.54 floor)
    — a gap of at least 1.797 mm that no box height can close. So the
    horizontal pair is this fixture's ADJACENT PROPERTY: text that was already
    correct, which the fix must not displace. It does not — measured over the
    real fleet, 0 of 166 grounded horizontal passives move.

    THE BLINDNESS PROOF, asserted inline: the defective sheet's netlist is
    node-for-node identical to the fixed one and its ERC is 0. Property
    ANCHORS are not connectivity, so ERC, `--schematic-parity`, S-NETMERGE and
    every other connectivity-keyed gate is structurally blind to this — the
    only gate that could ever see it is S-OCCL, and S-OCCL could not see it
    either until `2914dcad` gave it symbol geometry.

    WHOLE-FILE GIT SWAP, MEASURED 2026-07-31 (tests/README step 3): with
    `git show 2914dcad:skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py`
    swapped in, this suite prints **25 passed / 3 failed** — exactly
    `t_property_clears_its_own_ground_glyph` (the subject), this fixture's
    "the FIXED converter still draws over graphics" leg, and
    `t_glyph_geometry_is_measured` (`sym_xf` / `glyph_box` / `power_syms` do
    not exist pre-fix). Restored: **28 / 0 / 9 known-bad**.
    `t_gnd_fixtures_are_discriminating` stays GREEN through the swap on
    PURPOSE — it grades the FIXTURE's discriminating power through the
    monkeypatched pre-fix rows, so a red there would mean the fixture had
    changed, not the fix.
    """
    red, black = [], []
    for base, pin, why in _GND_CASES:
        cj = _gnd_fixture(base, pin)
        d, bad = _convert_json(cj, f"{base}_g{pin}_pre", prefix=True)
        hits, _ = _property_ink_hits(bad)
        (red if hits else black).append((why, hits))
        d2, good = _convert_json(cj, f"{base}_g{pin}_fix")
        check(not _property_ink_hits(good)[0],
              f"{why}: the FIXED converter still draws over graphics")
        eq(netlist_of(bad), netlist_of(good),
           f"{why}: netlist of the DEFECTIVE sheet vs the fixed one")
        eq(erc_errors(bad), 0, f"{why}: ERC on the DEFECTIVE sheet")
    eq([w for w, _ in red],
       ["vertical, GND on the LOWER pin", "vertical, GND on the UPPER pin"],
       "which orientations the PRE-FIX converter draws text over ink in")
    for why, hits in red:
        names = {h[0].split(" ", 1)[0] for h in hits}
        check(names, f"{why}: no hit recorded")
    # the LOWER-pin case must hit the VALUE and the UPPER-pin case the REFERENCE
    eq(sorted({h[0].split(" ", 1)[0] for h in red[0][1]}), ["Value"],
       "the lower-pin defect lands on")
    eq(sorted({h[0].split(" ", 1)[0] for h in red[1][1]}), ["Reference"],
       "the upper-pin defect lands on")


@test("the four ground-glyph fixtures are DISCRIMINATING: pre-fix the text is "
      "drawn over MORE ink than a stroke width, and the glyph really is on the "
      "pin the property sits by")
def t_gnd_fixtures_are_discriminating():
    """Canon M-DISC. A fixture whose overlap is a rounding artefact would pass
    both before and after and prove nothing. Two properties, both measured:
    the pre-fix overlap must exceed the 0.254 mm stroke width (so it is real
    ink over real ink, not tangency), and the ground symbol must actually be
    attached to the pin whose side the displaced property sits on."""
    for (base, pin, why), want in zip(_GND_CASES[:2], ("Value", "Reference")):
        d, bad = _convert_json(_gnd_fixture(base, pin), f"{base}_g{pin}_disc",
                               prefix=True)
        hits, _ = _property_ink_hits(bad)
        check(hits, f"{why}: the fixture does not reproduce the defect at all")
        worst = max(h[1] for h in hits if h[0].startswith(want))
        check(worst > 0.254,
              f"{why}: pre-fix overlap {worst:.3f} mm does not exceed one "
              f"0.254 mm stroke width — the fixture is not discriminating")
        txt = bad.read_text()
        gm = re.search(r'\(symbol \(lib_id "elt:GND"\) \(at ([-\d.]+) '
                       r'([-\d.]+) (\d+)\)', txt)
        check(gm is not None, f"{why}: no ground symbol on the fixture sheet")
        im = re.search(r'\(symbol \(lib_id "elt:SYM_\w+"\) \(at ([-\d.]+) '
                       r'([-\d.]+) ', txt)
        check(im is not None, f"{why}: no component instance on the sheet")
        gy, iy = float(gm.group(2)), float(im.group(2))
        check((gy > iy) == (want == "Value"),
              f"{why}: the ground symbol at y={gy} is on the wrong side of the "
              f"body at y={iy} for a {want} defect")


@test("the attached-glyph geometry the converter places is MEASURED from "
      "KiCad's own render, not derived — transform AND extent")
def t_glyph_geometry_is_measured():
    """Canon M1: the emitter must not grade its own geometry. `prop_rows` moves
    text on the strength of two claims — that `sym_xf` is KiCad's instance
    transform, and that `glyph_box` is where the ground triangle really lands —
    and both are re-derived here from `kicad-cli sch export svg` INK.

    The transform is probed with an ASYMMETRIC rectangle, so a wrong handedness
    cannot pass by symmetry: local (1,2)-(7,4) must land at sheet-relative
    (1,-4)-(7,-2) / (-4,-7)-(-2,-1) / (-7,2)-(-1,4) / (2,1)-(4,7).

    Two inherited constants in this repo's schematic geometry were recently
    found wrong in OPPOSITE directions — a plate cross-extent 13% narrow
    (silence) and a property half-height 70% too tall (invention) — which is
    why this measures the BOX and not just the direction."""
    sys.path.insert(0, str(SCRIPTS))
    import circuit_json_to_kicad_sch as C          # noqa: E402
    d = tmpdir("glyphprobe_")
    n = [0]

    def uu():
        n[0] += 1
        return "00000000-0000-0000-0000-%012d" % n[0]

    probe = ('    (symbol "elt:PROBE" (in_bom no) (on_board yes)\n'
             '      (property "Reference" "#P" (at 0 0 0)'
             ' (effects (font (size 1.27 1.27)) hide))\n'
             '      (property "Value" "P" (at 0 0 0)'
             ' (effects (font (size 1.27 1.27)) hide))\n'
             '      (symbol "PROBE_0_1"\n'
             '        (polyline (pts (xy 1 2) (xy 7 2) (xy 7 4) (xy 1 4)'
             ' (xy 1 2)) (stroke (width 0.254) (type default))'
             ' (fill (type none)))\n'
             '      )\n    )')
    out = ['(kicad_sch (version 20230121) (generator probe)',
           '  (uuid "00000000-0000-0000-0000-000000000001")',
           '  (paper "User" 500.00 300.00)',
           '  (title_block (title "probe") (date "2026-07-31") (rev "p")', '  )',
           '  (lib_symbols', C.power_syms()["GND"], probe, '  )']
    sites = {}
    for i, ang in enumerate((0, 90, 180, 270)):
        for j, (lib, key) in enumerate((("elt:GND", "GND"),
                                        ("elt:PROBE", "PROBE"))):
            x, y = 60 + i * 110, 80 + j * 130
            sites[(key, ang)] = (x, y)
            out += [f'  (symbol (lib_id "{lib}") (at {x} {y} {ang}) (unit 1)'
                    f' (in_bom no) (on_board yes) (dnp no) (uuid "{uu()}")',
                    f'    (property "Reference" "#{key[0]}{ang:03d}"'
                    f' (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))',
                    f'    (property "Value" "{key}" (at {x} {y} 0)'
                    f' (effects (font (size 1.27 1.27)) hide))',
                    f'    (pin "1" (uuid "{uu()}"))',
                    f'    (instances (project "probe" (path "/00000000-0000-'
                    f'0000-0000-000000000001" (reference "#{key[0]}{ang:03d}")'
                    f' (unit 1))))', '  )']
    out += ['  (sheet_instances (path "/" (page "1")))', ')']
    sch = d / "probe.kicad_sch"
    sch.write_text("\n".join(out) + "\n")
    _runs, graphics = _svg_ink(sch)

    def ink_box(x, y, reach=12.0):
        acc = [q for seg in graphics for q in seg
               if abs(q[0] - x) < reach and abs(q[1] - y) < reach]
        check(acc, f"no ink within {reach} mm of ({x}, {y})")
        return (min(q[0] for q in acc), min(q[1] for q in acc),
                max(q[0] for q in acc), max(q[1] for q in acc))

    # ---- the transform, on an ASYMMETRIC rectangle
    want_rel = {0: (1, -4, 7, -2), 90: (-4, -7, -2, -1),
                180: (-7, 2, -1, 4), 270: (2, 1, 4, 7)}
    for ang, rel in want_rel.items():
        x, y = sites[("PROBE", ang)]
        got = ink_box(x, y)
        for k in range(4):
            want = (x if k % 2 == 0 else y) + rel[k]
            check(abs(got[k] - want) <= 0.20,
                  f"PROBE at {ang} deg: rendered edge {k} is {got[k]:.3f}, "
                  f"sym_xf predicts {want:.3f}")
        pred = [sym for sym in [C.sym_xf(a, b, ang)
                                for a, b in ((1, 2), (7, 2), (7, 4), (1, 4))]]
        eq((round(min(p[0] for p in pred)), round(min(p[1] for p in pred)),
            round(max(p[0] for p in pred)), round(max(p[1] for p in pred))),
           rel, f"C.sym_xf at {ang} deg maps the probe rect to")

    # ---- the GROUND GLYPH's extent, all four rotations
    for ang in (0, 90, 180, 270):
        x, y = sites[("GND", ang)]
        got = ink_box(x, y, 8.0)
        pred = C.glyph_box(C.power_syms()["GND"], x, y, ang)
        for k in range(4):
            check(abs(got[k] - pred[k]) <= 0.20,
                  f"elt:GND at {ang} deg: rendered edge {k} is {got[k]:.3f}, "
                  f"C.glyph_box predicts {pred[k]:.3f}")
        # ...and it reaches AWAY from the pin, 2.54 mm, across 2.00 mm
        span = (round(pred[2] - pred[0], 4), round(pred[3] - pred[1], 4))
        eq(span, (2.0, 2.54) if ang in (0, 180) else (2.54, 2.0),
           f"elt:GND at {ang} deg spans (x, y) mm")


# ==================== LABEL DE-COLLISION (canon S11, 2026-07-31) ============
# THE DEFECT. Every one of the 182 S-OCCL findings left on this fleet after the
# label-DIRECTION fix (`948ef54d`) and the property-row fix (`9088b4f4`) had a
# global_label as one of its two members — 77 label-vs-pin, 42 label-vs-
# Reference, 32 label-vs-label, 16 label-vs-glyph, 8 label-vs-body, 7
# label-vs-Value, and NOTHING else. The plates were emitted exactly where
# tscircuit's anchor put them and never checked against the sheet they landed
# on. The load-bearing instance is pluto-rx2-8way-v2's `ANT2 x 3V3_MOD`: two
# plates reaching toward each other along one row, overlapping by 0.5515 mm of
# REAL INK, compositing into `N3V3_MOD2` — a sheet that reads as though the 3V3
# rail reaches an RF port.
#
# THE MODEL IS MEASURED, and this is where the previous constant went wrong in
# the dangerous direction. The converter's shipped plate width was
# `(len + 2) * 1.05` — every character the same. KiCad's stroke font is
# PROPORTIONAL: 95 characters measured out of rendered ink give an exact k/21 of
# the font size, k from 8 to 28. The flat model is 6.48 mm too NARROW for a
# 20-character name of capitals, so a de-collision search built on it would
# place plates it called clear and KiCad draws through their neighbours.

def _plate_ink(sheet):
    """name -> [plate rectangles] and name -> [text-run boxes], both straight
    out of `kicad-cli sch export svg`. A plate is identified by its MEASURED
    cross extent (2.5408 mm, zero spread) — not as 'the smallest polyline
    containing the text', which is the PAGE BORDER for every label on the
    sheet and reads as a 433 mm plate."""
    runs, _graphics = _svg_ink(sheet)
    txt = sheet.read_text()
    names = set(re.findall(r'\(global_label "([^"]*)"', txt))
    d = sheet.parent
    svg = (d / (sheet.stem + ".svg")).read_text()

    def pts(s):
        return [(float(a), float(b)) for a, b in
                re.findall(r"(-?\d+\.?\d*)[\s,]+(-?\d+\.?\d*)", s)]

    body = re.sub(r'<g class="stroked-text">.*?</g>', "", svg, flags=re.S)
    polys = []
    for m in re.finditer(r'<(?:path|polyline)\b[^>]*?\b(?:d|points)="([^"]+)"',
                         body):
        p = pts(m.group(1))
        if len(p) >= 5:
            polys.append((min(q[0] for q in p), min(q[1] for q in p),
                          max(q[0] for q in p), max(q[1] for q in p)))
    plates, texts = {}, {}
    for nm, boxes in runs.items():
        if nm not in names:
            continue
        for b in boxes:
            texts.setdefault(nm, []).append(b)
            hit = None
            for pb in polys:
                if not (2.45 <= min(pb[2] - pb[0], pb[3] - pb[1]) <= 2.65):
                    continue
                if (pb[0] - 0.6 <= b[0] and b[2] <= pb[2] + 0.6 and
                        pb[1] - 0.6 <= b[1] and b[3] <= pb[3] + 0.6):
                    if hit is None or ((pb[2] - pb[0]) * (pb[3] - pb[1]) <
                                       (hit[2] - hit[0]) * (hit[3] - hit[1])):
                        hit = pb
            if hit:
                plates.setdefault(nm, []).append(hit)
    return plates, texts


def _ink_overlap(a, b):
    """Signed overlap of two boxes: positive means ink really is on top of ink."""
    return min(min(a[2], b[2]) - max(a[0], b[0]),
               min(a[3], b[3]) - max(a[1], b[1]))


def _worst_pair(boxes_a, boxes_b):
    return max([_ink_overlap(x, y) for x in boxes_a for y in boxes_b] + [-1e9])


def _twin_fixture(base, dx, dy, rename):
    """`base` with a SECOND copy of its one component offset by (dx, dy)
    tscircuit units, and the four nets renamed so exactly the FACING pair of
    plates collides. A good input broken in exactly one way (tests/README):
    the geometry is the shipped fixture's, only doubled and spaced."""
    import json
    import tempfile
    src = json.load(open(T0 / base / "circuit.json"))
    ids = set()
    for e in src:
        for k, v in e.items():
            if isinstance(v, str) and (k.endswith("_id") or
                                       k == "subcircuit_connectivity_map_key"):
                ids.add(v)

    def clone(e):
        o = {}
        for k, v in e.items():
            if isinstance(v, str) and v in ids:
                o[k] = v + "__2"
            elif isinstance(v, dict) and "x" in v and "y" in v:
                o[k] = {"x": v["x"] + dx, "y": v["y"] + dy}
            else:
                o[k] = v
        if o.get("type") == "source_component":
            o["name"] = "R2"
        return o

    out = [dict(e) for e in src] + [clone(e) for e in src]
    for e in out:
        if e["type"] in ("source_net", "schematic_net_label"):
            key = e.get("source_net_id")
            if key in rename:
                if e["type"] == "source_net":
                    e["name"] = rename[key]
                else:
                    e["text"] = rename[key]
    p = Path(tempfile.mkdtemp(prefix="twinfx_")) / "circuit.json"
    p.write_text(json.dumps(out))
    return p


# The facing pair is R1's SECOND pin (reaches right / down) against R2's FIRST
# (reaches left / up). Those two get long names; the outer two stay short so
# nothing else on the sheet is in contention.
_FACE_A, _FACE_B = "COLLIDING_PLATE_ONE", "COLLIDING_PLATE_TWO"
_RENAME = {"sn_b": _FACE_A, "sn_a__2": _FACE_B, "sn_a": "LA", "sn_b__2": "LB"}


def _decollide_case(base, dx, dy):
    """(fixed sheet, un-de-collided sheet) for one axis."""
    cj = _twin_fixture(base, dx, dy, _RENAME)
    d1, good = _convert_json(cj, f"{base}_twin_fixed")
    d2, bad = _convert_json(cj, f"{base}_twin_raw", raw=True)
    return good, bad


@test("converter: two labels colliding HORIZONTALLY are separated by the "
      "de-collision pass — asserted in RENDERED INK", kind="known_bad")
def t_decollide_horizontal():
    """THE HEAD-ON SHAPE, which is `ANT2 x 3V3_MOD` on pluto-rx2-8way-v2.

    Two parts face each other across a gap and each fires a plate into it. The
    two plates are longer than the gap, so this is not a placement accident and
    no anchor position could have avoided it.

    RED SIDE RE-RUN EVERY RUN, never asserted in prose: the same circuit.json is
    converted with `place_labels` held off — which is EXACTLY what the converter
    did before this change — and KiCad's own render must show the two labels'
    GLYPH RUNS drawn through each other by more than one 0.254 mm stroke width.
    Then the fixed converter must show them not touching at all.

    THE BLINDNESS PROOF, inline: the two sheets have the SAME netlist, node for
    node, and both ERC at 0 errors. A label's anchor is connectivity, so moving
    one along its own net changes nothing any connectivity-keyed gate can see —
    which is why S-OCCL is the only gate that could ever have caught this, and
    why its own plate model had to be re-measured first.

    WHOLE-FILE GIT SWAP, MEASURED 2026-07-31 (tests/README step 3). With
    `git show HEAD:skills/kicad-pcb/scripts/circuit_json_to_kicad_sch.py`
    swapped in, this suite prints **28 passed / 8 failed** — exactly the eight
    fixtures added with the de-collision pass and nothing else. Restored:
    **36 / 0 / 13 known-bad**. The `_NO_DECOLLIDE_SHIM` used as the red side
    here is therefore equivalent to the real pre-pass file: the pre-pass file
    has no `place_labels` to monkeypatch, and it produces the same sheets."""
    good, bad = _decollide_case("label_sides_h", 3.2, 0.0)
    pb, tb = _plate_ink(bad)
    for nm in (_FACE_A, _FACE_B):
        check(nm in tb, f"{nm}: no rendered glyph run on the un-de-collided sheet")
    red = _worst_pair(tb[_FACE_A], tb[_FACE_B])
    check(red > 0.254,
          f"the un-de-collided sheet draws the two glyph runs {red:.4f} mm "
          f"through each other, which does not exceed one 0.254 mm stroke "
          f"width — the fixture is not discriminating")
    check(_worst_pair(pb[_FACE_A], pb[_FACE_B]) > 0.254, "plates do not overlap")
    pg, tg = _plate_ink(good)
    black = _worst_pair(tg[_FACE_A], tg[_FACE_B])
    check(black <= 0.0,
          f"the FIXED converter still draws the two glyph runs {black:.4f} mm "
          f"through each other")
    eq(netlist_of(bad), netlist_of(good),
       "netlist of the un-de-collided sheet vs the de-collided one")
    eq(erc_errors(bad), 0, "ERC on the un-de-collided sheet")
    eq(erc_errors(good), 0, "ERC on the de-collided sheet")


@test("converter: two labels colliding VERTICALLY are separated by the "
      "de-collision pass — the axis the horizontal fixture cannot see",
      kind="known_bad")
def t_decollide_vertical():
    """A fix proven on one axis is not proven. The vertical case exercises a
    different half of every table this pass touches: `SIDE_REACH['top'|
    'bottom']`, the perpendicular the search steps along, and the branch of
    `plate_box` that puts the 2.5408 mm cross extent on X instead of Y.

    It is also the axis where the stub has to be HORIZONTAL, so it tests the
    other half of the wire-safety rules."""
    good, bad = _decollide_case("label_sides_v", 0.0, -3.2)
    pb, tb = _plate_ink(bad)
    for nm in (_FACE_A, _FACE_B):
        check(nm in tb, f"{nm}: no rendered glyph run on the un-de-collided sheet")
    red = _worst_pair(tb[_FACE_A], tb[_FACE_B])
    check(red > 0.254,
          f"the un-de-collided sheet draws the two glyph runs {red:.4f} mm "
          f"through each other — not discriminating")
    pg, tg = _plate_ink(good)
    black = _worst_pair(tg[_FACE_A], tg[_FACE_B])
    check(black <= 0.0,
          f"the FIXED converter still draws the two glyph runs {black:.4f} mm "
          f"through each other")
    eq(netlist_of(bad), netlist_of(good),
       "netlist of the un-de-collided sheet vs the de-collided one")
    eq(erc_errors(bad), 0, "ERC on the un-de-collided sheet")
    eq(erc_errors(good), 0, "ERC on the de-collided sheet")


@test("THE ADJACENT PROPERTY: a sheet with NO collisions comes out of the "
      "de-collision pass byte-for-byte unmoved")
def t_decollide_moves_nothing_it_should_not():
    """The control, and the property this pass is most likely to violate
    quietly. A de-collider that improves the crowded sheets by nudging every
    label a little has not fixed anything — it has replaced an author's layout
    with its own and made the diff unreadable.

    Graded the strongest way available: the two shipped no-collision fixtures
    are converted WITH the pass and with it held OFF, and the sheets must be
    IDENTICAL once UUIDs are normalised — not merely 'no findings either way'.

    MEASURED on the real fleet at the same time: the converter reports `moved 0
    of 33 labels` on smc0985-cooksense's interposer, whose S-OCCL count was
    already 0, and that sheet is byte-identical across this change too."""
    uu = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
    for fx in ("label_sides_h", "two_resistors"):
        cj = T0 / fx / "circuit.json"
        d1, good = _convert_json(cj, f"{fx}_ctl")
        d2, raw = _convert_json(cj, f"{fx}_ctl", raw=True)
        eq(uu.sub("U", good.read_text()), uu.sub("U", raw.read_text()),
           f"{fx}: the de-collision pass moved something on a clean sheet")

    # THE THIRD SHIPPED FIXTURE IS NOT A CONTROL, and finding that out is the
    # reason this test is worth more than its name suggests. `label_sides_v`
    # LOOKS clean — `t_label_sides_vertical` passes it — but that test grades
    # plate-vs-body and plate-vs-plate only. Its two VERTICAL plates run right
    # through the Reference and the Value, which are centred on the same x.
    # So it must MOVE, and the move is graded here in INK: the property glyph
    # runs are inside plate ink before and outside it after.
    cj = T0 / "label_sides_v" / "circuit.json"
    d1, good = _convert_json(cj, "lsv_ctl")
    d2, raw = _convert_json(cj, "lsv_ctl", raw=True)
    check(uu.sub("U", good.read_text()) != uu.sub("U", raw.read_text()),
          "label_sides_v was expected to MOVE — its vertical plates cross its "
          "own Reference and Value")
    for sheet, want_hit in ((raw, True), (good, False)):
        plates, _texts = _plate_ink(sheet)
        runs, _g = _svg_ink(sheet)
        worst = -1e9
        for prop in ("R1", "1k"):
            for pb in runs.get(prop, []):
                for boxes in plates.values():
                    for pl in boxes:
                        worst = max(worst, _ink_overlap(pb, pl))
        if want_hit:
            check(worst > 0.254,
                  f"un-de-collided label_sides_v: property ink is only "
                  f"{worst:.4f} mm inside a plate — not discriminating")
        else:
            check(worst <= 0.0,
                  f"de-collided label_sides_v STILL draws a plate {worst:.4f} "
                  f"mm through its own property text")


def _boxed_in_fixture():
    """`label_sides_h` with ONE thing added: a 3.0 x 3.0-unit component parked
    over everything the right-hand label could reach. 38.1 mm square is wider
    than the search's whole outward reach (6 x 1.27 mm) and taller than its
    whole sideways reach (2 x 10 x 1.27 mm), so no offset in the ladder escapes
    it — and that is arithmetic, not luck."""
    import json
    import tempfile
    src = json.load(open(T0 / "label_sides_h" / "circuit.json"))
    out = [dict(e) for e in src]
    for e in out:
        if e["type"] == "source_net" and e["source_net_id"] == "sn_b":
            e["name"] = "UNPLACEABLE_LABEL_NAME"
        if e["type"] == "schematic_net_label" and e["source_net_id"] == "sn_b":
            e["text"] = "UNPLACEABLE_LABEL_NAME"
    out += [
        {"type": "source_component", "source_component_id": "sc_BLK",
         "name": "U_BLK", "ftype": "simple_chip", "supplier_part_numbers": {}},
        {"type": "source_net", "source_net_id": "sn_g", "name": "GND",
         "subcircuit_connectivity_map_key": "k_g"},
        {"type": "source_port", "source_port_id": "sp_BLK_1",
         "source_component_id": "sc_BLK", "pin_number": 1, "name": "p1",
         "subcircuit_connectivity_map_key": "k_g"},
        {"type": "source_port", "source_port_id": "sp_BLK_2",
         "source_component_id": "sc_BLK", "pin_number": 2, "name": "p2",
         "subcircuit_connectivity_map_key": "k_g"},
        {"type": "schematic_component", "schematic_component_id": "shc_BLK",
         "center": {"x": 2.2, "y": 0.0}, "rotation": 0,
         "size": {"width": 3.0, "height": 3.0}, "pin_spacing": 0.2,
         "source_component_id": "sc_BLK", "symbol_name": "box"},
        {"type": "schematic_port", "schematic_port_id": "shp_BLK_1",
         "schematic_component_id": "shc_BLK", "center": {"x": 3.9, "y": 0.2},
         "source_port_id": "sp_BLK_1", "pin_number": 1,
         "facing_direction": "right"},
        {"type": "schematic_port", "schematic_port_id": "shp_BLK_2",
         "schematic_component_id": "shc_BLK", "center": {"x": 3.9, "y": -0.2},
         "source_port_id": "sp_BLK_2", "pin_number": 2,
         "facing_direction": "right"},
    ]
    p = Path(tempfile.mkdtemp(prefix="boxfx_")) / "circuit.json"
    p.write_text(json.dumps(out))
    return p


@test("a label with NO legal placement is a HARD ERROR naming it — never a "
      "silent drop and never a fallback to a different emitter",
      kind="known_bad")
def t_decollide_hard_error_names_the_label():
    """Canon S11, and the same rule the silkscreen `_place_owned` search has
    carried since a board shipped with no reference designators on it at all.

    Two things this asserts that a bare non-zero exit would not:
      * the message NAMES the label, because a de-collider that fails without
        saying which label is unplaceable sends the next agent to read a whole
        sheet;
      * it is NOT a `LayoutFallback`. Falling back to `--mode grid` would
        answer 'this label cannot be placed legibly' with a DIFFERENT SHEET,
        and the run would exit 0 with a quietly worse artifact. The fixture
        proves the exit is non-zero and the stdout carries no `MODE=grid`.

    THE ADJACENT PROPERTY, re-measured every run: remove the blocking component
    and NOTHING else, and the same label places without complaint. That is what
    separates 'the search is bounded correctly' from 'the search is broken'."""
    import json
    cj = _boxed_in_fixture()
    d = tmpdir("boxed_")
    r = run([PY, CONV, cj, "-o", d / "boxed.kicad_sch", "--project", "boxed"])
    must_fail(r, "converter on a boxed-in label", "UNPLACEABLE_LABEL_NAME")
    contains(r.out, "no legal placement", "converter output")
    contains(r.out, "LABEL PLACEMENT FAILED", "converter output")
    eq(r.rc, 3, "converter exit code on an unplaceable label")
    check("MODE=grid" not in r.out,
          "an unplaceable label fell back to --mode grid instead of failing — "
          "that answers the question with a different sheet")
    check(not (d / "boxed.kicad_sch").is_file() or
          "MODE=" not in r.out, "a sheet was reported written despite the error")
    # ...and with the blocker removed, the very same label is placeable.
    src = [e for e in json.load(open(cj))
           if e.get("source_component_id") != "sc_BLK"
           and e.get("schematic_component_id") not in ("shc_BLK",)
           and e.get("source_net_id") != "sn_g"]
    p2 = cj.parent / "unblocked.json"
    p2.write_text(json.dumps(src))
    d2, ok = _convert_json(p2, "unblocked")
    check(ok.is_file(), "the unblocked fixture did not convert")


@test("PRE-FIX INTERACTION: the de-collision pass HIDES the label-direction "
      "defect — so a clean S-OCCL is not a proof of direction",
      kind="known_bad")
def t_prefix_decollide_masks_the_direction_defect():
    """A finding about the gates, not about a board, and it is the reason
    `t_prefix_inverts_horizontal` and `t_prefix_inverts_vertical` hold this
    pass OFF instead of running end-to-end.

    With the PRE-FIX direction derivation restored, both plates of a horizontal
    2-pin part fire INWARD across the body. Run the de-collision pass on that
    sheet and it does its job: it shoves them somewhere they do not overlap, and
    the sheet comes out with ZERO collisions while every plate still points at
    the wrong pin. The occlusion count went to zero and the sheet still lies.

    So this fixture pins the ORDER of the two claims: direction is graded by
    `t_kicad_direction_table_is_measured` and by the two PRE-FIX fixtures with
    de-collision held off; S-OCCL grades crowding. Neither substitutes for the
    other, and anyone who later reads a green S-OCCL as evidence that labels
    point the right way has this test to tell them otherwise."""
    d, masked = convert_prefix("label_sides_h")      # PRE-FIX dirs, pass ON
    coll, plates, body = label_collisions(masked)
    check(not coll,
          f"expected the de-collision pass to HIDE the direction defect, but "
          f"the sheet still collides: {coll} — if this is now failing, the "
          f"pass has stopped masking it and the two PRE-FIX fixtures can go "
          f"back to running end-to-end")
    # ...while the direction is still wrong: the plate on the LEFT-hand pin
    # must still be reaching RIGHT, which is what makes the clean count a lie.
    j2s = {v: k for k, v in _C_MOD().LABEL_ANG_JUST.items()}
    sides = {}
    for m in re.finditer(r'\(global_label "([^"]+)".*?\(at [-\d.]+ [-\d.]+ '
                         r'(\d+)\).*?\(justify (\w+)\)', masked.read_text()):
        sides[m.group(1)] = j2s[(int(m.group(2)), m.group(3))]
    eq(sides.get(NET_L), "right",
       f"{NET_L} sits on the LEFT-hand pin; pre-fix its plate reaches")
    eq(sides.get(NET_R), "left",
       f"{NET_R} sits on the RIGHT-hand pin; pre-fix its plate reaches")


def _C_MOD():
    sys.path.insert(0, str(SCRIPTS))
    import circuit_json_to_kicad_sch as C          # noqa: E402
    return C


@test("the label PLATE geometry the de-collision search runs on is MEASURED "
      "from KiCad's own render, not derived — base, cross extent and the "
      "whole per-character advance table")
def t_text_geometry_is_measured():
    """Canon M1: the emitter must not grade its own geometry, and the brief's
    standing rule that a geometry constant is measured, never inherited. Two
    constants in this repo's schematic geometry were recently found wrong in
    OPPOSITE directions — a plate cross extent 13% narrow (silence) and a
    property half-height 70% too tall (invention) — and this is the third:
    `CH_W = 1.05` per character, flat, against a PROPORTIONAL stroke font.

    Everything the search depends on is re-derived here from `kicad-cli sch
    export svg` ink on a probe sheet KiCad renders itself:
      * PLATE_BASE and PLATE_CROSS, both of which measure with ZERO spread;
      * the FULL per-character advance table, every entry of which must come
        back an exact k/21 of the font size (KiCad's newstroke em is 21 units,
        so a non-integer would mean the measurement, not the font, is wrong);
      * the property text's up/down extents and the no-connect half-extent.

    It also asserts the model is an UPPER bound on rendered ink, which is the
    direction that matters: a plate model that under-reaches places labels the
    search calls clear and KiCad draws through their neighbours."""
    C = _C_MOD()
    import schwriter2 as SW                        # noqa: E402
    d = tmpdir("textprobe_")
    n = [0]

    def uu():
        n[0] += 1
        return "00000000-0000-0000-0000-%012d" % n[0]

    chars = sorted(C.ADV21)
    out = ['(kicad_sch (version 20230121) (generator probe)',
           '  (uuid "00000000-0000-0000-0000-000000000001")',
           '  (paper "User" 1600.00 2400.00)',
           '  (title_block (title "probe") (date "2026-07-31") (rev "p")', '  )',
           '  (lib_symbols'] + list(SW.power_lib_symbols("elt").values()) + ['  )']
    sites, i = {}, 0
    for c in chars:
        for rep in (1, 10):
            nm = c * rep
            x, y = 90 + (i % 6) * 250, 60 + (i // 6) * 30
            sites[(c, rep)] = (x, y)
            esc = nm.replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'  (global_label "{esc}" (shape passive) (at {x} {y} 0)'
                       f' (fields_autoplaced) (effects (font (size 1.27 1.27))'
                       f' (justify left)) (uuid "{uu()}"))')
            i += 1
    ncx, ncy = 90, 60 + (i // 6 + 3) * 30
    out.append(f'  (no_connect (at {ncx} {ncy}) (uuid "{uu()}"))')
    out += ['  (sheet_instances (path "/" (page "1")))', ')']
    sch = d / "probe.kicad_sch"
    sch.write_text("\n".join(out) + "\n")
    _runs, graphics = _svg_ink(sch)
    polys = {}
    for (p, q) in graphics:
        polys.setdefault(None, []).append((p, q))
    # rebuild closed boxes from the raw segment soup: group by proximity to a
    # probe site and take the extent of everything near it.
    def ink_box(x, y, reach):
        acc = [v for seg in graphics for v in seg
               if abs(v[0] - x) < reach and abs(v[1] - y) < reach]
        check(acc, f"no ink within {reach} mm of ({x}, {y})")
        return (min(v[0] for v in acc), min(v[1] for v in acc),
                max(v[0] for v in acc), max(v[1] for v in acc))

    bases, crosses, nonint = set(), set(), []
    for c in chars:
        x1, y1 = sites[(c, 1)]
        x10, y10 = sites[(c, 10)]
        b1 = ink_box(x1, y1, 24.0)
        b10 = ink_box(x10, y10, 24.0)
        adv = ((b10[2] - b10[0]) - (b1[2] - b1[0])) / 9.0
        k = adv / 1.27 * 21.0
        if abs(k - round(k)) > 0.02:
            nonint.append((c, round(k, 3)))
        eq(round(k), C.ADV21[c], f"advance of {c!r}, in 21sts of the font size")
        bases.add(round((b1[2] - b1[0]) - adv, 4))
        crosses.add(round(b1[3] - b1[1], 4))
    check(not nonint,
          f"advances that are not an integer 21st of the font size: {nonint}")
    eq(sorted(bases), [round(C.PLATE_BASE, 4)],
       "PLATE_BASE measured out of the render (a set, so ZERO spread is "
       "asserted, not averaged away)")
    eq(sorted(crosses), [round(C.PLATE_CROSS, 4)],
       "PLATE_CROSS measured out of the render (zero spread asserted)")

    # the model must never UNDER-reach the ink it stands for
    for c in chars:
        for rep in (1, 10):
            x, y = sites[(c, rep)]
            got = ink_box(x, y, 24.0)[2] - ink_box(x, y, 24.0)[0]
            want = C.plate_span(c * rep)
            check(want >= got - 0.002,
                  f"plate_span({c * rep!r}) = {want:.4f} mm UNDER-reaches the "
                  f"{got:.4f} mm KiCad draws")

    # the no-connect marker
    nb = ink_box(ncx, ncy, 6.0)
    for e, want in zip(nb, (ncx - C.NC_HALF, ncy - C.NC_HALF,
                            ncx + C.NC_HALF, ncy + C.NC_HALF)):
        check(abs(e - want) <= 0.02,
              f"no_connect marker edge {e:.4f} vs NC_HALF prediction {want:.4f}")


@test("property text: the up/down extents the de-collision search treats a "
      "Reference/Value as occupying are MEASURED, and are an upper bound")
def t_prop_text_geometry_is_measured():
    """`prop_box` is the other half of the obstacle model — 49 of the fleet's
    182 findings were a plate on a Reference or a Value — and its vertical
    extent is ASYMMETRIC about the anchor (a descender reaches further down
    than any capital reaches up), which a single half-height cannot express."""
    C = _C_MOD()
    d = tmpdir("proptext_")
    n = [0]

    def uu():
        n[0] += 1
        return "00000000-0000-0000-0000-%012d" % n[0]

    probe = ('    (symbol "elt:BOX" (in_bom no) (on_board yes)\n'
             '      (property "Reference" "#B" (at 0 0 0)'
             ' (effects (font (size 1.27 1.27)) hide))\n'
             '      (property "Value" "B" (at 0 0 0)'
             ' (effects (font (size 1.27 1.27)) hide))\n'
             '      (symbol "BOX_0_1"\n'
             '        (rectangle (start -2 -2) (end 2 2)'
             ' (stroke (width 0.254) (type default)) (fill (type none)))\n'
             '      )\n    )')
    out = ['(kicad_sch (version 20230121) (generator probe)',
           '  (uuid "00000000-0000-0000-0000-000000000001")',
           '  (paper "User" 1400.00 900.00)',
           '  (title_block (title "probe") (date "2026-07-31") (rev "p")', '  )',
           '  (lib_symbols', probe, '  )']
    cases, i = [], 0
    for txt in ("R1", "C_SW2", "C3716677", "WWWWWWWWWW", "IIIIIIIIII"):
        x, y = 90 + (i % 4) * 300, 90 + (i // 4) * 120
        cases.append((txt, x, y))
        out += [f'  (symbol (lib_id "elt:BOX") (at {x} {y} 0) (unit 1)'
                f' (in_bom no) (on_board yes) (dnp no) (uuid "{uu()}")',
                f'    (property "Reference" "#B{i:02d}" (at {x} {y - 8} 0)'
                f' (effects (font (size 1.27 1.27)) hide))',
                f'    (property "Value" "{txt}" (at {x} {y + 8} 0)'
                f' (effects (font (size 1.27 1.27))))',
                f'    (pin "1" (uuid "{uu()}"))',
                f'    (instances (project "probe" (path "/00000000-0000-0000-'
                f'0000-000000000001" (reference "#B{i:02d}") (unit 1))))', '  )']
        i += 1
    out += ['  (sheet_instances (path "/" (page "1")))', ')']
    sch = d / "probe.kicad_sch"
    sch.write_text("\n".join(out) + "\n")
    runs, _g = _svg_ink(sch)
    seen = 0
    for txt, x, y in cases:
        boxes = [b for b in runs.get(txt, []) if abs(b[1] - (y + 8)) < 4]
        check(boxes, f"{txt!r}: no rendered glyph run near its anchor")
        b = boxes[0]
        pred = C.prop_box(txt, x, y + 8)
        check(pred[0] <= b[0] + 1e-6 and b[2] <= pred[2] + 1e-6,
              f"prop_box({txt!r}) x-extent {pred[0]:.3f}..{pred[2]:.3f} does "
              f"not contain the rendered {b[0]:.3f}..{b[2]:.3f}")
        check(pred[1] <= b[1] + 1e-6 and b[3] <= pred[3] + 1e-6,
              f"prop_box({txt!r}) y-extent {pred[1]:.3f}..{pred[3]:.3f} does "
              f"not contain the rendered {b[1]:.3f}..{b[3]:.3f}")
        seen += 1
    eq(seen, len(cases), "property texts measured out of the render")


@test("the de-collision search is DETERMINISTIC and refuses to change a "
      "label's reach direction or its net")
def t_decollide_is_deterministic_and_refuses():
    """Two properties the pipeline's regenerability rests on.

    DETERMINISM: the same circuit.json converted twice must place every label
    at the same coordinate. The sheet is not byte-comparable (UUIDs are fresh
    every run by design), so this compares the label set itself.

    WHAT IT REFUSES: every emitted label must still carry the (angle, justify)
    of the side it started on. A plate is read as belonging to the pin at its
    blunt end, so turning one around re-attributes it to a different pin — the
    exact defect `948ef54d` fixed — and no amount of extra whitespace is worth
    re-introducing it."""
    C = _C_MOD()
    cj = _twin_fixture("label_sides_h", 3.2, 0.0, _RENAME)

    def labels(sheet):
        return sorted(re.findall(
            r'\(global_label "([^"]+)" \(shape passive\) \(at ([-\d.]+) '
            r'([-\d.]+) (\d+)\).*?\(justify (\w+)\)', sheet.read_text()))

    d1, a = _convert_json(cj, "det_a")
    d2, b = _convert_json(cj, "det_b")
    eq(labels(a), labels(b), "label placement across two identical runs")
    d3, raw = _convert_json(cj, "det_raw", raw=True)
    before = {n: (ang, j) for n, _x, _y, ang, j in labels(raw)}
    after = {n: (ang, j) for n, _x, _y, ang, j in labels(a)}
    eq(after, before, "the (angle, justify) of every label across the pass")
    check(set(after) == set(before),
          f"the pass changed the label SET: {set(before) ^ set(after)}")
    # ...and it really did move something, or the assertion above is vacuous
    moved = [n for n, x, y, _a, _j in labels(a)
             if (n, x, y) not in {(m, p, q) for m, p, q, _c, _d in labels(raw)}]
    check(moved, "no label moved at all — this fixture proves nothing")


if __name__ == "__main__":
    sys.exit(main())
