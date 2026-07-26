# 02_parts — status + deviations register

Status: one dir per MPN used on the board; `part.yaml` facts extracted per the
folder contract.

## Deviations register

| MPN | Deviation | Why | Before bring-up |
|---|---|---|---|
| CL21A225KBQNNNE | no committed PDF | series-sheet passive (Samsung CL series); facts verified against the JLC catalog record 2026-07-26, entry exists to clear a bom_source_check UNVERIFIABLE-VALUE (C377773) | none — value/ratings are the only load-bearing facts and are catalog-verified |
| 0402WGF6800TCE | no committed PDF | series-sheet passive (UNI-ROYAL 0402WGF series); facts verified against the JLC catalog record 2026-07-26, entry exists to clear a bom_source_check UNVERIFIABLE-VALUE (C25130) | none — value/ratings are the only load-bearing facts and are catalog-verified |
| 1277AS-H-1R0M / 1277AS-H-2R2M | no committed PDF | series-sheet power inductors (pre-existing entries; deviation recorded when this register was created 2026-07-26) | none — part.yaml carries the extracted ratings |
