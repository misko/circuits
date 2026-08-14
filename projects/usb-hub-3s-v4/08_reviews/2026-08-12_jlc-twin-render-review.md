subject: usb-hub-3s-v4 2c15f1dd1ef600bed4c6081062bc7f3640c25237 JLC digital-twin render
date: 2026-08-12
reviewer: render-review (fresh-context human JLC digital-twin lens)
context-given: full-tree
source_commit: 2c15f1dd1ef600bed4c6081062bc7f3640c25237
board_sha256: 9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb
design_verdict: SOUND
order_verdict: DO-NOT-ORDER

# Fresh-context JLC digital-twin render review

## Verdict

The exact render set below is visually faithful enough to support the routed
design: the populated bodies that the images can resolve are registered to
their footprints, no grossly rotated or displaced housing is visible, and the
top, two isometric and two edge views agree about position and height. The
automated top overlay independently reports `a-render_verdict: PASS` against
the same exact board.

This is not permission to order. C23 has no JLC model and its polarity cannot
be inspected locally; its adjudication explicitly requires the JLC order
preview to show the negative stripe opposite board pad 1. Other declared
JLC-preview, resolved-BOM, uploader and first-article duties also remain open,
as enumerated below. Nothing in this review changes those gates.

## Exact evidence reviewed

All digests are SHA-256. The source commit identifies repository ancestry;
the hashes below are the authority for the reviewed bytes in the dirty working
tree.

| artifact | SHA-256 |
|---|---|
| `04_kicad/usb_hub_3s_v4.kicad_pcb` | `9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb` |
| `06_build/twin/twin.kicad_pcb` | `66bd660312e11c1d4c3cd23d0d3907777168de009e45462f33165786769be0f1` |
| `06_build/twin/twin_top.png` | `9c76ad3f0af3d98c9de85ce811ea24642c874dc61a01cbde8dd02aee2bea49c0` |
| `06_build/twin/twin_bottom.png` | `d32aabec7124bc110f13eaa7750cf4f994d1ca01e166c97dfd39806f19114bc9` |
| `06_build/twin/twin_iso_nw.png` | `42784e125a2f8507c0fc65021af060a30331e578954ba22084e61361c5fe5cd9` |
| `06_build/twin/twin_iso_se.png` | `64fd48ae915d86e3a5df82da9cfa3831eb67177f44998db8e417ae315a72d0ec` |
| `06_build/twin/twin_edge_west.png` | `1bef7431b3e821a53dea2daca24e37f4b748c012538e5639568aac354dc23f68` |
| `06_build/twin/twin_edge_east.png` | `526dcff6217386e1672b116bfb2ef816a226178e5fcd51e897fc178b403c5154` |
| `06_build/twin/twin_bare_top.png` | `896173dba7a3e535323ead8b7f294df10c6fb0b7a3928a508f3b505aac6110af` |
| `06_build/twin/twin_bare_bottom.png` | `2109230ca4f692eb58b2d2908a4103ea58cf336473bb04f3d8c5511cda4da11f` |
| `06_build/twin/twin_report.csv` | `62aaecae32ff8a9db36ef855522918af21a1a4b9a6993f62939a1c28c7bb884c` |
| `06_build/verification/twin_overlay.md` | `0ce8ab0e6ee84d22e787efdeee6ae24bac47ee08d0f8301af12bfd4428fec6ba` |
| `06_build/twin/overlay_top/twin_top_courtyard_overlay.png` | `0c4e49a96f579e5e4b5c1ad4c4955eba4c0fb2c577c27f1cd3430c1eb3f5cb81` |

The duties retained by this review were read from these exact bytes:

| duty source | SHA-256 |
|---|---|
| `03_src/rules/twin_adjudications.yaml` | `e94e67e8a7c55bb3cf9ae273b51193e2a82e143d5c8740b5edb61e7ab08895e2` |
| `03_src/rules/assembly.yaml` | `e27bad9fbb6337124bbd524b415cde4a784325f5afbc962ad0bc57d0e91c9753` |
| `06_build/fab/rotation_human_gate.txt` | `035950f76ebbadc3c397973e476e114c94079554128e9e80b757d3facbca1b6c` |
| `06_build/fab/bom_echo_gate.txt` | `6d5604fe7ceffee6a9626ea26c0d71bb604c6311815b1114f113860ccff8c407` |

## Automated overlay boundary

The exact overlay report binds board SHA-256 `9888b126...` and reports:

