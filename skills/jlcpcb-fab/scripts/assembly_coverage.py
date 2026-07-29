#!/usr/bin/env python3
"""A-POP — the population set is DECLARED, not emergent.

    assembly_coverage.py TARGET [--assembly PATH] [--json OUT]

`TARGET` is a sealed release directory (`07_releases/<ver>-<date>/`, read
READ-ONLY) or a project directory (`04_kicad/` + `06_build/fab/`).

WHY THIS EXISTS. "Which parts does JLC actually place?" had no machine home.
It was an emergent property of three artifacts that nothing compared:

  * the BOARD's `exclude_from_pos_files` attributes,
  * `fab/cpl.csv` (what the machine is told to place),
  * and a PROSE `not_assembled:` sentence in the release MANIFEST.

Measured on sealed bytes (2026-07-25):

  cooksense v1.1  — 13 CPL placement rows whose BOM line carries a BLANK
    LCSC (J_TC + the twelve K_* Standex reed relays). JLC was told to place
    12 parts the MANIFEST declares not_assembled, and to source a 13th
    (J_TC) declared nowhere at all. Every gate green.
  cooksense interposer v1.0 — a blank-LCSC BOM row whose refs are ALSO on
    the CPL, no `not_assembled:` line anywhere, and a disposition that is
    PROSE telling a human to delete rows before uploading.
  crow-recorder-central-v2 v1.3 — MANIFEST `not_assembled: ... U1 (XU316
    consign)` while U1 sits ON the CPL. Consigned means YOU ship the part
    and JLC PLACES it: a sourcing class, not a population class.

INDEPENDENCE (canon M1). The population delta is computed from the BOARD's
own text and the CPL bytes — never from `export_jlc_package.py`'s filter
logic, which is what produced the CPL in the first place. `read_footprints()`
below parses the `.kicad_pcb` s-expression directly, so this checker needs no
pcbnew and shares no oracle with the exporter. (Cross-checked against pcbnew
on a real sealed board: 195/195 footprints agree on refdes, footprint name,
orientation, layer, pad count and attribute flags — 0 mismatches. That
agreement is asserted as a test, so the parser cannot rot into a second,
quieter bug.)

FAILS
  NO-ASSEMBLY-DECL       no `03_src/rules/assembly.yaml` while the board has
                         unpopulated parts — "not assembled" with no decision
                         record is a free outcome, which is the whole defect.
  UNDECLARED-UNPOPULATED a board footprint absent from the CPL that no
                         `not_assembled:` entry and no declared
                         `exempt_prefixes:` accounts for.
  DECLARED-BUT-PLACED    a ref declared not-assembled that is still ON the
                         CPL — the declaration and the machine instruction
                         disagree, and the machine wins.
  DECLARED-NOT-EXCLUDED  a declared-unpopulated ref whose board footprint
                         does NOT carry `exclude_from_pos_files` — it will
                         come back onto the CPL at the next export.
  POS-ATTR-VS-CPL        the BOARD says exclude-from-pos but the shipped CPL
                         places it anyway: the CPL predates the board.
  UNCODED-ON-CPL         a BOM row with a BLANK LCSC whose refs are on the
                         CPL (the cooksense 13) — JLC cannot source it.
  CPL-NO-BOM-ROW         a placed designator with no BOM line at all.
  BAD-REASON / NO-EVIDENCE / CONSIGN-AS-UNPOPULATED
                         schema failures in `assembly.yaml` itself.
  MANIFEST-UNDECLARED    a release with unpopulated parts and no MANIFEST
                         `not_assembled:` line.
  MANIFEST-DRIFT         the MANIFEST's `not_assembled:` set differs from
                         `assembly.yaml`'s — it is GENERATED from that file,
                         never hand-written in two places.

Exit 0 = the population set is fully declared; 1 = at least one FAIL.
Plain python3 (NO pcbnew).
"""
import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:                                   # pragma: no cover
    yaml = None

# `reason:` is a CLOSED vocabulary (03_src/rules/assembly.yaml). If none fits,
# the honest answer is that the part must be re-specified to a placeable one.
REASONS = {"not_in_catalog", "consign", "user_supplied", "dnp_by_design",
           "mechanical", "test_point", "process_incompatible"}

# `process_incompatible` (added 2026-07-25) is the reason the vocabulary was
# MISSING and boards were therefore mis-declaring: a part that IS in the
# catalog, IS stocked, and IS wanted on the board, but that the ORDERED
# process cannot place — the classic case being a true THT part on a
# `sides: [top]` SMT-only order, whose pads carry no F.Paste so it cannot be
# intrusive-reflowed. crow-recorder-central-v2 v1.4 shipped exactly that (J1,
# a stocked C381116 barrel jack, the board's only power inlet) and the nearest
# available reason would have been `not_in_catalog` — which is FALSE. A closed
# vocabulary with no true option forces a lie into the decision record.

