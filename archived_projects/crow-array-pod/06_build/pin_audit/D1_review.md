# Fresh-context pin review: D1 (TI TPD2E2U06DRLR, DRL/SOT-553) — v1.1 spot re-review

Reviewer: fresh-context agent, 2026-07-19. No design-session context (by protocol).
Datasheet: `02_parts/TPD2E2U06DRLR/tpd2e2u06_sllseg9c_2019-12.pdf` (SLLSEG9C), page 3
rendered at 300 dpi and read directly. Package pinout derived independently from the
"DRL Package, 5-Pin SOT, Top View" figure — not from the dossier or part.yaml.

## Independent derivation (datasheet figure, top view)

- Pin 1 = NC, top-LEFT corner. Pins 1-2-3 run DOWN the left side (3 pins west).
- Pin 3 = IO1, bottom-left. Pin 4 = GND, bottom-RIGHT. Pin 5 = IO2, top-right (2 pins east).
- Winding 1..5: down the left, up the right = **CCW (top view)**. No exposed pad; 5 pads total.
- Pin Functions table (DRL column): IO1=3, IO2=5, NC=1,2, GND=4. IO pins: "Connect these
  pins to the data line **as close to the connector as possible**."

## Verdict table

| pad | dossier local (x,y), +y down | side | expected (datasheet) | board net | verdict |
|---|---|---|---|---|---|
| 1 | (-0.71, -0.50) top-left | W | NC (float/GND/VCC ok) | unconnected | PASS |
| 2 | (-0.71, +0.00) mid-left | W | NC | unconnected | PASS |
| 3 | (-0.71, +0.50) bottom-left | W | IO1 — protected data line | AUDIO_P | PASS |
| 4 | (+0.71, +0.50) bottom-right | E | GND | GND | PASS |
| 5 | (+0.71, -0.50) top-right | E | IO2 — protected data line | AUDIO_N | PASS |

- **Winding/mirror:** dossier's computed CCW (top view), 3 pads W / 2 pads E, pin 1 at
  top-left matches the datasheet figure pad-for-pad under zero rotation. NOT mirrored. PASS.
- **Pin count / EP:** 5 pads, no EP — matches DRL package. PASS.
- **Electrical sanity:** two I/O clamp channels on the balanced audio pair, GND on ground,
  NCs floating (datasheet permits). Matches ADR-0001 intent (clamp AUDIO_P/N to GND). PASS.

## Placement (the reason for this spot re-review)

D1 pin 3 (IO1): expected AT the cable entry per datasheet ("as close to the connector as
possible") and ADR-0001 §1 ("strike energy dumps at the entry", 68R resistors between amp
and clamp) vs dossier shows D1 at **(88.5, 59.0)** while J1 is at (78, 64) with the
AUDIO_P/N tails at ~(76-78, 64-65.1) — **~11.6 mm from the nearest tail**. The v1.1
re-route moved the jack (screw terminal -> RJ45) but the clamp did not follow it; ~12 mm of
trace between the connector and the clamp carries the raw strike, and the clamp no longer
sits upstream at the entry as ADR-0001 requires. **FAIL.**

## Overall

**VERDICT: FAIL** (placement). Pin mapping, winding, and net assignment are all correct —
the v1.0 net contract is intact — but the moved part no longer performs entry clamping.
Block release until D1 is repositioned adjacent to the J1 AUDIO_P/N tails (~(76-78,
64-65.1)), with the clamp in the path before any downstream routing, or the ~11.6 mm
deviation is explicitly accepted in writing against ADR-0001.
