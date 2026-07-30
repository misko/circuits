#!/usr/bin/env python3
"""P-FACT — grade the board + release against every part's OWN declared facts.

    part_facts_check.py PROJECT_OR_RELEASE [--parts DIR] [--strict]

WHY THIS EXISTS
---------------
`02_parts/<MPN>/part.yaml` is the most expensive artifact this pipeline makes:
a hand-verified, datasheet-cited fact store, ~187 of them across the fleet. It
is ALMOST ENTIRELY UNREAD BY MACHINES. Today only `pins:`, `escape:`,
`layout:`, `type:` and `sourcing:` reach a gate; everything a human learned by
reading 60 pages lands in `gotchas:` — free prose that nothing can check.

The cost is not hypothetical. Every one of these was CORRECTLY WRITTEN DOWN in
a part.yaml and became a defect anyway:

  "PAD 1 IS NEGATIVE - polarity is a PART FACT"   XT60 shipped reversed
  "keep off the JLC-assembly BOM"                 the part reached the BOM
  "no copper under the opto"                      LTV-817S barrier: cooksense
                                                  shipped 0.175 mm of copper
  "MSL 3, 168h floor life"                        the consigned XU316 shipped
                                                  with ZERO MSL text in the
                                                  order paperwork

A fact that is written down and never read is indistinguishable from a fact
nobody knew. `asserts:` makes the part's own facts EXECUTABLE, in the same
spirit as canon E-INV made an ADR's intent executable.

THE `asserts:` BLOCK (02_parts contract; every entry REQUIRES `why:`)
--------------------------------------------------------------------
    asserts:
      - {assert: pad1_net_polarity, pad: 1, polarity: negative,
         why: "XT60 pad 1 is the '-' blade; datasheet fig 2"}
      - {assert: value, equals: 1k, tolerance_pct: 5,
         why: "TI SLVS165O 7.3.4 names 1k explicitly"}
      - {assert: not_on_assembly_bom, why: "THT + stock 0; hand-wired"}
      - {assert: msl, level: 3, floor_life_h: 168,
         why: "consigned; J-STD-033D bake if the bag is open >168h"}
      - {assert: keepout_region, layers: [F.Cu, In1.Cu, In2.Cu, B.Cu],
         region: under_body, why: "5kV isolation barrier, IEC 60950 creepage"}

GRADED HERE (offline, no pcbnew, no network):
  value               the fab BOM's Comment for every ref of this part must
                      decode to the declared value (SI-aware, m != M).
  not_on_assembly_bom no ref of this part may carry a non-blank LCSC on the
                      BOM or appear on the CPL.
  msl                 the release's order paperwork must STATE the MSL level
                      and floor life for this part. Consigned/EP parts ship
                      with a moisture obligation the assembler cannot infer.
  pad1_net_polarity   pad 1's NET, read from the exported netlist, must carry
                      the declared polarity token ('-'/negative nets: GND,
                      *_N, VSS, ...; '+' nets: everything else). Complements
                      canon P2/P-POL, which grades the same fact from the
                      BOARD — two artifacts, one fact (canon M1).

DEFERRED, and named rather than silently missing:
  keepout_region      needs board geometry (copper vs the part's body
                      outline). It is the LTV-817S isolation-barrier class and
                      it is the one this file cannot yet see. Recorded in
                      design-policies.md as the open half of P-FACT.

THE DENOMINATOR IS THE VERDICT (fixed 2026-07-29, canon M-COVER)
----------------------------------------------------------------
MEASURED on pluto-rx2-8way at stage 5: `16 assertion(s) graded`, all 16
reported P-FACT-UNREACHED, final line `P-FACT OK`, exit 0. `graded` was
incremented on ENTRY to the assertion loop, before anything was compared, so
the count that was supposed to be the coverage proof counted the misses too.
That is the `jlc_twin`-exited-0-on-11-unverified-parts shape verbatim, and it
is what canon M-COVER exists to forbid: **a zero denominator is a FAIL.**

Two things changed:
  * `graded` now counts only assertions that REACHED A COMPARISON, `unreached`
    counts the rest, and both numbers are printed on every run — on the OK
    path too, because that is the path where a silent zero did the damage.
  * REFDES RESOLUTION HAPPENS WHERE THE FACT ENTERS (ADR-0007 M-ENTRY). It
    used to be BOM-only, and the fab BOM does not exist until stage 7, so at
    stage 5 every assertion missed its refs — including `pad1_net_polarity`,
    whose evidence artifact (the exported netlist) has been on disk since
    stage 4. The map is now taken from the first artifact that HAS it — fab
    BOM, else `03_tscircuit/build/circuit.json` (`supplier_part_numbers`),
    else the netlist's own `(comp (value "C…"))` — and the run says WHICH.
    On pluto-rx2-8way that turns the two polarity assertions (KT-0603R LED
    and the SMBJ6.0A TVS — the XT60 class) from UNREACHED into graded at the
    placement gate instead of at the order gate.

VACUITY: (canon G-VACUOUS — the input class on which this gate PASSES while the
fact it grades is FALSE, fixtured by `t1_part_facts.py`
`t_vacuity_all_deferred_or_all_config_prints_OK_over_a_zero_denominator`.)

The 2026-07-29 fix closed the case `graded == 0 and unreached > 0`, which now
exits 1 at the `P-FACT GRADED NOTHING` line. It did NOT close the other two ways
to reach a zero denominator, and both still print `P-FACT OK — 0/0 assertions
graded` and exit 0 under default flags:

  * every declared assertion is of a kind this checker cannot yet grade, so each
    lands as `P-FACT-DEFERRED` — neither graded nor unreached. This one is
    deliberate and argued for in the code.
  * every declared assertion is MALFORMED, so each lands as `P-FACT-CONFIG`.
    Measured: a part whose only assertion is `pad1_net_polarity` with
    `polarity: minus` (instead of `negative`) yields
    `P-FACT-CONFIG ... got 'minus'` and then `P-FACT OK — 0/0`, exit 0. A typo
    in a safety-relevant polarity claim therefore reads as a pass, and the
    reversed CE1 electrolytic in this repo's history is what that class costs.

Both block under `--strict`, so the blind spot is exactly: DEFAULT flags, and a
part whose assertions are ALL deferred or ALL malformed. The fixture reproduces
the second case, which is the undocumented one.
"""
import argparse
import csv
import glob
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:                                   # pragma: no cover
    yaml = None

