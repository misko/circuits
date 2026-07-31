"""JLC order package: gerbers + drills + BOM + CPL + upload zip.

    /usr/bin/python3 export_jlc_package.py BOARD.kicad_pcb OUTDIR [--layers 4]

Run with the KiCad-bundled interpreter (import pcbnew must work).
Run only AFTER the audit gate and classified DRC pass (kicad-pcb skill).

- The zip contains gerbers + drills + job file ONLY (JLC's PCB uploader);
  bom.csv / cpl.csv upload separately in the assembly step.
- Parts whose Value contains "DNP" are excluded from BOM/CPL (still in
  gerbers). Reference prefix H* is skipped as mounting holes.
- LCSC part numbers come from the AUTHORITATIVE per-refdes source
  (circuit.json `supplier_part_numbers`, auto-discovered or --lcsc-source),
  and the BOM is grouped by (LCSC code, footprint) — so two distinct codes on
  the same value+footprint stay on SEPARATE rows and a code can never be
  substituted by a value-token match (the usb-hub-3s-v3 v1.1 defect). A prior
  bom.csv is only a per-refdes FALLBACK for parts the source does not code.
- Bottom-side CPL coordinates are NOT mirrored (JLC handles that), but
  bottom ROTATIONS are the classic failure — check the assembly preview.
- The BOM is graded as its RECIPIENT parses it (canon F-LEGIBLE, ADR-0006):
  the MPN comes from `02_parts/<MPN>/part.yaml` (the dossier's `mpn:` field,
  then the vetted passives ledger) and a coded row resolving NO MPN BLOCKS;
  the Comment is a real value, never an LCSC code or a `simple_*` placeholder;
  and the file carries a UTF-8 byte-order-mark so a cp936 reader cannot render
  `Ω` as `惟`. `lcsc_mpn_map.csv` is RETIRED as an input.

THE ASSEMBLY FILES ARE NAMED `bom.csv` AND `cpl.csv`, AND THAT IS THE CONTRACT'S
NAME, NOT A PREFERENCE. `07_releases/contracts.md` requires `fab/bom.csv` +
`fab/cpl.csv` and all 34 sealed releases carry those names; this exporter wrote
`bom_jlc.csv`/`cpl_jlc.csv` and every seal bridged the gap by HAND-COPYING. The
hand-copy is what made the mismatch invisible — and on pluto-rx2-8way-v2 the
copy did not happen, so the staged archive shipped the exporter's names. The
consequence was not a cosmetic file-not-found: `release_freshness_check.py`
resolves A-STOCK and A-BUY through `fab/bom.csv`, so with the name absent both
gates reached a ZERO DENOMINATOR and emitted NOTES — "no coded, placed line to
grade" and "sourcing UNGRADED — 0 line(s) measured" — instead of failures.
Two gates that exist BECAUSE five sealed releases shipped failing stock
evidence went silent over an empty set (measured 2026-07-31; adding only the
two correctly-named copies flips them to `11 graded line(s), verdict=PASS` /
`SOURCING: CLEAR`). A producer that does not emit the name its consumers
resolve is the defect, not the consumers.

LEGACY `bom_jlc.csv`/`cpl_jlc.csv` in the OUTDIR are read for LCSC carry-over
(so an existing 06_build/fab/ still seeds hand-solder codes) and then REMOVED,
on the success path as well as the two block paths. Leaving them is the same
failure the block paths already guard: a plausible-looking uploadable file that
is not the one this run produced.
"""
import argparse
import csv
import re
import sys
import time
import zipfile
from pathlib import Path

import pcbnew

run_start = time.time()

# CANON A-ROT (2026-07-25). JLC's zero-orientation is a PER-PART fact, and the
# ONLY authority for it is the per-LCSC MEASURED table (jlc_lcsc_rotations.csv).
# The community footprint-NAME DB (jlc_rotations_db.csv) is still loaded — and
# is now ADVISORY: it is reported and cross-checked, never obeyed. Authority
# inherited by pattern-matching a footprint NAME produced P0s on FIVE boards in
# one day through five distinct mechanisms (wrong key / negated offset / no
# rule fired / partial prefix / unevidenced rule); the post-mortem is the module
# docstring of jlc_rotation_resolve.py. A placement with no measured row is
# UNSOURCED and BLOCKS the assembly half of this export — unless its footprint
# MEASURES as its own 180-degree reflection (jlc_footprint_symmetry), the one
# exemption, which reads no names and no tables.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jlc_footprint_symmetry import symmetry
from jlc_rotation_resolve import (SRC_UNSOURCED, load_lcsc_rows,  # noqa: E402
                                  load_name_db, resolve)

# ONE loader, shared with jlc_rotation_audit.py, so the exporter and the
# auditor cannot disagree about what the files say. (It also catches ValueError
# on the refutation continuation rows: a `#`-annotated rule once HARD-CRASHED
# the fab export for every board — a comment in a data file must never be able
# to stop a board shipping.)
_ROT_DB = load_name_db()
_LCSC_ROWS = load_lcsc_rows()
_LCSC_ROT = {c: r["offset"] for c, r in _LCSC_ROWS.items()}

