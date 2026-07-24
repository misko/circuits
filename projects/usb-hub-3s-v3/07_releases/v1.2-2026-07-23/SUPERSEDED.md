# SUPERSEDED — DO NOT ORDER

This release **v1.2-2026-07-23** is **DO NOT ORDER** and is superseded by the
**v1.3** fix pass: `07_releases/v1.3-2026-07-23/` (sealed 2026-07-23; R12 C2984354, D5 C113976, R30 C25803 — all three wrong-part/directionality blockers fixed and re-verified).

An external human review (2026-07-23), verified against this sealed archive,
found real order-blockers that the automated gates + the fresh red-team missed
(both were code-identity / self-consistency checks, blind to catalog VALUE and
artifact FRESHNESS — the systemic gaps are being fixed as gate tasks):

1. **R12 wrong part (undervoltage).** The shipped BOM resolves R12 to
   **C2933210** (MPN `FRC0603F3741TS` = **3.74 kΩ**), NOT the intended
   **4.12 kΩ** — driving the buck-C setpoint to ~4.97 V undervoltage and
   recreating the v1.0 problem. part.yaml carried `lcsc: null "confirm at order"`;
   tscircuit value-resolved to C2933210 *claiming* 4.12 kΩ, never catalog-verified.
   **M-BOM PASSED because it checks code IDENTITY (BOM code == circuit.json code),
   not the LCSC's actual catalog value.**
   *Addendum (2026-07-23, semantic-gate ledger seeding):* the same class hit a
   SECOND part — **R30** (Q6 gate pull-up, QG→PMID) ships **C2933195**
   (MPN `FRC0603F3091TS` = **3.09 kΩ**), labeled **100 kΩ**. Functionally the
   FET logic still works (Q7 overpowers it; OFF-state pull-to-source holds), but
   it burns ~1.6 mA through Q7 when ON and is the wrong part. v1.2 therefore
   carries BOTH R12 and R30 wrong-part defects; both are caught by the semantic
   M-BOM gate (leg C + vetted LCSC ledger) that now gates every seal.

2. **Stale / inconsistent release artifacts.** v1.2's
   `pdf/assembly_back.pdf`, `pdf/assembly_front.pdf`, and `pdf/pcb_layers.pdf`
   are **byte-identical (sha256-confirmed) to v1.1's** — the redesigned board
   shipped v1.1's fab drawings. The shipped `verification/policy_audit.md` says
   "M-BOM FAIL" and references v1.1 while the MANIFEST claims "0-FAIL / PASS".
   The README was a draft. `power_tree.yaml` still used the removed-eFuse IR
   model (34–48 mΩ) for the setpoint math.

**v1.3** will: assign a catalog-verified 4.12 kΩ 0.1% R12 and re-derive the
setpoint against the ACTUAL Q6+F2 path (not the eFuse model); revise the
over-voltage protection for a deterministic cutoff (final architecture pending
user re-confirmation) with the D5 TVS directionality resolved against the
manufacturer datasheet; move SW1 off automated assembly pending pitch
confirmation; and regenerate ALL artifacts from v1.3 source with a red-team that
resolves every LCSC to its catalog value/tolerance/MPN.

v1.2 remains a valid historical record of what was sealed on 2026-07-23 and is
otherwise unchanged (immutable). This file is the only addition.