- `a-render_verdict: PASS`;
- orthographic calibration of 7.4174 px/mm by 7.4251 px/mm, anisotropy
  0.9990;
- 35 measured bodies out of 69 refs with an expected body;
- 34 bodies named as unresolvable by construction, zero resolvable bodies
  omitted from measurement, and 7 refs with no JLC model at all;
- zero measured body beyond the 1.00 mm centre/outward tolerance.

That pass establishes render faithfulness only for what it measured. It does
not convert the 34 unresolvable or 7 model-less refs into visual passes, and it
does not answer polarity when the model/footprint marking channel is blind.

## Human image findings

| ref(s) | what the current images can establish | what remains open |
|---|---|---|
| Q1 | The crop and both isometrics show the housing centred on the footprint, with no gross 90/270-degree displacement. Expected and measured boxes coincide closely (`0.071 mm` centre delta, `0.059 mm` outward). | The scene uses `MOUNT-FALLBACK` after the generic JLC land fails the exact manufacturer-land fit. The image does not independently prove source/gate/drain mapping or pin-1 rotation. The declared JLC-preview rotation check remains open. |
| D1 | The SMB body and both metal end caps are centred over the two lands; expected and measured outlines agree (`0.097 mm` centre delta). | No unambiguous cathode band is visible. `POLARITY-FIT-BLIND` is therefore correctly unresolved; the JLC order preview must confirm cathode/pad 1 at VIN and anode/pad 2 at GND. |
| D5 | The small SOD-123 body appears centred, and its visible left-end band is consistent with the left/pad-1 cathode end of the board land. | A-RENDER classifies the 1.60 mm minor dimension below its resolvability floor, so this is visual consistency rather than pixel metrology. Final preview inspection remains prudent and is not waived here. |
| C17, C18, C19 | All three cans are upright and centred. Each rendered dark polarity sector is on the right, opposite the board `+` mark/pad 1 on the left; the local twin is visibly non-reversed. Expected/measured registration deltas are `0.136`, `0.162`, and `0.063 mm`. | These refs are still named by the single-channel `rotation_human_gate.txt`; their JLC order-preview check remains open despite the locally consistent image. |
| C22 | The can is centred. Its pink polarity sector is on the right, opposite the board `+` mark/pad 1 on the left; the local twin is visibly non-reversed. Expected/measured centre delta is `0.443 mm`, inside the gate. | C22 remains on the declared single-channel JLC order-preview gate. |
| C23 | The crop correctly shows only pads, courtyard and the board `+` mark; there is no body to inspect. | Explicit blocker: JLC's order preview must show the negative stripe opposite board pad 1. No local polarity or body-registration conclusion is possible. |
| J5 | Top, crop and isometric views show the Type-C shell centred on the contact field and stakes, square to the south edge, with the receptacle mouth projecting across the board edge as intended. Expected/measured centre delta is `0.166 mm`. | The adjudication's JLC order-preview body-registration check remains open; the image does not waive uploader-side confirmation. |
| U1 | The module housing is square and centred over its land/via field; the crop has coincident expected/measured boxes (`0.224 mm` centre delta). | The body hides the pad field and does not provide an independent board-to-model pin-1 proof. U1 remains on the declared JLC order-preview rotation gate. |
| SW1 | The current full top and isometric renders show the through-hole switch body seated over its three holes, long axis aligned with the `OFF / ON` legend. A-RENDER measured it at `0.077 mm` centre delta. | SW1 is hand-soldered, not a JLC placement. Common/OFF pin identity, actuator direction, seating and OFF-state EN_BUS-to-GND continuity remain first-article checks. The standalone `overlay_SW1.png` is not used: it predates the current `twin_top.png` (06:37:31 versus 06:38:07 local time), contains no switch body, and is not named in the current overlay report's per-ref crop list. |
| U3 | The flagged crop shows its body square and centred; expected and measured boxes coincide, and the report records `MODEL-REG-OK`. | U3 remains on the declared single-channel JLC order-preview rotation gate. |
| J1 | The crop has no body. The board pads, outline and `+ BAT` / `- GND` legends are visible, but seating and terminal orientation cannot be inferred from an absent model. | Hand-soldered J1 physical seating, edge access, terminal retention, joints and first-power polarity/continuity remain first-article duties. |
| J2, J3, J4 | The crops have no connector bodies; only holes, outlines and edge datums are visible. | Hand-soldered connector seating, shell/signal joints, edge alignment, mating access and contact continuity/short tests remain first-article duties. |
| R24, R5 | Their crops show exposed standard 0603 lands because the JLC library fetch failed. They are unpolarized, so the absent body creates no polarity ambiguity. | The images cannot establish body registration. The exact-code library-absence adjudications remain the applicable evidence. |