sys.path.insert(0, str(Path(__file__).resolve().parent))

KINDS_GRADED = {"value", "not_on_assembly_bom", "msl", "pad1_net_polarity"}
KINDS_DEFERRED = {"keepout_region"}

#: nets that ARE the negative/return side. Anything else is treated as
#: positive. Deliberately a closed, readable list rather than a heuristic.
NEG_NET = re.compile(r"^(GND\b|AGND|DGND|PGND|VSS|GNDA|0V|VEE|.*_N$|.*-$)",
                     re.I)

_SI = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "μ": 1e-6, "m": 1e-3,
       "R": 1.0, "r": 1.0, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9}
_UNIT_RE = re.compile(r"(ohms?|Ω|Ω|F|H|V|A|W|%)$", re.I)


def parse_si(text):
    """SI-aware value decode. `m` is MILLI and `M` is MEGA — a case-folding
    parser reads a 4.7M resistor as 4.7 milliohms and reports a pass."""
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    s = _UNIT_RE.sub("", s.split()[0].replace(",", ""))
    m = re.fullmatch(r"([0-9]*)([pnuµμmRrkKMG])([0-9]+)", s)
    if m:
        try:
            return float(f"{m.group(1) or '0'}.{m.group(3)}") * _SI[m.group(2)]
        except (ValueError, KeyError):
            return None
    m = re.fullmatch(r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)"
                     r"([pnuµμmRrkKMG]?)", s)
    if not m:
        return None
    try:
        return float(m.group(1)) * (_SI[m.group(2)] if m.group(2) else 1.0)
    except (ValueError, KeyError):
        return None


