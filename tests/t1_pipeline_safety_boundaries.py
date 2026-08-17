#!/usr/bin/env python3
"""Red fixtures for the routing/pause/first-article safety boundaries."""
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, SCRIPTS, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

PROGRESS = SCRIPTS / "route_progress_guard.py"
OWNERSHIP = SCRIPTS / "route_ownership_preflight.py"
CANDIDATE = SCRIPTS / "route_candidate_workspace.py"
EXPERIMENT = SCRIPTS / "route_experiment_store.py"
PAUSE = ROOT / "skills/pcb-design/scripts/pause_state.py"
FIRST_ARTICLE = FAB_SCRIPTS / "first_article_check.py"
REALIZED_WIDTH = SCRIPTS / "realized_track_width_guard.py"


@test("new route controls are enforce-by-default without changing the public stage")
def t_route_control_integration():
    template = yaml.safe_load((ROOT / "skills/pcb-design/templates/03_src/route.yaml")
                              .read_text(encoding="utf-8-sig"))
    route = template["route"]
    for key in ("ownership_preflight", "candidate_grade", "exploration_guard"):
        if route[key].get("mode") != "enforce":
            raise AssertionError(f"new-project {key} is not enforce mode")
    driver = (SCRIPTS / "route_and_stitch_generic.py").read_text(
        encoding="utf-8-sig")
    ownership = driver.index("_route_ownership_gate(cfg, build)")
    route_call = driver.index("cur = _wave_chain(cfg, py, krt, waves")
    candidate = driver.index("_grade_route_candidate(\n                cfg, workdir")
    progress = driver.index("progress.setdefault(\"waves\", []).append")
    if not ownership < route_call or not candidate < progress:
        raise AssertionError("route control boundary order regressed")
    authority = json.loads((ROOT / "skills/pcb-design/references/skill-authority-map.json")
                           .read_text(encoding="utf-8-sig"))
    stage_ids = [row["spec"]["id"] for row in authority["stages"]]
    if stage_ids.count("KICAD-ROUTING") != 1:
        raise AssertionError("public KICAD-ROUTING stage was split or duplicated")


@test("route_progress_guard.py stops coordinate-only churn", kind="known_bad")
def t_progress_plateau():
    directory = tmpdir("progress-red-")
    state = directory / "state.json"
    observation = directory / "observation.json"
    body = {"subject": "r0:wave", "unresolved": ["SCL"],
            "hard_findings": [{"type": "clearance", "x_mm": 1.0,
                               "owner": "hub_top"}],
            "frontier": [{"owner": "hub_top", "x_mm": 1.0}]}
    observation.write_text(json.dumps(body))
    must_pass(run([sys.executable, PROGRESS, "observe", observation, state]),
              "first semantic observation")
    body["hard_findings"][0]["x_mm"] = 99.0
    body["frontier"][0]["x_mm"] = 99.0
    observation.write_text(json.dumps(body))
    must_fail(run([sys.executable, PROGRESS, "observe", observation, state]),
              "repeated semantic frontier", "STAGNATED")


@test("route_ownership_preflight.py refuses unowned many-pad power", kind="known_bad")
def t_unowned_power():
    project = tmpdir("ownership-red-")
    (project / "03_src/rules").mkdir(parents=True)
    (project / "04_kicad").mkdir()
    board = project / "04_kicad/board.kicad_pcb"
    code = f"""
import pcbnew
V=pcbnew.VECTOR2I_MM
b=pcbnew.CreateEmptyBoard(); net=pcbnew.NETINFO_ITEM(b,'P5V'); b.Add(net)
for i in range(8):
 f=pcbnew.FOOTPRINT(b); f.SetReference('U%d'%(i+1)); b.Add(f); f.SetPosition(V(5+i*2,5))
 p=pcbnew.PAD(f); p.SetNumber('1'); p.SetShape(pcbnew.PAD_SHAPE_RECT)
 p.SetSize(V(1,1)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetLayerSet(pcbnew.PAD.SMDMask())
 f.Add(p); p.SetPosition(V(5+i*2,5)); p.SetNet(net)
pcbnew.SaveBoard(r'{board}',b)
"""
    must_pass(run([KPY, "-c", code]), "ownership board fixture")
    (project / "03_src/route.yaml").write_text("""
project: {board: 04_kicad/board.kicad_pcb}
prep: {waves: {groups: {pwr: [P5V]}}}
route:
  waves: [{name: pwr, group: pwr}]
""")
    (project / "03_src/rules/nets.yaml").write_text("""
classes:
  POWER: {nets: [P5V], routing: pour_or_wide_track}
""")
    must_fail(run([KPY, OWNERSHIP, project / "03_src/route.yaml"]),
              "unowned many-pad power", "O-PWR")


@test("route_candidate_workspace.py detects receipt artifact tampering", kind="known_bad")
def t_candidate_receipt_tamper():
    directory = tmpdir("candidate-red-")
    artifact = directory / "subject.kicad_pcb"
    artifact.write_text("changed")
    receipt = {"schema": 1, "verdict": "ACCEPTED", "checks": {},
               "artifacts": {artifact.name: {"sha256": "0" * 64,
                                              "size": artifact.stat().st_size}}}
    (directory / "receipt.json").write_text(json.dumps(receipt))
    must_fail(run([sys.executable, CANDIDATE, "verify",
                   directory / "receipt.json"]), "tampered candidate receipt",
              "artifact changed")