#: A-ROT/A-POL accumulators, drained into the blocking report below.
_UNSOURCED = {}      # lcsc -> {"refs": [...], "fp": str, "why": str}
_XCHECK = []         # (finding_id, text) — advisory name-DB disagreements
_HUMAN_GATE = {}     # lcsc -> [refs] for rows declared A-POL single-channel


def jlc_rotation(fp, fpname, rot, lcsc=""):
    """(cpl_rotation, offset) for one placement, recording A-ROT/A-POL state.

    `fp` is the pcbnew FOOTPRINT — needed for the MEASURED symmetry exemption.
    """
    r = resolve(fpname, rot, lcsc, _ROT_DB, _LCSC_ROT)
    _XCHECK.extend(r.findings if r.source != SRC_UNSOURCED else [])
    if r.source == SRC_UNSOURCED:
        sym = symmetry(fp)
        if not sym["exempt"]:
            e = _UNSOURCED.setdefault(lcsc, {"refs": [], "fp": fpname,
                                             "why": sym["why"],
                                             "advice": r.advice,
                                             "advice_pat": r.advice_pattern})
            e["refs"].append(fp.GetReference())
    else:
        pol = (_LCSC_ROWS.get(lcsc, {}).get("polarity") or "").lower()
        if pol == "single-channel":
            _HUMAN_GATE.setdefault(lcsc, []).append(fp.GetReference())
    return r.cpl, r.offset


def placement_datum(fp):
    """JLC's placement datum for a footprint, in BOARD coordinates.

    JLC places a part so that ITS OWN part origin lands on the CPL's Mid X/Y.
    That origin is NOT KiCad's footprint anchor — it is the CENTRE OF THE
    BOUNDING BOX OF THE PAD CENTRES.

    MEASURED, not assumed (2026-07-25, crow-recorder-central-v2 v1.5). Over
    228 cached EasyEDA/JLC-native footprints across six boards of this fleet,
    the model origin sits on its own pad-centre bbox centre to <=0.01mm in
    227 cases (99.6%). The single outlier, C464587, is a part already recorded
    as NOT a land drop-in. Two weaker hypotheses were tested on the same 228
    and REFUTED: bbox of pad OUTLINES 213/228 (93.4%) and CENTROID of pad
    centres 198/228 (86.8%). Both fail on exactly the connectors that matter,
    because a connector's pads differ in size and count between rows.

    The anchor is a KiCad authoring convenience with no fab meaning, and on
    this fleet it differs from the datum on 12/203, 12/227, 12/114, 14/238,
    2/40 and 1/39 footprints per board — up to 24.16mm. It was emitted here
    for the fleet's whole history. The defect that found it: crow-recorder-
    central-v2 v1.4 shipped its only USB-C (J2) 1.3025mm off, against 1.150mm
    contacts -> 0.000mm pad overlap and four shell posts that miss their
    holes, i.e. a connector that cannot physically seat.

    CROSS-CHECKED against JLC's own models by a numbering-free landmark fit
    (pad names never read) on the two affected refs of that board:
      J1 C381116  our pad lattice maps onto JLC's exactly, rms 0.0000mm ->
                  datum at local (-3.000, +2.350); this function returns the
                  same point to 0.0000mm.
      J2 C3020560 three independent landmark families agree: shell posts
                  -1.295, NPTH pegs -1.275, SMD contact row -1.310; this
                  function returns -1.3025, inside that 0.035mm spread.

    Copper pads only, which is JLC's own convention: their models carry the
    plastic-peg holes as copper-layer pads too, and including them is what
    reproduces 227/228. Falls back to the anchor for a footprint with no
    copper pads (mounting holes, fiducials) — those are never on the CPL.
    """
    xs, ys = [], []
    for p in fp.Pads():
        if p.GetLayerSet().Contains(pcbnew.F_Cu) or \
           p.GetLayerSet().Contains(pcbnew.B_Cu) or \
           p.GetLayerSet().Contains(pcbnew.In1_Cu):
            pos = p.GetPosition()
            xs.append(pos.x)
            ys.append(pos.y)
    if not xs:
        return fp.GetPosition()
    return pcbnew.VECTOR2I(int(round((min(xs) + max(xs)) / 2)),
                           int(round((min(ys) + max(ys)) / 2)))