class ConfigError(Exception):
    """A schema problem — distinct from a graded failure."""


# --------------------------------------------------------------------------
def load_parts(parts_dir):
    """{mpn: {"asserts": [...], "path": Path, "lcsc": str}} for parts that
    declare an `asserts:` block. A part with none is not graded and is
    reported in the coverage line — silence is visible, not assumed clean."""
    out, total = {}, 0
    for f in sorted(Path(parts_dir).glob("*/part.yaml")):
        total += 1
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8-sig")) or {}
        except Exception as e:
            raise ConfigError(f"{f}: unparseable ({e})")
        if not isinstance(d, dict):
            continue
        a = d.get("asserts")
        if not a:
            continue
        if not isinstance(a, list):
            raise ConfigError(f"{f}: 'asserts:' must be a list")
        for i, e in enumerate(a):
            if not isinstance(e, dict):
                raise ConfigError(f"{f}: asserts[{i}] is not a mapping")
            k = e.get("assert")
            if k not in KINDS_GRADED | KINDS_DEFERRED:
                raise ConfigError(
                    f"{f}: asserts[{i}] unknown kind {k!r} "
                    f"(graded: {sorted(KINDS_GRADED)}; deferred: "
                    f"{sorted(KINDS_DEFERRED)})")
            if len(str(e.get("why", "")).strip()) < 5:
                raise ConfigError(
                    f"{f}: asserts[{i}] ({k}) has no substantive 'why:' — a "
                    f"part fact without its reason is the prose gotcha this "
                    f"block exists to replace")
        src = d.get("sourcing") or {}
        out[str(d.get("mpn") or f.parent.name)] = {
            "asserts": a, "path": f,
            "lcsc": str(src.get("lcsc") or d.get("lcsc") or "").strip()}
    return out, total


def load_fab(root):
    """(bom rows, cpl designators, ref->lcsc, ref->comment) from fab/."""
    d = Path(root)
    fab = d / "fab" if (d / "fab").is_dir() else d
    bom_p = next((fab / n for n in ("bom.csv", "bom_jlc.csv")
                  if (fab / n).exists()), None)
    cpl_p = next((fab / n for n in ("cpl.csv", "cpl_jlc.csv")
                  if (fab / n).exists()), None)
    ref_lcsc, ref_comment, cpl = {}, {}, set()
    if bom_p:
        for row in csv.DictReader(open(bom_p, encoding="utf-8-sig")):
            code = (row.get("LCSC") or "").strip()
            com = (row.get("Comment") or "").strip()
            for r in (row.get("Designator") or "").split(","):
                if r.strip():
                    ref_lcsc[r.strip()] = code
                    ref_comment[r.strip()] = com
    if cpl_p:
        for row in csv.DictReader(open(cpl_p, encoding="utf-8-sig")):
            r = (row.get("Designator") or "").strip()
            if r:
                cpl.add(r)
    return ref_lcsc, ref_comment, cpl, bom_p, cpl_p


def load_netlist_pad1(root):
    """{ref: net_on_pad_1} parsed from the exported netlist, text only.

    Deliberately a DIFFERENT artifact from the board that canon P2/P-POL
    grades: two independent readings of one fact (canon M1)."""
    pats = ("06_build/netlists/*.net", "source/*.net", "04_kicad/*.net",
            "*.net")
    hits = []
    for p in pats:
        hits = sorted(glob.glob(str(Path(root) / p)))
        if hits:
            break
    if not hits:
        return {}, None
    text = Path(hits[0]).read_text(encoding="utf-8-sig")
    out = {}
    for m in re.finditer(r'\(net\s+\(code[^)]*\)\s*\(name\s+"([^"]*)"\)'
                         r'(.*?)(?=\n\s*\(net\s+\(code|\Z)', text, re.S):
        net = m.group(1)
        for n in re.finditer(r'\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)',
                             m.group(2)):
            if n.group(2) == "1":
                out.setdefault(n.group(1), net)
    return out, Path(hits[0])