# A-POS tolerance. 0.05mm is ~1/20 of the smallest land this fleet places
# (0402, 0.5mm) and ~8x the largest disagreement seen between the two
# independent datum measurements, so it separates "different convention" from
# "measurement noise" without flagging rounding in the CPL's 4-decimal field.
DATUM_TOL_MM = 0.05


# ----------------------------------------------------------------- board
def _match_paren(text, i):
    """Index of the ')' closing the '(' at index i (string-aware)."""
    depth, n, in_str = 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n - 1


def _children(text, start):
    """(head, span_text) for each DIRECT child list of the node opening at
    `start`. Nested lists are skipped wholesale, so a pad's `(at ...)` can
    never masquerade as the footprint's own `(at ...)`."""
    i, n, in_str = start + 1, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "(":
            j = _match_paren(text, i)
            m = re.match(r"\(\s*([A-Za-z_0-9]+)", text[i:j + 1])
            yield (m.group(1) if m else ""), text[i:j + 1]
            i = j + 1
            continue
        if c == ")":
            return
        i += 1


def _atoms(span):
    """Tokens of a flat s-expr `(head a "b c" 3)` -> ['head','a','b c','3']."""
    return [a or b for a, b in
            re.findall(r'"((?:[^"\\]|\\.)*)"|([^\s()"]+)', span[1:-1])]