def declared_off_bom(board_path):
    """The refdes set declared `on_bom: false` in 03_src/rules/assembly.yaml.

    THE DECISION EXISTED AND WAS NOT REGENERABLE. crow-mic-pod-v2 v1.1
    (2026-07-25) removed MK1 and J1 from its assembly BOM because both carried a
    blank or unbuyable code and neither is on the CPL, and "the upload stalls at
    JLC's BOM/CPL matcher". That removal was made IN THE ARTIFACT: re-running
    this exporter on the same board puts both rows straight back, so the sealed
    v1.2 `fab/bom.csv` is not reproducible from `03_src/` + `03_tscircuit/`
    (canon M3). `on_bom: false` moves the decision into `assembly.yaml`, which
    already calls itself "the ONE machine-readable home for who gets placed, and
    why not" — this is the same file answering the adjacent question, who gets
    SOURCED.

    IT IS NOT DERIVABLE FROM `reason:`, and that was tried first. usb-hub-3s-v3
    declares F1 `user_supplied` and F1 IS on its BOM (the holder ships with the
    order at stock 1213; only the fuse ELEMENT is bought locally). crow-mic-pod-v2
    declares MK1 and J1 `user_supplied` and both must LEAVE the BOM. Same reason
    code, opposite BOM answer, because `reason:` records WHY a part is not
    placed and this records whether JLC is asked to source it. A rule inferred
    from `reason:` would have silently dropped usb-hub-3s-v3's fuse holder.

    Default is TRUE (stay on the BOM): every board that does not use the key
    exports byte-identically.
    """
    refs, path = set(), None
    p = Path(board_path).resolve()
    for anc in list(p.parents)[:4]:
        cand = anc / "03_src" / "rules" / "assembly.yaml"
        if cand.is_file():
            path = cand
            break
    if path is None:
        return refs, None
    try:
        import yaml
    except ImportError:
        return refs, None
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    for e in (data.get("not_assembled") or []):
        if e.get("on_bom") is False:
            refs.update(str(r) for r in (e.get("refs") or []))
    return refs, path


def declared_unpopulated(board_path):
    """The `not_assembled:` refdes set from 03_src/rules/assembly.yaml.

    assembly.yaml calls itself "the ONE machine-readable home for who gets
    placed, and why not" — but until 2026-07-25 NOTHING read it at export
    time. The only real mechanism was `exclude_from_pos_files` on the board,
    so a population decision could only be expressed by touching COPPER-era
    bytes: on a board whose gerbers are already sealed and correct, "do not
    place R_inj1" was unsayable without invalidating the whole release.

    Reading the declaration here makes the CPL follow the decision record.
    It cannot resurrect a row (it only ever REMOVES), so a board whose
    attributes already agree with its declaration — every other board in the
    fleet — exports byte-identically.

    A-POP still grades board attribute vs declaration; this is the second
    mechanism, not a replacement for the first.
    """
    p = Path(board_path).resolve()
    for anc in list(p.parents)[:4]:
        cand = anc / "03_src" / "rules" / "assembly.yaml"
        if cand.is_file():
            try:
                import yaml
            except ImportError:
                print(f"  WARNING: {cand} exists but PyYAML is missing — the "
                      f"not_assembled: declaration is NOT being honoured")
                return set(), None
            data = yaml.safe_load(cand.read_text(encoding="utf-8-sig")) or {}
            refs = {str(r) for e in (data.get("not_assembled") or [])
                    for r in (e.get("refs") or [])}
            return refs, cand
    return set(), None

ap = argparse.ArgumentParser()
ap.add_argument("board")
ap.add_argument("outdir")
ap.add_argument("--layers", type=int, default=4, choices=(2, 4, 6))
ap.add_argument("--lcsc-source", default="",
                help="circuit.json (or a 03_tscircuit dir) — the AUTHORITATIVE "
                     "per-refdes LCSC source. Auto-discovered from the board "
                     "path when omitted.")
ap.add_argument("--allow-unsourced-rotations", action="store_true",
                help="LOUD, DISCOURAGED ESCAPE HATCH (canon A-ROT): write the "
                     "BOM/CPL even though some placements have NO measured "
                     "per-LCSC rotation row. Every unsourced code is printed "
                     "and written to rotations_unsourced.csv either way. Use "
                     "it to produce the measurement worklist — never to place "
                     "an order.")
ap.add_argument("--allow-illegible-bom", action="store_true",
                help="LOUD, DISCOURAGED ESCAPE HATCH (canon F-LEGIBLE): write "
                     "the BOM even though some coded rows resolve NO MPN from "
                     "02_parts/<MPN>/part.yaml or the vetted ledger, or some "
                     "Comment is an LCSC code / a `simple_*` placeholder. Use "
                     "it to produce the worklist — never to place an order.")
args = ap.parse_args()

board = pcbnew.LoadBoard(args.board)
# ABSOLUTE outdir: PLOT_CONTROLLER resolves relative paths against the BOARD
# file's directory, silently writing gerbers to <board_dir>/<outdir> while the
# zip step (python cwd-relative) sees only drills (found 2026-07-16)
out = Path(args.outdir).resolve()
out.mkdir(parents=True, exist_ok=True)
stem = Path(args.board).stem

pc = pcbnew.PLOT_CONTROLLER(board)
po = pc.GetPlotOptions()
po.SetOutputDirectory(str(out))
po.SetPlotFrameRef(False)
po.SetAutoScale(False)
po.SetMirror(False)
po.SetUseGerberAttributes(True)
po.SetUseGerberProtelExtensions(True)
po.SetCreateGerberJobFile(True)
po.SetSubtractMaskFromSilk(True)
LAYERS = [("F_Cu", pcbnew.F_Cu), ("B_Cu", pcbnew.B_Cu),
          ("F_Silkscreen", pcbnew.F_SilkS), ("B_Silkscreen", pcbnew.B_SilkS),
          ("F_Mask", pcbnew.F_Mask), ("B_Mask", pcbnew.B_Mask),
          ("F_Paste", pcbnew.F_Paste), ("B_Paste", pcbnew.B_Paste),
          ("Edge_Cuts", pcbnew.Edge_Cuts)]
