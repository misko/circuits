subject: programmable-usb2-hub exact placed board a03a05e83f32
date: 2026-08-02
reviewer: fresh independent pin-review agent (GPT-5, adversarial physical-pin/package-land lens)
context-given: exact placed board, current circuit.json, current part dossiers, SHA-selected local manufacturer PDFs, exact local footprints/models, and pin-review protocol; prior review verdicts excluded as authority
review_stage: pre-route
review_kind: pin
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: a03a05e83f32df6a6104a24dea888683618e7b5fe40e6b70904f6959b98f63ed
parts_sha256: 2a498042bcf6166713dbbe90aacc63134cd30edf3ed4cd3094327b4e1af19854
design_rules_sha256: d732d22b90dbae6f31d9099d2c789ab06df32d96e2c43e207232c55faa24100e
circuit_json_sha256: ef8b92784881a561614181f0f2ea4357d5ed6a5a3e23bf6f4d25b07bd19e85aa
phoenix_dossier_sha256: 0a76f58769a541659878fd089db38a7ee937691483eafbadb56f04c3b99843a6
phoenix_pdf_sha256: 760ff908523dd6eccff7d1c8accbd8bedce0bf8e57bc1cbe3cc2485c7b98e83a
phoenix_footprint_sha256: c5ae63346f73e2d07b03f03783f4e110f8839481e97ad2bcc8fa7b3a4c7210ec
phoenix_model_sha256: f3626bbcbe789ed874ed67dc39bced198667a7618d2682017b876ceec3553ffc
tdk_dossier_sha256: c067cb4d482635fcc64a57d53554084349219e31770bf058f76578a5eed966ea
tdk_pdf_sha256: 237d4767bf558f38bdaeffda2cedf203aa5ce3e208bb5c708acf175002f25127
tdk_footprint_sha256: 641866d3df6d33cf9dbdcceb1a9b6516ce16113e9d48202f0d869871f34b22b3
r3_dossier_sha256: 1d216303bf2450eb7539e7fff274a5957d6eb06bf9723cfb280bf90991ea5a6d
r3_28758_pdf_sha256: d4043c24ae541c92e891ffbb58991966b7ddfbd498828c37f5a0e5323804b3e3
r3_28950_pdf_sha256: 9e2b145c937da3be1e926b8afc2856959754eeb4d1103241d838038f7308144e
twin_adjudications_sha256: 08cb3549b2a4baa23a1d1e81735cc83c62f6ab9a41c13e94ac5c6e2366a4e388

# Independent pre-route physical-pin and package-land review

## Verdict

No P0 or P1 physical-pin, winding, exposed-pad, pair-polarity, package-land,
or exact-evidence finding remains on the hash-bound board. The design is
**SOUND to proceed to routing** under this lens.

This is not an order authorization. Routing, copper/thermal realization,
filled-zone and DRC evidence, fabrication outputs, sourcing, assembly, and
release qualification remain downstream gates; therefore `order_verdict`
remains `DO-NOT-ORDER`.

- P0 findings: none.
- P1 findings: none.
- P2 findings: none.
- P-PINMAP: **PASS**, 33 multi-pin references and 405/405 declared physical
  pin identities graded.
- S-COUNT: **PASS**, 4/4 representations agree with the manifest over 211
  refdes (board, circuit JSON, KiCad schematic, and netlist).
- Exact board/netlist parity: **PASS**, 0 discrepancies over 151 nets and 708
  connected nodes; both sides contain the same 57 explicit no-connects.

The machine results above establish source/board consistency only. The PASS
verdicts below were derived independently from the SHA-selected manufacturer
documents and then compared with the exact board pads and nets, as required by
the fresh-context pin-review protocol.

## Corrected exact packages

### J1 — Phoenix Contact 1935161 / PT 1,5/2-5,0-H / C3819953

**VERDICT: PASS**

