# ORDER_README — crow-recorder-central v1.0 (2026-07-22)

8-channel USB audio recorder: XMOS XU316 (TQFP-128) + dual PCM1865 ADCs +
USB-HS device (to a Pi 5) + 8 RJ45 "pod" ports (**NOT ETHERNET** — custom
5V/audio pinout). 6-layer JLC board, powered from a 5 V barrel jack.

Gate summary at seal: DRC 0 violations / 2 ADR-0010-waived GND slivers /
0 parity; ERC 0; audit PASS; jlc_twin exit 0; policy_audit 0 FAIL
(E-TOPO/E-INV/E-ADR PASS); both red-team verdicts ORDER; render PASS-WITH-NOTES.

---

## ⚠️ ORDER-DAY SOURCING — READ FIRST (two zero-stock lines)

### 1. XU316-1024-TQ128-I24 (U1) — CONSIGNMENT LINE (the critical one)
JLC assembly stock for **C6938291 is 0** and has been throughout the design
(commission → seal); this is a CHRONIC condition, not a momentary dip
(ADR-0013). **Plan for it explicitly at order time:**
- **Primary: JLC global-sourcing / consignment.** Order the XU316 through
  JLC's global parts sourcing, OR self-supply the part and ship it to JLC as a
  **consigned** line on the assembly order. Lead time is the long pole — start
  this BEFORE finalizing the rest of the order.
- Secondary (user-approval only): a C-grade equivalent (C6362698 was seen with
  ~10 stock at seal — NOT a drop-in; verify the exact MPN/speed grade).
- Everything else on the BOM is a normal in-stock JLC line.

### 2. 10k 0402 resistor (R12, R13, R15, R30, R50) — jellybean re-pick
The seeded code **C25744 (UNI-ROYAL 0402WGF1002TCE) read stock 0** on
2026-07-22. This is a jellybean 10 kΩ ±1% 0402 with hundreds of equivalents —
**substitute any in-stock 10 kΩ 1% 0402 at order time.** Verified drop-in:
**C25804** (10 kΩ 1% 0402, stock ~6.97 M). No layout impact.

### 3. Substitution lines already resolved on the BOM
- **1.8 V LDO (U12): TLV70018DDCR (C79924)** is on the BOM; the pin-compatible
  TCR2LF18 (Toshiba) is the exact-MPN Digi-Key fallback (ADR-0015).
- **24 MHz crystal (Y1): X322524MOB4SI (C70590)** is on the BOM; FA-238 is the
  Digi-Key fallback (ADR-0014).

---

## JLC order options
- **Layers: 6.** Impedance not controlled-ordered (USB pair is a geometry
  target, not a fab-controlled impedance line).
- **Fab tier: 6-layer + SMALL VIA** (min via 0.30 mm dia / 0.15 mm drill;
  min track/clearance 0.09 mm). This is REQUIRED — the XU316 0.4 mm TQFP-128
  via-in-pad escape does not close at the standard tier (D-TIER ADR-0012,
  small-via ADR-0009). Confirm the small-via option is selected.
- Surface finish: ENIG recommended (0.4 mm pitch + via-in-pad).
- Assembly: economic/standard PCBA. `fab/bom.csv` + `fab/cpl.csv` are the
  assembly inputs; `fab/crow_recorder_central_gerbers.zip` is the PCB input.

## Rotation-preview checklist (do this on the JLC assembly preview page)
The CPL rotations were normalized by the exporter; still eyeball the preview:
- **U1 XU316** pin-1 (chamfer) and the EP orientation.
- **U2/U3 PCM1865** (TSSOP-30) pin-1.
- **U4 flash / U5 clock buffer** pin-1.
- **All SOT-23 FETs (Q1-Q8, Q9)** — G/S/D orientation.
- **U10/U11 AP61102 (SOT-563)** and **U12/U13 LDO** pin-1.
- **D9 SMBJ / D10 ESD / D21-D28 ESD** band/pin-1 (polarity).
- **C90 (100 µF electrolytic)** polarity (its twin model FETCH-FAILED —
  verify the + band on the preview; footprint land is the standard 4 mm land).

## Hand-solder lines (NOT JLC-assembled — populate by hand)
| Ref | Part | Why hand-solder |
|---|---|---|
| J1–J8 | RJHSE-5384 RJ45 | LCSC has no assembly stock (THT tabs) |
| J9 | DC-005C barrel jack | THT |
| J12 | USB4105-GF-A USB-C | through-hole shield tabs (mid-mount) |
| J10 | INJ 1x02 header | THT |
| J13, J14 | xSYS debug 1x02 headers | THT |
Note **J7/J8 are DNP** (channels reserved; jacks not populated).

## First-power ritual
1. **USE A 5 V SUPPLY ONLY.** The barrel jack is not voltage-keyed and the
   board has NO over-voltage protection above ~6.5 V (red-team F1): a 9 V or
   12 V wall-wart on this jack will pass through the reverse-FET and kill both
   bucks and the analog LDO. Reverse polarity and ESD ARE protected; wrong
   VOLTAGE is not. Label the enclosure "5 V ONLY".
2. Bring up on a current-limited bench supply (limit ~500 mA). Reverse-polarity
   guard: at correct polarity the body diode drops ~0.7 V then the P-FET
   enhances; confirm the 5V rail comes up.
3. **Check the rails in sequence:** 5V → 3V3 (3.32 V, U10 buck) → 0V9 (0.90 V,
   U11 core buck, gated by 3V3 power-good) → 1V8 (U12 LDO) → 3V3A (U13 analog
   LDO). All present before proceeding.
4. USB: plug to the Pi 5 host; confirm the XU316 enumerates as a UAC2 device.
   The USB-C port (J12) is a device port with 5.1 k CC Rd pulldowns.
5. **JTAG/xSYS debug:** J13/J14 sit on the XU316 1.8 V IOB bank — use a
   **1.8 V-level** probe, not 3.3 V (red-team F8).

## Next-rev (v1.1) work order — carried from the red-team review (all P1, none block v1.0)
- **F1:** add real over-voltage protection on the 5 V input (series eFuse or a
  clamp below the 6.5 V downstream abs-max) so a wrong-voltage supply is safe.
- **L1:** re-route the USB-HS pair F.Cu-only (v1.0 splits it across F.Cu/B.Cu/
  In2 with 7 vias — HS-robust and will enumerate, but it violates the intended
  no-via USB rule).
- **L2:** move both buck input caps to <2 mm from VIN/GND (v1.0 ~6 mm).
- **L3:** shorten/balance the long analog ADC input legs (AIN_P4 = 106 mm).
- **F3:** consider forced-PWM on the bucks (v1.0 runs PFM; tolerable because
  the bucks feed digital rails and the analog is LDO-buffered).
- **F6:** confirm the D9 SMBJ5.0A datasheet provenance (part.yaml carried a
  copy-artifact sha; the part identity + limits are correct).

Full findings + dispositions: `verification/DISPOSITIONS.md` and the two
`verification/2026-07-22_v1.0_redteam_*.md` reviews.