if args.layers >= 4:
    LAYERS[2:2] = [("In1_Cu", pcbnew.In1_Cu), ("In2_Cu", pcbnew.In2_Cu)]
if args.layers >= 6:
    LAYERS[4:4] = [("In3_Cu", pcbnew.In3_Cu), ("In4_Cu", pcbnew.In4_Cu)]
for name, layer in LAYERS:
    pc.SetLayer(layer)
    pc.OpenPlotfile(name, pcbnew.PLOT_FORMAT_GERBER, name)
    pc.PlotLayer()
pc.ClosePlot()

ew = pcbnew.EXCELLON_WRITER(board)
ew.SetOptions(False, False, board.GetDesignSettings().GetAuxOrigin(), False)
ew.SetFormat(True)
ew.CreateDrillandMapFilesSet(str(out), True, False)

# AUTHORITATIVE per-refdes LCSC comes from the SOURCE (circuit.json), NOT from
# the board (which carries only a Value string like "10uF") and NOT from a
# value-token carry-over. Two parts that share a value+footprint but differ in
# LCSC — 10uF/50V C77102 on the input rail vs 10uF/25V C77100 elsewhere — are
# INDISTINGUISHABLE by value+footprint, and the old carry-over collapsed them
# onto one row under a single code (usb-hub-3s-v3 v1.1 shipped 25V input caps;
# the 100uF output cap was likewise substituted C84455->C90143). Keying the BOM
# by the per-refdes source code keeps distinct codes on SEPARATE rows and makes
# the code impossible to substitute — it is copied from the source, not matched.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bom_source_check import refdes_codes_from_circuit, resolve_circuit_json

src_hint = args.lcsc_source
if not src_hint:
    # walk up from the board to a sibling 03_tscircuit/{build,dist}/circuit.json
    for parent in [Path(args.board).resolve(), *Path(args.board).resolve().parents]:
        cand = parent / "03_tscircuit"
        if cand.is_dir():
            src_hint = str(cand)
            break
src_code = {}   # refdes -> authoritative LCSC
cj = resolve_circuit_json(src_hint) if src_hint else None
if cj:
    src_code = refdes_codes_from_circuit(cj)
    print(f"LCSC source: {cj} ({sum(1 for v in src_code.values() if v)} coded refdes)")
else:
    print("WARNING: no circuit.json found (pass --lcsc-source). LCSC codes will "
          "fall back to any prior bom.csv (per-refdes) and otherwise be "
          "BLANK — there is no authoritative source to key on. Fix the source "
          "path; the bom_source_check gate has nothing to compare against here.")

# THE CONTRACT'S NAMES. `07_releases/contracts.md` requires fab/bom.csv +
# fab/cpl.csv; the legacy names this exporter used to write are read for
# carry-over and then removed (see the module docstring).
bom_path = out / "bom.csv"
cpl_path = out / "cpl.csv"
LEGACY_NAMES = ("bom_jlc.csv", "cpl_jlc.csv")


def sweep_uploadable(*extra, why):
    """Delete every assembly file in the outdir that this run did not write.

    `extra` names the CURRENT-name files to drop as well (a blocked run drops
    both); the LEGACY names are always dropped, because after the rename they
    are the ones most likely to be picked up by hand.
    """
    for _stale in (*extra, *(out / n for n in LEGACY_NAMES)):
        if _stale.exists():
            _stale.unlink()
            print(f"  removed stale {_stale.name} ({why})")


