#!/usr/bin/env python3
"""net_reference_audit — E-NETREF: every net name a RULE FILE, a PART DOSSIER or
a FLOORPLAN references must EXIST in the netlist.

    python3 net_reference_audit.py PROJECT_DIR
    python3 net_reference_audit.py PROJECT_DIR --netlist path.net   # override
    python3 net_reference_audit.py --root REPO_ROOT                 # fleet sweep

WHY THIS EXISTS, AND WHY IT IS NOT A `supplies:` CHECK.

A net name written in hand-authored source is a REFERENCE: some gate, generator
or fab artifact will look it up. When the lookup misses, almost nothing in this
repo says so out loud — the reference silently grades, generates or prints
NOTHING, and the surrounding verdict stays green. MEASURED on smc0985-cooksense
v1.7 (2026-07-29): **10 of 123 net names referenced by its rule files and
dossiers are not nets on that board**, and three of the ten had already been
paid for:

  1. THE SILK PRINTED A GHOST. A keypad caption read "KEYPAD ISOLATION COMB
     >=6mm creepage GND_ISO ONLY". `grep -c GND_ISO` on `cooksense.net` is 0;
     the only ISO-bearing net name on the board is `SPI_MISO`, which matches
     `GND_ISO` only by SUBSTRING. It reached the shipped F.Silkscreen and two
     release documents, and it reversed a proposed v1.4 fix that would have
     bonded a tab 0.581 mm from keypad copper against a 6.000 mm requirement.
  2. A SAFETY-RELEVANT BUDGET WAS UNENFORCEABLE AND READ AS COVERED.
     `02_parts/TPS259573DSGR/part.yaml` addresses its eFuse input-decoupling
     `keep_short` to `5V_SELV` — not a net on this board. `5V_IN`, `5V_FUSED`
     and `5V_RPP` are the real input-side rails and none of them was graded.
  3. A WHOLE SUPPLY RAIL WAS INVISIBLE TO A GRADER. `supplies: {N3V3: 3.3}`
     named the tsx AUTHOR-PREFIX form of a net the netlist calls `3V3`.

Case 3 was closed narrowly in `electrical_invariants.py` (fa22228) by checking
ONE FIELD. That fix is correct and it STAYS; this gate is the general one, and
the reason it exists is canon M-WIDTH: **which reference sites are safe is a
fact about the tree, not about the schema.** So the sites are ENUMERATED by
reading the consumers, and the denominator is PRINTED — a gate that covers 3 of
11 reference kinds and reports OK is the vacuous pass this repo keeps
rediscovering (canon M-COVER).

THE ELEVEN REFERENCE KINDS (the denominator; `--kinds` prints it):

  nets.yaml           K1  classes.<C>.nets[]            netclass pattern
                      K2  scoped_floors[].nets[]        DRU insideArea clause
  electrical_
    invariants.yaml   K3  supplies.<NET>                node_level rail map
                      K4  invariants[].net              pin_on_net/net_has_part/
                                                        node_level subject
                      K5  invariants[].chain[]          series_chain net element
  power_tree.yaml     K6  rails[].name,                 rail LABEL (advisory)
                          linear_rails[].name
  02_parts/*/
    part.yaml         K7  layout.keep_short[].net       P-ADJ span budget
  floorplan.yaml      K8  zones[].net                   copper pour net
                      K9  asserts.pad_net[].net         pad-net assertion
                      K10 placement.patterns[]
                            .pad_overrides[].on_net     pad-override selector
                      K11 silk.captions[].text          net-shaped PROSE token

HOW A MISS IS CLASSIFIED — THE HARD PART IS NOT FINDING THEM.

A name absent from the netlist is not automatically an error. A board may be
mid-pipeline; a rule may deliberately cover a net some sibling board carries.
Failing every such reference produces a gate that gets waived into uselessness,
and passing them produces the silence this file was written to end. So each
reference resolves into exactly one of three classes, and all three are
PRINTED:

  RESOLVED   the name (or, for K1, the glob PATTERN) matches >= 1 net.
  GHOST      absent AND the reference was supposed to grade, generate or print
             something. This FAILS (exit 1). K1/K2/K3/K4/K5/K7/K8/K9/K10 and
             the K11 prose tokens are all in this class: each one is consumed by
             a named piece of code that will now quietly do nothing.
  UNREACHED  absent, and NOTHING was going to resolve it against the netlist
             anyway, so calling it a defect would be a false lead. Exactly one
             kind is here by construction: K6. `power_topology.py` grades a
             rail's NUMBERS (`vin_*`/`vout_*`/`iout_max_A`/`converter`) and
             never looks its `name:` up as a net — cooksense legitimately
             writes `name: 3V3_SW_A / 3V3_SW_B / 3V3_SW_RHA / 3V3_SW_RHE` for
             four load-switch rails with one envelope, and usb-hub-3s-v3
             writes `name: USB-A` for a port bank. UNREACHED is also where a
             board with NO netlist yet lands — the whole audit, named as such,
             never a zero.

NEAR-MISS DIAGNOSIS IS MOST OF THE VALUE. `N3V3` -> `3V3` and `5V_SELV` -> the
real input rail are each one edit away, and a verdict that names the candidate
turns a hunt into a fix. Four independent hint sources are tried, in order of
how much they say: case-fold, the tsx author-prefix `N` (add AND strip, counted
separately because it is a SYSTEMATIC TRAP — authors read net names off the tsx
source where they carry a prefix the netlist does not), difflib similarity, and
the net FAMILY sharing the first underscore token.

MATCHING IS EXACT (or explicit glob), NEVER SUBSTRING. `GND_ISO` survived
review because something matched it against `SPI_MISO`, and a containment test
is how that happens: every net name on a board is a substring of some other
string. K1 alone honours `*`/`?`, because KiCad netclass PATTERNS are globs and
`generate_rules_generic.py` writes them through verbatim.

INDEPENDENCE (canon M1). The oracle is the exported `.net` file, read here with
a small dedicated regex over the `(nets ...)` section — NOT through
`electrical_invariants.py`'s s-expression tokenizer, and not through pcbnew.
The checked artifacts are hand-written YAML; nothing that produced them
contributes to the answer.

NOT YET WIRED INTO `policy_audit.py`, DELIBERATELY, AND THAT IS A GAP.
This gate is landed with its tests and its canon row but is NOT called by the
policy audit, so no board's `policy_audit.md` reports E-NETREF yet. The reason
is scheduling, not doubt: at landing time (2026-07-29) the first fleet sweep
measured 64 ghosts over 908 reference sites and FOUR of six boards fail —
including smc0985-cooksense, which was mid-fix-and-rebuild on three
order-blockers with a review battery in flight, and pluto-rx2-8way, which was
under active edit. Turning four boards red inside another agent's evidence run
corrupts that evidence; an unwired gate plus a measurement is recoverable in one
follow-up. **The follow-up is owed:** add an `E-NETREF` row beside `E-INV` in
`policy_audit.py`'s electrical block (`net_reference_audit.py PROJECT_DIR`, exit
0 = PASS, 2 = UNGRADED not N-A) once the boards are quiet, and expect it to
FAIL on crow-mic-pod-v2, crow-recorder-central-v2, pluto-rx2-8way and
smc0985-cooksense until their `keep_short` budgets are re-addressed. Until then
run it by hand; the canon row and this file are the authority, and
`--root REPO` is the census.

Exit 0 when every reference resolves (UNREACHED does not fail), 1 on any GHOST,
2 when the audit itself could not run (unparseable source — never a zero).
"""
import argparse
import difflib
import fnmatch
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:                                       # pragma: no cover
    sys.exit("net_reference_audit needs pyyaml")

