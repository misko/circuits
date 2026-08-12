#!/usr/bin/env bash
# Prepare an immutable, exact-subject placement-review request.
#
# This project-local adapter closes a process gap: the shared placement gate
# can reject stale human evidence, but it does not commission replacement
# evidence.  Keep this adapter data-driven and promote it to the shared
# backend before a second board copies it.
set -euo pipefail
cd "$(dirname "$0")/.."                       # -> project root

PY=/usr/bin/python3
REPO_ROOT="$(cd "$(git rev-parse --show-toplevel 2>/dev/null || echo ../../..)" && pwd)"
S="$REPO_ROOT/skills/kicad-pcb/scripts"
[ -f "$S/pre_route_review_check.py" ] || S="$HOME/.claude/skills/kicad-pcb/scripts"

readarray -t CONFIG_PATHS < <("$PY" - <<'PYEOF'
from pathlib import Path
import yaml

doc = yaml.safe_load(Path("03_src/route.yaml").read_text(encoding="utf-8-sig")) or {}
project = doc.get("project") or {}
prep = doc.get("prep") or {}
board = project.get("board")
build_dir = project.get("build_dir")
prep_out = prep.get("out")
if not all(isinstance(value, str) and value.strip()
           for value in (board, build_dir, prep_out)):
    raise SystemExit(
        "placement-review prepare: route.yaml must name project.board, "
        "project.build_dir and prep.out")
print(board)
print((Path(build_dir) / prep_out).as_posix())
PYEOF
)
BOARD="${CONFIG_PATHS[0]:-}"
PREP_R0="${CONFIG_PATHS[1]:-}"
ROUTE=03_src/route.yaml
FLOORPLAN=03_src/floorplan.yaml
PLACEMENT_DRC=06_build/drc/pre_route.json
REQUEST_ROOT=06_build/pre_route/placement_review_requests
CURRENT=06_build/pre_route/placement_review_current.json

for required in "$BOARD" "$PREP_R0" "$ROUTE" "$FLOORPLAN" "$PLACEMENT_DRC"; do
    [ -f "$required" ] || {
        echo "placement-review prepare: required exact input missing: $required" >&2
        exit 2
    }
done

# Capture the dual outcome before computing the exact subject identity. The
# authoritative, visible gate still runs immediately after this stage.
REVIEWS_CURRENT=false
if "$PY" "$S/pre_route_review_check.py" . --phase placement \
        --board "$BOARD" >/dev/null 2>&1; then
    REVIEWS_CURRENT=true
fi

# Do not spend reviewer time on a board whose promoted route cannot replay
# from the exact prepared r0.  This check is cheap, visible, and bounded.
echo "[placement-review] verify promoted-route compatibility"
timeout --foreground --kill-after=5s 60s \
    "$PY" "$S/promoted_route_check.py" "$BOARD" "$ROUTE"

