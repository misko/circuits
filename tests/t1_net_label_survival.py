#!/usr/bin/env python3
"""T1: net_label_survival.py — the schematic NET-MERGE gate (candidate
S-NETMERGE) — plus the template rebuild_all.sh semantic-battery wiring.

Motivating incident (crow-recorder-central-v2, 2026-07-23, red-team P0):
`kicad-cli sch export netlist` connects wires whose endpoint touches a foreign
wire (T-junction) or that overlap collinearly. TWO nets merged this way on one
board — P5VA_4 -> AUDIO4M (port-4 +5V pins landed on the ch4 balanced-minus
into the ADC) and MID2P -> 5V (an RC mid-node DC-shorted to the 5V rail).
Every downstream gate stayed green (ERC 0, DRC 0/0, count_parity 194==194)
because all are SELF-consistent with the merged netlist; only the label-intent
-vs-netlist comparison sees it. The bespoke gate that caught MID2P
(crow-recorder 03_src/check_port_nets.py, main commit 8017400) is promoted
here to the config-driven shared skill script.

RED-VERIFIED (new-gate variant, per tests/README "Adding a regression"):
net_label_survival.py did not exist before this change, so the suite cannot
run against pre-fix code. Instead every known-bad fixture is the clean fixture
broken in exactly ONE way, and the incident itself is pinned: the P5VA_4 test
reproduces the merge shape (label present in the sch, net absent from the
netlist, its pins living under the foreign net). Measured against the REAL
repaired board (main tree, 2026-07-23): PASS — 115 labels all survive.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

GATE = SCRIPTS / "net_label_survival.py"
TEMPLATE = ROOT / "skills" / "pcb-design" / "templates" / "03_src" / "rebuild_all.sh"


# --------------------------------------------------------------- fixtures
def netlist(nets):
    """nets: {netname: [(ref, pin), ...]} -> a KiCad .net string."""
    blocks = []
    for i, (name, nodes) in enumerate(nets.items(), 1):
        ns = "".join(f'(node (ref "{r}") (pin "{p}") (pintype "passive"))'
                     for r, p in nodes)
        blocks.append(f'(net (code "{i}") (name "{name}") {ns})')
    return '(export (version "E") (nets ' + "".join(blocks) + "))"


def schematic(labels):
    body = "".join(
        f'(global_label "{l}" (shape input) (at 0 0 0))\n' for l in labels)
    return f'(kicad_sch (version 20250114)\n{body})'


def project(labels, nets, cfg_text=None):
    """Scratch tree exercising auto-location: 03_tscircuit/kicad sch,
    06_build/netlists net, 03_src/rules/electrical_invariants.yaml config."""
    d = tmpdir("nls_")
    (d / "03_tscircuit" / "kicad").mkdir(parents=True)
    (d / "06_build" / "netlists").mkdir(parents=True)
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "03_tscircuit" / "kicad" / "b.kicad_sch").write_text(
        schematic(labels))
    (d / "06_build" / "netlists" / "b.net").write_text(netlist(nets))
    if cfg_text is not None:
        (d / "03_src" / "rules" / "electrical_invariants.yaml").write_text(
            cfg_text)
    return d


# The incident shape: two audio ports. Clean = each label owns its net.
CLEAN_NETS = {
    "AUDIO4M":  [("J6", "2"), ("U9", "5")],
    "P5VA_4":   [("J6", "4"), ("J6", "7"), ("F4", "2")],
    "GND":      [("J6", "5"), ("J6", "8")],
}
CLEAN_LABELS = ["AUDIO4M", "P5VA_4", "GND"]

PIN_CFG = """\
label_survival:
  pin_map:
    - refs: [J6]
      n_start: 4
      pins: {"2": "AUDIO{n}M", "4": "P5VA_{n}", "7": "P5VA_{n}", "5": GND}
      unconnected: ["9"]