def read_footprints(path):
    """Every footprint on a `.kicad_pcb`, parsed from the FILE TEXT.

    -> [{ref, value, fp, layer, rot, pads, attrs, at, datum, drilled,
    drilled_pasted}] where `pads` is the set of pad NUMBERS and `attrs` the
    `(attr ...)` flag words.

    No pcbnew: this is the INDEPENDENT reading of the board (canon M1). The
    exporter reads the same facts through the pcbnew API, so a checker that
    imported pcbnew would be re-asking the exporter's own oracle.
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    out = []
    for m in re.finditer(r"\(footprint\s", text):
        i = m.start()
        end = _match_paren(text, i)
        head = _atoms(text[i:min(i + 400, end + 1)] + ")")
        fpid = head[1] if len(head) > 1 else ""
        rec = {"ref": "", "value": "", "fp": fpid.split(":")[-1],
               "layer": "", "rot": 0.0, "pads": set(), "attrs": set(),
               "at": (0.0, 0.0), "datum": None,
               "drilled": 0, "drilled_pasted": 0}
        pad_xy = []
        for kind, span in _children(text, i):
            if kind == "at":
                a = _atoms(span)
                rec["at"] = (float(a[1]), float(a[2])) if len(a) > 2 else (0.0, 0.0)
                rec["rot"] = float(a[3]) if len(a) > 3 else 0.0
            elif kind == "layer" and not rec["layer"]:
                a = _atoms(span)
                rec["layer"] = a[1] if len(a) > 1 else ""
            elif kind == "attr":
                rec["attrs"] = set(_atoms(span)[1:])
            elif kind == "property":
                a = _atoms(span)
                if len(a) > 2 and a[1] == "Reference":
                    rec["ref"] = a[2]
                elif len(a) > 2 and a[1] == "Value":
                    rec["value"] = a[2]
            elif kind == "pad":
                a = _atoms(span)
                if len(a) > 1 and a[1]:
                    rec["pads"].add(a[1])
                ptype = a[2] if len(a) > 2 else ""
                lay, at, drill = None, None, None
                for k2, s2 in _children(span, 0):
                    if k2 == "at" and at is None:
                        at = _atoms(s2)
                    elif k2 == "layers":
                        lay = _atoms(s2)[1:]
                    elif k2 == "drill":
                        drill = _atoms(s2)[1:]
                on_cu = bool(lay) and any(
                    L.endswith(".Cu") or L == "*.Cu" for L in lay)
                if on_cu and at and len(at) > 2:
                    pad_xy.append((float(at[1]), float(at[2])))
                if drill and ptype != "np_thru_hole":
                    rec["drilled"] += 1
                    if lay and any(L in ("F.Paste", "B.Paste", "*.Paste")
                                   for L in lay):
                        rec["drilled_pasted"] += 1
        if pad_xy:
            rec["datum"] = _pad_array_centre(pad_xy, rec["at"], rec["rot"])
        if rec["ref"]:
            out.append(rec)
    return out


def _pad_array_centre(pad_xy, anchor, rot_deg):
    """JLC's placement datum in BOARD coords: the centre of the bounding box
    of the PAD CENTRES, rotated out of the footprint's local frame.

    `pad_xy` are pad `(at x y)` values, which KiCad stores in the footprint's
    LOCAL (unrotated) frame. Board Y is DOWN, and a footprint rotated by +A
    rotates its stored local geometry by -A in that frame — hence the sign
    pattern below. Verified against pcbnew's own already-global
    `pad.GetPosition()` on a sealed 203-footprint board: max disagreement
    0.0000 um. That agreement is what lets this checker stay pcbnew-free
    (canon M1) without being a second, quieter implementation.
    """
    mx = (min(x for x, _ in pad_xy) + max(x for x, _ in pad_xy)) / 2
    my = (min(y for _, y in pad_xy) + max(y for _, y in pad_xy)) / 2
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)
    return (anchor[0] + mx * ca + my * sa, anchor[1] - mx * sa + my * ca)


# ------------------------------------------------------------- artifacts
def read_cpl(path):
    """[(designator, rotation_deg_or_None, layer)] from a JLC CPL."""
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            ref = (r.get("Designator") or "").strip()
            if not ref:
                continue
            try:
                rot = float((r.get("Rotation") or "0").strip())
            except ValueError:
                rot = None
            rows.append((ref, rot, (r.get("Layer") or "").strip()))
    return rows


def read_cpl_xy(path):
    """{designator: (mid_x_mm, mid_y_mm)} from a JLC CPL.

    JLC's Mid Y is the NEGATED KiCad board Y (the CPL is Y-up, the board is
    Y-down), so the comparison in _check_datum negates it back."""
    out = {}
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            ref = (r.get("Designator") or "").strip()
            if not ref:
                continue
            try:
                out[ref] = (float((r.get("Mid X") or "").strip()),
                            float((r.get("Mid Y") or "").strip()))
            except ValueError:
                out[ref] = None
    return out


def read_bom_rows(path):
    """[(lcsc, [refs])] — BOM LINES, so a blank-code line is one finding."""
    out = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            refs = [d.strip() for d in (r.get("Designator") or "").split(",")
                    if d.strip()]
            if refs:
                out.append(((r.get("LCSC") or "").strip(), refs))
    return out


# ------------------------------------------------------------- discovery
def discover(target):
    """(board, cpl, bom, project_root) for a release dir or a project dir.
    Sealed releases are opened READ-ONLY."""
    t = Path(target).resolve()
    board = cpl = bom = None
    if (t / "fab").is_dir() and (t / "source").is_dir():          # release
        board = next(iter(sorted((t / "source").glob("*.kicad_pcb"))), None)
        for name in ("cpl.csv", "cpl_jlc.csv"):
            if (t / "fab" / name).is_file():
                cpl = t / "fab" / name
                break
        for name in ("bom.csv", "bom_jlc.csv"):
            if (t / "fab" / name).is_file():
                bom = t / "fab" / name
                break
        root = t.parent.parent                       # projects/<board>/
    else:                                                          # project
        board = next(iter(sorted((t / "04_kicad").glob("*.kicad_pcb"))), None)
        fab = t / "06_build" / "fab"
        for name in ("cpl_jlc.csv", "cpl.csv"):
            if (fab / name).is_file():
                cpl = fab / name
                break
        for name in ("bom_jlc.csv", "bom.csv"):
            if (fab / name).is_file():
                bom = fab / name
                break
        root = t
    return board, cpl, bom, root


def load_assembly(path):
    if not path or not Path(path).is_file() or not yaml:
        return {}
    return yaml.safe_load(Path(path).read_text(encoding="utf-8-sig")) or {}


def manifest_line(asm):
    """The MANIFEST `not_assembled:` line, GENERATED from assembly.yaml.

    REFDES ONLY, comma-separated, sorted naturally — no prose, no
    parentheticals, no explanation. The explanation belongs in
    assembly.yaml's `evidence:`/`disposition:`, which is where a reader can
    act on it; a MANIFEST line exists to be COMPARED, and prose cannot be.

    Measured on crow-mic-pod-v2 v1.0: the hand-written line yielded 16
    whitespace tokens of which 13 were not refdes on the board ('BOM',
    'HAND-SOLDER', 'NOW', 'ORDER_README', 'POPULATED'), so A-POP could only
    report it ungradeable. Two homes for one fact is how they drift; this
    function makes the MANIFEST a projection of the declaration."""
    refs = [str(r) for e in (asm.get("not_assembled") or [])
            for r in (e.get("refs") or [])]

    def key(r):
        m = re.match(r"^([A-Za-z_]+)(\d*)$", r)
        return (m.group(1), int(m.group(2) or -1)) if m else (r, -1)

    return "not_assembled: " + ", ".join(sorted(set(refs), key=key))


_RANGE = re.compile(r"^([A-Za-z_][A-Za-z_]*?)(\d+)(?:\.\.|-)(?:[A-Za-z_]*)(\d+)$")


def expand_refs(text):
    """Refdes tokens out of a MANIFEST prose line, expanding the two range
    shapes the fleet actually writes: `K_U1..6` and `J3-J10`."""
    refs = set()
    for tok in re.findall(r"[A-Za-z_][A-Za-z_0-9]*(?:(?:\.\.|-)[A-Za-z_0-9]+)?",
                          text):
        m = _RANGE.match(tok)
        if m:
            pre, a, b = m.group(1), int(m.group(2)), int(m.group(3))
            if b >= a and b - a < 200:
                refs |= {f"{pre}{i}" for i in range(a, b + 1)}
                continue
        refs.add(tok)
    return refs


def manifest_not_assembled(path):
    """(tokens, raw_value) from a release MANIFEST `not_assembled:` line, or
    (None, '') when the MANIFEST states nothing — absence is a DIFFERENT
    finding than drift.

    Continuation lines are consumed: the fleet wraps this value across
    indented lines (crow-recorder-central-v2 v1.3 puts `JP_INJ + J_DBG` on
    the second line), and reading only the first line silently under-reads
    the declaration — which would then surface as a bogus MANIFEST-DRIFT."""
    if not path or not Path(path).is_file():
        return None, ""
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    for i, line in enumerate(lines):
        if not re.match(r"\s*not_assembled\s*:", line):
            continue
        body = line.split(":", 1)[1]
        for cont in lines[i + 1:]:
            # an indented line that does not start a new `key:` continues it
            if not cont[:1].isspace() or not cont.strip():
                break
            if re.match(r"\s*[A-Za-z_][\w ]*:", cont):
                break
            body += " " + cont
        raw = body.strip()
        # strip parenthetical prose ("(12x Standex DIP05-1A72-12L")
        return expand_refs(re.sub(r"\([^)]*\)?", " ", body)), raw
    return None, ""


# ------------------------------------------------------------------ gate
def check_datum(fps, cpl_xy, tol=DATUM_TOL_MM):
    """A-POS — every CPL row sits on JLC's PLACEMENT DATUM, not KiCad's anchor.

    JLC places a part so its own origin lands on Mid X/Y, and that origin is
    the centre of the bounding box of the PAD CENTRES (measured 227/228 on
    JLC-native models across six boards; see export_jlc_package.placement_datum
    for the full measurement and the two refuted alternatives).

    KiCad's footprint ANCHOR is an authoring convenience with no fab meaning.
    The two coincide for most parts, which is exactly why emitting the anchor
    survived the fleet's entire history undetected — and why the failures are
    concentrated in CONNECTORS, where the anchor is conventionally put on pin
    1 or a mounting feature: on this fleet the anchor differs from the datum
    on up to 24.16mm, and crow-recorder-central-v2 v1.4 shipped its only USB-C
    1.3025mm off, against 1.150mm-long contacts -> 0.000mm pad overlap, with
    four shell posts that miss their holes. That board passed DRC 0/0/0,
    schematic parity 0, A-POP, A-ROT and two red-team lenses: nothing in the
    fleet compared a CPL COORDINATE to anything at all.

    This is a PURE-BYTES check with no network and no JLC dependency: board
    text on one side, shipped CPL bytes on the other.
    """
    fails, worst = [], []
    by_ref = {f["ref"]: f for f in fps}
    for ref, xy in sorted(cpl_xy.items()):
        f = by_ref.get(ref)
        if f is None or f.get("datum") is None:
            continue
        if xy is None:
            fails.append(
                f"  CPL-DATUM-UNREADABLE: {ref} has a non-numeric Mid X/Y — "
                f"the placement coordinate cannot be graded")
            continue
        dx = xy[0] - f["datum"][0]
        dy = xy[1] - (-f["datum"][1])          # CPL is Y-up, the board Y-down
        d = math.hypot(dx, dy)
        worst.append((d, ref))
        if d > tol:
            ax, ay = f["at"]
            d_anchor = math.hypot(xy[0] - ax, xy[1] - (-ay))
            why = (" — this is the FOOTPRINT ANCHOR, not the pad-array centre"
                   if d_anchor <= tol else "")
            fails.append(
                f"  CPL-DATUM-OFF: {ref} ({f['fp'][:38]}) Mid X/Y "
                f"({xy[0]:.4f}, {xy[1]:.4f}) is {d:.4f}mm from its pad-array "
                f"centre ({f['datum'][0]:.4f}, {-f['datum'][1]:.4f}){why}. "
                f"JLC places the part THERE, so every pad is off by {d:.4f}mm")
    worst.sort(reverse=True)
    return fails, worst


def check_smt_placeable(fps, cpl_refs, asm):
    """A-POS — every CPL ref is placeable by the process actually ORDERED.

    A part with plated DRILLED pads and NO paste on any of them cannot be
    reflowed: there is no solder in the barrel and none on the land. On an
    order declaring `service: standard` / `sides: [top]` (SMT only, no
    selective-solder or wave line bought), such a ref on the CPL is an
    instruction the assembler cannot execute — they re-quote with an
    unbudgeted hand-solder line, or they silently drop the part.

    crow-recorder-central-v2 v1.4 shipped J1 — a true THT barrel jack, and
    the board's ONLY power inlet — on a top-side-SMT-only CPL, while its own
    assembly.yaml asserted in writing that "the only other THT parts are
    already off the CPL". Nothing compared the sentence to the bytes.

    Pin-in-paste (intrusive reflow) is CORRECTLY exempt: J2 on that same
    board has 4 drilled shell posts that all carry F.Paste, so paste is
    printed into the barrels and it reflows with everything else. The
    discriminator is paste coverage, never the `through_hole` attribute —
    which is why this check reads pad layers rather than `(attr through_hole)`.

    THE THROUGH-HOLE PROCESS, WHEN IT IS ACTUALLY BOUGHT (2026-07-26).
    Until now this check could only be satisfied by taking the part OFF the CPL,
    which is wrong for a board that PAID for through-hole assembly: leaving J1-J4
    on the CPL is the entire point of buying the line. `service:` was read but
    never decided on — it was interpolated into the message and otherwise ignored —
    so usb-hub-3s-v3, whose `service:` names "THROUGH-HOLE assembly (4 refdes / 22
    plated holes)", still failed on all five connectors. Its own assembly.yaml had
    already recorded the gap in writing ("this schema has no dedicated
    through_hole: key ... raised as a skill/template change, PCBA-9").

    The exemption is now a DECLARATION, not a string match on prose:

        through_hole:
          process: "JLCPCB through-hole assembly (selective/wave), ordered"
          refs: [J1, J2, J3, J4, J5]
          evidence: "<dated measurement: hole census + what was ordered>"

    All three keys are REQUIRED and a ref must be NAMED. Silence stays a FAIL,
    an empty `refs` exempts nothing, and a ref not on the list is still caught —
    so the crow-recorder-central-v2 v1.4 case (a THT barrel jack on a top-side-SMT
    CPL, with assembly.yaml asserting in prose that THT parts were off the CPL)
    still fails exactly as it did. Prose cannot buy a process; a declaration with
    evidence can, and it is checkable.
    """
    fails = []
    by_ref = {f["ref"]: f for f in fps}
    sides = [str(s) for s in (asm.get("sides") or [])]
    service = str(asm.get("service") or "")
    th = asm.get("through_hole") or {}
    th_proc = str(th.get("process") or "").strip()
    th_ev = str(th.get("evidence") or "").strip()
    th_refs = {str(r) for r in (th.get("refs") or [])}
    th_ok = bool(th_proc and th_ev and th_refs)
    if th_refs and not (th_proc and th_ev):
        fails.append(
            "  THT-DECL-INCOMPLETE: assembly.yaml `through_hole:` names "
            f"{sorted(th_refs)} but is missing "
            + " and ".join(k for k, v in (("process", th_proc),
                                          ("evidence", th_ev)) if not v)
            + " — a bought process is a purchase with evidence, not an "
              "assertion; without both keys the declaration exempts nothing")
    for ref in sorted(cpl_refs):
        f = by_ref.get(ref)
        if f is None or not f["drilled"]:
            continue
        if f["drilled_pasted"]:
            continue                      # pin-in-paste: reflows normally
        if th_ok and ref in th_refs:
            continue                      # the THT line was BOUGHT for this ref
        fails.append(
            f"  CPL-NOT-SMT-PLACEABLE: {ref} ({f['fp'][:38]}) has "
            f"{f['drilled']} plated DRILLED pad(s) and F.Paste on NONE of "
            f"them, yet it is on the CPL of a service={service or '?'} "
            f"sides={sides or '?'} order — no reflow process can solder it. "
            f"Either declare the bought process in assembly.yaml "
            f"`through_hole:` {{process, refs, evidence}} naming this ref, or "
            f"declare it not_assembled (reason: process_incompatible) and "
            f"hand-solder it")
    return fails


def check(fps, cpl_rows, bom_rows, asm, manifest_refs, have_assembly,
          cpl_xy=None):
    """-> (fails, notes, summary). Pure; unit-testable without files."""
    fails, notes = [], []
    by_ref = {f["ref"]: f for f in fps}
    board_refs = set(by_ref)
    cpl_refs = {r[0] for r in cpl_rows}
    codes = {}
    for code, refs in bom_rows:
        for r in refs:
            codes[r] = code

    exempt = [str(p) for p in (asm.get("exempt_prefixes") or [])]
    declared, entry_of = set(), {}
    for e in (asm.get("not_assembled") or []):
        refs = [str(r) for r in (e.get("refs") or [])]
        declared |= set(refs)
        for r in refs:
            entry_of[r] = e
        if str(e.get("reason") or "") not in REASONS:
            fails.append(
                f"  BAD-REASON: not_assembled entry {refs[:4]} has reason="
                f"{e.get('reason')!r}, outside the closed vocabulary "
                f"{sorted(REASONS)} — if none fits, the part must be "
                f"re-specified to a placeable one")
        elif e.get("reason") == "consign":
            fails.append(
                f"  CONSIGN-AS-UNPOPULATED: {refs[:4]} is listed under "
                f"not_assembled with reason=consign, but a CONSIGNED part is "
                f"POPULATED — you ship it, JLC PLACES it. It belongs in "
                f"`consigned:` and stays ON the CPL (crow-recorder-central-v2 "
                f"v1.3 declared its placed U1 'not_assembled' this way)")
        if len(str(e.get("evidence") or "")) < 20:
            fails.append(
                f"  NO-EVIDENCE: not_assembled entry {refs[:4]} carries no "
                f"dated `evidence:` measurement — 'hand-solder' is a sourcing "
                f"wall you PROVE you hit (the catalog query and its result), "
                f"never a style (canon M4)")
        if not str(e.get("disposition") or "").strip():
            fails.append(
                f"  NO-EVIDENCE: not_assembled entry {refs[:4]} carries no "
                f"`disposition:` — what happens to the unplaced part is part "
                f"of the decision record")
    consigned = {str(r) for e in (asm.get("consigned") or [])
                 for r in (e.get("refs") or [])}
    both = sorted(declared & consigned)
    if both:
        fails.append(
            f"  CONSIGN-AS-UNPOPULATED: {both} appear in BOTH `consigned:` "
            f"and `not_assembled:` — consigned parts are PLACED; a ref cannot "
            f"be both populated and not")

    # ---- the core set identity: {board} - {CPL} == declared (mod exempt)
    unpopulated = sorted(board_refs - cpl_refs)
    unexplained = sorted(
        r for r in unpopulated
        if r not in declared
        and not any(r.startswith(p) for p in exempt))
    if unpopulated and not have_assembly:
        fails.append(
            f"  NO-ASSEMBLY-DECL: {len(unpopulated)} board footprint(s) are "
            f"absent from the CPL and there is no 03_src/rules/assembly.yaml "
            f"declaring who is placed and why not — an unpopulated part is a "
            f"DEFECT WITH A DECISION RECORD, never a free outcome")
    if unexplained:
        fails.append(
            f"  UNDECLARED-UNPOPULATED: {len(unexplained)} board footprint(s) "
            f"absent from the CPL with no assembly.yaml entry and no declared "
            f"exempt prefix: {', '.join(unexplained[:24])}"
            + (" ..." if len(unexplained) > 24 else ""))
    placed_but_declared = sorted(declared & cpl_refs)
    if placed_but_declared:
        fails.append(
            f"  DECLARED-BUT-PLACED: {len(placed_but_declared)} ref(s) are "
            f"declared not_assembled yet appear ON the CPL — JLC is being "
            f"told to place them: {', '.join(placed_but_declared[:24])}")
    # An evidence-backed DEFER for the board attribute, exactly parallel to
    # A-STOCK's `sourcing_plan:`. It exists because the attribute lives in
    # COPPER-era bytes: on a board whose gerbers are sealed and correct, the
    # only way to satisfy this check used to be regenerating the board — which
    # churns every UUID (measured: 81626 diff lines on a semantically identical
    # rebuild) and turns a data-only fix into a full respin needing the whole
    # verification battery. The DECISION is still enforced: the ref must be
    # off the shipped CPL (DECLARED-BUT-PLACED, above, is not deferrable), the
    # exporter must honour the declaration, and the plan must name the
    # revision that lands the attribute.
    attr_plan = {}
    for e in (asm.get("board_attr_plan") or []):
        for r in (e.get("refs") or []):
            attr_plan[str(r)] = e
    for r in sorted(declared & board_refs):
        if "exclude_from_pos_files" in by_ref[r]["attrs"]:
            continue
        e = attr_plan.get(r)
        if e and str(e.get("measured_on") or "").strip() \
              and len(str(e.get("plan") or "")) >= 20:
            notes.append(
                f"  DEFERRED-BOARD-ATTR: {r} is declared not_assembled and is "
                f"OFF the shipped CPL, but its board footprint still lacks "
                f"`exclude_from_pos_files`; board_attr_plan measured_on="
                f"{e.get('measured_on')} lands it at the next board revision")
            continue
        fails.append(
            f"  DECLARED-NOT-EXCLUDED: {r} is declared not_assembled but "
            f"its board footprint has no `exclude_from_pos_files` "
            f"attribute, and no `board_attr_plan:` entry (with "
            f"`measured_on:` + `plan:`) defers it — nothing stops the next "
            f"export putting it straight back on the CPL")
    for r in sorted(declared - board_refs):
        fails.append(
            f"  UNDECLARED-UNPOPULATED: assembly.yaml declares {r} "
            f"not_assembled but no such footprint exists on the board")

    # ---- board attribute vs the CPL actually shipped
    attr_but_placed = sorted(
        r for r in cpl_refs
        if r in by_ref and "exclude_from_pos_files" in by_ref[r]["attrs"])
    if attr_but_placed:
        fails.append(
            f"  POS-ATTR-VS-CPL: {len(attr_but_placed)} ref(s) carry "
            f"`exclude_from_pos_files` on the BOARD yet are placed by the "
            f"shipped CPL — the CPL does not match the board it claims to "
            f"come from: {', '.join(attr_but_placed[:24])}")

    # ---- a placed part JLC cannot source
    uncoded_placed = sorted({r for code, refs in bom_rows if not code
                             for r in refs} & cpl_refs)
    if uncoded_placed:
        fails.append(
            f"  UNCODED-ON-CPL: {len(uncoded_placed)} ref(s) have a BLANK "
            f"LCSC on their BOM line yet appear on the CPL — JLC is told to "
            f"place a part it has no code to source: "
            f"{', '.join(uncoded_placed)}")
    no_row = sorted(cpl_refs - set(codes))
    if no_row:
        fails.append(
            f"  CPL-NO-BOM-ROW: {len(no_row)} placed designator(s) have no BOM "
            f"line at all: {', '.join(no_row[:24])}")

    # ---- the MANIFEST line is GENERATED from assembly.yaml, not re-typed
    if manifest_refs is None:
        if unpopulated:
            fails.append(
                "  MANIFEST-UNDECLARED: the release MANIFEST carries no "
                "`not_assembled:` line while the board has unpopulated parts "
                "— the population decision must be visible in the order "
                "paperwork")
    elif manifest_refs - board_refs:
        # PROSE, not a declaration. A GENERATED not_assembled: line contains
        # ONLY refdes; this one carries free text, so every token in it is a
        # guess and accusing a specific ref from it is a FALSE POSITIVE
        # WAITING TO HAPPEN. Measured on usb-hub-3s-v3 v1.4 (2026-07-25): the
        # line yields 50 tokens of which 44 are English words ("must", "be",
        # "the", "blade"), and its four REAL refdes — C53/C54/R34/R35 — sit in
        # a clause that says the OPPOSITE ("remain POPULATE-BY-DEFAULT on
        # BOM/CPL"). An earlier cut of this checker accused all four. Prose is
        # not machine-readable; that is precisely why the line must be
        # GENERATED. So: report the ungradeable line, name NO refs.
        junk = sorted(manifest_refs - board_refs)
        fails.append(
            f"  MANIFEST-PROSE: the MANIFEST's not_assembled: line is free "
            f"prose, not a declaration — {len(manifest_refs)} whitespace "
            f"tokens of which {len(junk)} are not refdes on this board "
            f"(e.g. {', '.join(repr(j) for j in junk[:5])}). No gate can "
            f"grade it and it is not cross-checked here: GENERATE it from "
            f"03_src/rules/assembly.yaml (a bare refdes list) so it can be")
    else:
        stray = sorted(manifest_refs & cpl_refs)
        if stray:
            fails.append(
                f"  DECLARED-BUT-PLACED: the MANIFEST's not_assembled: line "
                f"names {len(stray)} ref(s) that are ON the CPL: "
                f"{', '.join(stray[:24])}")
        if have_assembly:
            miss = sorted(declared - manifest_refs)
            extra = sorted(manifest_refs - declared - cpl_refs)
            if miss or extra:
                fails.append(
                    f"  MANIFEST-DRIFT: the MANIFEST's not_assembled: set "
                    f"disagrees with assembly.yaml (missing from MANIFEST: "
                    f"{miss[:12]}; not in assembly.yaml: {extra[:12]}) — the "
                    f"MANIFEST line is GENERATED from assembly.yaml, never "
                    f"hand-written in two places")

    # ---- A-POS: the CPL COORDINATE, and the process that must execute it
    datum_worst = []
    if cpl_xy:
        dfails, datum_worst = check_datum(fps, cpl_xy)
        fails.extend(dfails)
    fails.extend(check_smt_placeable(fps, cpl_refs, asm))

    hist = {}
    for _ref, _rot, layer in cpl_rows:
        hist[layer or "?"] = hist.get(layer or "?", 0) + 1
    summary = {"board": len(board_refs), "cpl": len(cpl_refs),
               "datum_max_mm": round(datum_worst[0][0], 5) if datum_worst else None,
               "datum_max_ref": datum_worst[0][1] if datum_worst else None,
               "datum_graded": len(datum_worst),
               "unpopulated": len(unpopulated), "declared": len(declared),
               "consigned": len(consigned), "exempt_prefixes": exempt,
               "sides": hist, "unexplained": unexplained}
    return fails, notes, summary


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="A-POP: the population set is DECLARED, not emergent")
    ap.add_argument("target")
    ap.add_argument("--assembly", default="")
    ap.add_argument("--board", default="")
    ap.add_argument("--cpl", default="")
    ap.add_argument("--bom", default="")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--json", default="", metavar="OUT")
    ap.add_argument("--emit-manifest-line", action="store_true",
                    help="print the MANIFEST `not_assembled:` line GENERATED "
                         "from assembly.yaml (refdes only) and exit — paste "
                         "it into MANIFEST.txt instead of hand-writing it")
    # RED-VERIFY hooks (tests only): neuter ONE family of findings so a
    # known-bad fixture is shown to pass when — and only when — that family is
    # disabled, proving the finding came from that check and nothing else.
    ap.add_argument("--_disable-setid", action="store_true",
                    help="neuter the board-vs-CPL set identity checks")
    ap.add_argument("--_disable-uncoded", action="store_true")
    ap.add_argument("--_disable-datum", action="store_true",
                    help="neuter A-POS CPL-DATUM-OFF")
    ap.add_argument("--_disable-smt", action="store_true",
                    help="neuter A-POS CPL-NOT-SMT-PLACEABLE")
    args = ap.parse_args(argv)

    board, cpl, bom, root = discover(args.target)
    board = Path(args.board) if args.board else board
    cpl = Path(args.cpl) if args.cpl else cpl
    bom = Path(args.bom) if args.bom else bom
    asm_p = (Path(args.assembly) if args.assembly
             else root / "03_src" / "rules" / "assembly.yaml")
    man_p = (Path(args.manifest) if args.manifest
             else Path(args.target) / "MANIFEST.txt")

    if args.emit_manifest_line:
        if not Path(asm_p).is_file():
            print(f"FATAL: no assembly.yaml at {asm_p}", file=sys.stderr)
            return 2
        print(manifest_line(load_assembly(asm_p)))
        return 0

    print(f"== A-POP assembly_coverage: {Path(args.target).name} ==")
    if not board or not Path(board).is_file():
        print("FATAL: no .kicad_pcb found (pass --board)", file=sys.stderr)
        return 2
    if not cpl or not Path(cpl).is_file():
        print("FATAL: no cpl.csv found (pass --cpl)", file=sys.stderr)
        return 2
    if not bom or not Path(bom).is_file():
        print("FATAL: no bom.csv found (pass --bom)", file=sys.stderr)
        return 2

    asm = load_assembly(asm_p)
    fails, notes, summary = check(
        read_footprints(board), read_cpl(cpl), read_bom_rows(bom), asm,
        manifest_not_assembled(man_p)[0], Path(asm_p).is_file(),
        cpl_xy=read_cpl_xy(cpl))

    if args._disable_datum:
        fails = [f for f in fails if "CPL-DATUM-" not in f]
    if args._disable_smt:
        fails = [f for f in fails if "CPL-NOT-SMT-PLACEABLE" not in f]
    if args._disable_setid:
        fails = [f for f in fails
                 if not any(k in f for k in ("UNDECLARED-UNPOPULATED",
                                             "DECLARED-BUT-PLACED",
                                             "POS-ATTR-VS-CPL",
                                             "NO-ASSEMBLY-DECL"))]
    if args._disable_uncoded:
        fails = [f for f in fails if "UNCODED-ON-CPL" not in f]

    print(f"  board={summary['board']} footprints, cpl={summary['cpl']} "
          f"placements, unpopulated={summary['unpopulated']} "
          f"(declared={summary['declared']}, consigned={summary['consigned']}, "
          f"exempt_prefixes={summary['exempt_prefixes']})")
    print("  placement histogram: "
          + ", ".join(f"{k}={v}" for k, v in sorted(summary["sides"].items())))
    if summary.get("datum_graded"):
        print(f"  A-POS datum: {summary['datum_graded']} CPL row(s) graded "
              f"against the pad-array centre, worst = "
              f"{summary['datum_max_mm']:.5f}mm ({summary['datum_max_ref']}), "
              f"tolerance {DATUM_TOL_MM}mm")
    for n in notes:
        print(n)
    for f in fails:
        print(f)
    if args.json:
        Path(args.json).write_text(json.dumps(
            {"target": str(args.target), "summary": summary, "fails": fails},
            indent=1) + "\n")
    if fails:
        print(f"A-POP: FAIL ({len(fails)} finding(s))")
        return 1
    print("A-POP: PASS (every unpopulated part is declared with evidence)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