SUBJECT_ID=$("$PY" - "$S" "$BOARD" "$PREP_R0" <<'PYEOF'
from pathlib import Path
import hashlib
import json
import sys

scripts = Path(sys.argv[1]).resolve()
board = Path(sys.argv[2])
prep_r0 = Path(sys.argv[3])
sys.path.insert(0, str(scripts))
from pre_route_review_check import design_rules_digest  # noqa: E402
from promoted_route_check import _track_rows, _via_rows  # noqa: E402
import pcbnew  # noqa: E402

project = Path.cwd()

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

parts = sorted((project / "02_parts").glob("*/part.yaml"))
if not parts:
    raise SystemExit("placement-review prepare: no 02_parts/*/part.yaml inputs")
parts_hash = hashlib.sha256(b"".join(
    path.relative_to(project).as_posix().encode() + b"\0" +
    path.read_bytes() + b"\0" for path in parts)).hexdigest()
rules_hash = design_rules_digest(project)
if rules_hash is None:
    raise SystemExit("placement-review prepare: adopted design-rule digest is unavailable")
prepared = pcbnew.LoadBoard(str(prep_r0))
prepared_copper = {
    "tracks": sorted(_track_rows(prepared),
                     key=lambda row: json.dumps(row, sort_keys=True)),
    "vias": sorted(_via_rows(prepared),
                   key=lambda row: json.dumps(row, sort_keys=True)),
}
prepared_semantic_hash = hashlib.sha256(json.dumps(
    prepared_copper, sort_keys=True, separators=(",", ":")
).encode()).hexdigest()
placement_drc = json.loads(
    (project / "06_build/drc/pre_route.json").read_text(encoding="utf-8"))
placement_drc.pop("date", None)
placement_drc_semantic_hash = hashlib.sha256(json.dumps(
    placement_drc, sort_keys=True, separators=(",", ":")
).encode()).hexdigest()
identity = {
    "schema": 1,
    "board_sha256": digest(board),
    "prepared_r0_semantic_sha256": prepared_semantic_hash,
    "placement_drc_semantic_sha256": placement_drc_semantic_hash,
    "parts_sha256": parts_hash,
    "design_rules_sha256": rules_hash,
}
payload = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
print(hashlib.sha256(payload).hexdigest())
PYEOF
)
[ "${#SUBJECT_ID}" -eq 64 ] || {
    echo "placement-review prepare: invalid subject identity: $SUBJECT_ID" >&2
    exit 2
}

REQUEST_DIR="$REQUEST_ROOT/$SUBJECT_ID"
mkdir -p "$REQUEST_ROOT"

write_current_pointer() {
    local status="${1:-INCOMPLETE}"
    "$PY" - "$SUBJECT_ID" "$REQUEST_DIR" "$CURRENT" "$status" <<'PYEOF'
from pathlib import Path
import json
import os
import sys

subject_id, request_dir, output, status = sys.argv[1:]
target = Path(output)
target.parent.mkdir(parents=True, exist_ok=True)
value = {
    "schema": 1,
    "status": status,
    "subject_id": subject_id,
}
if status == "INCOMPLETE":
    value.update({
        "commission": f"{request_dir}/commission.json",
        "a_render_request": f"{request_dir}/a_render.md",
        "top_render": f"{request_dir}/top.png",
        "isometric_render": f"{request_dir}/iso.png",
    })
elif status != "ALREADY_ADMISSIBLE":
    raise SystemExit(f"placement-review prepare: invalid pointer status {status}")
temporary = target.with_name(f".{target.name}.tmp.{os.getpid()}")
temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
os.replace(temporary, target)
PYEOF
}

if [ "$REVIEWS_CURRENT" = true ]; then
    write_current_pointer ALREADY_ADMISSIBLE
    echo "[placement-review] exact human evidence is already current; wrote truthful boundary pointer and preserved every witness"
    exit 0
fi

verify_request() {
    "$PY" - "$SUBJECT_ID" "$REQUEST_DIR" <<'PYEOF'
from pathlib import Path
import hashlib
import json
import sys

subject_id = sys.argv[1]
request = Path(sys.argv[2])
manifest_path = request / "commission.json"
if not manifest_path.is_file():
    raise SystemExit(f"placement-review prepare: immutable request is incomplete: {manifest_path}")
doc = json.loads(manifest_path.read_text(encoding="utf-8"))
if doc.get("subject_id") != subject_id or doc.get("status") != "INCOMPLETE":
    raise SystemExit("placement-review prepare: immutable request identity/status mismatch")
for name, key in (("top.png", "top_render_sha256"),
                  ("iso.png", "isometric_render_sha256"),
                  ("a_render.md", "a_render_request_sha256")):
    path = request / name
    if not path.is_file():
        raise SystemExit(f"placement-review prepare: immutable request is incomplete: {path}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != doc.get(key):
        raise SystemExit(f"placement-review prepare: immutable request was modified: {path}")
PYEOF
}

if [ -d "$REQUEST_DIR" ]; then
    # The request is content-addressed and immutable.  Reuse it only when all
    # commissioned bytes remain complete and self-consistent; never repair it
    # in place or overwrite a prior reviewer subject.
    verify_request
    write_current_pointer
    echo "[placement-review] reused immutable request $REQUEST_DIR"
    echo "[placement-review] deliberate pause: complete the commissioned human reviews, then rerun"
    exit 0
fi

TMP_DIR=$(mktemp -d "$REQUEST_ROOT/.tmp.${SUBJECT_ID}.XXXXXX")
cleanup() {
    case "${TMP_DIR:-}" in
        "$REQUEST_ROOT"/.tmp.*) rm -rf -- "$TMP_DIR" ;;
    esac
}
trap cleanup EXIT

