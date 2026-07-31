# ARCHITECTURE — pluto-rx2-8way-v2

**This is the MODULE arm of a two-arm comparison.** `projects/pluto-rx2-8way`
(v1) is the bare-RP2040 arm, is NOT superseded, and is not written to. Every RF
decision below is held identical to v1 deliberately, so the two boards differ in
ONE variable: how the MCU is realised.

Decisions live in `decisions/`; this file says WHAT IS. Machine-readable net
facts live in `03_src/rules/nets.yaml`, rail envelopes in
`03_src/rules/power_tree.yaml` — not restated here.

## 1. The one-paragraph description

An SP8T RF switch (PE42482A-X) sits at the centre of a radial star of ten
vertical SMA jacks. Eight are antenna ports; the ninth (`J_RX2`) carries the
switch common to PlutoSDR RX2; the tenth (`J_RX1`) carries the RX1 antenna
straight through to PlutoSDR RX1. **Antenna 8 is not a dedicated element — it IS
the RX1 antenna**, sampled by a two-resistor pickoff so that RX1 keeps its own
path and the array gains a phase reference it shares with the receiver's other
channel. A **Waveshare RP2040-Zero module** drives the switch's four select
lines from a free-running PIO sequencer, so the antenna sweep is self-timed and
the host does nothing but capture.

## 2. Signal chain

    J_ANT1..J_ANT7  -- ANT1..ANT7 ------------> U_SW RF1..RF7
                                                   |
    J_ANT8 (= the RX1 antenna)                     |
       |                                           |
       +--- RX1_MAIN --+---------------------> J_RX1   (to PlutoSDR RX1)
                       |
                       +-- R_T1 220 -- RX1_TAP_MID -- R_T2 220 --
                                                   RX1_TAP --> U_SW RF8

                                       U_SW RFC -- RX2_OUT --> J_RX2 (to RX2)

    U_MCU GP0..GP3 -- SEL_V1..SEL_V4 -- R_S1..R_S4 (47R) -- SW_V1..SW_V4
                                                               |    |
                                            R_PD1..R_PD4 (10k)-+    +--> U_SW V1..V4
                                                               |
                                                              GND

`U_SW` pin 1 (`LS`) is tied to GND, not to a pulled-down net: it carries a
1 Mohm INTERNAL pull-up, so a float reads as logic 1 and selects the
COMPLEMENTED half of the truth table — the board would still sweep eight
antennas, in a plausible-looking wrong order. Pin 20 (`NC`) is also tied to GND;
it sits between RF8 and GND inside the RF fan, so grounding it closes the via
fence there rather than leaving an unterminated stub.

**What changed from v1 in this chain: nothing.** The RF core and the control
plane are identical, by design.

