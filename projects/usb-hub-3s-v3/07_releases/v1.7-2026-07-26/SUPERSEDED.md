# SUPERSEDED — v1.7-2026-07-26

**Order from `07_releases/v1.8-2026-07-26/` instead.**

## THIS IS NOT A BOARD CHANGE

**v1.8's fab payload is BYTE-IDENTICAL to this release** — `fab/bom.csv`,
`fab/cpl.csv`, the 13-file gerber zip and both drill files are the same bytes,
verified with `diff -r`. **The board in this release is correct.** v1.8 is a
VERIFICATION-COMPLETENESS supersede.

## What was missing

A new gate, `release_required_check.py` (canon **A-EVID**), enforces the
**REQUIRED** direction of `07_releases/contracts.md`. Nothing had ever checked it:
`contracts_audit` iterates the files that EXIST and asks whether each is
*permitted*, which structurally cannot see an absence. Run against this release it
reports **5 missing artifacts**.

Two were genuine evidence gaps: **this board had never shipped a `pin_review.md`
or a `render_review.md`** — not in v1.5, not in v1.6, not here. A
diff-against-the-predecessor check could never have found it, because every
predecessor was missing them too.

Three were naming: the current red-team reviews shipped only under their dated
`08_reviews/` names rather than the contract names `redteam_layout.md` /
`redteam_topology.md`, and the assembly drawings shipped as
`assembly_front.pdf` + `assembly_back.pdf` rather than the contract's single
`pdf/assembly.pdf`.

## What the reviews then found

Running them was not a formality — both **PASS**, and both found something:

* **U12 (CONCERN).** As shipped, with R42 unpopulated, the USBLC6-2SC6 sits on
  VBUSC at 5.352 V nominal / 5.479 V no-load, roughly **100-230 mV above its
  5.25 V V_RWM, continuously**. Below breakdown, so elevated leakage rather than
  damage — but it is operation above a datasheet rating in the configuration that
  ships, and **no document in this release says so**. v1.8 states it plainly at
  bench gate Q9. Whether to populate R42 by default is a v-next design decision.
* **SW1 (documentation defect).** The tsx comment described the deleted eFuse-era
  D6 / EN_C enable scheme as if it were current, contradicting the same file's own
  v1.2 header. The copper was never wrong, which is precisely why no
  machine-checkable gate caught it.

Neither is a defect in the copper of this release.

## Why no gate caught the omission

Until A-EVID, `M-REL` required only that `verification/` **exist and be
non-empty**. A presence check cannot see a missing artifact — the same shape as
`jlc_twin` exiting 0 on 11 parts it never verified.

## Status of this directory

**IMMUTABLE.** Nothing in it has been edited; this file is an addition.
