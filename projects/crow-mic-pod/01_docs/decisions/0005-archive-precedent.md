# ADR-0005 — reuse of the archived crow-array-pod as design precedent

Status: accepted 2026-07-21

## Context

This commission (Rev-A doc, July 18 2026, + the "ethernet connectors
everywhere" directive) was previously executed in this repo:
`archived_projects/crow-array-pod/` reached sealed releases v1.0-2026-07-18
(screw terminal) and v1.1-2026-07-19 (RJ45 termination per the same user
directive, recorded there as A4). The archive is read-only reference; the
skill's commission rule forbids copying CONTRACTS/config blindly from
another project, and this is a normal production run where repo precedent
is explicitly in scope.

## Decision

1. Contracts and 03_src schema seeds come from the SKILL's canonical
   templates (done at commission), never from the archive.
2. The archived pod v1.1 design — ARCHITECTURE/DETAIL_DESIGN math, the
   verified 02_parts part.yamls (pin maps read from datasheet figures
   there), the 03_src generators/floorplan/route config, the promoted KRT
   route chain, and the twin adjudications — is adopted as the DESIGN
   SOURCE for this project, imported with this provenance note and
   adapted (project rename, contract-template alignment).
3. NOTHING is trusted on import: every gate is RE-RUN and RE-MEASURED in
   this project (ERC, audit, DRC severity-all + parity, bom/stock with
   TODAY's stock, jlc_twin, fresh-context pin + render reviews,
   policy_audit). The archive's verdicts are precedent, not evidence;
   evidence is regenerated here.
4. Any divergence found between archive behavior and current gates is
   fixed HERE (and journaled), not papered over with the archive's waiver.

## Rejected

- Clean-room re-derivation: would re-pay ~2 days of verified work
  (datasheet figure reads, enclosure pixel-verification, KRT convergence)
  for zero verification gain — the gates re-earn the evidence either way.
- Pointing the user at the archived release: the commission asks for a
  fresh project pair; archived releases are sealed under the OLD project
  identity and the repo treats archives as reference only.
