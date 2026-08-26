# learnings — verify stage (crow-mic-pod-v2)

Harvest source for canon M9. Written at the v1.1 paperwork release
(2026-07-25), reflecting on what the v1.0 seal shipped and what the
post-seal adjudication measured.

## An unpopulated part with no decision record is a free outcome

- what happened: v1.0 sealed with 39 board footprints, 26 CPL placements, and
  13 unpopulated parts justified by an `exclude_from_pos_files` attribute bit
  and nothing else. The consequence was not cosmetic: `fab/bom.csv` carried
  assembly rows for MK1 and J1 — two parts JLC is never told to place and
  cannot source (MK1's MPN *and* LCSC columns were both empty) — which stalls
  the upload at JLC's BOM/CPL matcher. BOM 28 designators / 17 lines vs CPL 26.
- root cause: "which parts get placed, and why not" had no machine-readable
  home. It was an emergent property of three artifacts nothing compared: the
  board's attribute bits, `fab/cpl.csv`, and a PROSE sentence in the MANIFEST.
  A-POP measured that MANIFEST line as 16 whitespace tokens of which 13 were
  not refdes at all ('BOM', 'HAND-SOLDER', 'NOW', 'ORDER_README', 'POPULATED')
  — no gate could grade it, so none did.
- avoid next time: `03_src/rules/assembly.yaml` is the ONE home; the MANIFEST
  `not_assembled:` line is GENERATED from it
  (`assembly_coverage.py --emit-manifest-line`), never hand-written twice.
- candidate-canon: no — A-POP and A-STOCK already exist and already caught
  this; the gap was that this board predated them. Local record only.

## "Not in the catalog" is a measurement, not a recollection

- what happened: the v1.0 part dossier, the twin adjudication AND the
  ORDER_README all asserted the AOM-5024 electret is "not in the JLC catalog".
  A live parts-library query on 2026-07-25 returned the exact MPN as
  **C3273706**, Extended tier. The claim was false and had been copied
  across three files without ever being run.
- root cause: a sourcing conclusion was recorded as a PROPERTY OF THE PART
  ("not in the catalog") rather than as a dated observation ("query X on date
  Y returned Z"). Properties get inherited; observations expire visibly. The
  true wall is different and narrower: stock 0 across all three AOM-5024
  variants, plus through-hole on an SMT-only order.
- avoid next time: `assembly.yaml`'s `evidence:` field must be the QUERY AND
  ITS RESULT with a date. "Searched and absent" and "catalogued and out of
  stock" are different facts with different expiry dates, and only one of
  them survives a restock.
- candidate-canon: yes — the closed-vocabulary `reason: not_in_catalog`
  should require an evidence string naming the query and the date, so the
  cheapest way to write it is to run it. (Same discipline as canon M4.)

## A reflection-invariant metric cannot certify a correspondence

- what happened: the sealed LS1 twin waiver stated "JLC pad 1 = our pad 2".
  Re-measured with an oriented fit, that mapping fits at **rms 7.1007 mm at
  all four rotations** — it fits nowhere. The true mapping is a 3<->4 swap of
  two NC dummy pads (rms 0.1414 @0, 50x separation). The waiver had read our
  `.kicad_mod` y-down and JLC's identically-formatted one y-UP.
- root cause: the waiver validated itself with the **6 pairwise pad-pair
  distances**, and got a plausible 0.20-0.28 mm spread. Re-run under both
  mappings, the distance sets are IDENTICAL. Pairwise distances are invariant
  under rigid motion AND under reflection, and the two mappings differ by
  exactly a reflection — so the method was structurally incapable of
  detecting its own error. It was not a careless check; it was the wrong
  instrument, and a wrong instrument reports success.
- avoid next time: establish a pad correspondence with an ORIENTED fit
  (formA at four angles, pads matched by NUMBER) and report the winning rms
  **together with its separation from the runner-up**. "7.1007 at all four
  angles" is legible as failure; "0.20-0.28 mm on every pair" reads as
  success. Never a distance set.
- candidate-canon: yes — worth a canon line under the twin/rotation family:
  *a correspondence claim must report its runner-up*. A fit with no preferred
  rotation is not a fit.

## A rule that cannot fire is worse than no rule

- what happened: 2 of the 4 rules in the sealed `.kicad_dru` cannot fire.
  `AUDIO_width` conditions on NetClass 'AUDIO' which the `.kicad_pro` does not
  define; `pad_rescue_stubs` conditions on a rule area absent from the board.
  The board carries 3 tracks at 0.2498 mm — 0.0002 mm under the floor the
  dead rule names — and DRC reports 0/0/0.
- root cause: TWO mechanisms, and the second is the interesting one.
  (a) `nets.yaml` deliberately DROPPED the AUDIO class because its 0.25 mm
  floor collided with KRT's 0.2498 mm imported width (the nanometre-floor
  trap). The class went; the DRU rule naming it did not. The rule was removed
  from the enforcement path to make DRC pass, and its TEXT was left behind
  reading like enforcement.
  (b) `rules_audit` could not have caught it: every check it had iterated over
  the classes **declared in nets.yaml**, so a rule naming a class nets.yaml no
  longer declares was examined by nothing at all. The checker's scope was
  defined by the same file the defect had been removed from.
- avoid next time: `rules_audit.py` gained **A-FIRE**, which walks the DRU's
  OWN rules rather than nets.yaml's classes, and it now runs as a gate in
  `03_src/rebuild_all.sh` between the last `generate_rules` and the DRC gate —
  so a non-firing rule is a BUILD ERROR. Fleet sweep on landing: 3 boards
  affected (this one x2, usb-hub-3s, usb-hub-3s-v2), 5 clean.
- candidate-canon: yes, and it generalises past DRU rules — **scope a checker
  by the artifact being checked, not by the declaration it is supposed to
  agree with.** A checker that enumerates from the same source as the thing
  it checks can only ever find disagreements *within* that source.

## A generated report that is never read back can ship corrupt and hash clean

- what happened: v1.0's `policy_audit.md` shipped with a 51-byte splice at
  offset 387 that deleted the P-TIER row and orphaned its tail. The file's own
  Summary claimed PASS=23; its table contains PASS=22. The MANIFEST sha256
  **verified** — it was generated corrupt and then faithfully hashed.
- root cause: the report path was also the process's redirected stdout.
  `import pcbnew` writes to that fd at C level, advancing the SHARED file
  offset to 387; `write_text()` wrote the report from offset 0 through its own
  fd; at interpreter exit Python's block-buffered stdout flushed its 51-byte
  summary line at offset 387, into the finished file. Two writers, one path,
  independent offsets. Compounding it, the Summary was computed from the
  in-memory counter that produced the rows, so it could only ever agree with
  itself.
- avoid next time: write the report to a temp file and `os.replace()` it after
  flushing stdout — a NEW inode is unreachable by a stale fd no matter when it
  flushes. Then RE-READ it from disk and re-derive the grade counts from the
  published table. A read-back placed before process exit would not have
  caught this one, which is why the atomic write is the load-bearing half.
- candidate-canon: yes — **every integrity check downstream of generation
  certifies whatever generation produced.** A hash proves the file has not
  changed since it was hashed; it says nothing about whether it was right when
  written. Artifacts that gate a release need a self-consistency assertion at
  WRITE time, not just a hash.

## Nothing learned (explicitly)

The copper itself taught nothing new at v1.1: DRC re-measured 0/0/0 with 0
lib_footprint_issues standalone on the sealed source, all 26 CPL rotations
re-derived to 0 mismatches, and all three polarized parts cleared on
numbering-free channels. Every finding in this file is about the PAPERWORK and
the GATES, not the board — which is itself the observation: this board's
verification gap was never in the physics.