# Carry-over from a prior BOM: ONLY a fallback for refdes the source does not
# code (hand-solder parts, or a non-tscircuit board). Keyed per-refdes via the
# Designator column so it can never re-merge distinct codes. The legacy name is
# accepted as a SOURCE here and nowhere else — an outdir written before this
# rename still seeds, and then loses the stale file below.
old_lcsc = {}       # refdes -> LCSC (from a prior export)
_carry = next((p for p in (bom_path, out / "bom_jlc.csv") if p.exists()), None)
if _carry is not None:
    if _carry.name != bom_path.name:
        print(f"  LCSC carry-over read from the LEGACY {_carry.name}; this run "
              f"writes {bom_path.name} and removes the legacy file")
    with open(_carry, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            # An LCSC code is C-prefixed digits. A carried-over MPN string (a
            # hand-solder part's FPID handle, e.g. AOM-5024L-HD-R) is NOT an LCSC
            # and must never be resurrected into the LCSC column from a stale BOM
            # (crow-mic-pod-v2 MK1) — the source (refdes_codes_from_circuit)
            # already blanks it; harden the carry-over to match.
            code = (row.get("LCSC") or "").strip()
            if code and re.fullmatch(r"C\d+", code):
                for r in (row.get("Designator") or "").split(","):
                    if r.strip():
                        old_lcsc.setdefault(r.strip(), code)

groups, cpl = {}, []
_off_bom, _off_bom_path = declared_off_bom(args.board)
_dropped_off_bom = []
if _off_bom:
    print(f"  assembly.yaml: {len(_off_bom)} ref(s) declared `on_bom: false` -> "
          f"dropped from the BOM as well as the CPL ({_off_bom_path})")
_declared_np, _asm_path = declared_unpopulated(args.board)
if _asm_path:
    print(f"  assembly.yaml: {len(_declared_np)} ref(s) declared "
          f"not_assembled -> dropped from the CPL ({_asm_path})")
_dropped_by_decl = []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("H"):
        continue
    val = fp.GetValue()
    if "DNP" in val:
        continue
    if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM:
        # test points / board-only artifacts: not assembled, not placed
        continue
    fpname = str(fp.GetFPID().GetLibItemName())
    code = src_code.get(ref) or old_lcsc.get(ref, "")
    # ...or declared `on_bom: false` in assembly.yaml: JLC is asked neither to
    # place it nor to source it, so it leaves the ASSEMBLY BOM entirely. A row
    # JLC cannot match stalls the whole upload at its BOM/CPL matcher
    # (crow-mic-pod-v2 v1.0: MK1 with MPN *and* LCSC both empty).
    if ref in _off_bom:
        _dropped_off_bom.append(ref)
        continue
    # group by (CODE, val, footprint): distinct codes NEVER share a row
    groups.setdefault((code, val, fpname), []).append(ref)
    # exclude_from_pos: hand-solder / DNP-position parts stay in the BOM (for
    # reference) but are dropped from the CPL — JLC does not machine-place them
    # (matches KiCad's native POS export, which honours FP_EXCLUDE_FROM_POS_FILES).
    if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES:
        continue
    # ...or declared not_assembled in 03_src/rules/assembly.yaml. Same
    # outcome, second mechanism: the population DECISION is now able to
    # reach the CPL without touching the board (see declared_unpopulated).
    if ref in _declared_np:
        _dropped_by_decl.append(ref)
        continue
    # JLC's datum is the PAD-ARRAY CENTRE, not KiCad's anchor (measured
    # 227/228 on JLC's own models; see placement_datum). Emitting the anchor
    # put crow-recorder-central-v2 v1.4's USB-C 1.3025mm off its own pads.
    pos = placement_datum(fp)
    d_mm = pcbnew.ToMM(int(round(((pos.x - fp.GetPosition().x) ** 2
                                  + (pos.y - fp.GetPosition().y) ** 2) ** 0.5)))
    if d_mm > 0.01:
        print(f"  datum {ref}: anchor -> pad-array centre, shifted "
              f"{d_mm:.4f}mm ({fpname[:40]})")
    jrot, off = jlc_rotation(fp, fpname, fp.GetOrientationDegrees(), code)
    if off:
        print(f"  rot-correct {ref}: {fp.GetOrientationDegrees():.0f} "
              f"+ {off:.0f} -> {jrot:.0f} ({fpname[:40]}) [MEASURED lcsc row]")
    cpl.append([ref, val, fpname,
                round(pcbnew.ToMM(pos.x), 3), round(-pcbnew.ToMM(pos.y), 3),
                "top" if fp.GetLayer() == pcbnew.F_Cu else "bottom",
                jrot])

# ONE BOM LINE PER PART: JLC's uploader warns "multiple lines matched to same
# part" if two lines carry the same LCSC code — so merge groups that share the
# same NON-EMPTY (code, footprint) (same physical part, perhaps a different
# value string). Groups with different codes are already distinct keys and can
# NEVER merge. Merged Comment is the shared value token, else "a / b".
# ============================================ canon F-LEGIBLE (ADR-0006) ===
# THE MPN COMES FROM THE PART'S OWN DOSSIER, and a coded row that resolves none
# is a FAIL. This column used to be filled from an OPTIONAL, HAND-MAINTAINED
# side-file, `OUTDIR/lcsc_mpn_map.csv`, read with `mpn_map.get(code, "")` — a
# silent default, the exact `row_kind` shape canon M-COVER forbids. Only ONE
# project ever created that file, so eight of nine boards shipped 100% blank
# MPN and nothing noticed: 914 of 1205 sealed BOM rows fleet-wide. The
# author had ALREADY DIAGNOSED the symptom in this file's own comment ("a
# Comment like 'LM5145' left C485912 at 'No Part Selected'; 'LM5145RGYR'
# matches") and then made the remedy opt-in. A known remedy behind an opt-in
# flag is not a remedy.
#
# The authoritative MPN was in the tree the whole time: `02_parts/<MPN>/
# part.yaml`. usb-hub-3s-v3's own release history proves the mechanism — v1.5
# blank-MPN 0 (side-file complete), v1.6-v1.8 blank-MPN 3, and those three
# codes (C25757, C2296, C2297) ALL HAVE DOSSIERS. The side-file is a SECOND
# HOME for a fact that already has one, and it drifted the moment a part was
# added. It is RETIRED as an input here; an override belongs in the part's own
# part.yaml, which is the one home.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bom_legibility_check import (MpnAuthority, comment_defect,  # noqa: E402
                                  legible_comment)


