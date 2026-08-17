# Resume

<!-- pause-state:794738eddf17eb074eddeef58437739156a75ce3c07d3f39c391a4687982af45 -->

Canonical state: `01_docs/pause_state.json`

1. Verify: `python3 skills/pcb-design/scripts/pause_state.py verify .`
2. Confirm blocker: Obtain explicit human approval of the exact v0.1.2 connector-facing orientation subject, then retain the approval in verification before sealing.
3. Resume with: `python3 skills/jlcpcb-fab/scripts/release_freshness_check.py projects/usb-controlled-debug-hub-v1/06_build/release_staging/v0.1.2-2026-08-17 --claim design`

The authenticated checkpoint is `04_kicad/usb_controlled_debug_hub.kicad_pcb` at
`c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68`.
