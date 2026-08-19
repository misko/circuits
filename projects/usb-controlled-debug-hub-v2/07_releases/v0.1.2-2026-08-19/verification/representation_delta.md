# Representation-only supersede assertion

candidate: v0.1.2-2026-08-19
predecessor: v0.1.1-2026-08-18
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING

The strict representation-supersede gate must prove:

- `fab/` is byte-identical, including Gerbers, drills, ZIP, BOM and CPL;
- `3d/` is byte-identical;
- `source/` is byte-identical except for
  `03_src/rules/twin_adjudications.yaml`;
- that adjudication file changed; and
- MANIFEST and ORDER_README changed.

The intentional delta declares `render_model_source: native` for `J_DATA` and
`J_POWER`. It rejects the 2.00-mm-recessed C165948 catalog representation for
rendering while retaining its identity in the receipt. The selected native
model must match SHA-256
`f902880f83a1b397b76360ed8686b6132a66920b3c1aac8e98239315842ff43e`.

Acceptance evidence is `verification/twin/connector_datum_receipt.json`,
`verification/a_render_top.md`, `verification/a_render_bottom.md`, and the
same-camera overlay PNGs. The final release rehearsal receipt is external to
the archive so its hash cannot make MANIFEST self-referential.
