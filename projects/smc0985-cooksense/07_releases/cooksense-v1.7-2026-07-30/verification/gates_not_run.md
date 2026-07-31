# Two standalone checkers that could NOT be invoked, and why that is not a skip

Both are recorded here rather than shipped as a crash traceback pretending to be
evidence. Neither leaves its subject ungraded — in both cases the SAME check runs
correctly inside `policy_audit`, whose report is `policy_audit.md` in this
directory.

## `escape_check.py` — standalone CLI

Every project-root invocation tried (`--project .`, `--project <abs>`,
positional) raises `IsADirectoryError` opening the project directory as a file.

**The subject is NOT ungraded.** `policy_audit` calls it correctly and ships two
PASS rows:

    P-ESC   PASS  47 parts: escape blocks agree with escape_check
    P-TIER  PASS  all parts escape at declared fab_tier 'jlc_4layer_advanced'

Recorded as an OWED skill patch (the standalone CLI's project-root handling),
not as a skipped gate.

## `board_netlist_parity.py` — standalone CLI

Raises `AttributeError: 'NoneType' object has no attribute 'GetFootprints'` —
it expects a SEALED release path to diff against and got a board file.

**The subject is NOT ungraded, and it is graded by something stronger.** The
release gate for parity is the DRC run itself:

    kicad-cli pcb drc --severity-all --refill-zones --schematic-parity
    -> Found 0 schematic parity issues        (exit 0, 2026-07-30)

and `count_parity.py --board cooksense` independently reconciles four source
pairs against the manifest:

    S-COUNT PASS: 4/4 source pair(s) agree with manifest over 239 refdes
    ok  board == manifest        (239/239)
    ok  circuit.json == manifest (239/239)
    ok  kicad_sch == manifest    (239/239)
    ok  netlist == manifest      (239/239)

Both outputs are in this directory (`drc.json`, `count_parity.txt`).

---

# THE REPO TEST SUITE IS EXIT 1 — SEVEN FAILURES, NONE OF THEM THIS BOARD'S

Recorded by name and by owner rather than waited on or rounded to green.
**None of the seven blocked this pass** — the blocker was the topology re-gate's
`DO-NOT-ORDER` (see `build_gates.md`). A separate agent is diagnosing all seven;
this pass did not attempt to fix any of them and did not duplicate that work.

**Re-run per file by me, 2026-07-30, raw exit codes:**

| test file | my raw exit | FAIL count | check | whose |
|---|---|---|---|---|
| `t1_escape_tier.py` | **1** | 2 | P-LAND known-bad fixture: `got 5, want 11` pads under their class floor | **`pluto_cal_switch.kicad_pcb`** — different board, pre-existing |
| `t1_layout_precedent.py` | **0** ⚠️ | 1 | `PREC_GRADED_FLOOR`: "tier-graded parts measured (92 in scope) … got 1, want 0" | fleet ratchet floor, concurrent in-flight work |
| `t1_adr_bounds.py` | **1** | 2 | `CITED_FLOOR` ×2 — 37 of 38 bound-publishing ADRs OWED | fleet-wide M-BOUND debt |
| `t1_schema_reader.py` | **1** | 2 | `G-ORPHAN`: 307/307 keys graded, **1 orphan** | the orphan is **`pluto-rx2-8way-v2/02_parts/RP2040-Zero/part.yaml` `mechanical`** — different board |

**7 failures total, which reproduces the reported count exactly.**

**Attribution — checked, not assumed.** Every failing assertion names its own
subject, and not one names a cooksense artifact: the P-LAND fixture is
`pluto_cal_switch`, the G-ORPHAN orphan is an `RP2040-Zero` dossier in
`pluto-rx2-8way-v2`, and the two floor failures are fleet counters. cooksense
ADRs *do* appear in `t1_adr_bounds`' output — but in the **OWED listing**, which
is pre-existing named debt, not the failing assertion. Nothing this pass changed
(`rebuild_schematic.sh`, `assembly.yaml`, 13 `.tsx` comments, the schematic,
`DISPOSITIONS.md`, the journal, the beacon, one new review) declares a schema key
or publishes an ADR bound, so none of them can reach these four checks.

## ⚠️ AND ONE OF THE SEVEN IS INVISIBLE TO AN EXIT CODE

`t1_layout_precedent.py` prints **`10 passed, 1 failed`** and **exits 0**.
Reproduced twice, raw `$?` captured both times:

```
$ /usr/bin/python3 tests/t1_layout_precedent.py ; echo $?
      harness.Failed: tier-graded parts measured (92 in scope) vs
      PREC_GRADED_FLOOR — it may only RISE, and it may not lag adoption
      either: got 1, want 0
  10 passed, 1 failed
0
```

A test file that reports a failure and returns success is the exact shape this
repo's testing contract exists to forbid — *"a gate that cannot fail is
worthless"*, the `jlc_twin` exit-0-on-11-unverified-parts incident. Anything
gating on this file's exit code sees green while it says it is red; only a
text-parsing runner sees the seventh failure at all. **Not fixed here** (a
different board's owner and a diagnosing agent already assigned) and **not
counted as a cooksense gate**, but named, because it is the difference between
a suite that is 7-red and a suite that reports 7-red while one of them can be
skipped by whoever reads `$?`.
