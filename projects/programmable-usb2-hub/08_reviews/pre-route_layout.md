subject: programmable-usb2-hub pre-route placed board a03a05e83f32
date: 2026-08-02
reviewer: fresh independent redteam-agent (GPT-5, layout/thermal/power-integrity lens)
context-given: exact placed board, active design contracts, local authoritative datasheets, and official editable LTC3889 reference layout
review_stage: pre-route
review_kind: layout
design_verdict: SOUND
order_verdict: DO-NOT-ORDER
board_sha256: a03a05e83f32df6a6104a24dea888683618e7b5fe40e6b70904f6959b98f63ed
design_rules_sha256: d732d22b90dbae6f31d9099d2c789ab06df32d96e2c43e207232c55faa24100e

# Independent pre-route layout re-gate

I independently re-measured the exact track-free placed board with pcbnew,
inspected an orthographic KiCad render, and compared the power cells with the
locally vendored LTC3889 Rev. A, LMR36510 Rev. B, TPS25947 Rev. C and AP63203
datasheets. For the LTC3889 I also measured the manufacturer's editable
DC2595A PADS layout rather than relying only on a rendered figure.

No P0 or P1 pre-route layout finding remains.

## Prior finding re-gate

- **LTC3889 dual 4 A bucks — fixed.** Each high-side/low-side switch-land gap
  is now 1.300 mm, compared with 11.148 mm before the backtrack. Gate paths are
  bounded at 11.618/6.270 mm for channel A and 11.618/6.632 mm for channel B,
  all inside the adopted partner-specific limits derived from DC2595A. The
  inductor-to-shunt spans are symmetric at 6.339 mm. Bootstrap paths, local
  rail bypasses and all four compensation paths pass their named limits.
  The four sense-filter series resistors are 1.542-2.213 mm from U2's actual
  ISENSE pins. C4/C5 centres are 8.59/7.62 mm from U2 centre; the corresponding
  1 nF C18/C28 centres in Analog Devices' exact DC2595A2.ASC are 10.97/10.31 mm
  from its U1 centre, so the present filter placement is not a relaxation from
  the official routed precedent. The long shunt-to-filter runs remain paired
  Kelvin routing obligations, not placement defects.
- **LMR36510 auxiliary buck — fixed.** U3-to-C200 is 2.936 mm on VIN and
  3.028 mm on GND; VCC bypass is 3.011 mm; BOOT/SW bootstrap paths are
  2.942/3.222 mm; SW-to-L6 is 3.854 mm; and FB-to-R200 is 2.979 mm. These are
  within the partner-specific bounds derived from SNVSBD7B Figure 8-24.
- **TPS259470 port cells — fixed.** The four required 22 uF OUT capacitors are
  each 3.765 mm from the matching OUT land against the 5 mm ceiling. Input
  bypasses are each 1.375 mm away, RILM distances are each 2.787 mm, CdVdt
  distances are each 1.848 mm, and CITIMER distances are each 3.252 mm. The
  prior duplicated-custom-pad false pass is closed by explicit `partner_refs`
  on all four >=1 uF output-bypass obligations.
- **AP63203 logic buck — fixed.** U4-to-L3 on `SW_3V3` is 3.103 mm against the
  3.5 mm partner-specific limit; C21 input and C22 bootstrap adjacency also
  pass.

## Integrated feasibility

- `placement_gates.py` passes: 0.41 mm tightest pad-to-outline margin, 46-net
  worst cut against 280 two-layer track slots, and zero courtyard/body or
  envelope-to-foreign-pad findings across 211 assembled envelopes.
- `pad_separation.py` passes 849 copper pads on 218 footprints, 351,268
  inter-footprint pad pairs and 599,784 paste-to-foreign-copper pairs at the
  0.09 mm advanced-tier floor.
- The current placement policy report passes all 52/52 partner-aware
  keep-short budgets and both 2/2 explicit adjacency budgets. The four USB-A
  connector/ESD/switch cells preserve P/N ordering and edge access, while the
  hub has enough F.Cu escape/corridor capacity for the declared no-via USB
  pairs over the reserved In1.Cu ground reference. Actual pair impedance,
  uncoupled length, matching and plane continuity remain routed-artifact
  checks.
- The 24 V SELV input region, fuse, mounting holes and edge connectors have
  adequate placement clearance. The eFuse land patterns include their
  via-assisted thermal geometry; the LTC3889 MOSFET/inductor/shunt cells leave
  continuous room for the declared high-current pours and parallel thermal
  transitions.
- The final rules-only edit is coherent with the physical review: the stitch
  chain now executes its second authoritative `fill`, then `fresh_reload`,
  then `unify_zone_priorities` and connectivity-sensitive `heal_islands`.
  This does not move placement geometry and prevents island healing from
  consulting stale filled-zone connectivity.
- The final route-recovery corrections are also coherent with this placement.
  `FB_B` does not exist in the current netlist and is absent from both the
  `final_recover` group and its rip list. The F.Cu `switch` wave now contains
  exactly the six live `SWITCH_POWER` nets (`SW_A`, `SW_B`, `SENSE_A`,
  `SENSE_B`, `AUX_SW`, `SW_3V3`) at 1.0 mm, above the 0.25 mm class floor.
  The declared 0.5 mm local neckdown and taper provide legal launches at the
  small LMR36510/AP63203 lands, while the compact FET/inductor/shunt placement
  leaves continuous top-layer corridors for the full-width trunks.

## Verdict

The design verdict is **SOUND** for entry into routing. This is not an order
authorization: the board is intentionally track-free and still requires the
canonical route, full DRC/parity, routed USB/power review, fabrication and
assembly gates, sourcing recheck and release seal. Therefore the order verdict
remains **DO-NOT-ORDER**.
