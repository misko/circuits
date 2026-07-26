# SUPERSEDED — v1.6-2026-07-26

**Order from `07_releases/v1.7-2026-07-26/` instead.**

## THIS IS NOT A BOARD DEFECT

**The fab payload of v1.7 is BYTE-IDENTICAL to this release** — `fab/bom.csv`,
`fab/cpl.csv`, the 13-file gerber zip and both drill files are the same bytes,
verified with `diff -r`. **The board in this release is correct and was correct.**
What was wrong is the EVIDENCE shipped alongside it.

## What was missing

This release carries **13** verification files. v1.5 carried **34**. The 21
missing ones are not decoration — they are the machine evidence for the claims
this release's own MANIFEST makes. It asserts DRC 0/0/0, twin 119/119, passives
26/26, A-STOCK and freshness, while carrying no `drc.json`, no `erc.json`, no
`bom_source_check.txt`, no stock check — and no **`manifest_selfcheck.txt`**, the
artifact whose entire job is proving that this MANIFEST's prose matches its
machine evidence. **The release asserts its own gate results with the evidence
stripped out.**

Two distinct causes:

1. **Generated, never staged** — all six `twin_*.png` existed in `06_build/twin/`
   dated 01:02 the same day; the staging step did not carry them.
2. **Never produced** — the bare renders and all nine machine-evidence files
   existed nowhere. The gates RAN, and their output went to stdout instead of to
   a file.

## The missing evidence hid a real defect

`source/fp-lib-table` in this release was copied raw from `04_kicad/` and points
at `${KIPRJMOD}/../03_src/lib/...`, a path that **does not exist inside the
archive**. Extracted on its own, this archive produces **12
`lib_footprint_issues`** (DRC) and **12 `footprint_link_issues`** (ERC) — it does
not stand alone. v1.5 rewrote that table to `${KIPRJMOD}/`, pointing at the
vendored `.pretty` directories that ship beside it; this release did not.

The gate that catches precisely this is `standalone_archive_drc.json` — **one of
the 21 files this release is missing**. v1.7 fixes the table and ships the proof:
standalone archive DRC **0/0/0**.

**Practical impact:** anyone opening `source/` from this archive gets unresolved
footprint libraries. The gerbers and drills — what you actually order — are
unaffected, which is why the fab payload needed no change.

## Why no gate caught it

M-REL requires only that `verification/` **exist and be non-empty**. Thirteen
files satisfied it. A directory-presence check cannot see a missing artifact.

## Status of this directory

**IMMUTABLE.** Nothing in it has been edited; this file is an addition.