"""


# --------------------------------------------------------------- clean cases
@test("survival PASSES when every schematic label is a netlist net (no config)")
def t_clean_no_config():
    d = project(CLEAN_LABELS, CLEAN_NETS)
    r = must_pass(run([KPY, GATE, d]), "survival on an intact netlist")
    # G-COVER (2026-07-27): the verdict now carries an N/M denominator, so a
    # run over ZERO labels can no longer read like a run over three.
    contains(r.out, "3/3 labels survive", "verdict carries its denominator")
    contains(r.out, "input: schematic", "verdict names the artifact it graded")


@test("pin_map PASSES pin-for-pin with {n} substitution")
def t_clean_pin_map():
    d = project(CLEAN_LABELS, CLEAN_NETS, PIN_CFG)
    r = must_pass(run([KPY, GATE, d]), "survival + pin_map on the clean board")
    contains(r.out, "pin-map assertions hold", "verdict")


@test("an exempt label with why-evidence is allowed to be absent")
def t_clean_exempt():
    cfg = ('label_survival:\n  exempt:\n'
           '    - {label: SPARE, why: "unloaded test-point label, ADR-0009"}\n')
    d = project(CLEAN_LABELS + ["SPARE"], CLEAN_NETS, cfg)
    must_pass(run([KPY, GATE, d]), "survival with an evidenced exemption")


@test("schema-only validates label_survival without generated artifacts")
def t_schema_only_clean():
    d = project(CLEAN_LABELS, CLEAN_NETS, PIN_CFG)
    (d / "03_tscircuit/kicad/b.kicad_sch").unlink()
    (d / "06_build/netlists/b.net").unlink()
    r = must_pass(run([KPY, GATE, d, "--schema-only"]),
                  "source-only label schema")
    contains(r.out, "S-NETMERGE-SCHEMA PASS", "source-only verdict")


# ----------------------------------------------------------- known-bad cases
@test("survival FAILS the P5VA_4->AUDIO4M merge: label swallowed at export",
      kind="known_bad")
def t_merged_label():
    """THE INCIDENT (crow-recorder-central-v2 red-team P0, 2026-07-23): the
    clean fixture broken in exactly one way — the geometric merge's netlist
    signature: P5VA_4 remains a schematic global_label but its pins live
    under AUDIO4M and no P5VA_4 net exists. ERC/DRC/count-parity are all
    green on this shape; only label-intent-vs-netlist sees it."""
    merged = {
        "AUDIO4M": [("J6", "2"), ("U9", "5"),           # the foreign net ate
                    ("J6", "4"), ("J6", "7"), ("F4", "2")],  # P5VA_4's pins
        "GND":     [("J6", "5"), ("J6", "8")],
    }
    d = project(CLEAN_LABELS, merged)
    r = must_fail(run([KPY, GATE, d]), "survival on the merged netlist",
                  "LABEL-LOST")
    contains(r.out, "P5VA_4", "the finding names the swallowed label")


@test("pin_map FAILS when a port pin lands on the wrong net", kind="known_bad")
def t_pin_map_wrong_net():
    """The specific half of the incident: J6.4 (+5V-audio) on the ch4
    balanced-minus. Both labels still exist as nets, so survival alone is
    silent — the pin_map is the check that bites."""
    swapped = {
        "AUDIO4M": [("J6", "2"), ("U9", "5"), ("J6", "4")],  # J6.4 misplanted
        "P5VA_4":  [("J6", "7"), ("F4", "2")],
        "GND":     [("J6", "5"), ("J6", "8")],
    }
    d = project(CLEAN_LABELS, swapped, PIN_CFG)
    must_fail(run([KPY, GATE, d]), "pin_map on a misplanted port pin",
              "PIN-MAP: J6.4")


@test("pin_map FAILS when a must-be-unconnected pin carries a real net",
      kind="known_bad")
def t_pin_map_unconnected():
    nets = dict(CLEAN_NETS)
    nets["AUDIO4M"] = nets["AUDIO4M"] + [("J6", "9")]     # NC pin wired
    d = project(CLEAN_LABELS, nets, PIN_CFG)
    must_fail(run([KPY, GATE, d]), "pin_map on a wired NC pin",
              "PIN-MAP: J6.9")


@test("an exempt entry WITHOUT why-evidence is a config error (canon M4)",
      kind="known_bad")
def t_exempt_needs_evidence():
    cfg = 'label_survival:\n  exempt:\n    - {label: SPARE}\n'
    d = project(CLEAN_LABELS, CLEAN_NETS, cfg)
    r = must_fail(run([KPY, GATE, d]), "unevidenced exemption", "why")
    check(r.rc == 2, f"config error must exit 2, got {r.rc}")


@test("schema-only rejects malformed label_survival before generation",
      kind="known_bad")
def t_schema_only_malformed():
    d = project(CLEAN_LABELS, CLEAN_NETS,
                "label_survival:\n  pin_map:\n    - refs: [J6]\n")
    r = must_fail(run([KPY, GATE, d, "--schema-only"]),
                  "malformed source-only schema", "needs 'refs:'")
    check(r.rc == 2, f"schema load error must exit 2, got {r.rc}")


@test("schema-only rejects board-specific labels at the wrong schema level",
      kind="known_bad")
def t_schema_only_rejects_unknown_keys_instead_of_passing_zero_rows():
    d = project(CLEAN_LABELS, CLEAN_NETS,
                "label_survival:\n  RF_COMMON: [J2.1, U1.22]\n")
    r = must_fail(run([KPY, GATE, d, "--schema-only"]),
                  "wrong-shape label map", "unknown key")
    contains(r.out, "not a pin_map", "diagnosis names the vacuous-pass trap")
    check(r.rc == 2, f"schema load error must exit 2, got {r.rc}")


@test("a netlist that parses to ZERO nets is a hard error, never a pass",
      kind="known_bad")
def t_zero_nets_guard():
    """Generator hard-rule 2: a parse that yields zero results is an ERROR
    (the KiCad 7->10 netlist format change class)."""
    d = project(CLEAN_LABELS, {})
    (d / "06_build" / "netlists" / "b.net").write_text("(export (nets))")
    r = must_fail(run([KPY, GATE, d]), "zero-net netlist", "0 nets")
    check(r.rc == 2, f"load error must exit 2, got {r.rc}")


@test("a SCHEMATIC that parses to ZERO global labels is a hard error too",
      kind="known_bad")
def t_zero_labels_guard():
    """THE OTHER SIDE OF THE SAME PARSE, and it was open (2026-07-27, G-COVER).
    The zero-NET guard above landed; the zero-LABEL case did not. A schematic
    yielding no global labels — a KiCad format change on the label side, a
    sheet whose labels never got written, the wrong file globbed — made
    `survival_findings` iterate an empty list and print
    `PASS — 0 labels all survive to the netlist`, exit 0. Every label
    trivially survives when there are none, and the incident this gate pins
    (P5VA_4 -> AUDIO4M) IS a label that vanished.
    RED-VERIFIED against pre-fix code (git show 5054b07:...net_label_survival
    .py): it exits 0 with that message, so must_fail goes RED."""
    d = project([], CLEAN_NETS)
    r = must_fail(run([KPY, GATE, d]), "zero-label schematic", "0 global")
    check(r.rc == 2, f"load error must exit 2, got {r.rc}")
    contains(r.out, "M-COVER", "cites the canon it is enforcing")


# ------------------------------------------- template rebuild_all.sh wiring
@test("template rebuild_all.sh wires the semantic battery in canonical order")
def t_template_wiring_order():
    """Deliverable check (Wave-1 skill text, 72915ba): tsx_preflight BEFORE
    tsci build; net_label_survival + electrical_invariants (+ --adr-coverage)
    + power_topology (+ --margin/--off-control) + count_parity + the
    --circuit-only M-BOM leg RIGHT AFTER netlist export; each failure aborts
    with a named GATE FAILED line; set -euo pipefail preserved."""
    txt = TEMPLATE.read_text()
    contains(txt, "set -euo pipefail", "template strictness")

    def pos(needle):
        i = txt.find(needle)
        check(i >= 0, f"template rebuild_all.sh is missing {needle!r}")
        return i

    preflight = pos("tsx_preflight.py")
    # The canonical driver runs the producer through pcb_flow's bounded
    # heartbeat/timeout wrapper.  Match that live invocation rather than the
    # pre-IMP-013 unbounded shell spelling.
    build = pos("run_stage tscircuit_build env --chdir=03_tscircuit "
                "./node_modules/.bin/tsci build")
    export = pos("sch export netlist")
    erc = pos("sch erc")
    schema = pos("--schema-only")
    post_label = txt.find("net_label_survival.py", schema + len("--schema-only"))
    check(post_label >= 0, "template needs the post-export S-NETMERGE gate too")
    pre_einv = txt.find("electrical_invariants.py", schema)
    post_einv = txt.find("electrical_invariants.py", build)
    battery = [post_label,
               post_einv,
               pos("--adr-coverage"),
               pos("power_topology.py"),
               pos("--margin"),
               pos("--off-control"),
               pos("count_parity.py"),
               pos("--circuit-only")]
    check(preflight < build, "tsx_preflight must run BEFORE tsci build "
                             "(tscircuit drops unmapped parts silently)")
    check(preflight < schema < build,
          "label_survival schema validation must run before tsci build")
    check(schema < pre_einv < build,
          "electrical invariant schema validation must run before tsci build")
    check(txt.find("early_design_check.py") < build,
          "source-only electrical schema validation must run before tsci build")
    check(export < min(battery), "the semantic battery must run AFTER the "
                                 "netlist export it grades")
    check(max(battery) < erc,
          "battery is wired right after netlist export (before the ERC step)")
    for g in ("TSX-PRE", "S-NETMERGE", "E-INV", "E-ADR", "E-TOPO", "E-MARGIN",
              "E-OFF", "S-COUNT", "M-BOM"):
        contains(txt, f"GATE FAILED", "named abort lines")
        check(g in txt, f"no named GATE FAILED line for {g}")


@test("template battery aborts on the FIRST failing gate with its named line",
      kind="known_bad")
def t_template_abort_names_gate():
    """Run the template's [0]+[1b] stanza against a scratch project whose
    invariants file violates the netlist — the driver must exit nonzero and
    print the E-INV named line, not continue to later steps. (The stanza is
    extracted and run standalone so no tsci/kicad-cli is needed — hermetic.)"""
    d = project(CLEAN_LABELS, CLEAN_NETS)
    (d / "02_parts").mkdir()
    (d / "03_src" / "rules" / "electrical_invariants.yaml").write_text(
        "invariants:\n"
        "  - assert: pin_on_net\n"
        "    pin: \"J6.4\"\n"
        "    net: TOTALLY_ELSEWHERE\n"
        "    adr: \"0001\"\n"
        "    why: \"deliberately violated fixture\"\n")
    txt = TEMPLATE.read_text()
    # extract the [1b] battery stanza verbatim from the template
    start = txt.index("# [1b]")
    end = txt.index("# [2]")
    stanza = txt[start:end]
    script = (f'set -euo pipefail\ncd "{d}"\nPY={KPY}\nS="{SCRIPTS}"\n'
              f'FS="{ROOT}/skills/jlcpcb-fab/scripts"\n' + stanza)
    r = run(["bash", "-c", script])
    check(r.rc != 0, "battery must abort on the violated invariant")
    contains(r.out, "GATE FAILED [1b] E-INV", "the abort names the gate")
    contains(r.out, "TOTALLY_ELSEWHERE", "the checker's own finding printed")


if __name__ == "__main__":
    sys.exit(main())
