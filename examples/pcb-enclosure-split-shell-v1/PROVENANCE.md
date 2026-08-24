# Sanitized split-shell enclosure fixture

- Source path: this clean-room synthetic snapshot directory; no production board or sealed release binary was copied.
- Repository baseline commit: `d36f032cd5a658d528909a1255b2b2a70c84c803`.
- Extraction date: 2026-08-24.
- Evidence of: a minimal `split_shell` configuration with shared board fasteners, two connector openings, and support-aware FDM outputs.
- Runnable: yes, for deterministic OpenSCAD generation and bounded verification. The assembly snapshot is deliberately not STEP geometry, so exact-solid clearance and the overall CAD verdict remain `INCOMPLETE` until a genuine exact STEP inspection is supplied.

From the repository root:

```sh
/usr/bin/python3 skills/pcb-enclosure/scripts/generate_enclosure.py \
  examples/pcb-enclosure-split-shell-v1/enclosure.yaml \
  --root examples/pcb-enclosure-split-shell-v1 \
  --build-dir /tmp/pcb-enclosure-split-shell-v1

/usr/bin/python3 skills/pcb-enclosure/scripts/verify_enclosure.py \
  examples/pcb-enclosure-split-shell-v1/enclosure.yaml \
  --root examples/pcb-enclosure-split-shell-v1 \
  --build-dir /tmp/pcb-enclosure-split-shell-v1 \
  --report /tmp/pcb-enclosure-split-shell-v1/verification.json
```

The verifier intentionally exits with status 2 at the default `cad` target because the exact-solid evidence is absent. `expected-verification.json` is the checked reference report for that bounded result; absolute build paths are not part of the snapshot.