The dossier now selects Phoenix Contact MPN `1935161`, and its declared PDF
digest exactly matches the vendored Phoenix-generated catalog PDF:
`760ff908523dd6eccff7d1c8accbd8bedce0bf8e57bc1cbe3cc2485c7b98e83a`.
That document identifies the exact two-position PT 1,5/2-5,0-H product and
states 5.00 mm pitch, 1.0 mm pins, 1.3 mm finished holes, 9 mm length,
11.3 mm height, and 17.5 A nominal current. The prior Kangnex WJ126V evidence
is no longer selected or used.

The exact board embeds `Phoenix_1935161_PT_1p5_2_5p0_H` with two 2.20 x
2.20 mm lands, 1.30 mm drills, and 5.00 mm pad-center pitch. Its fab outline
is 10.0 x 9.0 mm and the courtyard is 10.5 x 9.5 mm. At the board's legal
90-degree rotation, pad 1 is the rectangular pin-1 land at (25.5, 97.0) mm on
`VIN_RAW`; pad 2 is at (25.5, 92.0) mm on GND. The connector hardware is
non-polarized, so this is the intentional board polarity assignment, not a
manufacturer pin-direction claim.

The board also references the exact local JLC C3819953 model
`C3819953-1935161.wrl` at scale 1 and rotation 0. Its SHA-256 is
`f3626bbcbe789ed874ed67dc39bced198667a7618d2682017b876ceec3553ffc`.
The model's two terminal axes are approximately +/-2.49 mm about its local
origin; the footprint's +2.5 mm X offset registers them to pads at 0 and
5 mm. Its point cloud spans 9.00 mm in the body-depth axis and reaches
11.30 mm above the board datum, independently agreeing with the Phoenix
envelope. No mirror, 5.08 mm substitution, drill mismatch, or model-origin
error remains.

### L6 — TDK B82477G4333M000 / B82477G4 / C2045462

**VERDICT: PASS**

The dossier now declares
`237d4767bf558f38bdaeffda2cedf203aa5ce3e208bb5c708acf175002f25127`,
which exactly matches the vendored `b82477g4.pdf`. The SHA-selected TDK table
identifies B82477G4333M000 as 33 uH +/-20%, 3.00 A thermal current, 3.50 A
saturation current, and 0.053 ohm maximum DCR. The IND0493-B recommended land
drawing gives the geometry used on the exact board: two 3.10 x 5.60 mm lands,
7.00 mm inner gap, 10.10 mm center span, and 13.20 mm outer span.

Pad 1 is on `AUX_SW` and pad 2 is on `AUX_6V`, placing the non-polarized
winding in series with the LMR36510 output. A missing or mirrored identity is
not possible for this symmetric two-terminal winding, and no selected-PDF
digest mismatch remains. L6 has no attached 3D model; that does not weaken
its two-pad electrical/package-land proof and remains a render/twin concern,
not a pin-review blocker.

## Full required component sweep

Every remaining component group was re-read from its selected exact datasheet
and compared to the pads and nets on this board. Rotation is accepted; no
mirror is accepted.