def find_parts_dir(board_path):
    """The board's `02_parts/` — the MPN authority — or None."""
    p = Path(board_path).resolve()
    for anc in list(p.parents)[:4]:
        if (anc / "02_parts").is_dir():
            return anc / "02_parts"
    return None


_parts_dir = find_parts_dir(args.board)
_auth = MpnAuthority(_parts_dir, None)
print(f"MPN authority: {_auth.describe()}")

lines = {}
for (code, val, fpname), refs in sorted(groups.items()):
    key = (code, fpname) if code else ("", val, fpname)
    # LEGIBLE FIRST, THEN MERGE. The merge builds "a / b" out of two Comment
    # tokens; merging BEFORE legibility would let two illegible tokens produce
    # a string ("C82317 / C131025") that no narrow legibility test can refuse
    # while still being unreadable by every human on both sides of the upload.
    comment = legible_comment(val, _auth.resolve(code), fpname)
    if key in lines:
        line = lines[key]
        line[1].extend(refs)
        t_old = line[0].split()[0] if line[0].split() else line[0]
        t_new = comment.split()[0] if comment.split() else comment
        line[0] = t_old if t_old == t_new else f"{line[0]} / {comment}"
    else:
        lines[key] = [comment, list(refs), fpname, code]

# The retired side-file is IGNORED, loudly, and its DRIFT is measured — a
# second home that silently disagrees with the first is the whole defect.
_retired = out / "lcsc_mpn_map.csv"
if _retired.exists():
    print(f"  NOTE: {_retired.name} is RETIRED as an input (ADR-0006) and was "
          f"NOT read. Move any override into 02_parts/<MPN>/part.yaml.")
    with open(_retired) as f:
        for row in csv.DictReader(f):
            c, m = (row.get("LCSC") or "").strip(), (row.get("MPN") or "").strip()
            res = _auth.resolve(c) if c else None
            if c and m and res and res.mpn != m:
                print(f"    DRIFT {c}: side-file says {m!r}, {res.source} says "
                      f"{res.mpn!r} — the dossier wins")

# F-MPN / F-WORDS accumulators, drained into the blocking report below.
_NO_MPN = []        # (code, refs) — coded rows the authority cannot resolve
_ILLEGIBLE = []     # (refs, why) — Comment no human can review
for comment, refs, fpname, code in lines.values():
    if code and _auth.resolve(code) is None:
        _NO_MPN.append((code, sorted(refs)))
    why = comment_defect(comment)
    if why:
        _ILLEGIBLE.append((sorted(refs), why))

# ===================================================== canon A-ROT / A-POL ===
# THE ASSEMBLY HALF OF THIS EXPORT IS BLOCKED unless every CPL rotation is
# SOURCED — either from a MEASURED per-LCSC row, or by the footprint measuring
# as its own 180-degree reflection (which means there is no orientation to get
# wrong). Silence used to resolve to 0.0; silence is now a FAIL.
#
# The worklist is written EITHER WAY, so a blocked run still tells you exactly
# what to measure. The BOM/CPL are not written on a block, and any stale ones
# are REMOVED: a blocked run that leaves a plausible-looking cpl.csv behind
# is worse than no gate, because the next person uploads the stale file. The
# sweep covers the LEGACY names too — a stale bom_jlc.csv is exactly as
# uploadable as a stale bom.csv, and after the rename it is the likelier one.
uns_path = out / "rotations_unsourced.csv"
if _UNSOURCED:
    with open(uns_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LCSC", "footprint", "refs", "why_not_exempt",
                    "advisory_name_db_guess", "advisory_rule"])
        for code, e in sorted(_UNSOURCED.items()):
            w.writerow([code, e["fp"], ",".join(sorted(e["refs"])), e["why"],
                        "" if e["advice"] is None else f"{e['advice']:g}",
                        e["advice_pat"] or ""])
elif uns_path.exists():
    uns_path.unlink()

for _fid, _text in dict.fromkeys(_XCHECK):    # one line per distinct finding
    print(f"  {_fid}: {_text}")
if _HUMAN_GATE:
    gate_path = out / "rotation_human_gate.txt"
    with open(gate_path, "w") as f:
        f.write("A-POL SINGLE-CHANNEL — these placements have NO numbering-free\n"
                "channel corroborating their rotation. The pad-NUMBER fit is\n"
                "the only evidence, and a pad-number fit structurally cannot\n"
                "see a model whose own numbering differs from ours (C2296/\n"
                "C2297: fit 180 at a 17.7x margin, true offset 0). EACH MUST\n"
                "PASS THE JLC ORDER-PREVIEW HUMAN GATE BEFORE THE FIRST ORDER.\n\n")
        for code, refs in sorted(_HUMAN_GATE.items()):
            f.write(f"{code}: {','.join(sorted(refs))}\n")
    print(f"  A-POL SINGLE-CHANNEL ({len(_HUMAN_GATE)} code(s)) — JLC "
          f"order-preview human gate REQUIRED before first order: "
          f"{ {c: sorted(r) for c, r in _HUMAN_GATE.items()} } "
          f"-> {gate_path.name}")

