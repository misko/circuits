# Connector orientation review

machine_verdict: PASS
subject_sha256: f238832c6b768680454e9da4491e56e18fe7baffbe6ddaaa1b643980bb84ea7d
board_sha256: a0acddd9b0b4e1888583ffacad43f2c2446e76cb040ebc64844cd25779a73987

| ref | board access axis | edge | edge distance mm | mating-plane edge offset mm | model/footprint alignment | verdict |
|---|---|---|---:|---:|---:|---|
| J_DATA | [-1.0, 0.0, 0.0] | west | 3.65 | 0.0 | 1.000000 | PASS |
| J_PORT1 | [0.0, -1.0, 0.0] | north | 13.7 | -0.21 | 1.000000 | PASS |
| J_PORT2 | [0.0, -1.0, 0.0] | north | 13.7 | -0.21 | 1.000000 | PASS |
| J_PORT3 | [0.0, -1.0, 0.0] | north | 13.7 | -0.21 | 1.000000 | PASS |
| J_PORT4 | [0.0, -1.0, 0.0] | north | 13.7 | -0.21 | 1.000000 | PASS |
| J_POWER | [-1.0, 0.0, 0.0] | west | 3.65 | 0.0 | 1.000000 | PASS |

## Human-review representatives

| representative | machine-graded refs | tuple |
|---|---|---|
| J_DATA | J_DATA, J_POWER | `12099f9889cb8750` |
| J_PORT1 | J_PORT1, J_PORT2, J_PORT3, J_PORT4 | `ccd8eb03842311ac` |

## Machine findings

- none

## Machine notes

- J_DATA: orthogonal profiles omitted for repeated tuple ['J_DATA', 'J_POWER'] because edge-row instances can occlude one another
- J_PORT1: orthogonal profiles omitted for repeated tuple ['J_PORT1', 'J_PORT2', 'J_PORT3', 'J_PORT4'] because edge-row instances can occlude one another

## Human confirmation

Review every present image. Each ref requires `top`, `outside`, and `inside`; orthogonal profiles are included when the target is not occluded by another connector. Approve only when the visible mouth/access direction, mounting side, keying, and cable approach agree with the intended physical use.
