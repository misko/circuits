# SUPERSEDED by cooksense-v1.7-2026-07-30 — **AND THIS RELEASE IS DO-NOT-ORDER. DO NOT BUILD IT.**

## ⛔ DO NOT FABRICATE, ORDER OR HAND-BUILD THIS RELEASE

This is **NOT** a documentation supersede. The copper here is wrong.

**This release carries the `Relay_StandexDIP_1A_pinout12` land, and the part
that exists is pin-out `13`.** `DIP05-1A72-12L` and `DIP05-1A72-13L` are
DIFFERENT PIN-OUTS of the same body: on code 12, pins 1↔14 are tied as one
contact node and 7↔8 as the other, with the coil on the INNER pins. Fitting a
real `-13L` relay to this land shorts `5V_KEY_RELAY` to `U_SEL_BUS` and shorts
every ULN2803 output to its keypad line. **The 12-relay key-matrix array as
drawn on this board cannot work**, and no assembly option, rework or firmware
change rescues it.

The same defect makes **v1.0, v1.1, v1.3, v1.4, v1.5 and v1.6 — every cooksense
release ever sealed before v1.7 — DO-NOT-ORDER.** There was no good sealed one.

## What v1.7 is

**A REAL BOARD REVISION, the first since v1.3.** `source/cooksense.kicad_pcb` is
md5 `9f4fd5fae810f40a52b1035df727243c`; v1.3/v1.4/v1.5/v1.6 all carry
`420445b5141dd1111eccab038c68511b`. **Gerbers, drills, BOM and CPL all move.**
Nothing in this directory is a byte-source for v1.7 — go to
`cooksense-v1.7-2026-07-30/` for every fab file.

Beyond the relay land, v1.7 also carries, relative to this release:

* **The supply is SPECIFIED, not advised** — `J_PWR` held 4.850–5.250 V at the
  connector under full load (BRIEF D11, ADR-0021). A ±10 % or generic ±5 % brick
  is out of specification for this board.
* **The eFuse OVLO divider is corrected.** v1.2–v1.6 carried `R_OVT` 100k /
  `R_OVB` 15k = 9.200 V nominal, which is above BOTH the 5.25 V spec ceiling's
  nuisance-trip bound AND the SMBJ5.0A's 6.40 V minimum breakdown — i.e. the TVS
  conducts before the eFuse ever cuts off. v1.7 is 100k / 26.1k, both ±0.5 %,
  5.798 V nominal, worst case 5.3682 V earliest / 6.2394 V latest.
* **`R_OPENT` is 62 kΩ (`C37825`), not `C25915`** — see v1.7 ORDER_README §12.
* **The 3V3 rail's declared load and thermal ceiling are both re-derived**
  (ADR-0026/0027/0028): this release grades the AMS1117 at `iout_max_A: 0.3`
  against a `pdiss_max_mw: 1200` that is a 25 °C figure applied with no ambient
  term at all, and its `vin_min` counts three named component resistances and
  **none of the board's own copper**.
* **A DECLARED OPERATING AMBIENT, which no earlier release had** — 65 °C, with
  75 °C retained as the survive corner, plus a MANDATORY six-measurement bench
  gate before use above bench conditions (ADR-0029, v1.7 ORDER_README §0-T and
  §7b).

## What is still true here

The v1.6 content this release was cut for — the cross-plug hazard table (§10:
the unkeyed JST-GH family is **five** housings, not three, and an SHT45 pod
harness in `J_MODE` energises the coil rail with all seven AND-chain terms and
the manual rail-cut bypassed), the two host-firmware invariants (§7a: `REARM_N`
must be PULSED; MCP23017 `GPPUB` must be written `0x00`), and the declared-gaps
table — is **carried forward into v1.7 and extended**, not withdrawn. Read it in
v1.7's ORDER_README, not here.

## Order state of v1.7

**v1.7 is SEALED but NOT ORDERABLE TODAY**, and for a reason that has nothing to
do with its design: one BOM line, `C265111` (JST `SM08B-GHS-TB`, on `J_THERM_A`
/ `J_THERM_B`), reads **stock 5 against minPurchaseNum 21** — the minimum order
quantity exceeds the entire catalog stock, so the line is not "short", it is
UNBUYABLE AT ANY QUANTITY. v1.7 declares this out loud as
`SOURCING: BLOCKED-1` in both its MANIFEST and the first screen of its
ORDER_README, with the escape routes in its §5-0. **Re-measure on order day.**
