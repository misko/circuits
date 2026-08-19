#!/usr/bin/env python3
"""T1: connector mouth/edge geometry and hash-bound human evidence."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

import yaml
import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, check, contains, eq, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

GATE = FAB_SCRIPTS / "connector_orientation_gate.py"
sys.path.insert(0, str(FAB_SCRIPTS))
import connector_orientation_gate as orientation_gate  # noqa: E402
SOURCE_PROJECT = ROOT / "projects/usb-controlled-debug-hub-v1"
SOURCE_BOARD = SOURCE_PROJECT / "04_kicad/usb_controlled_debug_hub.kicad_pcb"


def fixture(kind="usb_b"):
    project = tmpdir("connector_orientation_") / "board"
    board_dir = project / "04_kicad"
    model_dir = project / "03_src/lib/3d"
    rules_dir = project / "03_src/rules"
    for directory in (board_dir, model_dir, rules_dir):
        directory.mkdir(parents=True, exist_ok=True)
    board = board_dir / SOURCE_BOARD.name
    shutil.copy2(SOURCE_BOARD, board)

    if kind == "usb_b":
        refs = ["J_UP"]
        model_name = "JLC_C86462_USB-B_TH_BF90.step"
        edge_rows = [{"ref": "J_UP", "edge": "x0", "min_offset_mm": 0.5}]
        orientation = {
            "authority": "TE ENG_CD_292304 Rev D4 and exact official STEP",
            "mount_side": "front",
            "footprint_access_axis_local": [0, 1, 0],
            "model_access_axis_local": [0, 1, 0],
            "model_up_axis_local": [0, 0, 1],
            "mating_plane_offset_mm": 12.45,
            "edge_offset_range_mm": [0.0, 0.4],
            "key_pad": "1",
            "model_z_offset_range_mm": [-0.01, 0.01],
        }
    else:
        refs = ["J_PORT1", "J_PORT2"]
        model_name = "KH-AF90DIP-112.step"
        edge_rows = [
            {"ref": ref, "edge": "y0", "min_offset_mm": 1.0}
            for ref in refs
        ]
        orientation = {
            "authority": "Kinghelm drawing and exact-code STEP",
            "mount_side": "front",
            "footprint_access_axis_local": [0, 1, 0],
            "model_access_axis_local": [0, 1, 0],
            "model_up_axis_local": [0, 0, 1],
            "mating_plane_offset_mm": 13.49,
            "edge_offset_range_mm": [-0.35, -0.05],
            "key_pad": "1",
            "model_z_offset_range_mm": [-0.01, 0.01],
        }

    source_model = SOURCE_PROJECT / "03_src/lib/3d" / model_name
    shutil.copy2(source_model, model_dir / model_name)
    keep = tuple(refs)
    mutate = (
        "import pcbnew,sys\n"
        "p=sys.argv[1]; b=pcbnew.LoadBoard(p); keep=set(" + repr(keep) + ")\n"
        "for fp in list(b.GetFootprints()):\n"
        "  if fp.GetReference() not in keep: b.Remove(fp)\n"
        "b.Save(p)\n"
    )
    must_pass(run([KPY, "-c", mutate, board]), "reduce exact board fixture")
    model_sha = hashlib.sha256((model_dir / model_name).read_bytes()).hexdigest()
    config = {
        "schema": 1,
        "groups": [{
            "id": kind,
            "refs": refs,
            "model_sha256": model_sha,
            "orientation": orientation,
        }],
        "orientation_exemptions": [],
    }
    (rules_dir / "model_registration.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    (project / "03_src/floorplan.yaml").write_text(
        yaml.safe_dump({"asserts": {"edge_faces": edge_rows}}, sort_keys=False),
        encoding="utf-8")
    return project, board, refs


def command(project, *extra):
    return [
        KPY, GATE, project, "--board",
        "04_kicad/usb_controlled_debug_hub.kicad_pcb",
        "--width", "800", "--height", "600", *extra,
    ]


@test("inside-camera grey-blue board strips remain measurable")
def t_inside_camera_board_strip_colour():
    image = orientation_gate.Image.new("RGB", (240, 160), (164, 164, 188))
    for y in range(78, 82):
        for x in range(30, 210):
            image.putpixel((x, y), (107, 111, 125))
    x0, x1, y = orientation_gate.side_board_span(image)
    eq((x0, x1), (30, 209), "cool reverse-camera board edge span")
    check(78 <= y <= 81, "cool reverse-camera board edge row")


@test("footprint axes use pcbnew's y-down transform at 90 and 270 degrees")
def t_footprint_axis_transform_matches_real_pad_positions():
    board = pcbnew.LoadBoard(str(SOURCE_BOARD))
    original = board.FindFootprintByReference("J_UP")
    for angle in (90.0, 270.0):
        fp = pcbnew.Cast_to_FOOTPRINT(original.Duplicate(False))
        fp.SetPosition(pcbnew.VECTOR2I(0, 0))
        fp.SetOrientationDegrees(angle)
        pad = next(item for item in fp.Pads() if str(item.GetNumber()) == "1")
        actual = (pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6)
        predicted = orientation_gate.footprint_to_board((1.25, -2.0, 0.0), fp)
        check(abs(actual[0] - predicted[0]) < 1e-6 and
              abs(actual[1] - predicted[1]) < 1e-6,
              f"{angle:g} degree axis transform matches pcbnew pad position")


@test("connector orientation pauses for a real hash-bound human decision")
def t_review_pause_and_approval():
    project, _board, refs = fixture("usb_b")
    pending = run(command(project))
    eq(pending.rc, 2, "clean machine result without human approval")
    contains(pending.out, "P-ORIENT REVIEW REQUIRED: machine 1/1 PASS",
             "explicit review pause")
    check(not (project / "08_reviews/connector_orientation.yaml").exists(),
          "machine pass did not self-approve")

    out = project / "06_build/pre_route/orientation"
    receipt = json.loads((out / "orientation_receipt.json").read_text())
    eq(receipt["verdict"], "PASS", "machine verdict")
    eq(receipt["refs"], refs, "complete connector denominator")
    eq(receipt["review_groups"][0]["refs"], refs,
       "visual representative denominator")
    for suffix in ("top", "outside", "inside"):
        image = out / "views" / f"J_UP_{suffix}.png"
        check(image.is_file() and image.stat().st_size > 1000,
              f"required {suffix} evidence exists")

    approved = must_pass(
        run(command(project, "--approve-reviewer", "regression-human")),
        "explicit synthetic human approval")
    contains(approved.out, "P-ORIENT PASS: machine 1/1, human 1/1",
             "human denominator")
    approval = yaml.safe_load(
        (project / "08_reviews/connector_orientation.yaml").read_text())
    eq(approval["subject_sha256"], receipt["subject_sha256"],
       "approval binds the semantic subject")
    eq(approval["refs"], refs, "approval binds the complete ref denominator")


@test("a reversed connector fails before human approval", kind="known_bad")
def t_reversed_board_axis_fails():
    project, board, _refs = fixture("usb_b")
    mutate = (
        "import pcbnew,sys\n"
        "p=sys.argv[1]; b=pcbnew.LoadBoard(p); f=b.FindFootprintByReference('J_UP')\n"
        "f.SetOrientationDegrees(90); b.Save(p)\n"
    )
    must_pass(run([KPY, "-c", mutate, board]), "reverse connector fixture")
    bad = must_fail(run(command(project, "--machine-only")),
                    "backwards connector",
                    "board access axis disagrees with contract")
    contains(bad.out, "P-ORIENT FAIL", "machine refusal")


@test("identical repeated connectors share views but not machine coverage")
def t_repeated_tuple_visual_compression():
    project, _board, refs = fixture("usb_a")
    result = must_pass(run(command(project, "--machine-only")),
                       "repeated USB-A orientation")
    contains(result.out, "P-ORIENT render 5/5",
             "all tuples share five fixed exact-board cameras")
    receipt = json.loads((project /
        "06_build/pre_route/orientation/orientation_receipt.json").read_text())
    eq(receipt["refs"], refs, "both physical refs remain machine graded")
    eq(len(receipt["measurements"]), 2, "two instance measurements")
    eq(len(receipt["review_groups"]), 1, "one exact visual tuple")
    eq(receipt["review_groups"][0]["refs"], refs,
       "representative lists every covered instance")


@test("canonical rebuilds run bounded orientation after model registration")
def t_template_wiring():
    for path in (
        ROOT / "skills/pcb-design/templates/03_src/rebuild_all.sh",
        ROOT / "skills/pcb-design/templates/03_src/rebuild_reuse.sh",
    ):
        text = path.read_text()
        model = text.index("model_registration_gate.py")
        orient = text.index("connector_orientation_gate.py")
        review = text.index("pre_route_review_check.py", orient)
        check(model < orient < review, f"{path.name} canonical gate order")
        contains(text[orient - 140:orient], "timeout",
                 f"{path.name} bounds the renderer")


if __name__ == "__main__":
    main()
