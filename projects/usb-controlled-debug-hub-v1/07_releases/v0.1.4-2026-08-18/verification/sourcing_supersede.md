# v0.1.4 sourcing-supersede evidence

Parent release: `v0.1.3-2026-08-18`.

## Immutable design subject

- PCB SHA-256 in both releases:
  `c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68`
- CPL is byte-identical: 138 placements.
- BOM shape is identical: 33 rows in the same designator-group order.
- Ten BOM rows change MPN and LCSC together; no Comment, footprint or
  designator group changes.
- The normalized Gerber/drill payload is semantically identical. Only exporter
  generation timestamps may differ in a fresh reproduction.
- The TSX source changes and is the authority for every new code.

The exact delta is documented in ADR-0010 and `ORDER_README.md`. No firmware
was generated or included.

## Design verdict

DESIGN: PASS. This is a sourcing-only change. The v0.1.3 electrical, layout,
DRC/ERC, routing, render, model, orientation and first-article evidence remains
applicable to the byte-identical hardware subject.

## Sourcing verdict

SOURCING: INCOMPLETE / DO-NOT-ORDER. The pre-adoption candidate upload was
reported to resolve every candidate row except the shortened C54411084 logic
gate identity. That row is now corrected to exact Nexperia C6053, but the final
33-row BOM has not yet been re-uploaded and the schema-v2 MOQ/cost response is
blank. Public catalog stock is advisory and is not promoted to JLC allocation.

Complete `prelayout_response_template_v2.csv` from the exact JLC interface,
then grade it against `prelayout_request_v2.json` and the saved procurement
policy. Availability and economics must both be accepted before ordering.
