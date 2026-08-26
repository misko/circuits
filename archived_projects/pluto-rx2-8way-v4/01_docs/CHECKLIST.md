# Checklist

## Commission and parts

- [x] Exact prompt and hash recorded.
- [x] Prior boards used as incident evidence only.
- [x] No rigid foreign mate; no `mates.yaml`.
- [x] Hard-cell stock rechecked on 2026-07-31.
- [x] Module-first selection and rejected alternatives recorded.
- [x] Module underside, USB overhang and user-fit posture recorded.

## Capture and layout

- [x] TSX count/parity/footprint preflight clean.
- [x] ERC has zero errors; converter geometry warnings are baselined.
- [x] RP2040-Zero module and PE42482 escape/landability gates pass before routing.
- [x] P-LAND and placement gates pass.
- [x] RF impedance and stackup evidence archived.
- [x] Routing reproducible from promoted route chain.
- [x] Final DRC 0/0/0 and policy audit has zero failures.

## Release tests

- [x] JLC Gerber/drill/BOM/CPL candidate exported without escape hatches.
- [x] U_MCU absent from BOM, CPL, and paste; hand-fit instruction preserved.
- [x] A-POP population identity and CPL datum pass (27 placed / 5 declared off).
- [x] BOM source identity and F-LEGIBLE pass (11/11 rows).
- [x] Live catalog stock passes 11/11 lines for five boards.
- [x] Digital twin mounts 27/27 CPL bodies with zero model-registration errors.
- [x] Native firmware core and host simulator tests pass.
- [ ] Fresh-context pin review completed and dispositioned.
- [ ] Independent topology/protection red-team review completed.
- [ ] Independent layout/thermal red-team review completed.
- [ ] Fresh render review completed against the candidate population.
- [ ] All review findings dispositioned with zero open P0.
- [ ] M-REV, release-freshness, manifest-integrity, and final seal gates pass.
- [x] Cross-build with Pico SDK 2.1.1 + Arm GNU 13.3.Rel1 for
      `waveshare_rp2040_zero` (UF2 sha256 recorded in firmware README).
- [ ] Flash an RP2040-Zero.
- [ ] Verify RX2CTL/1 manual select, OFF, RUN/STOP, CONFIG, and STATUS over USB.
- [ ] Measure free-running cadence drift against Pluto sample indices; do not
  claim phase-locked sample boundaries without a shared clock/trigger.
- [ ] Confirm PE42482 orientation and LED polarity in JLC's order preview.
- [ ] Confirm JLC plug-in through-hole service for all ten SMA jacks.
- [ ] Confirm JLC04121H-7628 at 1.2 mm, advanced 0.25/0.15 mm vias (8.0:1), impedance solver
      adjustment, and coupon/TDR requirement in the actual order.
- [ ] Confirm uploader `(LCSC, value, refdes)` echo against the candidate BOM.

- [ ] 3V3_MOD and filtered 3V3 measured under representative module activity.
- [ ] Module underside clearance and solder joints inspected.
- [ ] Sample module metrology and insulating edge-support fixture record prove
      positive gap, parallelism, and no load on bottom components/crystal.
- [ ] USB enumerates in both connector orientations.
- [ ] PIO cadence matches the 62,464-sample frame.
- [ ] Each RF state and all-off state verified.
- [ ] VNA path loss, phase, return loss, and isolation published.
- [ ] RX1 main-line and reference-tap loss published.
- [ ] JLC fabrication/assembly package sealed; order-day stock rechecked.