#: the (nets ...) section of a KiCad netlist. `\s+` between the atoms because
#: kicad-cli pretty-prints one atom per line; a single-line export matches too.
NET_RE = re.compile(r'\(net\s+\(code\s+"?\d+"?\)\s*\(name\s+"([^"]*)"\)')
#: components, so a REFDES in prose is not misread as a ghost net (K11).
COMP_RE = re.compile(r'\(comp\s+\(ref\s+"([^"]*)"\)')

#: a NET-SHAPED token inside prose: upper-case/digit runs joined by at least
#: one underscore. Requiring the underscore is what keeps K11 quiet — measured
#: over all 93 fleet captions it yields 2 tokens, `SPI_MISO`-shaped, not the
#: 400-odd English words a looser pattern would hand back.
PROSE_TOK = re.compile(r'\b[A-Z0-9]+(?:_[A-Z0-9]+)+\b')

#: reference kinds, in report order: id -> (where, jsonpath, consumer, hard?)
#: `hard=False` means a miss is UNREACHED, not a GHOST — see the module
#: docstring. Adding a kind here without a consumer is not allowed: the
#: consumer column is the ARGUMENT that a miss costs something.
KINDS = {
    "K1":  ("nets.yaml", "classes.<C>.nets[]",
            "generate_rules_generic.py -> .kicad_pro netclass_patterns", True),
    "K2":  ("nets.yaml", "scoped_floors[].nets[]",
            "generate_rules_generic.py -> .kicad_dru insideArea clause", True),
    "K3":  ("electrical_invariants.yaml", "supplies.<NET>",
            "electrical_invariants.py _grade_node_level rail map", True),
    "K4":  ("electrical_invariants.yaml", "invariants[].net",
            "electrical_invariants.py pin_on_net/net_has_part/node_level", True),
    "K5":  ("electrical_invariants.yaml", "invariants[].chain[]",
            "electrical_invariants.py _grade_series_chain", True),
    "K6":  ("power_tree.yaml", "rails[].name, linear_rails[].name",
            "power_topology.py (LABEL only — no net lookup)", False),
    "K7":  ("02_parts/*/part.yaml", "layout.keep_short[].net",
            "policy_audit.py P-ADJ net-span budget", True),
    "K8":  ("floorplan.yaml", "zones[].net",
            "generate_board_generic.py copper pour", True),
    "K9":  ("floorplan.yaml", "asserts.pad_net[].net",
            "generate_board_generic.py pad-net assertion", True),
    "K10": ("floorplan.yaml", "placement.patterns[].pad_overrides[].on_net",
            "generate_board_generic.py pad override selector", True),
    "K11": ("floorplan.yaml", "silk.captions[].text (net-shaped token)",
            "generate_board_generic.py -> F.Silkscreen", True),
}


