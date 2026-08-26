# Exact connector-orientation evidence

board_sha256: c5cd719571e216224c83aca142ac84e1f11facdfb48b1bcb771c9d5b97c06e68
machine_verdict: PASS
human_approval: APPROVED 2026-08-17
human_approval_evidence: orientation_approval.md
subject_sha256: 8a7f766c33855e7c9b325d1f792f928b0fd38197eb61d7f13969415eaea65f97
orientation_receipt_sha256: 8a057d61d5e9f209b5c2ee168536ed63a41f02743986e4b2469d132e594a8b86
orientation_review_sha256: d72f2c0344571b0e0a37ff1e0eadc292a934eff8c52038aa53a5523395af6cab
model_registration_config_sha256: 31755338cd2217d0a1510cc22cb7450099da19ddc926b74657ae3ad9775d9f46
floorplan_sha256: b85beebc8e1acbf1ffcd4aa4cb6daae7eec005eaaf10f0443fec09fd81f76df7

| connector | physical access | machine measurement | visual disposition |
|---|---|---|---|
| `J_PORT1..4` | north/outboard, top-mounted USB-A mouths | 13.70 mm origin-to-edge; mating plane -0.21 mm inboard; model/footprint axis 1.000; 4/4 PASS | `J_PORT1` representative top/outside/inside views show the keyed mouths from the cable side and rear shells from inside; row spacing leaves independent cable approaches. |
| `J_UP` | west/outboard, top-mounted USB-B mouth | 12.20 mm origin-to-edge; mating plane +0.25 mm outboard; model/footprint axis 1.000; PASS | Top/outside/inside plus both orthogonal profiles show the mouth west, rear east/inboard and body above the PCB. |
| `J_PWR` | southwest, side-entry two-position terminal | P-MODEL-REG PASS; intentionally exempt from edge-mouth P-ORIENT | Exact twin shows unobstructed wire-entry and screwdriver access. Hardware is non-polarized; board silk identifies lower pad 1 as `+5V` and upper pad 2 as `GND`. Confirm its THT side and polarity in JLC preview. |

The tool-generated images and hash-bound receipt are in `orientation/`. The
user/product owner approved this exact subject on 2026-08-17 after reviewing
the representative populated-top and outboard connector views. The approval is
recorded in `orientation_approval.md`; any board or subject hash change is a
stop condition and requires a new review.