echo "[placement-review] render exact track-free board (top; deadline 90 s)"
TOP_START=$(date +%s)
timeout --foreground --kill-after=5s 90s \
    kicad-cli pcb render --side top --quality high --background opaque \
    --floor -w 2400 -h 1700 -o "$TMP_DIR/top.png" "$BOARD"
TOP_END=$(date +%s)
[ -s "$TMP_DIR/top.png" ] || {
    echo "placement-review prepare: top render is absent/empty" >&2
    exit 1
}

echo "[placement-review] render exact track-free board (isometric; deadline 90 s)"
ISO_START=$(date +%s)
timeout --foreground --kill-after=5s 90s \
    kicad-cli pcb render --side top --quality high --background opaque \
    --floor --perspective --rotate 35,0,-35 -w 2400 -h 1700 \
    -o "$TMP_DIR/iso.png" "$BOARD"
ISO_END=$(date +%s)
[ -s "$TMP_DIR/iso.png" ] || {
    echo "placement-review prepare: isometric render is absent/empty" >&2
    exit 1
}

"$PY" - "$S" "$SUBJECT_ID" "$BOARD" "$PREP_R0" "$TMP_DIR" \
    "$REQUEST_DIR" "$((TOP_END - TOP_START))" "$((ISO_END - ISO_START))" <<'PYEOF'
from pathlib import Path
import hashlib
import json
import subprocess
import sys

scripts, subject_id, board_arg, prep_arg, temp_arg, request_arg, top_s, iso_s = sys.argv[1:]
project = Path.cwd()
scripts_path = Path(scripts).resolve()
board = Path(board_arg)
prep_r0 = Path(prep_arg)
temp = Path(temp_arg)
request = Path(request_arg)
sys.path.insert(0, str(scripts_path))
from pre_route_review_check import config, design_rules_digest  # noqa: E402
from promoted_route_check import _track_rows, _via_rows  # noqa: E402
import pcbnew  # noqa: E402

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

parts = sorted((project / "02_parts").glob("*/part.yaml"))
parts_hash = hashlib.sha256(b"".join(
    path.relative_to(project).as_posix().encode() + b"\0" +
    path.read_bytes() + b"\0" for path in parts)).hexdigest()
rules_hash = design_rules_digest(project)
top_hash = digest(temp / "top.png")
iso_hash = digest(temp / "iso.png")
route_hash = digest(project / "03_src/route.yaml")
board_hash = digest(board)
prep_hash = digest(prep_r0)
prepared = pcbnew.LoadBoard(str(prep_r0))
prepared_copper = {
    "tracks": sorted(_track_rows(prepared),
                     key=lambda row: json.dumps(row, sort_keys=True)),
    "vias": sorted(_via_rows(prepared),
                   key=lambda row: json.dumps(row, sort_keys=True)),
}
prep_semantic_hash = hashlib.sha256(json.dumps(
    prepared_copper, sort_keys=True, separators=(",", ":")
).encode()).hexdigest()
placement_drc_path = project / "06_build/drc/pre_route.json"
placement_drc = json.loads(placement_drc_path.read_text(encoding="utf-8"))
placement_drc.pop("date", None)
placement_drc_semantic_hash = hashlib.sha256(json.dumps(
    placement_drc, sort_keys=True, separators=(",", ":")
).encode()).hexdigest()
reviews = config(project)