class AuditError(Exception):
    """The audit could not run. Exit 2 — never a silent zero (canon M-COVER)."""


# --------------------------------------------------------------------- oracle
def read_nets(path):
    """{net names} and {refdes} from a KiCad netlist, by regex.

    Deliberately NOT the electrical_invariants tokenizer: canon M1 wants the
    oracle read by a method the checked side does not share, and a 2-regex read
    of the `(nets ...)` section cannot inherit a parser bug from the gate whose
    narrow `supplies:` case this widens.
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    nets = set(NET_RE.findall(text))
    if not nets:
        raise AuditError(f"{path}: no (net (code ..) (name ..)) entries — the "
                         f"netlist is empty or not a KiCad netlist; refusing "
                         f"to grade 0 references against 0 nets")
    return nets, set(COMP_RE.findall(text))


def load_yaml(path):
    try:
        d = yaml.safe_load(Path(path).read_text(encoding="utf-8-sig"))
    except Exception as e:                                # noqa: BLE001
        raise AuditError(f"{path}: unparseable YAML ({e})")
    return d if isinstance(d, dict) else {}


# ------------------------------------------------------------------ near-miss
def near_miss(name, nets):
    """Ordered hints for a name that is not a net. Most-specific first.

    The four sources answer four different author mistakes, and naming WHICH
    one fired is the difference between a fix and a hunt.
    """
    hits = []
    upper = {}
    for n in nets:
        upper.setdefault(n.upper(), n)
    u = name.upper()
    if u in upper and upper[u] != name:
        hits.append((upper[u], "case differs"))
    # THE TSX AUTHOR-PREFIX TRAP, both directions. Authors read net names off
    # the tsx source, where a net carries a leading `N` the converter strips.
    if u.startswith("N") and u[1:] in upper:
        hits.append((upper[u[1:]], "tsx author-prefix `N` — strip it"))
    if ("N" + u) in upper:
        hits.append((upper["N" + u], "tsx author-prefix `N` — the netlist "
                                    "carries it"))
    for c in difflib.get_close_matches(name, sorted(nets), n=3, cutoff=0.7):
        if c not in [h[0] for h in hits]:
            hits.append((c, "similar name"))
    if not hits:
        fam = name.split("_")[0]
        sibs = sorted(n for n in nets if n.split("_")[0] == fam)[:4]
        if sibs and fam:
            hits.append((", ".join(sibs), f"the {fam}_* family on this board"))
    return hits[:4]


def hint_text(name, nets):
    hits = near_miss(name, nets)
    if not hits:
        return " No net with a similar name exists either."
    return " Did you mean " + "; ".join(f"{c!r} ({why})" for c, why in hits) + "?"


# ------------------------------------------------------------------ collection
class Ref:
    __slots__ = ("kind", "site", "name", "glob")

    def __init__(self, kind, site, name, glob=False):
        self.kind, self.site, self.name, self.glob = kind, site, name, glob


def _str(v):
    return v if isinstance(v, str) else None


def collect_rules(rules_dir, refs):
    nets_y = rules_dir / "nets.yaml"
    if nets_y.is_file():
        d = load_yaml(nets_y)
        for cname, c in (d.get("classes") or {}).items():
            if not isinstance(c, dict):
                continue
            for i, n in enumerate(c.get("nets") or []):
                s = _str(n)
                if s:
                    refs.append(Ref("K1", f"nets.yaml classes.{cname}.nets[{i}]",
                                    s, glob=bool(set("*?[") & set(s))))
        for i, sf in enumerate(d.get("scoped_floors") or []):
            if not isinstance(sf, dict):
                continue
            for j, n in enumerate(sf.get("nets") or []):
                s = _str(n)
                if s:
                    refs.append(Ref("K2",
                                    f"nets.yaml scoped_floors[{i}].nets[{j}]",
                                    s))

    inv_y = rules_dir / "electrical_invariants.yaml"
    if inv_y.is_file():
        d = load_yaml(inv_y)
        sup = d.get("supplies")
        if isinstance(sup, dict):
            for k in sup:
                s = _str(k) or str(k)
                refs.append(Ref("K3", f"electrical_invariants.yaml "
                                      f"supplies.{s}", s))
        for i, inv in enumerate(d.get("invariants") or []):
            if not isinstance(inv, dict):
                continue
            s = _str(inv.get("net"))
            if s:
                refs.append(Ref("K4", f"electrical_invariants.yaml "
                                      f"invariants[{i}].net "
                                      f"(assert={inv.get('assert')})", s))
            for j, e in enumerate(inv.get("chain") or []):
                s = _str(e)
                if s:
                    # a chain element is a net OR a refdes; resolved against
                    # both, so a part name is not reported as a ghost net.
                    refs.append(Ref("K5", f"electrical_invariants.yaml "
                                          f"invariants[{i}].chain[{j}]", s))

    pt_y = rules_dir / "power_tree.yaml"
    if pt_y.is_file():
        d = load_yaml(pt_y)
        for key in ("rails", "linear_rails"):
            for i, r in enumerate(d.get(key) or []):
                if not isinstance(r, dict):
                    continue
                s = _str(r.get("name"))
                if not s:
                    continue
                # one envelope may legitimately label several sibling rails
                for tok in [t.strip() for t in s.split("/")]:
                    if tok:
                        refs.append(Ref("K6", f"power_tree.yaml "
                                              f"{key}[{i}].name", tok))


def collect_parts(parts_dir, refs):
    for py in sorted(parts_dir.glob("*/part.yaml")):
        d = load_yaml(py)
        lay = d.get("layout")
        if not isinstance(lay, dict):
            continue
        for i, ks in enumerate(lay.get("keep_short") or []):
            if not isinstance(ks, dict):
                continue          # prose budget: policy_audit reports it, not us
            s = _str(ks.get("net"))
            if s:
                refs.append(Ref("K7", f"02_parts/{py.parent.name}/part.yaml "
                                      f"layout.keep_short[{i}].net", s))


def caption_texts(fp):
    """Caption text in both shipped shapes: a mapping with `text:`, and the
    bare `[text, x, y]` list form that four boards use."""
    out = []
    for i, c in enumerate((fp.get("silk") or {}).get("captions") or []):
        if isinstance(c, dict):
            t = _str(c.get("text"))
        elif isinstance(c, list) and c:
            t = _str(c[0])
        else:
            t = _str(c)
        if t:
            out.append((i, t))
    return out


def collect_floorplan(path, rel, refs):
    d = load_yaml(path)
    for i, z in enumerate(d.get("zones") or []):
        if not isinstance(z, dict):
            continue
        s = _str(z.get("net"))
        if s:
            refs.append(Ref("K8", f"{rel} zones[{i}].net", s))
    for i, a in enumerate((d.get("asserts") or {}).get("pad_net") or []):
        if not isinstance(a, dict):
            continue
        s = _str(a.get("net"))
        if s:
            refs.append(Ref("K9", f"{rel} asserts.pad_net[{i}].net "
                                  f"({a.get('ref')}.{a.get('pad')})", s))
    for i, p in enumerate((d.get("placement") or {}).get("patterns") or []):
        if not isinstance(p, dict):
            continue
        for j, ov in enumerate(p.get("pad_overrides") or []):
            if not isinstance(ov, dict):
                continue
            s = _str(ov.get("on_net"))
            if s:
                refs.append(Ref("K10", f"{rel} placement.patterns[{i}]"
                                       f".pad_overrides[{j}].on_net", s))
    for i, text in caption_texts(d):
        for tok in dict.fromkeys(PROSE_TOK.findall(text)):
            refs.append(Ref("K11", f"{rel} silk.captions[{i}].text "
                                   f"({text[:40]!r})", tok))


def floorplans(proj):
    """Hand-written floorplans only. `06_build/` holds regenerated proof copies
    and sealed `04_kicad`/`07_releases` are IMMUTABLE — neither is source."""
    out = []
    for pat in ("03_src/floorplan.yaml", "03_src/*/floorplan.yaml"):
        for p in sorted(proj.glob(pat)):
            if p.resolve() not in [q.resolve() for q in out]:
                out.append(p)
    return out


def netlists(proj):
    d = proj / "06_build" / "netlists"
    return sorted(d.glob("*.net")) if d.is_dir() else []


# -------------------------------------------------------------------- grading
def grade(proj, netlist_override=None):
    """-> (rows, ghosts, unreached, notes, nets, comps). Raises AuditError."""
    proj = Path(proj)
    refs = []
    rules = proj / "03_src" / "rules"
    if rules.is_dir():
        collect_rules(rules, refs)
    parts = proj / "02_parts"
    if parts.is_dir():
        collect_parts(parts, refs)
    fps = floorplans(proj)
    for fp in fps:
        collect_floorplan(fp, str(fp.relative_to(proj)), refs)

    nl = [Path(netlist_override)] if netlist_override else netlists(proj)
    notes, parts_of = [], []
    nets, comps = set(), set()
    for n in nl:
        # A project may export SEVERAL netlists (cooksense's main board + its
        # interposer; usb-hub-3s-v3's v1.12 variants). 02_parts and the rule
        # files are SHARED across them, so the resolvable universe is the
        # UNION — the conservative direction, which cannot invent a ghost.
        a, b = read_nets(n)
        nets |= a
        comps |= b
        parts_of.append(f"{n.name} ({len(a)} nets)")
    notes.append(f"netlist(s): {', '.join(parts_of) or 'NONE'} -> "
                 f"{len(nets)} distinct nets, {len(comps)} refdes")

    rows, ghosts, unreached = {}, [], []
    for k in KINDS:
        rows[k] = [0, 0, 0, 0, 0]     # found, resolved, ghost, unreached, near

    if not nl:
        # THE WHOLE AUDIT IS UNREACHED, AND IT SAYS SO. A board before its
        # first netlist export has references nothing could resolve; reporting
        # every one as a ghost is the failure mode that gets a gate waived.
        for r in refs:
            rows[r.kind][0] += 1
            rows[r.kind][3] += 1
            unreached.append(f"[{r.kind}] {r.site}: {r.name!r} — no netlist "
                             f"exported yet (06_build/netlists/*.net absent), "
                             f"so NOTHING here is graded")
        return rows, ghosts, unreached, notes, nets, comps

    for r in refs:
        rows[r.kind][0] += 1
        if r.glob:
            if fnmatch.filter(sorted(nets), r.name):
                rows[r.kind][1] += 1
                continue
            rows[r.kind][2] += 1
            ghosts.append(f"[{r.kind}] {r.site}: netclass PATTERN {r.name!r} "
                          f"matches NO net on this board, so the class it "
                          f"names has no members and its width/clearance floor "
                          f"is enforced on nothing."
                          + hint_text(r.name.strip("*?[]"), nets))
            continue
        # K5 chain elements and K11 prose tokens may legitimately be a REFDES.
        if r.name in nets or (r.kind in ("K5", "K11") and r.name in comps):
            rows[r.kind][1] += 1
            continue
        hits = near_miss(r.name, nets)
        # A NAMED NEAR-MISS IS A DIFFERENT FINDING FROM A NAMELESS ONE, and the
        # split is counted because the two need different fixes. `N3V3`->`3V3`
        # and `5V_SELV`->the 5V_* family are ONE EDIT away, so the verdict is a
        # fix. A ghost with NO candidate is almost always a budget written
        # against the DATASHEET's reference-design pin function (`VCC`, `VDD`,
        # `D+`, `dVdt`) rather than a net this board ever had — the fix there is
        # to re-address it to the real node or drop it, not to spell it better.
        if hits:
            rows[r.kind][4] += 1
        if not KINDS[r.kind][3]:
            rows[r.kind][3] += 1
            unreached.append(
                f"[{r.kind}] {r.site}: {r.name!r} is not a net on this board — "
                f"reported, NOT failed: {KINDS[r.kind][2]}, so nothing was "
                f"going to resolve it." + hint_text(r.name, nets))
            continue
        rows[r.kind][2] += 1
        ghosts.append(f"[{r.kind}] {r.site}: {r.name!r} is NOT a net on this "
                      f"board, and {KINDS[r.kind][2]} will now silently grade/"
                      f"emit nothing for it." + hint_text(r.name, nets))
    return rows, ghosts, unreached, notes, nets, comps


def report(proj, rows, ghosts, unreached, notes, out=print):
    found = sum(v[0] for v in rows.values())
    res = sum(v[1] for v in rows.values())
    gh = sum(v[2] for v in rows.values())
    un = sum(v[3] for v in rows.values())
    near = sum(v[4] for v in rows.values())
    out(f"E-NETREF net-reference audit — {Path(proj).name}")
    for n in notes:
        out(f"  {n}")
    out(f"  {found} reference site(s) across {len(KINDS)} kinds: "
        f"{res} resolved, {gh} GHOST, {un} unreached; "
        f"{near}/{gh + un} unresolved names carry a NAMED near-miss")
    out(f"  {'kind':<5} {'found':>5} {'resd':>5} {'ghost':>5} {'unre':>5} "
        f"{'near':>5}  where / path")
    for k, (where, path, _consumer, hard) in KINDS.items():
        f, r, g, u, nm = rows[k]
        out(f"  {k:<5} {f:>5} {r:>5} {g:>5} {u:>5} {nm:>5}  {where} {path}"
            + ("" if hard else "   [advisory kind: a miss is UNREACHED]"))
    for label, items in (("GHOST", ghosts), ("UNREACHED", unreached)):
        if items:
            out(f"  {label} ({len(items)}):")
            for m in items:
                out(f"    {m}")
    out(f"E-NETREF: {'FAIL' if gh else 'PASS'} — {res}/{found} references "
        f"resolved, {gh} ghost ({near} with a named near-miss), "
        f"{un} unreached")
    return gh


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project", nargs="?")
    ap.add_argument("--netlist", help="grade against this netlist instead of "
                                      "06_build/netlists/*.net")
    ap.add_argument("--root", help="fleet sweep over ROOT/projects/*")
    ap.add_argument("--kinds", action="store_true",
                    help="print the reference-kind denominator and exit")
    a = ap.parse_args(argv)

    if a.kinds:
        for k, (where, path, consumer, hard) in KINDS.items():
            print(f"{k:<5} {'HARD ' if hard else 'ADVIS'} {where:<28} {path}"
                  f"\n            consumer: {consumer}")
        return 0

    targets = []
    if a.root:
        targets = [p for p in sorted((Path(a.root) / "projects").glob("*"))
                   if p.is_dir()]
    elif a.project:
        targets = [Path(a.project)]
    else:
        ap.error("give a PROJECT_DIR or --root")

    worst = 0
    for t in targets:
        try:
            rows, gh, un, notes, _n, _c = grade(t, a.netlist)
        except AuditError as e:
            print(f"E-NETREF: UNGRADED — {e}")
            worst = max(worst, 2)
            continue
        if report(t, rows, gh, un, notes):
            worst = max(worst, 1)
        if len(targets) > 1:
            print()
    return worst


if __name__ == "__main__":
    sys.exit(main())
