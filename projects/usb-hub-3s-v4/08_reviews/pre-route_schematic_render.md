review_stage: pre-route
review_kind: schematic_render
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
schematic_pdf_sha256: 1f108b7080a20a4c704e58bfcab9ee3f275ba53b480c526750f9f82df6be99d1
netlist_sha256: ed689c7d75719a3c7955511a2b1311fb0438443cb2ef6da58280ed97a4461763
exact_netlist_sha256: 222667931a0147368cac49ea1b0799e78826ef64f0282dc33907a8287af2612f
parts_sha256: 8e3d14083528ee127709753251ab2f8f4349a34203d73b93f0dd49a5f5dffb2e
design_rules_sha256: ef3693aae5be7dfbb29e762e15203d6e86db57164f31176238be1657b35dfb62
policy_waivers_sha256: c9f3abf083d35185be07465d7385296bb36a393b412f6696c327ec0502cc96c3
first_article_test_plan_sha256: bcaa103a011e1be88f9ab816b842ed535ab8fb1464916a85f2c2f20b7eb0d506
circuit_json_sha256: 0bca19d0da74d36e4c0d47e80b7d1f812c9c20bb655e7bc1c1c502d02fd8ca95
kicad_schematic_sha256: 114ba1ca14f8cf4bef649c6962bc011cbaebdb0ec494cff31fa8385d587bad43
schematic_checkpoint_sha256: bfbff9c0decfed7de348022ec1352238199f4b2b6c5b8ee05ed6ba659a4a75fc
authoring_source_sha256: 941fd90b246140a61b57c8c1f9abe2dcee8cf289a4b832015846e8a4dc638b7d

# Pre-route human schematic render review

## Verdict

**SOUND / DO-NOT-ORDER.** I freshly inspected all 10 pages of the exact PDF
bound above at normal full-page reading scale, then rechecked the C23 page at
180 dpi. C23 remains visibly 180uF with its positive terminal on `5VC_RAW`,
the new supplier selection is not misrepresented by stale prose, and the
complete power-only architecture remains readable. No blocking
human-readability or misleading supplier-boundary defect was found.

This is a schematic-readability verdict for these exact bytes. It does not
authorize an order.

The current policy-only refresh does not change that verdict. The new S-OCCL
disposition accurately confines three intersections to the machine-generated
KiCad parity artifact; none is present as an unreadable or ambiguous condition
in the exact human PDF. The P-SILK-FN disposition and controlled first-article
TP map make no claim that the missing PCB net-function captions exist, and do
not misrepresent schematic readability.

## Method and exact-artifact binding

- Review date: 2026-08-12.
- `06_build/checkpoints/schematic.json` was inspected; its recorded PDF,
  `circuit.json`, KiCad schematic, and raw-netlist hashes match the current
  files byte-for-byte.
- The normalized-netlist, aggregate part-dossier, and adopted-rule hashes were
  independently recomputed with the canonical functions in
  `skills/kicad-pcb/scripts/pre_route_review_check.py`.
- Every PDF page was rendered and visually inspected individually at 96 dpi
  page-fit scale. Page 9 was inspected again at 180 dpi. Extracted text and PDF
  word boxes were used only to check exact wording, complete headings and stale
  supplier strings.
- `circuit.json`, the exported netlist, the replacement part dossier and the
  adopted rules were checked for C23 identity, rating, polarity and
  connectivity. The electrical normalized-netlist digest remains unchanged;
  the exact source/artifact hashes correctly changed with the substitution.
- For the policy-only refresh, the unchanged exact page 9 PDF bytes were
  freshly rendered at 180 dpi and inspected specifically at R24, C9-C11/R24,
  and R11. The controlled TP1-TP12 map was independently compared ref-by-ref
  with the current exact exported netlist.

## Policy-waiver and test-plan delta audit

- **S-OCCL:** the waiver names exactly three machine-KiCad text intersections:
  R24 reference versus a `#PWR44` glyph, one 22uF value versus the R24 body,
  and the 4.12k value versus a wire. In the exact human PDF on page 9, R24 and
  `24.3Ω` are distinct and readable below the C9-C11 bank; each of the three
  `22uF` values is separately legible; R11 and `4.12kΩ` are legible without a
  conductor obscuring the value; and no `#PWR44` glyph is presented as human
  schematic content. Net labels, component identities and connections remain
  unambiguous. The evidence therefore supports the waiver's narrow claim that
  these are converter-artifact intersections rather than human-PDF defects.
- **P-SILK-FN:** this is explicitly a PCB-silkscreen/prototype-use
  disposition, not a claim about schematic captions. The test plan openly says
  TP3-TP12 are identified on the prototype PCB by reference rather than full
  net-name legends, requires the controlled table beside the bench, and
  disallows carrying the omission into production. Its map matches the exact
  netlist 12/12: TP1 `VIN`, TP2 `5VA`, TP3 `5VC_RAW`, TP4 `VBUSC`, TP5
  `EN_BUS`, TP6 `PG_A`, TP7 `PG_C`, TP8 `FAULT_C`, TP9 `FAULT_A1`, TP10
  `FAULT_A2`, TP11 `FAULT_A3`, and TP12 `GND`. It neither invents a caption nor
  relaxes the existing human-PDF readability verdict.

## Page-1 assembly correction

