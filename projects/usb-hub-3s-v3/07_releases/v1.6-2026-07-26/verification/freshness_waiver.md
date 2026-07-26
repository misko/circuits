# Freshness-gate waiver — v1.5-2026-07-25 (CPL-correction supersede)

`release_freshness_check.py`'s stale-artifact check flags **7** artifacts of
this release as sha256-IDENTICAL to sealed `v1.4-2026-07-23`. **That identity is
the release's central CLAIM, not a defect** — and unlike a routine "nothing
changed" case, it is the thing this release most needs to be true.

The gate exists to catch an UNINTENTIONAL stale artifact: a changed board
shipping an earlier release's generated output (the v1.1 KiCad-7/10
mixed-gerber incident class). v1.5 changes **no board and no copper**. It
corrects four CPL rotation cells and the order paperwork. A gerber that
DIFFERED from v1.4's here would be the defect, because it would mean the copper
moved when this release says it did not.

**Why `--docs-only-supersede` is NOT used.** That mode asserts `fab/` is
byte-identical to the predecessor. It is not: `fab/cpl.csv` and `fab/bom.csv`
both change (four rotation cells; the MPN column). v1.5 is a CPL-correction
supersede, not a docs-only one, so the seven genuinely-identical files are
waived individually with `--allow-identical`, and **every other freshness check
stays enforced** (README finality, audit-vs-manifest agreement, MANIFEST
consistency, and the always-on **A-STOCK** check (e)).

## The intentionally-identical set (7 files, sha256 == v1.4's MANIFEST values)

    f51344e45ddd2d848b86a0653ddc2e7b734cb3d588c7d1fdbfa57125f6371009  fab/usb_hub_3s_v2_gerbers.zip
    976841faeca24bc221bc20291727979ce1a9a31a19e1b5cce4427fc75161bf7f  fab/usb_hub_3s_v2-NPTH.drl
    03b93154865c75fa5da7d7293fcc5e26fd4a1f7f04db3e0ad9d917b8c1be0a00  fab/usb_hub_3s_v2-PTH.drl
    86c72ddce9114c65f21d951566b57965116f89a0110a8db4f6fc0883df08667d  pdf/assembly_back.pdf
    36337e5a9ae92bbbf6138f462f9b39db63ab176027e671792822c6445025afd7  pdf/assembly_front.pdf
    d93bcbb638c52cc45627aa0c156fea29401304656587130186d8dd5218de795e  pdf/pcb_layers.pdf
    25bc11180f722441887265d1067c12765fa9fcf3f8136426565275215ca237b9  pdf/schematic.pdf

`source/` (13 files) and `3d/` (1 file) are likewise byte-identical to v1.4 —
the freshness gate sweeps only `fab/` and `pdf/`, so they need no waiver, but
they are verified in `verification/cpl_acceptance_gate.md` §3 and hashed in the
MANIFEST. **20 payload files identical in total.**

## The EVIDENCE that the identity is earned, not inherited

This is the part a copied waiver would not have. The fab package was **RE-PLOTTED
from the unchanged board on 2026-07-25** and compared member-for-member against
v1.4's sealed zip — the identity was *measured*, not assumed:

- 13/13 zip members present in both.
- Per member, the only differing lines are the plot's **own timestamp comments**
  (`%TF.CreationDate`, `G04 Created by KiCad ... date`; drill files
  `; DRILL file KiCad ... date`, `; #@! TF.CreationDate`) — 4 diff lines
  (2 removed + 2 added) on every one of the 13, and nothing else.
- With those comment lines stripped, **all 13 members hash identically**
  (per-file hashes listed in `cpl_acceptance_gate.md` §3).

Because the plot is byte-stable apart from its own timestamp, v1.5 ships v1.4's
gerber and drill BYTES verbatim, so the MANIFEST's sha256-identity claim is
literal and any reader can check it with `sha256sum` alone.

Independent corroboration on the same unchanged board: DRC **0/0/0** with
`--schematic-parity`, and netlist parity vs v1.4's sealed `.net` at **110
components / 67 nets / 347 nodes, 0 differences**.

## A-STOCK (check (e)) — NOT waived, PASSED

`verification/stock_check.json` is the machine-parseable sidecar the gate
grades, produced by `jlc_stock_check.py --json` on 2026-07-25 against **this
release's** `fab/bom.csv` at `--min-stock 5` (the `build_quantity: 5` declared
in `03_src/rules/assembly.yaml`). Verdict **PASS: 43/43 coded lines OK, 0
uncoded**, so `sourcing_plan:` is legitimately empty — there is no non-OK line
to plan around. Tightest ceiling: C473910 at 75 in stock / 2 per board = **37
boards**, i.e. 7.4× the ordered quantity.
