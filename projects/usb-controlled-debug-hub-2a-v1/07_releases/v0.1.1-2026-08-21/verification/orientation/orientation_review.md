# Connector orientation review

machine_verdict: PASS
subject_sha256: 475cf8ff51ff459bd325a8cb987313a4d6f2fbbfc2ba1918bf218ba7b2f145d8
board_sha256: 78e0c6a1c3c2e4435b5f478808e113000c72d606aca05e29cbb425a85f4fa1dd

| ref | board access axis | edge | edge distance mm | mating-plane edge offset mm | model/footprint alignment | verdict |
|---|---|---|---:|---:|---:|---|
| J_DATA | [-1.0, 0.0, 0.0] | west | 3.65 | 0.0 | 1.000000 | PASS |
| J_PORT1 | [0.0, -1.0, 0.0] | north | 5.8 | -0.08 | 1.000000 | PASS |
| J_PORT2 | [0.0, -1.0, 0.0] | north | 5.8 | -0.08 | 1.000000 | PASS |
| J_PORT3 | [0.0, -1.0, 0.0] | north | 5.8 | -0.08 | 1.000000 | PASS |
| J_PORT4 | [0.0, -1.0, 0.0] | north | 5.8 | -0.08 | 1.000000 | PASS |
| J_POWER | [-1.0, 0.0, 0.0] | west | 3.65 | 0.0 | 1.000000 | PASS |

## Human-review representatives

| representative | machine-graded refs | tuple |
|---|---|---|
| J_DATA | J_DATA, J_POWER | `30cbb9572621b06e` |
| J_PORT1 | J_PORT1, J_PORT2, J_PORT3, J_PORT4 | `91f00cac357c88af` |

## Machine findings

- none

## Machine notes

- J_DATA: orthogonal profiles omitted for repeated tuple ['J_DATA', 'J_POWER'] because edge-row instances can occlude one another
- J_PORT1: orthogonal profiles omitted for repeated tuple ['J_PORT1', 'J_PORT2', 'J_PORT3', 'J_PORT4'] because edge-row instances can occlude one another

## Human confirmation

Review every present image. Each ref requires `top`, `outside`, and `inside`; orthogonal profiles are included when the target is not occluded by another connector. Approve only when the visible mouth/access direction, mounting side, keying, and cable approach agree with the intended physical use.
