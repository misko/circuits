# Sanitized edge-panel enclosure fixture

- Source path: this clean-room synthetic snapshot directory; no production board or sealed release binary was copied. The synthetic release-manifest snapshot exists solely to exercise the derived-enclosure dependency contract.
- Repository baseline commit: `d36f032cd5a658d528909a1255b2b2a70c84c803`.
- Extraction date: 2026-08-24.
- Evidence of: a minimal `base_lid_panels` configuration with separate perimeter fasteners, removable edge panels, top service access, and a declared ventilation group.
- Runnable: yes, for deterministic OpenSCAD generation and bounded verification. The assembly snapshot is deliberately not STEP geometry, so exact-solid clearance and the overall CAD verdict remain `INCOMPLETE` until a genuine exact STEP inspection is supplied.

From the repository root:

```sh
/usr/bin/python3 skills/pcb-enclosure/scripts/generate_enclosure.py \
  examples/pcb-enclosure-edge-panel-v1/enclosure.yaml \
  --root examples/pcb-enclosure-edge-panel-v1 \
  --build-dir /tmp/pcb-enclosure-edge-panel-v1

/usr/bin/python3 skills/pcb-enclosure/scripts/verify_enclosure.py \
  examples/pcb-enclosure-edge-panel-v1/enclosure.yaml \
  --root examples/pcb-enclosure-edge-panel-v1 \
  --build-dir /tmp/pcb-enclosure-edge-panel-v1 \
  --report /tmp/pcb-enclosure-edge-panel-v1/verification.json
```

The verifier intentionally exits with status 2 at the default `cad` target because the exact-solid evidence is absent. `expected-verification.json` is the checked reference report for that bounded result; absolute build paths are not part of the snapshot.
