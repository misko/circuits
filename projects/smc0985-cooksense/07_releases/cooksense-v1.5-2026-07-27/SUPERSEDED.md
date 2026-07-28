# SUPERSEDED by cooksense-v1.6-2026-07-27 — THE BOARD, THE BOM AND THE CPL HERE ARE ALL CORRECT. THE ORDER_README IS NOT.

## THIS RELEASE IS STILL ORDERABLE. ORDER IT IF YOU HOLD IT.

**Nothing in this directory is wrong except one document.** v1.6 is a
DOCUMENTATION-ONLY supersede: it regenerates nothing. Its `fab/` (19 files),
`source/` (11), `3d/` (2) and `pdf/` (3) are **byte-for-byte identical to this
release's** — 35 files, 0 differing, 0 added, 0 missing, measured by directory
sha256 in both directions and **ASSERTED** by `release_freshness_check.py
--docs-only-supersede`, which FAILs on any difference. `source/cooksense.kicad_pcb`
is md5 `420445b5141dd1111eccab038c68511b` in both, the same file `04_kicad/`,
v1.3 and v1.4 carry.

So: **this release's gerbers, BOM, CPL and 3D are the files to send.** They are
the same bytes v1.6 ships. What v1.6 replaces is `ORDER_README.md`, and it
replaces it because three of its statements about SAFETY were wrong.

## What is wrong with this release's ORDER_README

### 1. §10 claims a cross-plug is fail-safe when one of them is not. **WITHDRAWN.**

This release's §10 says the unkeyed 5-pin JST-GH family is "J_MODE / J_DOOR /
J_ESTOP" and that "Pinouts are arranged so any single cross-plug is fail-safe."

**There are FIVE identical housings, not three.** `fab/bom.csv` line 45, in this
very directory, ships one `C189896` SM05B-GHS-TB part across `J_DOOR`, `J_ESTOP`,
`J_MODE`, **`J_RH_AMBIENT`** and **`J_RH_EXHAUST`** — one footprint, nothing
mechanical to tell them apart. The two omitted ones carry POWERED SHT45 pod
harnesses.

**An SHT45 pod harness plugged into `J_MODE` energises the relay coil rail with
all seven AND-chain terms AND the Manual rail-cut bypassed.** The pod powers up
normally from pin 1 (3V3) and lands its module SCL pull-up on `J_MODE.4` =
`COIL_EN`, whose only hold is `R_COILENPD` = 100 kΩ with no ESD device and no
series element: 3.000 V at the documented 10 kΩ module pull-up, 3.152 V at
4.7 kΩ — both above the 2N7002's 2.5 V max `V_GS(th)`. `J_MODE` (196.75, −60.00)
sits 38.29 mm from `J_RH_EXHAUST` (186.00, −96.75) on this release's own
`fab/cpl.csv`, same cable, same connector.

**If you are commissioning from this release, read v1.6's §10 before you build a
single harness.**

### 2. No document here states the two host-firmware invariants. v1.6 §7a does.

- **`REARM_N` must be PULSED.** Held low it forces the fault latch's forbidden
  state and the latch permanently loses its memory — a fault that clears
  re-permits cooking with no re-arm. `REARM_N` has exactly one driver
  (`U_EXP.26`), no button, no pin, no test point; and because `EXP_RST_N` has no
  driver at all, the defeat survives every Pi reboot.
- **MCP23017 `GPPUB` must be written `0x00`.** Four AND-chain permissions
  (`WD_OK`, `ESTOP_OK`, `MODE_AUTO_HW`, `DOOR_OK`) carry no pull resistor; one
  register write puts a 100 kΩ internal pull-up on all four and turns their
  failure mode from indeterminate into deterministically PERMISSIVE.

### 3. §13 is missing five declared gaps, one of them a measurement

**11 of the 18 safety-chain nets carry no restrictive default at all.** v1.6
publishes the table, both single-part cases (`U_SCHM` floats three permissions,
`U_LATCHB` floats `FAULT_LATCH_CLEAR` into both the coil rail and the contactor),
and two stale source comments a harness builder could act on.

## Everything else in this release stands

The v1.5 content — the `C25744` → `C60490` and `C25862` → `C138040`
substitutions, the F-LEGIBLE BOM repair, and the E-TOPO / supply-specification
finding in §0 — is **carried forward verbatim into v1.6** and is still the
current answer. E-TOPO is still the one `policy_audit` FAIL and is still a
deliberate, user-held order gate.

Gates unchanged, because the artifacts are unchanged: DRC 0/0/0, ERC 0 errors,
A-ROT 189/189, A-POS worst 0.00000 mm, A-POP 226/189/37, A-BODY 189/189. E-INV
moves 83/83 → **85/85** in v1.6 — two new `part_value` asserts pinning
`R_COILENPD` = 100k and `R_REARMPU` = 100k, the two numbers the cross-plug bound
and the power-up-forced-SET property are computed from.

Full reasoning and every measurement:
`cooksense-v1.6-2026-07-27/verification/crossplug_and_permission_defaults.md`
and the v1.6 entry in `01_docs/CHANGELOG.md`.
