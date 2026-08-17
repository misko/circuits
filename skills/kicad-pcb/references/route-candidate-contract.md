# Authoritative route-candidate contract

A route verdict is a function of the PCB bytes **and** the exact prepared rule
authority. Candidate-adjacent `.kicad_pro` and `.kicad_dru` files are output
evidence; they never grade their own candidate.

```text
prepared r0 PCB -----> P-ROUTEBASE -----------+
prepared r0 PRO/DRU -> fresh basename -> DRC -+--> receipt
candidate PCB -------> via delta/connectivity-+    ACCEPTED
candidate PRO/DRU ---X (ignored)                    REJECTED
                                                    INCOMPLETE
```

The workspace is append-free and relocatable. It contains the candidate as
`subject.kicad_pcb`, prepared sidecars as `subject.kicad_pro/.kicad_dru`, raw
reports, and `receipt.json`. A second grading run uses a new workspace; it does
not overwrite the first verdict.

```bash
python3 skills/kicad-pcb/scripts/route_candidate_workspace.py grade \
  --prepared PROJECT/06_build/route/r0.kicad_pcb \
  --candidate PROJECT/06_build/route/r7.kicad_pcb \
  --workspace PROJECT/06_build/route/grades/r7-SHA \
  --required-net I2C_SCL --required-net I2C_SDA

python3 skills/kicad-pcb/scripts/route_candidate_workspace.py verify \
  PROJECT/06_build/route/grades/r7-SHA/receipt.json
```

## Minimal acceptance tests

| Case | Expected |
| --- | --- |
| Candidate sidecar relaxes USB clearance | ignored; authoritative DRC rejects |
| Prepared sidecar or tool output missing | INCOMPLETE, never clean |
| Workspace sidecar changes after receipt | receipt verification fails |
| Entire accepted workspace is relocated | receipt still verifies |
| Required net remains open | REJECTED |
