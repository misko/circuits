# Freshness-gate waiver — v1.4-2026-07-23 (docs-only supersede)

`release_freshness_check.py` flags 9 STALE findings on this release: every
fab/ and pdf/ artifact is sha256-IDENTICAL to sealed v1.3-2026-07-23. **This
is EXPECTED and is the release's declared purpose, not a defect.** The gate
targets UNINTENTIONAL stale artifacts — a changed board shipping an earlier
release's generated output (the v1.1 KiCad-7/10 mixed-gerber incident class).
v1.4 changes NO board, BOM, or generated artifact: it is a DOCS-ONLY supersede
correcting the v1.3 ORDER_README (SW1 shunt polarity reversed, F1 holder
misdescription, Vref-only margin table, packaging note) per the post-seal
external review (08_reviews/2026-07-23_v1.3_external-user_full.md,
DISPOSITIONS EXT13-3/4/5/6/8). Byte-identity of the payload is asserted in
the MANIFEST and verified by the docfix confirmation — an artifact that
DIFFERED from v1.3 here would be the defect.

## Evidence — the intentionally-identical set (sha256, == v1.3's MANIFEST values)

  20a16427f0b1006e7d399686b6b602b545675c83883d8550d5910ad9401d7b01  fab/bom.csv
  95d03cadba96d2af2784380215d4cffd01e21c7f4c09398577d50cecadbafd0e  fab/cpl.csv
  f51344e45ddd2d848b86a0653ddc2e7b734cb3d588c7d1fdbfa57125f6371009  fab/usb_hub_3s_v2_gerbers.zip
  976841faeca24bc221bc20291727979ce1a9a31a19e1b5cce4427fc75161bf7f  fab/usb_hub_3s_v2-NPTH.drl
  03b93154865c75fa5da7d7293fcc5e26fd4a1f7f04db3e0ad9d917b8c1be0a00  fab/usb_hub_3s_v2-PTH.drl
  86c72ddce9114c65f21d951566b57965116f89a0110a8db4f6fc0883df08667d  pdf/assembly_back.pdf
  36337e5a9ae92bbbf6138f462f9b39db63ab176027e671792822c6445025afd7  pdf/assembly_front.pdf
  d93bcbb638c52cc45627aa0c156fea29401304656587130186d8dd5218de795e  pdf/pcb_layers.pdf
  25bc11180f722441887265d1067c12765fa9fcf3f8136426565275215ca237b9  pdf/schematic.pdf

(source/ and 3d/ are likewise byte-identical — 22/22 copied files verified
against v1.3 by sorted find|sha256sum diff at staging; the freshness gate only
sweeps fab/pdf.)

## Gate run

The shipped `release_freshness.txt` is the gate re-run at stamp time with the
gate's own edge-case mechanism `--allow-identical <relpath>` for exactly these
9 files ("doc-only re-release", per the script's help text) — every OTHER
freshness check (README finality, audit-vs-manifest agreement) still enforced.

## Harvest flag (journaled)

The per-file `--allow-identical` enumeration is clumsy for a whole-payload
docs-only supersede; the gate needs a `--docs-only-supersede <predecessor>`
mode that asserts full fab/pdf identity instead of waiving it file-by-file.
Flagged in 01_docs/journal/v1.4_docs_supersede.md (a builder is delivering
this in parallel; NOT used here).
