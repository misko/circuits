#!/usr/bin/env python3
"""T1: critical differential-pair contract and copper proof."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, contains, main, must_fail, must_pass, run,  # noqa: E402
                     test, tmpdir)

CR = ROOT / "skills" / "kicad-pcb" / "scripts" / "critical_route_check.py"
RS = ROOT / "skills" / "kicad-pcb" / "scripts" / "route_and_stitch_generic.py"


def fixture(*, connected=False, reversed_pair=False, omit_match=False,
            add_via=False, omitted_inventory=False):
    d = tmpdir("critical_route_")
    src = d / "03_src"
    src.mkdir()
    rules = src / "rules"
    rules.mkdir()
    extra = ("\n  AUX:\n    members: {P: [AUX_P], N: [AUX_N]}\n"
             if omitted_inventory else "")
    (rules / "nets.yaml").write_text(
        "length_match:\n  USB:\n"
        "    members: {P: [USB_P], N: [USB_N]}\n" + extra)
    p, n = ("USB_N", "USB_P") if reversed_pair else ("USB_P", "USB_N")
    match = "[]" if omit_match else f"[[{p}, {n}]]"
    (src / "route.yaml").write_text(f"""project: {{name: test, board: b.kicad_pcb}}
prep:
  waves:
    groups: {{usb: [USB_P, USB_N]}}
route:
  common: {{layers: [F.Cu]}}
  preflight_critical_pairs:
    - {{name: USB, p: {p}, n: {n}, wave: usb, allowed_layers: [F.Cu], no_vias: true}}
  waves:
    - name: usb
      engine: diff
      group: usb
      layers: [F.Cu]
      length_match_group: {match}
""")
    board = d / "b.kicad_pcb"
    code = f"""
import pcbnew
V=pcbnew.VECTOR2I_MM
b=pcbnew.CreateEmptyBoard()
nets={{}}
for nm in ('USB_P','USB_N'):
 ni=pcbnew.NETINFO_ITEM(b,nm); b.Add(ni); nets[nm]=ni
def fp(ref,x):
 f=pcbnew.FOOTPRINT(b); f.SetReference(ref); b.Add(f); f.SetPosition(V(x,10))
 for i,nm in enumerate(('USB_P','USB_N')):
  p=pcbnew.PAD(f); p.SetNumber(str(i+1)); p.SetShape(pcbnew.PAD_SHAPE_RECT)
  p.SetSize(V(1,1)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetLayerSet(pcbnew.PAD.SMDMask())
  f.Add(p); p.SetPosition(V(x,10+i*2)); p.SetNet(nets[nm])
 return f
a=fp('U1',10); z=fp('J1',30)
if {connected!r}:
 for i,nm in enumerate(('USB_P','USB_N')):
  t=pcbnew.PCB_TRACK(b); t.SetNet(nets[nm]); t.SetLayer(pcbnew.F_Cu)
  t.SetWidth(pcbnew.FromMM(0.25)); t.SetStart(V(10,10+i*2)); t.SetEnd(V(30,10+i*2)); b.Add(t)
if {add_via!r}:
 v=pcbnew.PCB_VIA(b); v.SetNet(nets['USB_P']); v.SetPosition(V(20,10))
 v.SetWidth(pcbnew.FromMM(0.6)); v.SetDrill(pcbnew.FromMM(0.3)); b.Add(v)
pcbnew.SaveBoard(r'{board}',b)
"""
    must_pass(run([KPY, "-c", code]), "critical-route fixture")
    return d, board


@test("R-PAIRMAP passes a well-formed critical pair contract")
def t_contract_clean():
    d, board = fixture()
    r = must_pass(run([KPY, CR, d, "--board", board]), "critical contract")
    contains(r.out, "1 critical pair(s) contracted", "contract denominator")


@test("R-PAIRMAP reports an explicit no-differential-pair disposition with a zero denominator")
def t_no_critical_routes_clean():
    d, board = fixture()
    route = d / "03_src/route.yaml"
    route.write_text(
        "project: {name: test, board: b.kicad_pcb}\n"
        "route:\n"
        "  preflight_critical_pairs: []\n"
        "  no_critical_routes: Independent single-ended RF paths are graded elsewhere.\n"
    )
    r = must_pass(run([KPY, CR, d, "--board", board]),
                  "explicit no-critical-routes contract")
    contains(r.out, "no critical routes: Independent single-ended RF paths",
             "applicability reason")
    contains(r.out, "0 critical pair(s) contracted", "zero denominator")


@test("R-PAIRMAP rejects reversed P/N declarations", kind="known_bad")
def t_reversed():
    d, board = fixture(reversed_pair=True)
    must_fail(run([KPY, CR, d, "--board", board]),
              "reversed pair", "polarity")


@test("R-PAIRMAP rejects a pair absent from length matching", kind="known_bad")
def t_missing_match():
    d, board = fixture(omit_match=True)
    must_fail(run([KPY, CR, d, "--board", board]),
              "missing match group", "length_match_group")


@test("R-PAIRMAP rejects an omitted physical pair derived from independent "
      "length-match intent", kind="known_bad")
def t_omitted_inventory_pair():
    d, board = fixture(omitted_inventory=True)
    must_fail(run([KPY, CR, d, "--board", board]),
              "self-declared pair inventory omission", "AUX_P/AUX_N")


@test("direct adopted route prep cannot bypass R-PAIRMAP", kind="known_bad")
def t_direct_route_entry_is_gated():
    d, _ = fixture(omitted_inventory=True)
    (d / "03_src/rules/requirements.yaml").write_text(
        "schema: 1\npower_claims: []\n"
        "no_external_power_outputs: Fixture adoption marker.\n")
    must_fail(run([KPY, RS, "prep", d / "03_src/route.yaml"]),
              "direct route prep bypass", "AUX_P/AUX_N")


@test("R-CRITESC passes connected single-layer no-via copper")
def t_connected():
    d, board = fixture(connected=True)
    r = must_pass(run([KPY, CR, d, "--board", board, "--require-connected"]),
                  "connected critical pair")
    contains(r.out, "1 critical pair(s) connected", "connected denominator")


@test("R-CRITESC rejects an open critical pair", kind="known_bad")
def t_open():
    d, board = fixture()
    must_fail(run([KPY, CR, d, "--board", board, "--require-connected"]),
              "open critical pair", "unconnected pads")


@test("R-CRITESC rejects a via on a declared no-via pair", kind="known_bad")
def t_via():
    d, board = fixture(connected=True, add_via=True)
    must_fail(run([KPY, CR, d, "--board", board, "--require-connected"]),
              "via on no-via pair", "expected zero")


if __name__ == "__main__":
    sys.exit(main())
