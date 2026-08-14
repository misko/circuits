review_kind: render_review
subject: pluto-rx2-8way-v5 v0.1.2 native-model render correction
date: 2026-08-14
reviewer: Codex visual, 3D, mechanical and assembly reviewer
independence: fresh exact-artifact inspection; no previous render verdict inherited
evidence_scope: verification-only native-model PNG correction
source_commit: ba42fc9dba7f149f4187f50ef4fff697f0ed2a7a
release: projects/pluto-rx2-8way-v5/07_releases/v0.1.2-2026-08-14
board_sha256: 43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3
design_verdict: SOUND
production_verdict: HOLD
order_verdict: DO-NOT-ORDER
p0_design_findings: 0
p1_design_findings: 0
p2_design_findings: 0

# Exact-artifact native-model render and assembly review

## Verdict

The unchanged exact staged board remains **SOUND** through the visual,
component-access, assembly-population, silk, copper-presentation and mechanical
lenses. Production remains **HOLD** and ordering remains **DO-NOT-ORDER**
pending the real JLCPCB preview/process echoes and physical first article.

The six final populated PNGs are now rendered directly from the exact source
board. J2-J10 therefore use the provenance-bound native 901-143-6RFX STEP with
SHA-256
`17cbdea22e6ca94e56fb0facf4c7642df6b57fb94bc9835af2bbe51b7e712aba`,
not the internally misregistered converted WRL. No schematic, PCB, footprint,
placement, Gerber, drill, BOM, CPL or assembly STEP changed.

The previous v0.1.2 A-RENDER result is withdrawn as physical-registration
evidence. It compared a render of the converted WRL with an analytic
expectation derived from that same WRL, so agreement proved renderer
self-consistency rather than model-to-footprint correctness.

## Evidence

| Evidence inspected | SHA-256 / result |
|---|---|
| Exact populated top | `88856e26aab5bdf0bafbfba613cbeab4b1b08ea792bdac09713cb30df3bfb1e7` |
| Isometric northwest / southeast | `d6ea652058c48c9febfc1aae3976a2731c086bb5d7083086a1e64084fe544472` / `140e9b894b58da121b585eb2e7d9ca13582dad64f773dd2ad02ffdc5e66aa578` |
| East / west edge views | `4bfb81859d54436c56a1fa3776970bba483dab208fe8235fbaf052186b05051f` / `ea867a72a5b4bda0e7d1b8c77580bda7c01f0dcf57dfefcd8c7b37cac9df5d72` |
| Populated bottom | `4c7b0c3f337de96a48fa5f5646d7f297362080335aa7fa510e281727c0ffe4ba` |
| Native registration overlay | `933ebcdca69d0efed17ed36621facd4a14b290423c98b96fbfa3e5bf57a48905` |
| Native SMA STEP | `17cbdea22e6ca94e56fb0facf4c7642df6b57fb94bc9835af2bbe51b7e712aba` |
| Exact board | `43689fe44daa2bd437979c573e78da39a51aacd9d4664a24e7e29bc1c22ea0b3` |
| Model coverage | 29/29 fitted footprints resolve; zero missing. |
| SMA attachment field | 45/45 plated-hole centres inside the rendered native-model envelopes; minimum margin 0.524 mm at J4. |

## Visual and mechanical findings

- Five north-edge SMA connectors and two connectors on each side face outward.
  Top and isometric views show each native body centred over its five-hole
  field; edge views show its legs crossing the PCB rather than sitting beside
  it. No barrel approach is blocked.
- The registration overlay embeds its legend. Orange is the footprint
  courtyard, cyan is the plated-hole attachment field with a cross at signal
  pad 1, green is the independently measured populated-minus-bare model-pixel
  envelope and blue is the PCB edge. Every one of the 45 SMA hole centres lies
  inside the corresponding green envelope.
- The south-edge USB-C receptacle opens outward and is labelled `POWER ONLY`.
  The keyed 2x5 J11 SWD header has unobstructed vertical cable access. Four
  corner mounting holes remain clear.
- U1-U4, D1, F1, C1-C6 and R1-R6 are present and seated on their intended top
  lands. Port labels `PLUTO RX` and `ANT1` through `ANT8`, the frequency
  legend, `USB-C POWER ONLY` and `KEYED SWD J11` correspond to the rendered
  interfaces.
- Ordinary through-hole tails below the PCB require normal trimming and
  enclosure/standoff clearance.

## Evidence boundary and retained human gates

The JLC twin report remains catalog evidence for exact part codes, land
patterns and the real 0.10-mm JLC-versus-manufacturer SMA drill difference. Its
C429844 converted-WRL model-registration adjudication is superseded and is not
authority for these PNGs. The reusable automated `P-MODEL-REG` receipt from
IMP-055 is still implementation work; this correction is a focused visual and
pixel-envelope witness using the approved native STEP.

The live JLCPCB preview must still show nine SMA barrels and J1 opening
outward; J11 pin 1/key orientation; D1 polarity; U1/U2 orientation; exact
manufacturer-authoritative SMA, J11, D1 and USB-C lands; and all intended
fitted references. It must also accept exact C429844 for the declared
through-hole process. No render evidence waives uploader DFM, stackup,
impedance, via-fill or first-article obligations.

Severity summary: P0/P1/P2 design findings **0/0/0**. No render-driven board
change is requested; remaining work is external order validation and physical
qualification.
