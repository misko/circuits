# SUPERSEDED

**Superseded by:** `07_releases/crow-mic-pod-v2-v1.2-2026-07-26/`
**Date:** 2026-07-26

**This is a PACKAGING supersede, NOT a board change.** v1.2 differs from this
release in exactly one deliverable: the assembly drawing is merged into the
single 2-page `pdf/assembly.pdf` the 07_releases contract requires (canon
A-EVID, `release_required_check.py`, landed 94300f2 after this seal), replacing
this release's `assembly_front.pdf` + `assembly_back.pdf` pair. Same content.

**This release's board, fab files and evidence are all CORRECT and UNCHANGED
in v1.2**: `fab/`, `source/`, `3d/` and every `verification/` artifact are
byte-identical between the two (asserted by `release_freshness_check.py
--docs-only-supersede`). Anyone holding v1.1 gerbers/BOM/CPL can order them.
Use v1.2 for the complete contract-conformant archive.
