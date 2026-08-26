# Project status

<!-- pause-state:06bfe87196dcff805766df972c0598c2d59528eef80b539b8e0aa6b606b1fc12 -->

- Phase: `release_v014_sourcing_checkpoint`
- State: **PAUSED**
- Checkpoint: `07_releases/v0.1.4-2026-08-18/fab/bom.csv` (`703102bcf49c`)
- Blocker: Upload the exact v0.1.4 BOM to JLCPCB for quantity 5, save the resolved availability/MOQ/cost evidence, and complete the schema-v2 response without accepting substitutions.
- Next command: `python3 skills/jlcpcb-fab/scripts/jlc_pcba_availability.py grade projects/usb-controlled-debug-hub-v1/06_build/sourcing/v014-release/prelayout_request.json projects/usb-controlled-debug-hub-v1/06_build/sourcing/v014-release/prelayout_response.csv --out projects/usb-controlled-debug-hub-v1/06_build/sourcing/v014-release/prelayout_receipt.json`

## Bound receipts

- `01_docs/sourcing/procurement-policy.yaml` — `8bbd3aa18d93`
- `07_releases/v0.1.4-2026-08-18/verification/prelayout_request_v2.json` — `6269bace1deb`

This file is generated from `01_docs/pause_state.json`; edit the manifest with
`pause_state.py record`, not this view.
