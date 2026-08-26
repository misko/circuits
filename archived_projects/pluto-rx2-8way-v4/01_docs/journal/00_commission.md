# Commission journal

## 2026-07-31 — start

Reconstructed the requested v4 from the user's new-board directive. Prior v1
and v2 artifacts were read only to identify proven requirements and failure
modes; the incomplete v3 scaffold was excluded from evidence.

## 2026-07-31 — gate

Closed the functional, power, fabrication, mating, and timing fact locks. The
initial architectural choice was bare RP2040 plus TPS7A2433.

## 2026-07-31 — binding amendment

The user required an RP2040 module and explicitly prohibited bare silicon. The
bare-chip capture and its part scope were discarded before any generated board
artifact. Module-first selection chose RP2040-Zero. No commission blocker remains.