## 3. Power tree

    [module's own USB-C]  -->  RP2040-Zero  -->  RT9013-33 LDO  -->  3V3 pad
                               (on the module, off our board)              |
                                                                          |
      our board:   3V3_MOD --+-- C_BULK 4.7uF                              |
                             |                                            |
                             +-- FB_3V3 (ferrite) --+-- 3V3 -- U_SW VDD  <-+
                                                    |
                                                    +-- C_SW1 100nF
                                                    +-- C_SW2 1uF

**This board has no power connector of its own.** Its only power input is the
module's `3V3` castellation. That is a deliberate consequence of ADR-0002 and it
is why v1's PPTC/TVS/LDO chain is absent rather than merely unbuilt.

**The ferrite `FB_3V3` is an RF measure, not a protection measure.** The
RP2040's core and QSPI current transients ride on the module's 3V3 rail, and the
PE42482A-X's VDD biases its FET stack while publishing no PSRR figure. Series
ferrite plus a local ceramic AT the VDD pad is the whole mitigation.

**Headroom is not the constraint.** `U_SW` draws 120 uA typ / 200 uA max
(PE42482A-X Table 2, PDF p3) against an RT9013 rated 500 mA. `C_SW1`/`C_SW2`
exist for CONTROL-LINE transients, not for load current — which is exactly why
they must be at the pad to be anything at all.

Envelopes (vin/vout min-max, iout, converter, off-control, quiescent) are in
`03_src/rules/power_tree.yaml`, the E-TOPO/E-MARGIN/E-OFF input.

## 4. Net domains

Widths and the ampacity declarations are in `03_src/rules/nets.yaml`; this table
says what makes each class special.

| class | nets | what makes it special |
|---|---|---|
| `RF50` | `ANT1..ANT7`, `RX1_MAIN`, `RX1_TAP_MID`, `RX1_TAP`, `RX2_OUT` | **the width is an IMPEDANCE, not an ampacity.** Widening it is exactly as wrong as narrowing it. F.Cu only, no vias inside an arm, solid In1.Cu beneath |
| `CTRL` | `SEL_V1..SEL_V4`, `SW_V1..SW_V4` | switched DC, not RF. **No shunt capacitance anywhere on this class**: a 1k+1nF RC is 4.6 us to 99 %, more than the whole 4.267 us blanking allowance |
| `PWR` | `3V3_MOD`, `3V3` | width for IR drop and robustness, far above the ampacity need. `3V3_MOD` and `3V3` are separated by a SERIES ferrite, so they are two nets, not one continued |
| default | `LED_STAT`, `LED_STAT_A` | `LED_STAT_A` is the ballasted anode node between `R_LED` and `LED_ST`; a series resistor between a driver and an LED needs two nets |
| `GND` | pours + stitching on all four layers; no netclass width | `U_SW` pin 1 (`LS`) and pin 20 (`NC`) are ON this net, by vias at the pads |

**Classes v1 carries that v2 does NOT, and why the absence is a fact rather than
an omission:** `USB_D` (`USB_DP`/`USB_DM`) — no board USB, the module owns it.
`QSPI` — the flash bus is on the module's own PCB, so the comb v1 calls *"the
board's only continuous in-band spur source"* is no longer on this laminate.
`DVDD_1V1` — the RP2040 core rail and its copper link live inside the module.
Those three classes disappearing is the entire point of the board.

## 5. Stackup

`JLC04161H-7628`, 4 layers, impedance control requested, at fab tier
`jlc_4layer_advanced`. Layer roles:

| layer | role |
|---|---|
| **F.Cu** | RF, and only RF plus short control/power runs. Every one of the nine radial arms lives here and nowhere else |
| **In1.Cu** | **the SOLID, UNBROKEN RF REFERENCE. EXCLUDED from the routing layers.** Not a preference — it is what makes nine arm phases comparable at all |
| **In2.Cu** | power/signal |
| **B.Cu** | GND pour + stitching |

Excluding In1.Cu from routing is Ossmann's rule 1 (*"unbroken power planes on
the inside of your board"*), which v1 arrived at independently and which
`skills/kicad-pcb/references/rf-design.md` 3(d) now carries as canon.

Constants derived ONCE from this stackup (**ADR-0004**, regenerable — the ADR
carries the command, not the digits), and identified by the tuple canon
requires rather than by the stackup alone:

    (JLC04161H-7628 h=0.2104 er=4.4 t=0.035 / w = 0.360 mm /
     CONDUCTOR-BACKED COPLANAR WAVEGUIDE, s = 0.2005 mm both sides, BARE /
     quasi-static conformal mapping, Ghione-Naghed-Wolff CBCPW)

    eps_eff 3.1557   Z0 51.249 ohm   t_pd 5.9255 ps/mm
    lambda_g(6 GHz) 28.1269 mm       phase 12.7991 deg/mm

Every v2 document cites these; none re-types them.

**THESE REPLACED A BARE-MICROSTRIP SET, AND THE CROSS-SECTION IS WHY.**
ADR-0003 derived `eps_eff 3.3286 / t_pd 6.0857 / 13.145 deg/mm` for a strip
over a plane with nothing lateral. MEASURED 2026-07-30 off the saved board
(`03_src/line_type.py` -> `line_type.txt`; it marches a perpendicular
ray at 0.0005 mm into the F.Cu GND zone FILL and reads no rule file): a GND
pour runs alongside EVERY arm at **0.2005–0.2010 mm edge-to-edge on both
sides** — it went to the 0.200 mm DRC clearance and stopped — over **61.3 %
to 93.2 %** of each arm (mean 75.2 %). `g/h = 0.955`, `g/w = 0.558`. At
`g ~= h` the coplanar ground carries a real share of the return current, so
these arms are grounded coplanar waveguide, not microstrip.

The remainder is not microstrip either: it is ONE interval per arm,
1.40–1.75 mm at the SMA end, coinciding exactly with the In1.Cu antipad void
(ANT1 s = 0.00–1.75, ANT4 s = 12.62–14.32, …). That is the LAUNCH — no
coplanar ground and no reference plane. **There is no bare-microstrip section
anywhere on this board.** In1.Cu is otherwise continuous beneath every arm;
RX1_TAP has no void at all.

The correction is **−5.19 % on eps_eff** and **−4.97 deg of absolute phase on a
14.366 mm arm at 6 GHz**. Z0 moves +1.9 %, so the impedance survives and the
phase constant — the thing this board sells — did not. **OWED and stated, not
closed:** every constant set here is a BARE-trace model, and `rf-design.md`
4A(iii) measures a conformal solder mask at **+6.3 % on eps_eff**, larger than
this whole correction. The word BARE in the tuple is the disclosure.

## 6. Ground strategy

One ground net, poured on all four layers, with In1.Cu unbroken beneath the RF.
Each SMA jack's four ground posts gets its own via cluster AT the pad — the
posts are the launch's return path and are only electrically short if the return
is.

**WHAT THE GROUND VIAS BESIDE AN ARM ARE FOR CHANGED WHEN THE LINE TYPE WAS
MEASURED (ADR-0004), AND THE BOUND GOT TIGHTER, NOT LOOSER.** A via fence
beside a MICROSTRIP is a lateral shield, and `lambda_g/20` keeps it a
continuous wall instead of a periodic structure with a passband — that is what
ADR-0003's bound claimed. On a GCPW that job is already discharged and **not by
the fence**: the coplanar pour is solid copper 0.2005 mm from the trace edge, an
aperture of zero by construction that no via wall at any pitch improves on.

The vias' remaining job is the VERTICAL one. A conductor-backed CPW has TWO
grounds — the F.Cu coplanar pour and the In1.Cu reference — and those sheets
form a parallel-plate waveguide with **no cutoff**. Any asymmetry (a bend, the
launch, an unequal excitation of the two coplanar grounds) puts a voltage
between them and launches the parasitic parallel-plate/slotline mode, which
carries power out of the line and couples arm to arm. The vias SHORT the two
sheets, and a via wall is a short only where it is electrically short against
THAT mode. That mode fills the dielectric between two conducting planes, so it
runs at the BULK permittivity:

    lambda_pp = lambda_0/sqrt(er) = 49.9654/sqrt(4.4) = 23.8201 mm
    BOUND: along-arm ground-stitch spacing <= lambda_pp/20 = **1.1910 mm**

The divisor 20 is unchanged (the fleet's inherited via-wall divisor); only the
WAVELENGTH it applies to moved — the same correction `rf-design.md` 3(b) made
once already for microstrip. Ranked at 6 GHz: microstrip `lambda_g/20` 1.3693 ·
CBCPW `lambda_g/20` 1.4063 · **parallel-plate `lambda_pp/20` 1.1910 (BINDING)** ·
free space 2.4983. **1.3693 -> 1.1910 mm is 13 % TIGHTER**, and it is tighter
across the whole declared Dk window (4.2 -> 1.2190, 4.6 -> 1.1648).

**THIS CLOSES ONE OF THE THREE EXITS THIS SECTION USED TO OFFER.** The previous
revision said the P0 could be resolved by "an ADR-0003 amendment that re-derives
the bound the board can actually hold". There is no such amendment: the honest
re-derivation moves the bound the wrong way for that hope. Recorded so no
successor spends a session looking for it.

**AS BUILT: LATTICE 0.80 PLUS A 17-BARREL PER-ARM FENCE, AND THE BOUND IS MET**
(2026-07-31, measured — `06_build/verify/fence_pitch.txt`).

**A SQUARE LATTICE AT PITCH p IS NOT A FENCE AT PITCH p.** Its
nearest-neighbour distance is p in every direction, but the spacing that
governs is the projection onto the ARM AXIS, and eight of the nine arms lie on
45-degree multiples where one lattice row projects at `p*sqrt(2)`. The lattice
steps at **0.80** = `floor_0.05(1.1910/sqrt(2))`, giving **1.1314 mm** on a
diagonal arm and 0.800 on an axis arm.

**AND THE LATTICE ALONE COULD NOT CLOSE IT.** A board-wide square grid places
its sites relative to the BOARD ORIGIN, so where an arm's flank meets other
nets' copper it has one site to offer and no way to step aside. At 0.80 it left
**eleven** apertures over the bound. Those are closed by a **per-arm fence of
17 declared barrels** (`route.yaml` `stitch.seed_stubs`), each coordinate
MEASURED by `03_src/fence_sites.py`: it sweeps the continuum inside each
aperture's +/-2.5 mm flank band at 0.05 mm in arclength and lateral offset and
asks the stitcher's own `via_site_ok` — exact collision on every copper layer
plus net-blind hole-to-hole — whether a 0.25/0.15 GND barrel can legally stand
there, with the ten SMA `avoid` rings and the module-underside rect excluded.

**THE BOUND IS MET. Every number below is measured off the CURRENT board.**

MEASURED, `06_build/verify/fence_pitch.txt` (which reads the saved
`.kicad_pcb` through pcbnew and never reads `route.yaml`, so a declared pitch
cannot certify itself; it exits 1 on FAIL):

> **worst interior along-arm aperture 1.1769 mm at RX1_TAP sideE,
> s = 18.97..20.15, against the 1.1910 mm bound — `lambda_pp/20.24` — with
> 0 of 22 arm-sides over.** `VERDICT: PASS`, exit 0.

**THE FOUR CLASSES, AND HOW EACH ACTUALLY CLOSED.** The previous revision of
this section classified 34 apertures into four classes and predicted that two
of them (the SMA `avoid` rings and the star hub / tap) would need "a per-arm
fence pass the shared stitcher does not have, or a declared, measured
exception". The first half was right and the second half was not needed:

| class | n | what closed it |
|---|---|---|
| **A — lattice projection** | 18 | pitch 0.95 -> 0.80. NOT the config value alone: `stitch.via.spacing` sat at 0.85, i.e. 0.05 mm ABOVE the new pitch, and since every lattice site passes through that net-blind guard each site refused its own neighbour — 1668 grid vias where the 0.95 lattice emitted 2208. Corrected to 0.75 (under the pitch, and 1.88x the real hole-to-hole floor of 0.40 mm) |
| **B — SMA avoid ring** | 5 | **STITCHED, not excepted.** The ring was never the obstruction — legal ground exists OUTSIDE it, and the barrels that close these sit at 1.36-2.46 mm lateral offset. What could not step aside was the lattice |
| **C — SSE control corridor** | 5 | the re-route. Taking the meander length-match pass off the `rf` wave re-laid the arms straight, and the control copper moved with it |
| **D — star hub / tap** | 6 | **STITCHED.** Same finding as B: "occupied" is not "unstitchable" |

**THE CAUTION ABOUT CLASS B IS RESOLVED, AND IT IS RESOLVED THE HONEST WAY.**
This section used to carry a candidate exception argument — that the bound
should not apply inside a launch antipad — recorded as an OPEN CANDIDATE and
deliberately NOT applied, because it had been formed after seeing which
apertures failed. It is now **retired rather than adopted**. Class B closed in
copper, so no exception was needed at all; and the criterion that WOULD have
governed was derived separately, in a fresh context given the geometry but NOT
the failure list (**ADR-0005**: an isolated aperture `<= lambda_pp/12 =
1.985 mm` under five conditions). That criterion is **stricter** than the
retired argument in the one place they overlap — it grants NO relaxation
inside a launch region, which is exactly where the old argument wanted one.
**No exception is claimed anywhere in this release.**

The module contributes a second ground reference: its own PCB plane, tied to
ours only through the `GND` castellations. That is a real discontinuity and it
is ACCEPTABLE here for one reason — **no RF crosses it.** Nothing on the module
carries a signal this board's product depends on; only DC select lines and a
supply rail cross the boundary.

## 7. Critical geometries

- **The nine radial arms.** Equal pad radii from the switch centre. The
  governing tolerance is DRIFT (`d_tau = TC*dT*dL*t_pd`), NOT static mismatch:
  PE42482A-X's own part-to-part relative-phase window is 13.2 deg = 1.00 mm of
  copper, so a tolerance tighter than that is not physics. v1's withdrawn
  "+/-0.10 mm" (= 1.3 deg) is NOT re-adopted (BRIEF A5).
- **The octilinear floor must be checked from PADS, before routing.** KRT routes
  on 45-degree multiples, so `oct(dx,dy) = max(dx,dy) + 0.4142*min(dx,dy)` is
  the shortest copper it can lay. On v1 the Euclidean pad spread was 0.3238 mm
  against a 1.4966 mm octilinear floor — found by routing for hours, findable
  from pads in milliseconds. **Stage-5 obligation, recorded here so it is not
  re-learned.**
- **Min landable width per pad** vs the netclass floor, same stage, same reason.
- **`C_SW1`/`C_SW2` hard against `U_SW` pin 8**, span <= 3 mm.
- **`R_PD1..R_PD4` at the SWITCH end, `R_S1..R_S4` at the MODULE end.** The
  pull-downs are only a power-on guarantee if they are on the switch's side of
  the series resistor.
- **The module's USB-C must remain pluggable.** Its connector overhangs the
  module edge; the carrier board must not put a tall part or the board edge
  where a cable needs to go. A NEW mechanical constraint v1 did not have, and a
  stage-5 floorplan input.
- **The module is a 3D obstruction ON BOTH FACES, and the face that matters is
  the one facing US.** This bullet used to read "it stands on castellations with
  components on its top face" — that is WRONG, it was unfalsifiable from a photo
  of the top, and it is what let the commission agent choose CONSIGN. CORRECTED
  2026-07-30 against the vendor STEP assembly, measured independently twice:
  **23 components sit on the CARRIER-FACING face** — 12 MHz crystal **1.000 mm
  proud**, RP2040 QFN-56 0.850, RT9013 0.700, twenty 0201s 0.300. The 23
  castellation lands are 0.010 mm of copper on that *same* face, so the joint
  plane and the collision plane are the same plane and the module **cannot sit
  down**. There is no reflowable joint at a 1.0 mm standoff on 2.54 mm pitch and
  no pick-and-place nozzle target, so this part is **HAND-SOLDERED and off the
  CPL** (`03_src/rules/assembly.yaml`, ADR-0002), not consigned. Its keepout is
  its whole 18.00 x 23.50 mm outline, and it imposes TWO further carrier
  keepouts that nothing in the pipeline grades — a HEIGHT keepout over the
  bottom-side parts and a COPPER keepout under ten live underside pads. Both are
  drawn into the footprint (`Dwgs.User` / `User.Comments`); see
  `01_docs/journal/04_placement.md`. If a reflowable joint is ever wanted, the
  HEIGHT keepout becomes a CUTOUT of the same rectangle — that is the only route
  to one.
- **BOOT and RESET are the only way into the bootloader, forever.** Verified
  against the vendor schematic: BOOT, RESET and SWD reach NO castellation. Once
  the module is soldered down, those two 2.500 mm buttons are the sole hardware
  route in, and there is no in-circuit debug. Physical access to both is a
  stage-5 floorplan REQUIREMENT, not a nicety.

## 8. The timing frame — INHERITED from v1, and it is a DESIGN INPUT

8192 samples per antenna, 4096 at the reference, 128 blank between dwells; one
499,712-sample buffer at 30 Msps holds exactly eight complete sweeps, and the
half-length reference dwell is the frame marker. Driven by a free-running PIO
3-bit sequencer, which is the reason an MCU is on this board at all.

**INHERITED from v1's D1 and NOT re-derived here.** v2 changes how the MCU is
packaged, not what it does. The select lines are `GP0..GP3` — four CONSECUTIVE
GPIOs, in physical order down the module's right edge, because a PIO `out`
writes a CONTIGUOUS pin range and non-consecutive pins force a
read-modify-write.

## 9. Receiver configuration this design DEPENDS on

Host must configure RX2 as **MGC not AGC**, **RX FIR bypassed or short**, and
**DC-offset / quadrature tracking FROZEN**. These are DESIGN INPUTS, not
preferences: the 128-sample blanking allowance is false without them.
INHERITED from v1.

## 10. What this board does NOT solve

- **It does not remove the QSPI comb — it relocates it.** The flash still
  clocks; it clocks on the module's PCB, ~20 mm from the star, over the module's
  own reference plane, coupled to our RF only through the shared 3V3/GND
  castellations and free space. That is expected to be better and it is not
  measured. **The first physical unit should be spur-surveyed before any phase
  table is published.**
- **It ADDS one continuous source v1 does not have:** the module's WS2812B RGB
  LED, whose internal oscillator free-runs whenever powered. Recorded as a debit
  in ADR-0001, not argued away.
- **It does not make the board turnkey.** The module is **NOT ASSEMBLED and NOT
  on the CPL** — the builder supplies one RP2040-Zero and HAND-SOLDERS it to the
  23 castellation lands (ADR-0002 Amendment 1, `03_src/rules/assembly.yaml`
  `not_assembled:`). v1 is the arm that JLC can build unattended.
  CORRECTED 2026-07-30, and the correction is called out rather than made
  quietly because THIS SENTENCE IS WHY THE CHECK EXISTS: section 7 of this same
  file was brought into agreement with the physics earlier the same day and this
  one was not, so the document contradicted ITSELF for hours while every gate
  stayed green — a zero-context reviewer found it, no checker did. The physics
  (23 components on the carrier-facing face, crystal 1.000 mm proud, so the joint
  plane and the collision plane are the same plane) is measured in section 7 and
  in ADR-0002 Amendment 1; there is no reflowable joint for JLC to place.
- **It does not settle whether the module or the bare chip is better.** That is
  what having both arms is for.
