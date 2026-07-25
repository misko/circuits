#!/usr/bin/env python3
"""RELEASE-ARTIFACT FRESHNESS gate.

A release seal must ship the CURRENT board's own outputs, a manifest whose
claimed result matches the audit it bundles, and a FINAL (not draft) order
README. This gate FAILS a seal on three ways that combination has silently
broken in the past — each one a DO-NOT-ORDER defect no other gate caught.

Motivating incident (usb-hub-3s-v3 v1.2, 2026-07-23 — a redesigned board):

  (a) STALE ARTIFACT. pdf/assembly_back.pdf, pdf/assembly_front.pdf and
      pdf/pcb_layers.pdf were BYTE-IDENTICAL (sha256-confirmed) to the PRIOR
      release v1.1's same-named files — the redesigned board shipped the OLD
      board's fab drawings. A changed board's generated fab/PDF outputs MUST
      differ from an earlier release of the same board.

  (b) AUDIT / MANIFEST DISAGREEMENT. The shipped verification/policy_audit.md
      said "M-BOM FAIL" / "Summary: FAIL=1", while the MANIFEST claimed
      "policy_audit: 0 FAIL" and "M-BOM ... PASS". The bundle contradicted its
      own claimed result — the manifest under-reported the audit it ships.

  (c) DRAFT README. The shipped ORDER_README.md was a working draft
      ("> DRAFT for the v1.2 seal", "fold its verdict in before seal") — a
      pre-seal staging document, not the final order document.

Second motivating incident (crow-recorder-central-v2 v1.0, 2026-07-23 —
found 2026-07-24, AFTER sealing):

  (d) MANIFEST SELF-INCONSISTENCY. The manifest's human-readable gate
      summary disagreed with the machine evidence it SHIPS, three ways at
      once, and no gate caught any of them:
        - MANIFEST said "ERC 0 errors (1409 baselined warnings)" while the
          bundled verification/policy_audit.md said "S-ERC PASS 0 errors
          (1215 warnings)" (the bundled erc.json measures 1409 — the audit
          row was the stale one);
        - MANIFEST said "bom_source_check PASS (48 lines...)" while
          fab/bom.csv actually carries 49 data rows;
        - verification/bom_source_check.txt named
          "07_releases/v1.0-2026-07-23/fab/bom.csv" — a directory that is
          NOT this release's sealed name
          (crow-recorder-central-v2-v1.0-2026-07-23): the evidence was
          produced against a staging path and never re-pointed.
      Check (b) compares only the policy_audit RESULT, and the stale check
      compares only bytes across releases — prose counts and embedded paths
      had no gate. Check (d) closes that: any COUNT the MANIFEST states
      that is also present in shipped evidence must MATCH (ERC errors /
      warnings across MANIFEST, policy_audit.md's S-ERC row, and erc.json;
      bom_source_check's claimed line count vs fab/bom.csv's actual data
      rows), and any 07_releases/<dir>/ path embedded in verification
      evidence must name THIS release's directory (or an EXISTING sibling
      release — diffing against a real predecessor is legitimate). A count
      the MANIFEST does not state is not checked: absence != mismatch.

Fifth check — A-STOCK, always on (2026-07-25, the PCBA-default posture):

  (e) STOCK EVIDENCE THAT DOES NOT PASS. Five sealed releases in this fleet
      ship `verification/stock_check.*` whose LAST LINE says FAIL —
      crow-recorder-central-v2 v1.0-v1.3 record their own CPU (C6938291, the
      XU316 SoC) at LOW_STOCK(0) — because nothing ever parsed the verdict.
      Check (e) grades the shipped evidence for every coded BOM line that has
      a CPL row: stock >= qty x `build_quantity`, or a matching
      `03_src/rules/assembly.yaml` `sourcing_plan:` entry with
      `measured_stock` + `measured_on`. A MISSING OR UNPARSEABLE VERDICT IS A
      FAIL, NOT A SKIP: cooksense v1.1 ships a raw `--out` CSV report as
      stock_check.txt with ZERO verdict lines, so a parser that shrugged at an
      unfamiliar shape could be silenced by choosing a shape. The check is
      OFFLINE — it grades EVIDENCE; live re-query stays in the opt-in --net
      tier, because a gate that needs the network is a gate that gets skipped.

Usage:
    release_freshness_check.py <release_dir> [--releases-root DIR]
                               [--assembly 03_src/rules/assembly.yaml]
                               [--allow-identical RELPATH ]...
    release_freshness_check.py <release_dir> --docs-only-supersede PRIOR_DIR

DOCS-ONLY SUPERSEDE MODE (--docs-only-supersede <prior-release-dir>):
a documentation-only supersede release (usb-hub-3s-v3 v1.4, 2026-07-23)
INTENTIONALLY ships its fab outputs byte-identical to its predecessor — the
board did not change, only the documentation did. The default stale check
would flag exactly that identity as a defect. In this mode the declared
identity is ASSERTED instead of flagged:

  - fab/, source/, 3d/ MUST be byte-identical to the prior release (any
    differing, missing, or added file is a FAIL — a "docs-only" release
    that changes fab is lying about being docs-only);
  - pdf/ identical to the prior release is ALLOWED (not flagged);
  - the order README and MANIFEST MUST DIFFER from the prior release's (a
    supersede that changes no document supersedes nothing);
  - checks (b) audit==manifest and (c) no draft markers still run.

`<release_dir>` is one sealed release directory,
`07_releases/<version>-<date>/`. Earlier releases of the SAME board are its
siblings under `07_releases/` with a strictly-lower version; they are read
READ-ONLY for the stale comparison. Exit 0 = fresh, non-zero = a defect that
must block the seal.

Documented exception mechanism (for a legitimately-unchanged file across a
doc-only re-release — the edge case): list the relative path, WITH a reason,
one per line in `<release_dir>/verification/freshness_exceptions.txt`
(`pdf/schematic.pdf   reason: doc-only re-release, board unchanged`), or pass
`--allow-identical pdf/schematic.pdf`. An exception without a reason in the
file is itself rejected — a waiver needs evidence, not a bare path.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

# Generated fab/drawing artifacts whose bytes MUST change for a changed board.
# Compared subtrees; within them every file is a generated output.
_ARTIFACT_DIRS = ("pdf", "fab")

# README draft / placeholder markers. Word-bounded, case-insensitive.
_DRAFT_MARKERS = ("DRAFT", "TODO", "TBD", "FIXME", "WIP",
                  "PLACEHOLDER", "XXX", "FILL ME", "FILL-ME")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# Release dir name -> (board-prefix, version). Two shapes exist in the fleet:
#   bare            v1.2-2026-07-23
#   board-prefixed  cooksense-v1.1-2026-07-24 / crow-recorder-central-v2-v1.0-…
# The greedy board group makes the LAST v-token before the date the release
# version, so a board name that itself ends in -v2 (crow-recorder-central-v2)
# parses as board='crow-recorder-central-v2', ver=1.0 — not ver=2.
# HISTORY: the original regex was ^v(...) only, so EVERY board-prefixed
# release silently skipped the stale-artifact check (a) — the same silent-skip
# class as the M-REL glob bug. Found 2026-07-24.
_NAME_RE = re.compile(r"^(?:(?P<board>.+)-)?v(?P<ver>\d+(?:\.\d+)*)(?=-|$)")


def _version_key(dirname: str):
    """Release dir name -> (board_prefix_or_'', version_tuple), or None.

    Both naming shapes parse; the board prefix is kept so a shared
    07_releases/ root holding TWO boards (smc0985-cooksense holds cooksense-*
    AND interposer-*) never cross-compares them."""
    m = _NAME_RE.match(dirname)
    if not m:
        return None
    return (m.group("board") or "",
            tuple(int(x) for x in m.group("ver").split(".")))


def _earlier_releases(release_dir: Path, releases_root: Path):
    """Sibling release dirs of the SAME board with a strictly-lower version
    (any earlier one — a stale file can be inherited from any predecessor,
    not only the immediate one)."""
    me = _version_key(release_dir.name)
    if me is None:
        return []
    out = []
    for sib in sorted(releases_root.iterdir()):
        if not sib.is_dir() or sib.resolve() == release_dir.resolve():
            continue
        v = _version_key(sib.name)
        if v is not None and v[0] == me[0] and v[1] < me[1]:
            out.append(sib)
    return out


def _artifacts(release_dir: Path):
    """(relpath-posix, Path) for every generated fab/drawing file."""
    for sub in _ARTIFACT_DIRS:
        d = release_dir / sub
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                yield p.relative_to(release_dir).as_posix(), p


def _load_exceptions(release_dir: Path):
    """{relpath: reason} from verification/freshness_exceptions.txt. A line
    with a path but no reason is rejected (returned in `bad`)."""
    allow, bad = {}, []
    f = release_dir / "verification" / "freshness_exceptions.txt"
    if not f.is_file():
        return allow, bad
    for raw in f.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # "relpath   reason words..." — split on first run of whitespace
        parts = line.split(None, 1)
        rel = parts[0]
        reason = parts[1].strip() if len(parts) > 1 else ""
        if not reason:
            bad.append(rel)
        else:
            allow[rel] = reason
    return allow, bad


# --------------------------------------------------------------- check (a)
def check_stale(release_dir, releases_root, allow):
    """Any generated artifact sha256-identical to the same-named file in an
    EARLIER release of the same board (unless waived)."""
    findings = []
    earlier = _earlier_releases(release_dir, releases_root)
    for rel, path in _artifacts(release_dir):
        h = _sha256(path)
        for older in earlier:
            other = older / rel
            if other.is_file() and _sha256(other) == h:
                if rel in allow:
                    findings.append(
                        f"  note: {rel} identical to {older.name}/{rel} "
                        f"— WAIVED ({allow[rel]})")
                    continue
                findings.append(
                    f"  STALE: {rel} is sha256-IDENTICAL to "
                    f"{older.name}/{rel} — a changed board must not ship an "
                    f"earlier release's generated output")
    fails = [f for f in findings if f.lstrip().startswith("STALE:")]
    return fails, [f for f in findings if not f.lstrip().startswith("STALE:")]


# ------------------------------------------ docs-only supersede identity
# Subtrees a docs-only supersede must ship UNCHANGED. pdf/ is deliberately
# absent: identical drawings are allowed (the board did not change), but they
# are not required — a regenerated-but-equal-content PDF may differ in bytes
# (timestamps), and neither direction makes the release less docs-only.
_DOCS_ONLY_IDENTICAL_DIRS = ("fab", "source", "3d")


def _tree_files(d: Path):
    """{relpath-posix: Path} for every file under d ({} if d is absent)."""
    if not d.is_dir():
        return {}
    return {p.relative_to(d).as_posix(): p
            for p in sorted(d.rglob("*")) if p.is_file()}


def check_docs_only(release_dir, prior_dir):
    """Assert the docs-only-supersede contract against the DECLARED prior
    release: fab/source/3d byte-identical (any deviation = FAIL), order
    README + MANIFEST byte-DIFFERENT (identical docs supersede nothing)."""
    fails, notes = [], []
    for sub in _DOCS_ONLY_IDENTICAL_DIRS:
        cur = _tree_files(release_dir / sub)
        old = _tree_files(prior_dir / sub)
        for rel in sorted(set(cur) - set(old)):
            fails.append(
                f"  DOCS-ONLY DEVIATION: {sub}/{rel} exists here but not in "
                f"{prior_dir.name} — a docs-only supersede must not ADD "
                f"{sub}/ content; cut a full release instead")
        for rel in sorted(set(old) - set(cur)):
            fails.append(
                f"  DOCS-ONLY DEVIATION: {sub}/{rel} shipped in "
                f"{prior_dir.name} is MISSING here — a docs-only supersede "
                f"must carry the prior release's {sub}/ unchanged")
        same = 0
        for rel in sorted(set(cur) & set(old)):
            if _sha256(cur[rel]) != _sha256(old[rel]):
                fails.append(
                    f"  DOCS-ONLY DEVIATION: {sub}/{rel} DIFFERS from "
                    f"{prior_dir.name}/{sub}/{rel} — a 'docs-only' release "
                    f"that changes {sub}/ is lying; cut a full release "
                    f"instead")
            else:
                same += 1
        if same:
            notes.append(f"  note: {sub}/ byte-identical to {prior_dir.name} "
                         f"({same} file(s)) — ASSERTED by docs-only mode")
    # the documents themselves MUST change — that is the release's whole point
    doc_pairs = [("order README", _find_readme(release_dir),
                  _find_readme(prior_dir)),
                 ("MANIFEST.txt", release_dir / "MANIFEST.txt",
                  prior_dir / "MANIFEST.txt")]
    for label, cp, op in doc_pairs:
        if cp is None or not cp.is_file():
            fails.append(f"  MISSING: {label} in {release_dir.name}")
            continue
        if op is not None and op.is_file() and _sha256(cp) == _sha256(op):
            fails.append(
                f"  DOCS-ONLY UNCHANGED: {label} is byte-identical to "
                f"{prior_dir.name}'s — a docs-only supersede exists to CHANGE "
                f"the documentation; an unchanged {label} supersedes nothing")
    return fails, notes


# --------------------------------------------------------------- check (b)
def _audit_fail_count(audit_text):
    """FAIL count the shipped policy_audit.md actually reports. Prefer its
    'Summary: FAIL=N' line; else count '| ... | FAIL |' table rows."""
    m = re.search(r"Summary:.*?FAIL\s*=\s*(\d+)", audit_text)
    if m:
        return int(m.group(1)), "Summary line"
    rows = re.findall(r"^\s*\|[^|]*\|\s*FAIL\s*\|", audit_text, re.M)
    return len(rows), "table rows"


def _audit_fail_checkids(audit_text):
    """Check-IDs the audit marks FAIL, e.g. {'M-BOM'} from '| M-BOM | FAIL |'."""
    return set(re.findall(r"^\s*\|\s*([A-Za-z0-9\-]+)\s*\|\s*FAIL\s*\|",
                          audit_text, re.M))


def _manifest_claimed_fail(manifest_text):
    """FAIL count the MANIFEST claims for policy_audit. 'policy_audit: 0 FAIL'
    -> 0; a 'PASS' with no explicit FAIL count -> 0; unknown -> None."""
    for m in re.finditer(r"policy_audit\b[^\n]*", manifest_text):
        seg = m.group(0)
        n = re.search(r"(\d+)\s*FAIL", seg)
        if n:
            return int(n.group(1))
        if re.search(r"\bPASS\b|\b0\s*board-FAIL\b", seg):
            return 0
    return None


def check_audit_manifest(release_dir):
    """The manifest's claimed policy_audit result must not under-report the
    audit it ships (audit FAIL while manifest claims 0-FAIL / PASS)."""
    audit = release_dir / "verification" / "policy_audit.md"
    manifest = release_dir / "MANIFEST.txt"
    fails = []
    if not audit.is_file():
        return [f"  MISSING: verification/policy_audit.md (cannot verify the "
                f"manifest's claimed audit result)"]
    if not manifest.is_file():
        return [f"  MISSING: MANIFEST.txt"]
    at = audit.read_text()
    mt = manifest.read_text()
    audit_fail, how = _audit_fail_count(at)
    claimed = _manifest_claimed_fail(mt)
    if claimed is None:
        return fails  # manifest makes no machine-readable policy_audit claim
    if audit_fail > claimed:
        ids = _audit_fail_checkids(at)
        idtxt = (" [" + ", ".join(sorted(ids)) + "]") if ids else ""
        fails.append(
            f"  AUDIT/MANIFEST DISAGREEMENT: shipped policy_audit.md reports "
            f"FAIL={audit_fail}{idtxt} (from its {how}) but MANIFEST claims "
            f"policy_audit FAIL={claimed} — the bundle contradicts its own "
            f"claimed result")
    return fails


# --------------------------------------------------------------- check (c)
def _find_readme(release_dir):
    for name in ("ORDER_README.md", "README.md"):
        p = release_dir / name
        if p.is_file():
            return p
    return None


def check_draft_readme(release_dir):
    """The shipped order README must be FINAL — no draft/placeholder markers."""
    readme = _find_readme(release_dir)
    if readme is None:
        return [f"  MISSING: ORDER_README.md / README.md"]
    fails = []
    pat = re.compile(
        r"\b(" + "|".join(re.escape(m) for m in _DRAFT_MARKERS) + r")\b",
        re.I)
    for i, line in enumerate(readme.read_text().splitlines(), 1):
        for m in pat.finditer(line):
            fails.append(
                f"  DRAFT README: {readme.name}:{i} contains draft/placeholder "
                f"marker {m.group(0)!r}: {line.strip()[:100]!r}")
            break  # one finding per line is enough
    return fails


# --------------------------------------------------------------- check (d)
def _erc_claim(text, near=r"\bERC\b"):
    """(errors, warnings) stated in `text` near an ERC mention (`near` is a
    regex); either may be None if not stated. Parses tolerantly: '0 errors
    (1409 baselined warnings)', '0 errors (1215 warnings)', '0 errors / 12
    warnings' — the warning count is the LAST number before 'warning', with
    at most one qualifier word ('baselined') between."""
    m = re.search(near + r"[^\n]{0,120}", text)
    if not m:
        return None, None
    seg = m.group(0)
    e = re.search(r"(\d+)\s+error", seg)
    w = re.search(r"(\d+)(?:\s+[A-Za-z-]+)?\s+warning", seg)
    return (int(e.group(1)) if e else None,
            int(w.group(1)) if w else None)


def _erc_measured(erc_json_path):
    """(errors, warnings) actually recorded in the shipped erc.json, or None
    per field when it is no evidence for that field — file absent/unreadable,
    or the severity was NOT in the run's `included_severities` (an
    errors-only erc.json measures nothing about warnings: cooksense v1.0
    ships exactly that, and a 0 read off it would be a false mismatch)."""
    if not erc_json_path.is_file():
        return None, None
    try:
        import json
        d = json.loads(erc_json_path.read_text())
    except Exception:
        return None, None
    counts = {"error": 0, "warning": 0}
    for sheet in d.get("sheets", []):
        for v in sheet.get("violations", []):
            sev = v.get("severity")
            if sev in counts:
                counts[sev] += 1
    included = d.get("included_severities")
    if included is not None:
        for sev in list(counts):
            if sev not in included:
                counts[sev] = None
    return counts["error"], counts["warning"]


def _bom_data_rows(bom_csv_path):
    """Actual data-row count of fab/bom.csv (rows minus the header), or None
    if absent. csv-parsed so quoted multi-refdes cells count as ONE row."""
    if not bom_csv_path.is_file():
        return None
    import csv
    with bom_csv_path.open(newline="") as f:
        rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
    return max(len(rows) - 1, 0)


def _manifest_bom_lines(manifest_text):
    """Line count the MANIFEST's bom_source_check summary claims
    ('bom_source_check PASS (48 lines, ...)'), or None if not stated."""
    m = re.search(r"bom_source_check[^\n(]*\((\d+)\s+lines", manifest_text)
    return int(m.group(1)) if m else None


def _count_disagreement(label, stated):
    """One FAIL line if the non-None values in `stated` (list of
    (source, value)) disagree; else None. Absence is never a mismatch."""
    have = [(src, v) for src, v in stated if v is not None]
    if len({v for _, v in have}) <= 1:
        return None
    vals = ", ".join(f"{src}={v}" for src, v in have)
    return (f"  MANIFEST/EVIDENCE MISMATCH: {label} disagrees across the "
            f"bundle ({vals}) — the manifest's gate summary must match the "
            f"machine evidence it ships")


# 07_releases/<dir>/... references inside verification evidence. The dir
# component must look version-ish (contain v<digit>) so prose like
# '07_releases/.../source/x' or '07_releases/contracts.md' never matches.
_RELPATH_RE = re.compile(
    r"07_releases/((?=[^/\s`'\")\]]*v\d)[^/\s`'\")\]]+)/")


def check_manifest_consistency(release_dir, releases_root):
    """(d) the MANIFEST's human-readable gate summary must not disagree with
    the machine evidence shipped alongside it, and evidence must not embed a
    release path that is not this release."""
    fails = []
    manifest = release_dir / "MANIFEST.txt"
    mt = manifest.read_text() if manifest.is_file() else ""

    # -- ERC counts: MANIFEST vs policy_audit S-ERC row vs erc.json
    stated_e, stated_w = [], []
    if mt:
        e, w = _erc_claim(mt)
        stated_e.append(("MANIFEST", e))
        stated_w.append(("MANIFEST", w))
    audit = release_dir / "verification" / "policy_audit.md"
    if audit.is_file():
        row = re.search(r"^\s*\|\s*S-ERC\s*\|[^\n]*", audit.read_text(), re.M)
        if row:
            e, w = _erc_claim(row.group(0), near=r"^")
            stated_e.append(("policy_audit.md S-ERC", e))
            stated_w.append(("policy_audit.md S-ERC", w))
    me, mw = _erc_measured(release_dir / "verification" / "erc.json")
    stated_e.append(("erc.json", me))
    stated_w.append(("erc.json", mw))
    for label, stated in (("ERC error count", stated_e),
                          ("ERC warning count", stated_w)):
        f = _count_disagreement(label, stated)
        if f:
            fails.append(f)

    # -- BOM line count: MANIFEST claim vs fab/bom.csv actual data rows
    claimed = _manifest_bom_lines(mt)
    actual = _bom_data_rows(release_dir / "fab" / "bom.csv")
    if claimed is not None and actual is not None and claimed != actual:
        fails.append(
            f"  MANIFEST/EVIDENCE MISMATCH: MANIFEST claims bom_source_check "
            f"checked {claimed} lines but fab/bom.csv carries {actual} data "
            f"row(s) — the manifest's gate summary must match the BOM it "
            f"ships")

    # -- release paths embedded in verification evidence must name THIS
    #    release's directory (or an existing sibling — diffing a real
    #    predecessor is legitimate), never a staging/shortened path.
    ver = release_dir / "verification"
    if ver.is_dir():
        for f in sorted(ver.glob("*")):
            if f.suffix not in (".txt", ".md") or not f.is_file():
                continue
            try:
                text = f.read_text()
            except UnicodeDecodeError:
                continue
            seen = set()
            for m in _RELPATH_RE.finditer(text):
                name = m.group(1)
                if name in seen or name == release_dir.name:
                    continue
                seen.add(name)
                if (releases_root / name).is_dir():
                    continue  # a real sibling release — legitimate reference
                fails.append(
                    f"  EVIDENCE PATH MISMATCH: verification/{f.name} names "
                    f"'07_releases/{name}/' but this release's directory is "
                    f"'{release_dir.name}' (and no such sibling release "
                    f"exists) — the evidence was produced against a "
                    f"staging/foreign path, not this sealed archive")
    return fails


# --------------------------------------------------------------- check (e)
# A-STOCK — a release seals only against stock evidence that PASSES.
#
# Five sealed releases in this fleet ship stock evidence whose LAST LINE says
# FAIL, including crow-recorder-central-v2 v1.0-v1.3 whose own CPU
# (C6938291, the XU316 SoC) is recorded LOW_STOCK(0). Nothing ever read the
# verdict, so "stock verified" in the MANIFEST meant only that the tool ran.
# Worse, the fleet ships THREE incompatible evidence formats — stdout text, a
# `--out` CSV report saved as stock_check.txt (cooksense v1.1, ZERO verdict
# lines), and a stdout dump saved as .csv — so a parser that gives up on an
# unfamiliar shape is a parser that can be silenced by choosing a shape.
#
# Therefore: a MISSING or UNPARSEABLE VERDICT IS A FAIL, NOT A SKIP. The one
# legitimate way past a non-OK line is an assembly.yaml `sourcing_plan:` entry
# carrying the MEASURED stock and the date it was measured.
#
# This check is OFFLINE: it grades the EVIDENCE the release ships. Live
# re-query stays in the opt-in `--net` tier — a gate that needs the network
# is a gate that gets skipped.
_STOCK_EVIDENCE = ("stock_check.json", "stock_check.txt", "stock_check.csv")
_STOCK_BAD = ("LOW_STOCK", "NOT_FOUND", "QUERY_FAILED", "NO_MATCH")
_VERDICT_RE = re.compile(r"^\s*(PASS|FAIL)\s*:\s*(\d+)\s+coded", re.M)
_LINE_RE = re.compile(
    r"^\s{2,}(OK|LOW_STOCK\(\d+\)|NOT_FOUND|QUERY_FAILED)\s+(C\d+)\s+x(\d+)"
    r".*?(?:stock=(\S+))?\s*$", re.M)


def _placed_coded_lines(release_dir):
    """{lcsc: qty} for every coded BOM line with at least one ref ON the CPL.
    `qty` counts only the refs actually placed — an unpopulated ref consumes
    no stock. Returns None when the release ships no BOM/CPL to grade."""
    import csv as _csv
    bom = release_dir / "fab" / "bom.csv"
    cpl = release_dir / "fab" / "cpl.csv"
    if not bom.is_file() or not cpl.is_file():
        return None
    with cpl.open(newline="") as f:
        placed = {(r.get("Designator") or "").strip()
                  for r in _csv.DictReader(f)}
    out = {}
    with bom.open(newline="") as f:
        for r in _csv.DictReader(f):
            code = (r.get("LCSC") or "").strip()
            if not code:
                continue
            n = sum(1 for d in (r.get("Designator") or "").split(",")
                    if d.strip() in placed)
            if n:
                out[code] = out.get(code, 0) + n
    return out


def _parse_stock_evidence(path):
    """(verdict, {lcsc: (status, stock_or_None)}) from any of the shipped
    formats. `verdict` is 'PASS' / 'FAIL' / None — None means the file states
    no verdict, which is itself the finding."""
    lines = {}
    if path.suffix == ".json":
        import json as _json
        try:
            d = _json.loads(path.read_text())
        except Exception:
            return None, lines
        for e in d.get("lines", []):
            code = str(e.get("lcsc") or "").strip()
            if code:
                st = str(e.get("status") or "")
                try:
                    stock = int(e.get("stock"))
                except (TypeError, ValueError):
                    stock = None
                lines[code] = (st, stock)
        v = str(d.get("verdict") or "").upper()
        return (v if v in ("PASS", "FAIL") else None), lines
    text = path.read_text(errors="ignore")
    for m in _LINE_RE.finditer(text):
        st, code, _qty, stock = m.groups()
        try:
            stock = int(stock)
        except (TypeError, ValueError):
            stock = None
        lines[code] = (st, stock)
    if not lines:                       # the `--out` CSV report shape
        import csv as _csv
        try:
            rows = list(_csv.DictReader(path.open(newline="")))
        except Exception:
            rows = []
        for r in rows:
            code = (r.get("code") or r.get("LCSC") or "").strip()
            if not code:
                continue
            try:
                stock = int(r.get("stock"))
            except (TypeError, ValueError):
                stock = None
            lines[code] = ((r.get("status") or ""), stock)
    m = _VERDICT_RE.search(text)
    return (m.group(1) if m else None), lines


def check_stock(release_dir, assembly):
    """(e) grade the SHIPPED stock evidence for every coded, placed BOM line."""
    fails, notes = [], []
    want = _placed_coded_lines(release_dir)
    if want is None:
        notes.append("  note: A-STOCK: this release ships no fab/bom.csv + "
                     "fab/cpl.csv pair — no coded, placed line to grade")
        return fails, notes
    qty_mult = int(assembly.get("build_quantity") or 5)
    if not assembly.get("build_quantity"):
        notes.append("  note: A-STOCK: no assembly.yaml build_quantity — "
                     "grading against the 5-board default")
    plan = {}
    for e in (assembly.get("sourcing_plan") or []):
        code = str(e.get("lcsc") or "").strip()
        if (code and e.get("measured_stock") is not None
                and str(e.get("measured_on") or "").strip()):
            plan[code] = e
        elif code:
            fails.append(
                f"  STOCK-PLAN-INCOMPLETE: sourcing_plan entry for {code} is "
                f"missing measured_stock and/or measured_on — a plan without "
                f"the measured number and its date is a hope, not evidence")

    ver = release_dir / "verification"
    ev = next((ver / n for n in _STOCK_EVIDENCE if (ver / n).is_file()), None)
    if ev is None:
        fails.append(
            f"  STOCK-NO-EVIDENCE: {len(want)} coded line(s) are on the CPL "
            f"but verification/ ships no stock evidence "
            f"({'/'.join(_STOCK_EVIDENCE)}) — a release with unverified "
            f"sourcing is not orderable")
        return fails, notes
    verdict, lines = _parse_stock_evidence(ev)
    notes.append(f"  note: A-STOCK: grading verification/{ev.name} "
                 f"({len(lines)} graded line(s), verdict={verdict}) against "
                 f"{len(want)} coded+placed BOM line(s) x {qty_mult} boards")
    if verdict is None:
        fails.append(
            f"  STOCK-NO-VERDICT: verification/{ev.name} states no parseable "
            f"PASS:/FAIL: verdict — the VERDICT LINE IS THE GATE, so evidence "
            f"that omits it is unverified sourcing, never a pass (cooksense "
            f"v1.1 shipped a raw CSV report with zero verdict lines)")
    elif verdict == "FAIL":
        problem = {c for c, (st, _s) in lines.items()
                   if any(b in st for b in _STOCK_BAD)}
        # Only a problem line that is actually PLACED and unplanned accuses
        # this release: an unpopulated hand-solder/consign line legitimately
        # reads LOW_STOCK(0) and is A-POP's business, not A-STOCK's.
        bad = sorted((problem & set(want)) - set(plan))
        if bad:
            fails.append(
                f"  STOCK-VERDICT-FAIL: verification/{ev.name} ends in a FAIL "
                f"verdict; unplanned PLACED problem line(s): "
                f"{', '.join(bad[:12])} — seal only against a PASS, or record "
                f"each line in assembly.yaml `sourcing_plan:` with its "
                f"measured stock + date")
        elif problem:
            notes.append(
                f"  note: A-STOCK: verification/{ev.name} verdict is FAIL but "
                f"every problem line ({', '.join(sorted(problem)[:8])}) is "
                f"unplaced or covered by a sourcing_plan entry")
        else:
            fails.append(
                f"  STOCK-VERDICT-FAIL: verification/{ev.name} ends in a FAIL "
                f"verdict and no line-level status could be parsed from it — "
                f"the release cannot show WHICH line failed")
    for code, qty in sorted(want.items()):
        if code in plan:
            continue
        if code not in lines:
            fails.append(
                f"  STOCK-UNGRADED: {code} (x{qty} placed) has no line in "
                f"verification/{ev.name} — a placed part with no stock "
                f"evidence was never sourced, only assumed")
            continue
        st, stock = lines[code]
        need = qty * qty_mult
        if stock is not None and stock < need:
            fails.append(
                f"  STOCK-INSUFFICIENT: {code} stock={stock} < {qty} x "
                f"{qty_mult} boards = {need} (status {st}) and no "
                f"assembly.yaml sourcing_plan entry names a measured "
                f"alternative")
        elif stock is None and any(b in st for b in _STOCK_BAD):
            fails.append(
                f"  STOCK-INSUFFICIENT: {code} graded {st} with no readable "
                f"stock number and no sourcing_plan entry")
    return fails, notes


def _load_assembly(release_dir, override):
    """assembly.yaml for this release: --assembly, else the project's
    03_src/rules/assembly.yaml (a release is projects/<b>/07_releases/<r>/)."""
    p = Path(override) if override else (release_dir.parent.parent
                                         / "03_src" / "rules" / "assembly.yaml")
    if not p.is_file():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    return yaml.safe_load(p.read_text()) or {}


# ------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="release-artifact freshness gate")
    ap.add_argument("release_dir")
    ap.add_argument("--releases-root", default=None,
                    help="the 07_releases/ dir (default: release_dir's parent)")
    ap.add_argument("--allow-identical", action="append", default=[],
                    metavar="RELPATH",
                    help="waive a same-named-identical artifact (edge case: "
                         "doc-only re-release)")
    ap.add_argument("--docs-only-supersede", metavar="PRIOR_RELEASE_DIR",
                    default=None,
                    help="docs-only supersede mode: ASSERT fab/source/3d "
                         "byte-identical to PRIOR_RELEASE_DIR (any deviation "
                         "FAILs), allow identical pdf/, and REQUIRE the order "
                         "README + MANIFEST to differ; the stale check is "
                         "replaced by this identity assertion, checks (b)/(c) "
                         "still run")
    # RED-VERIFY hooks: neuter one check so a known-bad fixture is shown to
    # pass when — and only when — that check is disabled. Tests only.
    ap.add_argument("--_disable-stale", action="store_true")
    ap.add_argument("--_disable-audit-manifest", action="store_true")
    ap.add_argument("--_disable-readme", action="store_true")
    ap.add_argument("--_disable-manifest-consistency", action="store_true")
    ap.add_argument("--_disable-stock", action="store_true")
    ap.add_argument("--assembly", default="",
                    help="03_src/rules/assembly.yaml (auto-discovered from "
                         "the release path) — supplies build_quantity and the "
                         "sourcing_plan the A-STOCK check grades against")
    args = ap.parse_args(argv)

    release_dir = Path(args.release_dir).resolve()
    if not release_dir.is_dir():
        print(f"FATAL: not a directory: {release_dir}", file=sys.stderr)
        return 2
    releases_root = (Path(args.releases_root).resolve()
                     if args.releases_root else release_dir.parent)

    allow, bad_exceptions = _load_exceptions(release_dir)
    for rel in args.allow_identical:
        allow[rel] = "waived via --allow-identical"

    prior_dir = None
    if args.docs_only_supersede:
        prior_dir = Path(args.docs_only_supersede).resolve()
        if not prior_dir.is_dir():
            print(f"FATAL: --docs-only-supersede prior release is not a "
                  f"directory: {prior_dir}", file=sys.stderr)
            return 2

    print(f"== release-freshness: {release_dir.name} =="
          + (f" [docs-only supersede of {prior_dir.name}]" if prior_dir
             else ""))
    fails, notes = [], []

    if bad_exceptions:
        fails += [f"  BAD EXCEPTION: freshness_exceptions.txt lists {rel!r} "
                  f"with no reason — a waiver needs evidence"
                  for rel in bad_exceptions]

    if prior_dir is not None:
        # docs-only mode REPLACES the stale check: identity with the declared
        # prior release is asserted, not flagged.
        if not args._disable_stale:
            df, dn = check_docs_only(release_dir, prior_dir)
            fails += df
            notes += dn
    elif not args._disable_stale:
        sf, sn = check_stale(release_dir, releases_root, allow)
        fails += sf
        notes += sn
    if not args._disable_audit_manifest:
        fails += check_audit_manifest(release_dir)
    if not args._disable_readme:
        fails += check_draft_readme(release_dir)
    if not args._disable_manifest_consistency:
        fails += check_manifest_consistency(release_dir, releases_root)
    if not args._disable_stock:
        sf, sn = check_stock(release_dir, _load_assembly(release_dir,
                                                         args.assembly))
        fails += sf
        notes += sn

    for n in notes:
        print(n)
    for f in fails:
        print(f)

    if fails:
        print(f"FRESHNESS: FAIL ({len(fails)} finding(s))")
        return 1
    print("FRESHNESS: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