| references / package | independent expectation and exact-board comparison | verdict |
|---|---|---|
| U1 / LM74810 WSON-12 + pad 13 | CCW pins 1-12 are present; DGATE, VIN_FUSED, OV/UV sense, GND, HGATE, VIN_PROTECTED, common-drain FET_MID and CAP classes are correct. RTN pad 13 is explicitly unconnected as intended. | PASS |
| U2 / LTC3889 UKG52(46) + pad 53 | The top-view CCW perimeter omits only positions 3, 37, 41, 45, 49 and 51; all other 46 perimeter leads exist. Sixteen pad-53 tiles are all GND. SW/TG/BG/BOOST, ISNS, feedback, supplies and configuration identities remain channel-correct. | PASS |
| U3 / LMR36510 DDA0008B + pad 9 | PGND=1, VIN=2, EN=3, PG=4, FB=5, VCC=6, BOOT=7 and SW=8 match GND, VIN_PROTECTED, VIN_PROTECTED, AUX_PG_N, AUX_FB, AUX_VCC, AUX_BOOT and AUX_SW; pad 9 is grounded. The 1.55 x 0.60 mm perimeter lands, 5.40 mm opposing span, 1.27 mm pitch, 2.95 x 4.90 mm EP and six 0.20 mm vias match TI's land example. | PASS |
| U4 / AP63203 TSOT-23-6 | FB/EN/VIN/GND/SW/BST remain on pins 1-6 in the published top-view order. | PASS |
| U5, U17-U20 / USBLC6-2SC6 | IO1/GND/IO2 and IO2b/VBUS/IO1b remain on pins 1-6. D+/D- polarity is preserved through all five arrays. | PASS |
| U6 / USB2517 QFN-64 + pad 65 | All 64 perimeter pins and grounded pad 65 exist. Every upstream/downstream D-/D+ pair, power-control group, clock, PMBus and supply identity matches the Microchip top view; unused functions remain explicit no-connects. | PASS |
| U7 / STM32G0B1 LQFP-48 | The pin-1 corner and CCW winding are a pure rotation of the ST top view. Supply, USB, SWD, I2C, ADC, command, fault, clock and reset nets remain on their published pins. | PASS |
| U8 / 74LVC08A TSSOP-14 | All four A/B-to-Y gate groups, GND pin 7 and VCC pin 14 match the Nexperia order. | PASS |
| U9-U12 / TPS259470 RPW-10 | EN/UVLO, OVLO, AUXOFF, FLT, IN, OUT, DVDT, GND, ILM and ITIMER occupy pins 1-10 in every instance. Repeated IN/OUT copper preserves physical pad identities and all four ports are structurally symmetric. | PASS |
| U13-U16 / FSUSB42 MSOP-10 | Each used HSD1 pair retains P/N order, each unused HSD2 pair is explicitly no-connect, and VCC/GND/OE/SEL match the published pins across all four instances. | PASS |
| Q1-Q6 / CSD18533Q5A SON + pad 9 | Pins 1-3 are source, pin 4 gate, and pins 5-8 plus pad 9 drain. Q1/Q2 form the intended common-drain protection pair; Q3/Q4 and Q5/Q6 preserve high-side/low-side source, gate and drain classes for channels A/B. | PASS |
| Q7/Q8 / 2N7002K SOT-23 | G=1, S=2 and D=3 map respectively to RUN_A/B_HOLD, GND and RUN_A/B. Both instances are symmetric, and the exact unequal pad geometry matches the Diodes land recommendation without a mirror. | PASS |
| Q21/Q22 / MMBT3906 SOT-23 | B/E/C remain pins 1/2/3; each device is intentionally diode-connected to GND with its emitter on its TSNS net. | PASS |
| Y1 / CX3225SB | Crystal electrodes remain pads 1/3 and grounded case pads remain 2/4. | PASS |
| D1-D7 | D1 cathode is VIN_PROTECTED; D2/D3 cathodes are BOOST_A/B; D4-D7 cathodes are their port VBUS rails. Every anode returns to the intended rail or GND. | PASS |
| J2-J6 / USB connectors | VBUS=1, D-=2, D+=3 and GND=4 are preserved; all shell lands are GND. The upstream USB-B and four downstream USB-A packages retain their manufacturer top-view numbering and pair polarity. | PASS |
| J7 / SWD header | Pins 1-5 are 3V3, SWDIO, GND, SWCLK and GND; pins 6-8 are explicit no-connects; pins 9/10 are GND/NRST. Keying and pin-1 orientation match the exact header drawing. | PASS |
| F1 / Keystone 3568 | The two physical pad-1 lands are both VIN_RAW and the two physical pad-2 lands are both VIN_FUSED, matching the manufacturer's internally common holder-lead pairs without losing physical identity. | PASS |
| L4/L5 and other two-terminal passives | The power inductors are non-polarized and connect SW_A/B to their corresponding SENSE_A/B rails. Polarized capacitors and LEDs/diodes retain their explicit positive/cathode identities; ordinary R/C parts are electrically symmetric. | PASS |

## Post-review dossier rebind