def load_entry_refmap(root):
    """({lcsc_code: [refs]}, artifact_label) from the EARLIEST artifact that
    carries the refdes<->LCSC relation — canon M-ENTRY (ADR-0007): grade a fact
    where it enters the pipeline, not where it shows.

    Used only when there is no fab BOM (before stage 7). Keyed on the LCSC
    CODE, never on a value+footprint match (canon M6: the substitution class).
    """
    d = Path(root)
    for cj in ("03_tscircuit/build/circuit.json",
               "03_tscircuit/dist/src/*/circuit.json"):
        for hit in sorted(glob.glob(str(d / cj))):
            try:
                doc = json.loads(Path(hit).read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            els = doc if isinstance(doc, list) else (doc.get("elements") or [])
            out = {}
            for e in els:
                if not isinstance(e, dict) or e.get("type") != "source_component":
                    continue
                ref = e.get("name")
                for code in ((e.get("supplier_part_numbers")
                              or {}).get("jlcpcb") or []):
                    if ref and code:
                        out.setdefault(str(code).strip(), []).append(str(ref))
            if out:
                return out, str(Path(hit).relative_to(d))
    # last resort: this pipeline's converter writes the LCSC code into the
    # netlist's Value for library parts (U_LDO -> "C638611").
    for pat in ("06_build/netlists/*.net", "04_kicad/*.net", "*.net"):
        for hit in sorted(glob.glob(str(d / pat))):
            text = Path(hit).read_text(encoding="utf-8-sig")
            out = {}
            for m in re.finditer(r'\(comp\s*\(ref\s+"([^"]+)"\)\s*'
                                 r'\(value\s+"(C\d{3,})"\)', text):
                out.setdefault(m.group(2), []).append(m.group(1))
            if out:
                return out, str(Path(hit).relative_to(d))
    return {}, None


def order_text(root):
    """Every word of the release's order paperwork, concatenated."""
    parts = []
    for name in ("ORDER_README.md", "MANIFEST.txt"):
        p = Path(root) / name
        if p.exists():
            parts.append(p.read_text(encoding="utf-8-sig"))
    for p in sorted(Path(root).glob("verification/*.md")):
        parts.append(p.read_text(encoding="utf-8-sig"))
    return "\n".join(parts)


# --------------------------------------------------------------------------
def grade(root, parts_dir, strict=False):
    """Returns (findings, coverage, declaring_parts, total_parts) where
    coverage is {"graded": n, "unreached": n, "refmap": label}.

    `graded` counts assertions that REACHED A COMPARISON. It used to be
    incremented on entry to this loop, which made it count the misses too:
    pluto-rx2-8way printed `16 assertion(s) graded` with 16 UNREACHED under it
    and `P-FACT OK` at the bottom (canon M-COVER — the denominator IS the
    verdict)."""
    parts, total = load_parts(parts_dir)
    ref_lcsc, ref_comment, cpl, bom_p, cpl_p = load_fab(root)
    pad1, netp = load_netlist_pad1(root)
    otext = order_text(root)
    finds, graded, unreached = [], 0, 0

    # LCSC -> refs, so a part's facts reach the refs that ARE it. Keyed on the
    # code, never on a value+footprint match (canon M6: the substitution class).
    by_code = {}
    for r, c in ref_lcsc.items():
        if c:
            by_code.setdefault(c, []).append(r)
    refmap_label = str(bom_p.name) if bom_p else None
    if not by_code:
        # No fab BOM yet (any stage before 7). The relation still exists —
        # earlier, in the artifact where it was authored (M-ENTRY).
        by_code, refmap_label = load_entry_refmap(root)

    def miss(text):
        """One UNREACHED finding, counted."""
        nonlocal unreached
        unreached += 1
        finds.append(("P-FACT-UNREACHED", text))

    def why_no_ref(mpn, p):
        return (f"{mpn}: no refdes carries lcsc "
                f"{p['lcsc'] or '(undeclared in sourcing:)'} — "
                + ("there is no fab BOM and no refdes<->LCSC artifact under "
                   f"{root} at all, so nothing on this board can be resolved "
                   f"to this part (P-FACT grades from stage 7's BOM, or from "
                   f"03_tscircuit/build/circuit.json earlier)"
                   if refmap_label is None else
                   f"{refmap_label} names {len(by_code)} code(s) and this is "
                   f"not one of them")
                + " — an assertion that grades nothing is not a pass")

    for mpn, p in sorted(parts.items()):
        refs = sorted(by_code.get(p["lcsc"], [])) if p["lcsc"] else []
        for e in p["asserts"]:
            kind = e["assert"]
            if kind in KINDS_DEFERRED:
                finds.append(("P-FACT-DEFERRED",
                              f"{mpn}: `{kind}` is DECLARED but this checker "
                              f"cannot yet grade it (needs board geometry) — "
                              f"{e['why'][:90]}"))
                continue

            if kind == "not_on_assembly_bom":
                # THE ONLY assertion whose absence-of-evidence IS the pass —
                # but only against a BOM that exists. Without one there is
                # nothing for the part to be absent FROM.
                if bom_p is None:
                    miss(f"{mpn}: not_on_assembly_bom has no fab BOM to be "
                         f"absent from under {root} — an assembly claim is "
                         f"graded at stage 7, and an empty directory is not "
                         f"a clean BOM")
                    continue
                graded += 1
                bad = [r for r in refs if ref_lcsc.get(r)] + \
                      [r for r in refs if r in cpl]
                if bad:
                    finds.append((
                        "P-FACT", f"{mpn} declares not_on_assembly_bom but "
                        f"{sorted(set(bad))} carry an LCSC on the BOM or sit "
                        f"on the CPL — {e['why'][:90]}"))
                continue

            if kind == "value":
                raw = e.get("equals")
                want = parse_si(raw)
                # ---- STRING MODE (2026-07-28) --------------------------------
                # `equals:` used to be pushed through the SI decoder and
                # NOTHING ELSE, so an MPN operand — `RP2040`, `PE42482A-X`,
                # `TYPE-C-31-M-12A` — decoded to None, emitted a non-blocking
                # P-FACT-CONFIG note and GRADED NOTHING, while the run still
                # printed `P-FACT OK`. Measured before this fix: 11 of 13
                # asserts on pluto-rx2-8way (including both pre-existing
                # exemplars) and 5 on pluto-cal-switch checked nothing at all.
                # That is precisely the class the 02_parts contract names as
                # the REASON `asserts:` exists: a fact written down and never
                # read is indistinguishable from a fact nobody knew.
                #
                # An operand the SI decoder cannot read is not a broken
                # assertion — it is a LITERAL. Comparison is exact after
                # stripping surrounding whitespace, deliberately NOT
                # case-folded or punctuation-normalised: `SS12D07VG6 087` vs
                # `SS12D07VG6-087` is a real drift this fleet has already
                # shipped (ADR-0006/F-ECHO), so a compare loose enough to
                # accept it would re-open the hole it is here to close.
                strmode = want is None and str(raw or "").strip() != ""
                if want is None and not strmode:
                    finds.append(("P-FACT-CONFIG",
                                  f"{mpn}: value assert has no `equals:` at "
                                  f"all ({raw!r})"))
                    continue
                if strmode and "tolerance_pct" in e:
                    finds.append((
                        "P-FACT-CONFIG",
                        f"{mpn}: value assert carries `tolerance_pct:` but "
                        f"`equals: {raw!r}` is not a number — a tolerance on "
                        f"a literal grades nothing; drop it or make the "
                        f"operand numeric"))
                    continue
                tol = float(e.get("tolerance_pct", 0)) / 100.0
                if bom_p is None:
                    miss(f"{mpn}: value assert has no fab BOM to read a "
                         f"Comment from under {root} — the artifact it grades "
                         f"is written at stage 7 (an assertion that grades "
                         f"nothing is not a pass)")
                    continue
                if not refs:
                    miss(f"value assert: {why_no_ref(mpn, p)}")
                    continue
                graded += 1
                for r in refs:
                    if strmode:
                        seen = str(ref_comment.get(r) or "").strip()
                        if seen != str(raw).strip():
                            finds.append((
                                "P-FACT", f"{mpn}/{r}: BOM Comment "
                                f"{ref_comment.get(r)!r}, part.yaml asserts "
                                f"the literal {raw!r} — {e['why'][:90]}"))
                        continue
                    got = parse_si(ref_comment.get(r))
                    if got is None:
                        finds.append((
                            "P-FACT", f"{mpn}/{r}: BOM Comment "
                            f"{ref_comment.get(r)!r} cannot be decoded — a "
                            f"value the gate cannot read is not a pass"))
                    elif abs(got - want) > abs(want) * tol + 1e-12:
                        finds.append((
                            "P-FACT", f"{mpn}/{r}: BOM says "
                            f"{ref_comment.get(r)!r}, part.yaml asserts "
                            f"{e['equals']} — {e['why'][:90]}"))
                continue

            if kind == "msl":
                lvl = str(e.get("level", "")).strip()
                if not lvl:
                    finds.append(("P-FACT-CONFIG",
                                  f"{mpn}: msl assert has no `level:`"))
                    continue
                if not otext:
                    # ORDER PAPERWORK THAT DOES NOT EXIST YET IS NOT A
                    # VIOLATED FACT. This was a hard P-FACT fail either way,
                    # which failed every board at the placement gate for a
                    # document stage 7 writes — the mirror image of the
                    # zero-denominator bug in the same file: a verdict the run
                    # had not earned, pointing the wrong way. A target that
                    # HAS a fab BOM and no paperwork is the real defect (that
                    # is a release), so the two are told apart by the BOM.
                    if bom_p is None:
                        miss(f"{mpn}: declares MSL {lvl} and the target has no "
                             f"order paperwork at all yet (no fab BOM either) "
                             f"— the MSL obligation is graded on the RELEASE, "
                             f"at stage 7")
                        continue
                    graded += 1
                    finds.append((
                        "P-FACT", f"{mpn}: declares MSL {lvl} but the target "
                        f"has NO order paperwork to state it in "
                        f"(ORDER_README.md / MANIFEST.txt)"))
                    continue
                graded += 1
                if not re.search(rf"MSL\s*-?\s*{re.escape(lvl)}\b", otext,
                                 re.I):
                    finds.append((
                        "P-FACT", f"{mpn}: declares MSL {lvl} "
                        f"(floor life {e.get('floor_life_h', '?')}h) and the "
                        f"order paperwork never states it. The assembler "
                        f"cannot infer a moisture obligation — "
                        f"{e['why'][:90]}"))
                continue

            if kind == "pad1_net_polarity":
                want = str(e.get("polarity", "")).strip().lower()
                if want not in ("negative", "positive"):
                    finds.append(("P-FACT-CONFIG",
                                  f"{mpn}: pad1_net_polarity `polarity:` must "
                                  f"be negative|positive, got {want!r}"))
                    continue
                if netp is None:
                    miss(f"{mpn}: pad1_net_polarity declared but no "
                         f"exported netlist found under {root}")
                    continue
                if not refs:
                    miss(f"pad1_net_polarity: {why_no_ref(mpn, p)}")
                    continue
                graded += 1
                for r in refs:
                    net = pad1.get(r)
                    if net is None:
                        finds.append(("P-FACT",
                                      f"{mpn}/{r}: pad 1 is not in the "
                                      f"netlist — cannot carry a polarity"))
                        continue
                    got = "negative" if NEG_NET.match(net) else "positive"
                    if got != want:
                        finds.append((
                            "P-FACT", f"{mpn}/{r}: pad 1 is on net {net!r} "
                            f"({got}) but part.yaml asserts pad 1 is {want} — "
                            f"{e['why'][:90]}. THIS IS THE XT60 CLASS: the "
                            f"netlist is self-consistent either way, so no "
                            f"electrical check can see it"))
                continue

    return (finds, {"graded": graded, "unreached": unreached,
                    "refmap": refmap_label}, len(parts), total)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target", help="a project dir or a sealed release dir")
    ap.add_argument("--parts", default="",
                    help="02_parts dir (default: <target>/02_parts, else the "
                         "project the release belongs to)")
    ap.add_argument("--strict", action="store_true",
                    help="a DEFERRED or UNREACHED assertion is also a failure")
    args = ap.parse_args(argv)
    if yaml is None:
        print("P-FACT LOAD ERROR: PyYAML not available")
        return 2

    root = Path(args.target)
    pd = Path(args.parts) if args.parts else None
    if pd is None:
        for cand in [root / "02_parts"] + [a / "02_parts" for a in root.parents]:
            if cand.is_dir():
                pd = cand
                break
    if pd is None or not pd.is_dir():
        print(f"P-FACT N-A: no 02_parts/ found for {root}")
        return 0

    try:
        finds, cov, declaring, total = grade(root, pd, args.strict)
    except ConfigError as e:
        print(f"P-FACT LOAD ERROR: {e}")
        return 2

    hard = [f for f in finds if f[0] == "P-FACT"]
    soft = [f for f in finds if f[0] != "P-FACT"]
    graded, unre = cov["graded"], cov["unreached"]
    print(f"P-FACT: {declaring}/{total} part.yaml declare an `asserts:` block; "
          f"{graded}/{graded + unre} assertion(s) REACHED A COMPARISON against "
          f"{root} ({unre} unreached; refdes<->LCSC read from "
          f"{cov['refmap'] or 'NOTHING'})")
    for fid, text in finds:
        print(f"  {fid}: {text}")
    if hard or (args.strict and soft):
        print(f"P-FACT FAIL: {len(hard)} violated part fact(s)"
              + (f", {len(soft)} ungraded (strict)" if args.strict and soft
                 else ""))
        return 1
    if declaring == 0:
        print("P-FACT: nothing declared, so nothing was proved. This is the "
              "state that let 'PAD 1 IS NEGATIVE', 'keep off the "
              "JLC-assembly BOM', 'no copper under the opto' and 'MSL 3' all "
              "become defects while written down correctly.")
        return 0
    if graded == 0 and unre > 0:
        # A ZERO DENOMINATOR IS A FAIL, NEVER AN OK (canon M-COVER). Measured
        # on pluto-rx2-8way before this: 16 assertions, 16 unreached, `P-FACT
        # OK`, exit 0 — the exact shape of jlc_twin exiting 0 on 11 unverified
        # parts. It is NOT gated on --strict: `--strict` decides whether a
        # PARTIAL denominator blocks, and there is nothing partial about zero.
        # Guarded on `unre > 0` and not on `graded == 0` alone: a part that
        # declares ONLY a DEFERRED kind (`keepout_region`) has no gradeable
        # assertion to have a denominator over, and it already reports itself
        # by name and blocks under --strict. Failing that would be the same
        # error in the other direction.
        print(f"P-FACT GRADED NOTHING: {declaring} part.yaml declare "
              f"{unre} assertion(s) and NOT ONE of them reached a comparison "
              f"against {root}. A gate with no denominator cannot report OK "
              f"(canon M-COVER); every reason is listed above.")
        return 1
    print(f"P-FACT OK — {graded}/{graded + unre} assertions graded"
          + (f", {unre} UNREACHED and listed above (a partial denominator: "
             f"use --strict to make it block)" if unre else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