a_render = "\n".join((
    "a-render_verdict: INCOMPLETE",
    f"subject_id: {subject_id}",
    f"board_sha256: {board_hash}",
    f"prep_r0_semantic_sha256: {prep_semantic_hash}",
    f"route_yaml_sha256: {route_hash}",
    f"design_rules_sha256: {rules_hash}",
    f"top_render_sha256: {top_hash}",
    f"iso_render_sha256: {iso_hash}",
    "camera: KiCad 2400x1700 top orthographic plus fixed 35/0/-35 degree isometric corroboration",
    "",
    "# Deliberate placement-review pause",
    "",
    "This file is an automatically prepared request, not a human acceptance.",
    "Inspect both exact-subject renders and the native KiCad board. If the",
    "placement is acceptable, a human reviewer must write the configured",
    f"canonical A-RENDER report at `{reviews.get('a_render', '<unset>')}`.",
    "The producer never edits that report and never upgrades this request.",
    "",
))
(temp / "a_render.md").write_text(a_render, encoding="utf-8")

try:
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, check=True,
        text=True, capture_output=True, timeout=5).stdout.strip()
except (OSError, subprocess.SubprocessError):
    source_commit = "UNAVAILABLE"
try:
    renderer = subprocess.run(
        ["kicad-cli", "--version"], check=True, text=True,
        capture_output=True, timeout=5).stdout.strip()
except (OSError, subprocess.SubprocessError):
    renderer = "UNAVAILABLE"

manifest = {
    "schema": 1,
    "project": "usb-hub-3s-v4",
    "review_stage": "placement",
    "status": "INCOMPLETE",
    "subject_id": subject_id,
    "source_commit": source_commit,
    "board": board.as_posix(),
    "board_sha256": board_hash,
    "prepared_r0": prep_r0.as_posix(),
    "prepared_r0_sha256": prep_hash,
    "prepared_r0_semantic_sha256": prep_semantic_hash,
    "route_yaml_sha256": route_hash,
    "floorplan_sha256": digest(project / "03_src/floorplan.yaml"),
    "placement_drc_sha256": digest(placement_drc_path),
    "placement_drc_semantic_sha256": placement_drc_semantic_hash,
    "parts_sha256": parts_hash,
    "design_rules_sha256": rules_hash,
    "renderer": renderer,
    "top_render": f"{request.as_posix()}/top.png",
    "top_render_sha256": top_hash,
    "top_render_seconds": int(top_s),
    "isometric_render": f"{request.as_posix()}/iso.png",
    "isometric_render_sha256": iso_hash,
    "isometric_render_seconds": int(iso_s),
    "a_render_request": f"{request.as_posix()}/a_render.md",
    "a_render_request_sha256": digest(temp / "a_render.md"),
    "canonical_human_witnesses": {
        kind: reviews.get(kind) for kind in ("pin", "layout", "render", "a_render")
    },
    "required_human_actions": [
        "Review physical pin identity against the exact board, parts, and rules",
        "Review placement/layout against the exact board and rules",
        "Review the exact top and isometric renders",
        "Write fresh hash-bound canonical witnesses; do not edit this request",
        "Rerun either driver; the existing placement gate remains authoritative",
    ],
    "pause_reason": "fresh human placement evidence is missing or stale",
}
(temp / "commission.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PYEOF

# Same-filesystem rename publishes a complete request at once.  A concurrent
# publisher of the same exact subject wins without either process overwriting
# the other's immutable directory.
if ! mv -T "$TMP_DIR" "$REQUEST_DIR" 2>/dev/null; then
    [ -d "$REQUEST_DIR" ] || {
        echo "placement-review prepare: could not publish $REQUEST_DIR" >&2
        exit 1
    }
    verify_request
    cleanup
fi
TMP_DIR=""
trap - EXIT
write_current_pointer

echo "[placement-review] prepared immutable request $REQUEST_DIR"
echo "[placement-review] top render: $((TOP_END - TOP_START)) s; isometric render: $((ISO_END - ISO_START)) s"
echo "[placement-review] deliberate pause: complete the commissioned human reviews, then rerun"
