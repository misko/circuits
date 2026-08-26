# Connector orientation review

machine_verdict: PASS
subject_sha256: 8a7f766c33855e7c9b325d1f792f928b0fd38197eb61d7f13969415eaea65f97
board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68

| ref | board access axis | edge | edge distance mm | mating-plane edge offset mm | model/footprint alignment | verdict |
|---|---|---|---:|---:|---:|---|
| J_PORT1 | [0.0, -1.0, 0.0] | north | 13.7 | -0.21 | 1.000000 | PASS |
| J_PORT2 | [0.0, -1.0, 0.0] | north | 13.7 | -0.21 | 1.000000 | PASS |
| J_PORT3 | [0.0, -1.0, 0.0] | north | 13.7 | -0.21 | 1.000000 | PASS |
| J_PORT4 | [0.0, -1.0, 0.0] | north | 13.7 | -0.21 | 1.000000 | PASS |
| J_UP | [-1.0, 0.0, 0.0] | west | 12.2 | 0.25 | 1.000000 | PASS |

## Human-review representatives

| representative | machine-graded refs | tuple |
|---|---|---|
| J_PORT1 | J_PORT1, J_PORT2, J_PORT3, J_PORT4 | `ccd8eb03842311ac` |
| J_UP | J_UP | `da45208aacc01cce` |

## Machine findings

- none

## Machine notes

- J_PORT1: orthogonal profiles omitted for repeated tuple ['J_PORT1', 'J_PORT2', 'J_PORT3', 'J_PORT4'] because edge-row instances can occlude one another

## Human confirmation

Review every present image. Each ref requires `top`, `outside`, and `inside`; orthogonal profiles are included when the target is not occluded by another connector. Approve only when the visible mouth/access direction, mounting side, keying, and cable approach agree with the intended physical use.