Page 1 now visibly and without clipping states:

> BATTERY INPUT — HAND FIT 3568 HOLDER AFTER PCBA / USER FIT 0297010.WXNV
> 10 A, 32 VDC, 1 kA interrupt / external UV disconnect >=9.0 V / no active OVP

That agrees with `03_src/rules/assembly.yaml`: F1 is excluded from JLC
placement, the exact Keystone 3568 holder is hand-soldered after PCBA, and the
Littelfuse 0297010.WXNV is subsequently user-fitted. The previous misleading
claim that JLC fits the holder is absent from the PDF.

The rest of page 1 is also readable: `BAT_POS -> F1 -> VBAT_FUSED -> Q1 ->
VIN`, J1, the reverse-polarity gate network, D1/D5, C1 polarity, TP1, ground,
and the external-UV/no-active-OVP boundary are all visually explicit.

## C23 supplier-substitution audit

- Current `circuit.json` identifies C23 as Panasonic `16SVPF180M`, JLC
  `C136277`, 180uF. The replacement dossier fixes 16V, +/-20%, pad 1 `POS`,
  and pad 2 `NEG`.
- The normalized netlist hash is unchanged from the prior electrical witness.
  The exact netlist identifies C23 as 180uF and places C23.1 on `5VC_RAW` and
  C23.2 on GND. `electrical_invariants.yaml` states the same pad/net facts and
  value; `power_tree.yaml` continues to count one 180uF polymer contributor.
- Page 9 clearly prints `C23` and `180uF` at normal page-fit scale. The
  polarized-capacitor `+` mark is visible at the upper terminal tied to the
  `5VC_RAW` rail; the lower terminal joins the common GND return. The symbol,
  refdes, value and ground label do not overlap.
- The PDF contains no supplier code or manufacturer text for C23. In
  particular, it contains none of the retired `C369910`,
  `160AV5K181M0606C`, or APAQ identity, and therefore makes no stale
  supplier-specific claim. The current Panasonic/JLC identity remains in the
  machine-readable source and dossier where it belongs.

## C29/C30 audit

- Current `circuit.json` identifies C29 as 47 nF / JLC `C5451690` and C30 as
  3.3 nF / JLC `C77036`.
- Page 4 clearly prints `C29`, `47nF`, `C30`, and `3.3nF` at normal page-fit
  scale. C29 is visibly connected between `ITIMER_A` and GND; C30 is visibly
  connected between `DVDT_BANK` and GND. The exported netlist agrees.
- The adopted C29 tolerance is 5%, and C30's corrected tolerance is 5%. The
  PDF claims nominal capacitance only; it does not print a stale tolerance,
  manufacturer, or supplier catalog code.
- U9 remains legibly identified as `TPS259827ONRGET` and as a no-OVLO circuit
  breaker. `5VA_RAW -> U9 -> 5VA`, R26 = 210 ohm, TP2, the grounded pins, and
  the IMON/NRETRY/PG intentional opens are unambiguous.

## All-page visual audit

- **Page 1 — battery input:** Assembly wording is corrected as described
  above; protection flow, values, refdes, MPNs, polarity, rails, and boundaries
  are readable.
- **Page 2 — hard-off control:** VIN, R2, SW1, `EN_BUS`, GND, TP5, and TP12 are
  easy to follow. `ON_NC` has a visible open marker.
- **Page 3 — USB-A regulator:** U1 identity, 6 A rating, VIN/enable/output,
  feedback, boot, PG/SPSP/RT, capacitor bank, values, test point, and grounds
  are readable. SW, VCC, and NC intentional opens agree with the title.
- **Page 4 — aggregate protection:** C29/C30 pass the focused audit above;
  input/output banks, U9 MPN and role, values, refdes, grounds, and intentional
  opens remain clear.
- **Page 5 — charging signatures:** The three DP/DM charging-signature pairs,
  both TPS2513A blocks, `5VA`, and C20/C21 are readable. “No upstream data” is
  explicit, and U8 channel 2 is visibly open.
- **Pages 6-8 — USB-A ports:** Each page clearly shows `5VA -> TPS2559 ->
  VBUSAx -> USB-A`, ILIM and FAULT networks, ESD array, connector, grounded
  shield, and polarized bulk capacitor. Each title explicitly says
  `POWER ONLY`.
- **Page 9 — USB-C regulator:** U2 identity, 5.15 V / 15 mV reserve, VIN,
  `5VC_RAW`, feedback/RT/PG networks, capacitor values and polarity, and TP3/TP7
  are traceable. C23 is visibly 180uF with `+` on `5VC_RAW` and its other
  terminal on GND. SW and VCC intentional-open intent is explicit.
- **Page 10 — fixed USB-C output:** `5VC_RAW -> U3 -> VBUSC`, U3/J5/D6,
  CC1/CC2, C12/C13, TP4/TP8, and grounds are legible. Fixed 5 V, no PD, and no
  data are explicit. D+/D-, SBU, and unused U3 status pins have visible open
  markers; CC1/CC2 remain visibly separate from ground.

No page is missing, no heading or label is clipped, no title is wrong, and no
value, endpoint, open marker, polarity mark or critical power transition
requires unreasonable zoom. No text overlap creates an ambiguous identity or
connection. Blocking findings: none.