@test("route_experiment_store.py refuses a second accepted candidate", kind="known_bad")
def t_experiment_double_accept():
    directory = tmpdir("experiment-red-")
    artifact = directory / "candidate.kicad_pcb"
    artifact.write_text("copper")
    store = directory / "store"
    must_pass(run([sys.executable, EXPERIMENT, "record", store, "--id", "c1",
                   "--outcome", "ACCEPTED", "--parent", "r0", "--retain",
                   artifact]), "first accepted experiment")
    must_fail(run([sys.executable, EXPERIMENT, "record", store, "--id", "c2",
                   "--outcome", "ACCEPTED", "--parent", "r0", "--retain",
                   artifact]), "second accepted experiment", "already exists")


@test("pause_state.py refuses a changed checkpoint", kind="known_bad")
def t_pause_checkpoint_drift():
    project = tmpdir("pause-red-") / "board"
    (project / "01_docs").mkdir(parents=True)
    (project / "03_src").mkdir()
    checkpoint = project / "03_src/checkpoint.txt"
    checkpoint.write_text("accepted")
    must_pass(run([sys.executable, PAUSE, "record", project, "--phase", "routing",
                   "--checkpoint", "03_src/checkpoint.txt", "--blocker", "repair",
                   "--next-command", "resume"]), "record pause")
    checkpoint.write_text("changed")
    must_fail(run([sys.executable, PAUSE, "verify", project]),
              "changed pause checkpoint", "referenced file changed")


@test("first_article_check.py holds an unconfirmed exposed pad", kind="known_bad")
def t_first_article_exposed_pad():
    project = tmpdir("first-article-red-")
    (project / "03_src/rules").mkdir(parents=True)
    (project / "01_docs/journal").mkdir(parents=True)
    (project / "03_src/rules/first_article.yaml").write_text("""
stages:
  - {name: regulator-only, installed: [U2], exposed_pads: [U2]}
rails:
  - name: 5VA
    resistance: {probe: C17, min_ohm: 1000, max_ohm: 2500}
    voltage: {probe: C17, min_v: 5.0, max_v: 5.3}
    no_load_current: {probe: bench_supply, max_a: 0.03}
    supply: {probe: bench_supply, min_v: 9.5, max_v: 12.2,
             max_current_limit_a: 0.05}
""")
    record = {"stage": "regulator-only", "installed": ["U2"],
              "assembly_confirmations": {}, "measurements": {"5VA": {
                  "resistance": {"value": 1500, "unit": "ohm", "probe": "C17"},
                  "voltage": {"value": 5.17, "unit": "V", "probe": "C17"},
                  "no_load_current": {"value": 0.017, "unit": "A", "probe": "bench_supply"},
                  "supply_voltage": {"value": 10, "unit": "V", "probe": "bench_supply"},
                  "current_limit": {"value": 0.05, "unit": "A"}}}}
    (project / "01_docs/journal/first_article.json").write_text(json.dumps(record))
    must_fail(run([sys.executable, FIRST_ARTICLE, project]),
              "unconfirmed exposed pad", "FA-EP")


@test("realized_track_width_guard.py refuses sub-floor copper", kind="known_bad")
def t_realized_width_floor():
    directory = tmpdir("width-red-")
    board = directory / "board.kicad_pcb"
    code = f"""
import pcbnew
V=pcbnew.VECTOR2I_MM
b=pcbnew.CreateEmptyBoard(); net=pcbnew.NETINFO_ITEM(b,'SIG'); b.Add(net)
for ref,x in [('U1',5),('U2',15)]:
 f=pcbnew.FOOTPRINT(b); f.SetReference(ref); b.Add(f); f.SetPosition(V(x,5))
 p=pcbnew.PAD(f); p.SetNumber('1'); p.SetShape(pcbnew.PAD_SHAPE_RECT)
 p.SetSize(V(1,1)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetLayerSet(pcbnew.PAD.SMDMask())
 f.Add(p); p.SetPosition(V(x,5)); p.SetNet(net)
t=pcbnew.PCB_TRACK(b); t.SetNet(net); t.SetLayer(pcbnew.F_Cu)
t.SetWidth(pcbnew.FromMM(0.10)); t.SetStart(V(5,5)); t.SetEnd(V(15,5)); b.Add(t)
pcbnew.SaveBoard(r'{board}',b)
"""
    must_pass(run([KPY, "-c", code]), "width board fixture")
    must_fail(run([KPY, REALIZED_WIDTH, board, "--nets", "SIG",
                   "--nominal-width", "0.20", "--min-width", "0.15",
                   "--max-subnominal-length-per-net", "1.0",
                   "--max-subnominal-segments-per-net", "1"]),
              "sub-floor realized copper", "realized track width: FAIL")


if __name__ == "__main__":
    sys.exit(main())
