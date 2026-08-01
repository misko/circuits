# Verification journal

## 2026-07-31 21:18 — start
- did: Ran deterministic rebuild, quick connectivity, strict RF copper-length, module-first, and policy checks against the saved board.
- result: quick verdict CLEAN; P-MOD 1/1; R-LEN measured all 8/8 arms with 0 vias and 0.1657 mm spread against a 1.0 mm ceiling; policy audit has 0 failures.
- next: Execute the orchestrated layout seal from fresh tscircuit source.

## 2026-07-31 21:23 — finish
- did: Ran pcb_flow layout-seal, including fresh source regeneration, placement gates, promoted-route import, deterministic stitch/fill, P-LAND, and full-severity KiCad DRC with schematic parity.
- result: LAYOUT SEALED; DRC 0 violations / 0 unconnected / 0 parity, with 28/28 component parity and 0 P-LAND failures.
- next: Keep release open until firmware, JLC fabrication/assembly gates, order-day sourcing, and measured VNA characterization are complete.

## 2026-07-31 22:05 — iterate 1
- did: Re-ran layout-seal after contract-only artifact normalization invalidated the broad source-tree hash, then compared the regenerated worktree with the already reviewed board and restored the reviewed board rather than accepting unexplained generated-file churn.
- result: The rerun completed P-MOD 1/1, P-ESC 6/6, P-LAND with 0 failures, source parity 28/28, and DRC 0/0/0, but rewrote 7,460 PCB lines in each diff direction through stitching-via UUID/order churn. The retained reviewed board independently passes current P-MOD 1/1, P-LAND with 0 failures, and full-severity DRC 0/0/0. Its copper and candidate remain unchanged; the broad handoff hash is intentionally stale on governance-only source bytes.
- next: Treat source-hash scope and stitch-via byte determinism as pipeline work, not as authorization to churn reviewed copper. A future seal must regenerate a fresh witness and candidate only after the independent pre-seal reviews are complete.
