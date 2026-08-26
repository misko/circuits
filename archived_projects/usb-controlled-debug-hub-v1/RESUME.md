# Resume

<!-- pause-state:06bfe87196dcff805766df972c0598c2d59528eef80b539b8e0aa6b606b1fc12 -->

Canonical state: `01_docs/pause_state.json`

1. Verify: `python3 skills/pcb-design/scripts/pause_state.py verify .`
2. Confirm blocker: Upload the exact v0.1.4 BOM to JLCPCB for quantity 5, save the resolved availability/MOQ/cost evidence, and complete the schema-v2 response without accepting substitutions.
3. Resume with: `python3 skills/jlcpcb-fab/scripts/jlc_pcba_availability.py grade projects/usb-controlled-debug-hub-v1/06_build/sourcing/v014-release/prelayout_request.json projects/usb-controlled-debug-hub-v1/06_build/sourcing/v014-release/prelayout_response.csv --out projects/usb-controlled-debug-hub-v1/06_build/sourcing/v014-release/prelayout_receipt.json`

The authenticated checkpoint is `07_releases/v0.1.4-2026-08-18/fab/bom.csv` at
`703102bcf49cf0661dfc4b5a25dfcd2fa1f435a19be8405f9c3cb8d8bd45e5ff`.