The bottom render is unpopulated as declared. The edge views show no gross
height collision or underside body, but they cannot clear enclosure fit or
the absent J1/J2/J3/J4 bodies. F1's rendered local body is an envelope aid,
not a JLC placement instruction.

## Per-ref crop hashes

These are every supplied `overlay_*.png`, including the extra stale SW1 crop
identified above.

| crop | SHA-256 | crop | SHA-256 |
|---|---|---|---|
| `overlay_C17.png` | `c34e30f0b4185e166bf46766259f0adf18f2395acb138b1e950a7c92acc6ee9f` | `overlay_C18.png` | `851fdfdb60615219294bc8e7e0456552627e83c1d8e548d8bd1e3f7b358dfc78` |
| `overlay_C19.png` | `ba555e172034276295b6e2c19154574c1f28997d4bc485738f86667d96b6148f` | `overlay_C22.png` | `369a05004c95dd1e4b2e556fd369403f3b4c1e1ac1a2043357420620f04babc6` |
| `overlay_C23.png` | `474535f6e215744b5d8a0b15d672efd62072e20cae01f6373da27e9a5b4fbb97` | `overlay_D1.png` | `4ceea64a8d87f83dc3ba1a2e05995b762324223e960fdfe6be15090ac3eedf6c` |
| `overlay_D5.png` | `4bb22157b8aced9897bf47491410a52363b74782413744d8273a2ca17c58395e` | `overlay_J1.png` | `59562b9d598e0aa358c1aff3d5911dbe1f7e74d933a8fb0c49eaa355e0088ed4` |
| `overlay_J2.png` | `f3dfbe59d8291a9ac4b34a3304f394067a3c1df320df0ad42ac7ae372821a0dc` | `overlay_J3.png` | `00b8039868c2264c48bfaa28766a3a3cc11df8be40aab2ea91d192fd3bbf254b` |
| `overlay_J4.png` | `188bb605d39479dbd3aafb2479c20e9f65530dc193ee7306533e239848209f4f` | `overlay_J5.png` | `3c22d71583d8aca478a0d41a694fd7676402b948c6f2658096b07d09564f8e61` |
| `overlay_Q1.png` | `fc14db98b33256f40540809673cefc19bb103cfdb215790015920c1b47dd4f70` | `overlay_R24.png` | `ab59fb38f33cc493e7728812acaf3cec1a937c5356f79877b028e72f87c9ad79` |
| `overlay_R5.png` | `068a1b24c0882f169f74f518e43fe07bb6a005f8ff4a1eb7242a9000a8081c1d` | `overlay_SW1.png` | `92dcafe613ab2a04721630cc7393019bc009f003b63c4e7b13934eceb2a6a4d8` |
| `overlay_U1.png` | `5543d5e5fc45c518c28d052d700cc2b8489a0e8c57b8cfd67f706f978d8edf76` | `overlay_U3.png` | `bae64a6ca54063ec18133af4341f26eca4d9d751b049516d1d3868e6ad24773a` |

## Duties explicitly not closed by this review

- JLC order-preview rotation remains open for every ref named by
  `rotation_human_gate.txt`: U4-U6, C17-C19, C22, U7-U8, U3, U1, D2-D4 and
  C1.
- The adjudication-specific JLC preview duties remain open for Q1 rotation,
  D1 cathode-band polarity, J5 body registration and C23 polarity/rotation.
- F-ECHO remains open: JLC's resolved/matched BOM must be saved after upload
  and diffed against the project's BOM. Same-day stock/substitution review
  remains an order-day measurement.
- The Type-VII copper-paste-filled/copper-capped 0.20 mm drill-family choice
  still requires explicit uploader confirmation. Layer/process/quantity and
  the actual BOM/CPL preview remain order-form duties.
- Hand-solder and first-article checks remain open for F1, J1, J2-J4 and SW1,
  including joints, continuity, seating, edge/mating access and terminal or
  actuator orientation. The first powered article must independently meter
  input polarity/continuity before applying the battery.
- All project-wide hardware-only electrical, thermal, transient, dynamic,
  interconnect and supervised-use acceptance duties remain open. A render
  cannot discharge them.

Accordingly, the render lens finds no board-design defect, while the order
verdict remains `DO-NOT-ORDER` until the declared upload-side gates are
performed and accepted.
