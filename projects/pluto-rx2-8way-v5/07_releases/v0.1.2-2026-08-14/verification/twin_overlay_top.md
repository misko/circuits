# Native STEP registration overlay — `twin_top.png`

board_sha256: `43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3`

render_source: exact project/release board, not the substituted JLC WRL twin

SMA_model: `Amphenol_901_143_6RFX-JLC-C429844.step`

SMA_model_sha256: `17cbdea22e6ca94e56fb0facf4c7642df6b57fb94bc9835af2bbe51b7e712aba`

populated_top_sha256: `88856e26aab5bdf0bafbfba613cbeab4b1b08ea792bdac09713cb30df3bfb1e7`

overlay_sha256: `933ebcdca69d0efed17ed36621facd4a14b290423c98b96fbfa3e5bf57a48905`

registration_visual_verdict: **PASS for J2-J10**

previous_A-RENDER_physical-registration_claim: **WITHDRAWN**

## What this image proves

The populated top image was rendered directly from the exact board whose hash
is recorded above. That board mounts the provenance-bound native exact-code
STEP for every 901-143-6RFX. The image does not use the converted JLC WRL with
SHA-256
`983aafa89b4aff89d30dfcdeac276708bf5e7bf6800ccdfebc1542440aae5d50`,
whose internal XY registration is rejected.

The overlay uses two independent input channels:

- footprint courtyards, pad centres and drill diameters come from the exact
  saved KiCad board;
- the green envelope comes from pixels changed between populated and bare
  renders made with the same orthographic camera and resolution.

Calibration is 10.7103 px/mm X and 10.6912 px/mm Y, anisotropy 1.0018.

## Legend

- **Orange:** footprint `F.CrtYd`.
- **Cyan:** plated-hole centres and attachment field; the cross is signal pad
  1.
- **Green:** populated-minus-bare rendered native-model pixel envelope.
- **Blue:** PCB edge.

## SMA attachment-field result

| Ref | Five drill centres inside rendered envelope | Minimum centre-to-envelope margin |
|---|---:|---:|
| J2 | 5/5 | 0.588 mm |
| J3 | 5/5 | 0.556 mm |
| J4 | 5/5 | 0.524 mm |
| J5 | 5/5 | 0.556 mm |
| J6 | 5/5 | 0.563 mm |
| J7 | 5/5 | 0.577 mm |
| J8 | 5/5 | 0.629 mm |
| J9 | 5/5 | 0.588 mm |
| J10 | 5/5 | 0.621 mm |

Total: **45/45 plated-hole centres lie inside their own rendered native-model
envelope**, including all nine unique signal-pad centres. Top, isometric and
edge images also show the connector legs crossing the board at those fields
and all mating barrels facing outward.

## Scope and superseded evidence

This is a focused visual/pixel-envelope registration witness. It does not yet
implement the reusable hash-cached `P-MODEL-REG` receipt specified by IMP-055,
and it does not claim automatic STEP leg-feature recognition.

The earlier v0.1.2 green/magenta A-RENDER result measured pixels from the
converted WRL against expectations derived from the same converted WRL. That
was renderer self-consistency, not physical model registration. The JLC twin
report remains useful for catalog part, land-pattern and drill comparison, but
its C429844 model-registration adjudication must not be used as authority for
these final PNGs.