if _UNSOURCED and not args.allow_unsourced_rotations:
    n_refs = sum(len(e["refs"]) for e in _UNSOURCED.values())
    print(f"\nA-ROT BLOCKED: {n_refs} placement(s) over {len(_UNSOURCED)} LCSC "
          f"code(s) have NO MEASURED rotation row, and their footprints are "
          f"NOT 180-symmetric:")
    for code, e in sorted(_UNSOURCED.items()):
        adv = ("advisory name-DB rule %r would have guessed %g — a HINT, not "
               "an answer" % (e["advice_pat"], e["advice"])
               if e["advice"] is not None else
               "NO name-DB rule matched either: the old resolver shipped 0.0 "
               "in silence (the C98732 XT60 / C125121 opto class)")
        print(f"  {code or '(NO LCSC)'} {e['fp']}: "
              f"{','.join(sorted(e['refs']))}")
        print(f"      {e['why']}")
        print(f"      {adv}")
    print(f"\n  worklist written: {uns_path}")
    print("  FIX each: fit the board footprint against JLC's cached model with "
          "an operator VERIFIED AGAINST PCBNEW ITSELF (never jlc_twin's "
          "jlc_offset — canon M1, e0d735c), then add a row to "
          "jlc_lcsc_rotations.csv with residual + next-best separation + date "
          "+ the polarity column. For a polarized or 2-pad collinear part the "
          "row ALSO needs a NUMBERING-FREE channel (canon A-POL).")
    print("  ESCAPE HATCH (worklist only, NEVER for an order): "
          "--allow-unsourced-rotations")
    sweep_uploadable(bom_path, cpl_path,
                     why="a blocked run must not leave an uploadable "
                         "package behind")
    sys.exit(2)
elif _UNSOURCED:
    n_refs = sum(len(e["refs"]) for e in _UNSOURCED.values())
    print(f"\n  A-ROT OVERRIDDEN by --allow-unsourced-rotations: {n_refs} "
          f"placement(s) over {len(_UNSOURCED)} code(s) carry an UNSOURCED "
          f"rotation. THIS PACKAGE MUST NOT BE ORDERED. Worklist: {uns_path}")
else:
    print(f"  A-ROT OK: all {len(cpl)} CPL rotations are sourced (measured "
          f"per-LCSC row, or a footprint measured 180-symmetric)")

# ============================================== canon F-MPN / F-WORDS ======
# THE ASSEMBLY HALF IS BLOCKED unless every coded row resolves an MPN and every
# Comment is something a human can read. Same shape as the A-ROT block above,
# and for the same reason: silence used to resolve to a blank column, and
# silence is now a FAIL.
if (_NO_MPN or _ILLEGIBLE) and not args.allow_illegible_bom:
    print(f"\nF-LEGIBLE BLOCKED: {len(_NO_MPN)} coded row(s) resolve NO MPN "
          f"and {len(_ILLEGIBLE)} row(s) carry a Comment no human can review. "
          f"A fab artifact is graded as its RECIPIENT will parse it:")
    for code, refs in sorted(_NO_MPN):
        print(f"  F-MPN {code}: {','.join(refs)} — no 02_parts/<MPN>/part.yaml "
              f"declares this code and it is not in the vetted passives ledger")
    for refs, why in sorted(_ILLEGIBLE):
        print(f"  F-WORDS {','.join(refs)}: Comment is {why}")
    print("  FIX F-MPN: add `sourcing: {lcsc: <code>}` to the part's own "
          "02_parts/<MPN>/part.yaml (the dossier's `mpn:` field is the answer), "
          "or append a CATALOG-VERIFIED row to "
          "jlcpcb-fab/references/lcsc_passives_ledger.yaml. NEVER re-create "
          "lcsc_mpn_map.csv — that second home is what drifted.")
    print("  FIX F-WORDS: give the part a real value in the .tsx, or let the "
          "dossier supply one; the exporter falls back to the resolved MPN.")
    print("  ESCAPE HATCH (worklist only, NEVER for an order): "
          "--allow-illegible-bom")
    sweep_uploadable(bom_path, cpl_path,
                     why="a blocked run must not leave an uploadable "
                         "package behind")
    sys.exit(3)
elif _NO_MPN or _ILLEGIBLE:
    print(f"\n  F-LEGIBLE OVERRIDDEN by --allow-illegible-bom: "
          f"{len(_NO_MPN)} unresolved MPN(s), {len(_ILLEGIBLE)} illegible "
          f"Comment(s). THIS PACKAGE MUST NOT BE ORDERED.")
else:
    print(f"  F-LEGIBLE OK: {len(lines)}/{len(lines)} BOM lines carry a "
          f"resolved MPN (where coded) and a human-readable Comment")

# ENCODING: UTF-8 WITH A BYTE-ORDER-MARK. The file was always valid UTF-8 and
# `Ω` was always correctly `CE A9`; there was simply no BOM, so a reader
# defaulting to GBK/CP936 rendered those two bytes as `惟` — which is what the
# user saw. Nothing was corrupt; the reader's assumption was wrong and we gave
# it nothing to correct itself with. 23 of 26 sealed BOMs are in that state.
# The BOM marker is the fix chosen here; ASCII `Ohm` would do equally well and
# `bom_legibility_check.py` is deliberately indifferent to which.
with open(bom_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "MPN", "LCSC"])
    for val, refs, fpname, code in sorted(lines.values(), key=lambda x: x[0]):
        res = _auth.resolve(code)
        w.writerow([val, ",".join(sorted(refs)), fpname,
                    res.mpn if res else "", code])