The sole post-review source edit changed J1's free-text torque instruction
from 0.3 N m to the 0.35-0.4 N m range already stated by the dossier's
structured limit and SHA-selected Phoenix PDF. Replacing that one corrected
sentence with its former wording reproduces the previously reviewed dossier
SHA-256 `a6000c7f6f011b40ebe4ab076cedef2a73e263c4447ebb40ac6b07fee292640a`
exactly. The MPN, sourcing identity, electrical pins, package data, PDF,
footprint, model, and board are byte-unchanged, so the correction closes the
former P2 without reopening any pin/package conclusion.

## Final R3 evidence-only rebind

The sole final part-dossier edit vendors and SHA-selects Vishay 28758 and
28950 and adds their already-required package/preview note. Removing exactly
those two structured document blocks and that one note reproduces the prior
parts aggregate
`6c968c69e22b4a06450948e54a373768af35a4c4c6df199fd767bf561af6e129`.
No other dossier byte changed.

The selected 28758 PDF independently decodes `TNPW06034K64BEEA` as the
TNPW0603 4.64 kOhm, +/-0.1%, 25 ppm/K, lead-free tape part and specifies a
1.55 +/-0.05 x 0.85 +/-0.10 mm body. Selected Vishay 28950 gives 0603 reflow
G/Y/X/Z of 0.70/0.90/1.00/2.50 mm (IPC) and
0.90/0.55/0.90/2.00 mm (IEC). The exact board's two 0.80 x 0.95 mm lands on
1.65 mm centers yield G/Y/X/Z = 0.85/0.80/0.95/2.45 mm, inside those two
manufacturer patterns. Pad 1 remains `OV_SENSE`, pad 2 remains GND, and the
part remains an electrically symmetric resistor.

The sole final rule edit adds the C2078999 `FETCH-FAILED` adjudication;
removing exactly that entry reproduces the previously reviewed rules digest
`0398405fc9e70bcea37da6c45e5611f4161a4f5f0cc8fb0f9c500b08f4ae5034`.
The local twin report records the failed fetch, and LCSC's exact product page
independently identifies the same MPN while exposing no EDA-model resource.
The adjudication therefore uses manufacturer copper/body authority and
retains mandatory first-order JLC placement-preview confirmation. It grants
no value, pin, footprint, rotation, or board override.

## Route-rule rebinds

The only subsequent rule edit inserts `fresh_reload` immediately after the
second/final `fill` and before `unify_zone_priorities` and `heal_islands` in
the stitch pass chain. The parsed chain contains that pass exactly once.
Removing only this insertion reproduces the previously reviewed rules digest
`312c3b785ee79e1c441717a760211c035054bb64274c16a5ca4dffd0b20adabb`.
No part, circuit, footprint, model, or board byte changed, so no pin/package
conclusion is reopened.

The final route-contract edit removes nonexistent superseded `FB_B` from the
final-recovery group and signal rip list, then expands both the switch prep
group and switch route wave to the current `SWITCH_POWER` class: `SW_A`,
`SW_B`, `SENSE_A`, `SENSE_B`, `AUX_SW`, and `SW_3V3`. Each net exists on the
exact board and appears once in the generated `nets_switch.txt`; `FB_B` is
absent from the board and generated recovery file. All six retain 1.0 mm
F.Cu power routing with 0.8/0.4 mm via geometry. Reverting exactly these four
YAML field changes reproduces the preceding rules digest
`41fbbdfa4c9871aa1dbe0e2a057ad28fd3b5fd2758d3007974a1755f544c23e4`.
The generated prep output matches all 16 resolved wave groups, so the change
repairs route scheduling without changing any pin, net, part, footprint,
model, or board identity.

## Conclusion

The two former blockers are closed on these exact bytes: the TDK dossier now
selects the vendored TDK PDF by its true digest, and J1 now has coherent exact
Phoenix manufacturer evidence, a matching 5.00 mm custom footprint, and a
registered exact C3819953 model. All required active-device winding, pin-1,
pin-count/EP, function-to-net, and repeated-instance symmetry checks pass.
The SOUND design verdict is therefore warranted for the exact board and parts
aggregates recorded above.