# F-ECHO worklist — the human-gated half, beside A-POL's rotation_human_gate.txt.
# JLC RESOLVES our codes on their side and can redirect one: our source said
# C82317 for crow-recorder-central-v2's U5 in three places and JLC's resolved
# output said C131025. Nothing in this repo could see that, so the export names
# the triples to compare and the ORDER_README ritual says how.
echo_path = out / "bom_echo_gate.txt"
with open(echo_path, "w", encoding="utf-8") as f:
    f.write("F-ECHO — JLC's RESOLVED BOM vs OURS. After uploading bom.csv,\n"
            "save JLC's own resolved/matched part table out of their UI and run\n"
            "  bom_legibility_check.py <this outdir>/bom.csv --echo SAVED.csv\n"
            "A code JLC redirects is a SUBSTITUTION and is a FINDING, not a\n"
            "convenience. C82317 -> C131025 happened on a shipped board and no\n"
            "gate in this repo could have seen it.\n\n")
    for val, refs, fpname, code in sorted(lines.values(), key=lambda x: x[0]):
        if code:
            f.write(f"{code}\t{val}\t{','.join(sorted(refs))}\n")
print(f"  F-ECHO worklist: {echo_path.name} ({sum(1 for v in lines.values() if v[3])} "
      f"coded line(s) to confirm against JLC's resolved table)")

with open(cpl_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Layer",
                "Rotation"])
    for row in sorted(cpl):
        w.writerow(row)

# Both assembly files are now written under the CONTRACT's names. Anything left
# under the legacy names was written by an EARLIER run of this exporter into the
# same outdir, so it is stale by construction and uploadable by appearance.
sweep_uploadable(why="superseded by this run's contract-named bom.csv/cpl.csv")
if _dropped_by_decl:
    print(f"  CPL: {len(_dropped_by_decl)} row(s) dropped by the "
          f"assembly.yaml not_assembled: declaration: "
          f"{', '.join(sorted(_dropped_by_decl))}")
if _dropped_off_bom:
    print(f"  BOM: {len(_dropped_off_bom)} row(s) dropped by the assembly.yaml "
          f"`on_bom: false` declaration: {', '.join(sorted(_dropped_off_bom))}")
_placed = {r[0] for r in cpl}
_contradiction = sorted(set(_dropped_off_bom) & _placed)
if _contradiction:
    # Structurally impossible with the `continue` above, which drops the ref
    # before it can reach the CPL — asserted anyway, because the failure it
    # guards (JLC told to PLACE a part with no BOM line at all) is the
    # dangerous inversion of the A-POP defect this key exists to fix.
    print(f"\nA-POP BLOCKED: {_contradiction} are declared `on_bom: false` but "
          f"appear on the CPL — JLC would be told to place a part with no BOM "
          f"line to source it from")
    sys.exit(4)

# Upload zip: gerbers + drills (+ job file when present) — no BOM/CPL inside.
# Inner-layer Protel extensions are VERSION-DEPENDENT: KiCad 7 wrote
# In1/In2 as .g2/.g3; KiCad 10 writes .g1/.g2 — cover .g1-.g6 for both.
# KiCad 10's PLOT_CONTROLLER also stopped emitting the .gbrjob headlessly;
# JLC does not require it.
# Zip ONLY files this run just wrote (mtime >= run start): re-exporting
# under a different KiCad version leaves stale differently-named inner
# layers behind, and a glob-everything zip silently ships BOTH.
FAB_EXT = {".gtl", ".gbl", ".g1", ".g2", ".g3", ".g4", ".g5", ".g6",
           ".gts", ".gbs", ".gtp", ".gbp", ".gto", ".gbo", ".gm1",
           ".drl", ".gbrjob"}
zip_path = out / f"{stem}_gerbers.zip"
fresh, stale = [], []
for p in sorted(out.iterdir()):
    if p.suffix.lower() in FAB_EXT:
        (fresh if p.stat().st_mtime >= run_start else stale).append(p)
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in fresh:
        z.write(p, p.name)
n_zipped = len(zipfile.ZipFile(zip_path).namelist())
if stale:
    print(f"WARNING: {len(stale)} stale fab files in {out} EXCLUDED from zip "
          f"(old KiCad version leftovers?) — delete them: "
          f"{[p.name for p in stale]}")

uncoded = sum(1 for v in lines.values() if not v[3])
groups = lines
print(f"gerbers: {len(LAYERS)} layers + drills -> {out}")
print(f"zip: {zip_path.name} ({n_zipped} files)")
print(f"BOM: {len(groups)} lines ({uncoded} without LCSC); CPL: {len(cpl)} parts")
if uncoded:
    print(f"NEXT: python3 jlc_stock_check.py {bom_path} --search-missing")
