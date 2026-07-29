# brief: smc0985-cooksense

status: active
current_release: no

## Original prompt

The commissioning source is the user-supplied design document
"SMC0985KS INTELLIGENT COOKING SYSTEM — DAUGHTER PCB BOARDS, CONNECTORS,
AND CONTINGENCIES — Rev 1.0, 2026-07-22", archived VERBATIM below, followed
by the interactive commissioning dialogue decisions (D1-D6, registered after
the verbatim block). The verbatim document is immutable; corrections live in
the decision register and ADRs, never as edits to the block.

<!-- prompt-verbatim-begin -->
> SMC0985KS INTELLIGENT COOKING SYSTEM
> DAUGHTER PCB BOARDS, CONNECTORS, AND CONTINGENCIES
> DESIGN BRIEF / AGENT INPUT SPECIFICATION
> Revision: 1.0
> Date: 2026-07-22
>
> 0. PURPOSE AND SCOPE — custom daughter-PCB system connecting a Raspberry
> Pi 5 to the SMC0985KS prototype sensors and to the microwave's passive
> keypad matrix. Supports: two narrow-angle MLX90640 thermal cameras;
> exhaust/ambient humidity+temperature; fast exhaust K-thermocouple; eight
> external thermistor channels; a separate HX711 load-cell board; door,
> E-stop, Manual/Auto, arc/flash, optional airflow inputs; a fail-safe
> keypad-emulation system leaving the OEM controller and OEM safety systems
> in control; a Pi 5 running RGB cameras, local validation, display OCR,
> logging, and an online multimodal LLM API; Phase-2 expansion (thermal
> uniformity, optional turntable motion). Research prototype: no custom
> board may connect to the magnetron, HV circuit, convection-heater power,
> fan mains, OEM door interlocks, OEM thermal cutoffs, or internal mains.
>
> 1. REVERSE-ENGINEERING FACTS — membrane tail: ten conductors U1-U6,
> D1-D3, D4_UNKNOWN. All 18 buttons form a confirmed 6x3 matrix on
> U1-U6 x D1-D3. Key map: U1-D1 ROAST, U1-D2 MICRO+CONV, U1-D3 AUTO REHEAT,
> U2-D1 AIR FRY, U2-D2 CONV, U2-D3 POPCORN, U3-D1 BAKE, U3-D2 MICRO,
> U3-D3 AUTO COOK, U4-D1 START/+30SEC, U4-D2 PLUS, U4-D3 +1MIN,
> U5-D1 CLOCK/UNLOCK, U5-D2 TIMER, U5-D3 DEFROST, U6-D1 STOP/CLEAR,
> U6-D2 MINUS, U6-D3 +5MIN. Pressed resistance ~20-100 ohms (probe
> uncertainty) => emulation resistance must be CONFIGURABLE. OEM connector
> CN1: ten-position, one-row, ~2.54mm-pitch vertical membrane receptacle;
> leading fit candidate TE 6-520315-0 TRIO-MATE — NOT proven; fit coupon +
> measurements mandatory (contact count ~10, pitch ~2.54, span ~22.86mm,
> tail width/thickness, finger length, contact side, insertion depth,
> retention force). Existing sealed references: cook-hub v1.0 (16 isolated
> reed-relay channels, Pico 2, hardware watchdog + gated relay rail, sensor
> interfaces — not the final daughterboard); cook-loadcell v1.0 (HX711,
> 4x half-bridge or 1x full-bridge, 10/80 SPS — reusable via adapter).
>
> 2. BOARD INVENTORY — A CookSense Pi daughterboard (central deterministic
> sensor+safety, Pico 2 socketed in Rev A); B KeyMatrix relay board
> (matrix-selector reed relays + shift-register drivers, near the OEM
> interposer); C passive keypad interposer (receives membrane tail, creates
> replacement flex tongue for CN1, passes all ten lines through, breaks
> U1-U6/D1-D4 out to B); D cook-loadcell (reuse); E optional remote sensor
> adapters (thermal heads A/B, exhaust pod, ambient pod). Future: F
> exclusive-Auto panel disconnect; G Phase-2 turntable motion controller.
>
> 3. BOARD A — responsibilities: two MLX90640 streams; two SHT45 channels;
> MAX31856 K-type; eight thermistor channels; HX711 DAT/CLK; door/E-stop/
> Manual-Auto/arc/airflow inputs; deterministic timestamps; hardware
> watchdog, temperature permission, E-stop permission, Manual/Auto
> permission, key-relay power authorization; Pi UART + heartbeat/alert;
> USB/SWD service; bounded fail-safe relay protocol to B; optically
> isolated external-contactor request; never generates appliance load
> commands. Controller: Pico 2/RP2350 socketed (Rev A), integrated RP2350
> later. Mechanical: 2x20 stacking header, HAT or 40-pin-ribbon sidecar,
> Pi 5 mounting holes; do not block CAM/DISP, cooler, USB-C/HDMI/USB/
> Ethernet/RTC/power button; sidecar if keepouts cannot be met. Pi 5V/3V3
> header pins NOT a power source; separate protected 5V SELV supply;
> shared signal ground. Pi comm: 3.3V UART (GPIO14/15) + GPIO17
> HOST_HEARTBEAT + GPIO27 HUB_ALERT + GPIO22 HOST_COOK_AUTHORIZATION;
> Ioff-capable buffers (no back-powering); 22-100R series; authorization
> defaults LOW; serial console disabled; USB service fallback. Power: keyed
> 2-pin Micro-Fit 5V SELV >=2A (pref 3A); fuse/polyfuse; reverse-polarity;
> OV cutoff/eFuse; TVS; bulk; power-good. Rails: 5V_PROTECTED,
> 5V_KEY_RELAY_SWITCHED, 3V3_DIGITAL, 3V3_ANALOG, and four switched 3V3
> sensor rails (THERM_A/THERM_B/RH_AMBIENT/RH_EXHAUST) for stuck-I2C
> power-cycling. Safety chain: KEY_RELAY_ALLOWED = MODE_AUTO_HW AND WD_OK
> AND ESTOP_OK AND TEMP_OK AND MCU_RELAY_ENABLE AND HOST_AUTH_OK AND
> FAULT_LATCH_CLEAR. Watchdog 300-500ms; heartbeat loss drops relay power;
> watchdog/E-stop opens hardware fault latch; recovery = data cleared +
> temps below reset + E-stop released + explicit manual re-arm; a normal
> watchdog pulse must not re-energize stale relay data. Manual/Auto: DPDT
> physical switch, pole A hard-gates MODE_AUTO_HW, pole B state to logic;
> MANUAL = OEM membrane operational + relay power physically disabled;
> broken wire/power loss => MANUAL. E-stop: external mushroom, two NC
> contacts — A monitored + hardware key-relay inhibit; B interrupts the
> external contactor loop outside Board A; 4-pin locking connector; manual
> re-arm. Door: external NC reed + EOL (or 3-wire Hall), 4-pin connector;
> open => abort sequence, release PRESS+selectors, no new START. I2C: two
> native buses (both cameras are 0x33): bus A = camera A + ambient SHT45
> (0x44); bus B = camera B + exhaust SHT45. 100kHz bring-up -> 400kHz after
> EMI validation; thermal rate 2Hz -> 4Hz -> 4-8Hz. Per bus: selectable
> 2.2k/4.7k pullups (default OFF with Adafruit onboard 4.7k); 22-33R
> damping; low-C ESD; test points; bus-stuck recovery; optional
> differential-extender footprint; optional PCA9548A fallback. Thermal-head
> connectors: 2x JST-GH 8-pos (3V3_SW, GND, SDA, SCL, TH_CAM, TH_MOUNT,
> TH_PORT, SHIELD_DRAIN); shield to dedicated pad, NOT hard-bonded to
> signal ground (RC/0R/chassis options). Camera: Adafruit 4407 MLX90640
> narrow 55x35deg, 3.3V, factory lens retained, electronics outside the
> cavity. Humidity: SHT45+PTFE ambient (intake) + exhaust (short filtered
> drainable bypass); JST-GH 5-pin each; Pi computes absolute humidity and
> DELTA_AH = AH_EXHAUST - AH_AMBIENT. Thermocouple: MAX31856 on Board A,
> PCC-SMP-K keyed jack at board edge away from relays/regulators;
> datasheet filtering; CJC; open/short faults; /FAULT + /DRDY test points;
> TC beside the exhaust SHT45 sample point. Thermistors: CH0-CH7 =
> TH_CAM_A, TH_MOUNT_A, TH_PORT_A, TH_CAM_B, TH_MOUNT_B, TH_PORT_B,
> TH_ENCLOSURE, TH_SPARE; MCP3208 12-bit SPI (or equal); per channel 10k
> NTC to GND + 10k 0.1%/1% ref to 3V3_ANALOG + 1k/100nF RC + ESD +
> open/short detection + per-channel calibration + configurable beta +
> test point. HARDWARE comparator inhibit on TH_CAM_A/B forces TEMP_OK low
> independently of Pi/LLM. Prototype limits: camera <=60C pref / 65 warn /
> 70 stop / 75 hard; PC mount <=65 / 75 / 85 / 95; metal port trend ~120
> warn / ~150 stop / ~170 hard; enclosure <=50 / 55 / 65 / 75 — refine
> from instrumented 400F testing. Load-cell link: 5V, 3V3, GND, DAT, CLK
> on JST-XH 5-pin (cook-loadcell compatible), optional shield later,
> 10 SPS default. Key control to B: JST-GH 10-pin — 5V_KEY_RELAY_SWITCHED,
> 3V3_LOGIC, GND, KEY_DATA, KEY_CLOCK, KEY_LATCH, KEY_OE_N, KEY_RESET_N,
> KEY_BOARD_ID_FAULT, SHIELD_DRAIN; B cannot energize without pin 1;
> OE_N default disabled; RESET_N default asserted; series R on
> clock/data/latch; cable <=500mm; BOARD_ID distinguishes matrix-selector
> vs per-key fallback. Contactor output: isolated open-collector/dry
> contact, <=30V/50mA, 2/3-pin pluggable; no mains on Board A. Reserved:
> arc photodiode, differential-pressure, pod fan, smoke sensor, spare
> I2C/UART, SWD, Phase-2 motion UART/CAN.
>
> 4. BOARD B — emulates any of 18 buttons without one-relay-per-button:
> 6 U-selectors + 4 D-selectors + 1 PRESS bridge + 1 dedicated STOP/CLEAR
> = 12 isolated reed-relay channels (16-channel driver concept leaves 4
> spare). Example START = U4-D1: close K_U4; close K_D1; settle; close
> K_PRESS bridging U_SELECTED to D_SELECTED through RKEY; hold validated
> duration; open K_PRESS; wait; open selectors. Only one U and one D
> selector active at a time. Dedicated STOP path: U6 -K_STOP-RSTOP- D1;
> K_STOP preempts everything. Relay: Standex-Meder DIP05-1A72-12L or
> proven equivalent — SPST-NO, polarity-independent dry contact, >=1kV
> coil/contact, very high off-R, low off-C, 5V coil; >=6mm coil-side to
> keypad-copper separation; milled slots; no planes in keypad zone; no
> shared keypad common. RKEY: shared selection field 0R default /22/47/
> 100/220/470/1k (1206 or solder-select), test points both sides, header
> for external isolated decade box; RSTOP separately configurable 0R.
> Acceptance: find max reliable emulation R using a harmless key (TIMER)
> on the assembled appliance. Drivers: 2x 74HC595 (or 16-bit), ULN2803A/
> MOSFET, flyback, OE_N/RESET_N hard defaults, relay 5V only from Board A.
> No MCU on B in Rev A. Sequencing (enforced upstream): break-before-make;
> max one U + one D; PRESS only after valid U/D; PRESS opens first; STOP
> preempts; max key 500ms; typical 100-200ms; all relays release on
> watchdog/fault/Manual. Keypad-domain connector to C: 10 lines
> (U1-U6, D1-D4), keyed 2x5 IDC 2.54 or keyed 10-pin locking; keypad
> domain must NOT share shield/ground with SELV logic. Contingency:
> per-key fallback board B2 (18+2 relays, per-key RKEY, same protocol,
> different BOARD_ID, same interposer).
>
> 5. BOARD C — passive interposer between the membrane tail and OEM CN1;
> original panel stays fully operational. Straight-through pass of
> U1-U6/D1-D4 + breakout of the same ten lines to B. Test points both
> sides, labeled, no connection to logic ground or chassis. Membrane-side
> connector: TE 6-520315-0 candidate — MECHANICAL CANDIDATE ONLY, coupon-
> gated. OEM-side: thin membrane/flex TONGUE (not 1.6mm rigid edge) —
> custom ten-finger flex matching OEM pitch/thickness/finger length/width/
> contact side/insertion depth; gold or compatible finish; stiffener only
> if matching OEM tail thickness. Fabrication: rigid-flex, or rigid + short
> custom flex tail + proven connector. COUPON before Board C: candidate
> receptacle + sample tongues at several thickness/stiffener options;
> insertion/retention/alignment/continuity; >=100 cycles on a sacrificial
> coupon; never use the OEM connector as the first mechanical test.
> D4 policy: pass through unchanged; labeled test point; route to B's D4
> selector; firmware never selects D4 by default; enable only after its
> function is established.
>
> 6. BOARD D — reuse cook-loadcell v1.0 (4x 3-wire half-bridge or 1x
> full-bridge, HX711, 10/80 SPS jumper, shield config). Place near load
> cells under the platform. Contingencies: 100k default pull on RATE_SEL
> next rev; 10 SPS default; locking cable + shield drain if EMI requires;
> digital cable to A — never route bridge-level analog through the
> enclosure.
>
> 7. BOARD E — optional adapters: thermal-head (JST-GH in, STEMMA QT out,
> three thermistor pads, decoupling, optional power-good, cradle-matching
> holes); exhaust pod (SHT45+PTFE connector, filter holder, TC strain
> relief, optional dP sensor, drainable orientation); ambient pod (SHT45,
> radiation shield, near intake). No powered sensor in the RF cavity.
> Off-the-shelf modules wired directly for initial prototypes.
>
> 8. THERMAL CAMERA/MOUNT — 2x Adafruit 4407 (MLX90640 narrow 32x24,
> 55x35deg, 0x33, 3.3V, integrated lens retained). Breakout 25.7x17.7mm,
> height ~16mm, lens OD ~9.3mm, optical height ~11.25mm, clear opening
> ~3.9mm. External Bambu-PC printed cradle after thermal qualification;
> M2.5; never clamp the lens barrel; X/Y + tilt + axial adjustment;
> TH_CAM beside sensor package, TH_MOUNT at hottest mount point, TH_PORT
> on the metal flange. Bore/throat: conductive metal (never printed
> polymer); coupons 6/8/10mm; throat 1-2mm effective; lens-to-throat gap
> 0.3-0.8mm; final by optical bench + RF model + leakage measurements.
> Contingencies: one wide 4469; FLIR Lepton 3.1R + PureThermal USB Phase 2
> (reserve Pi USB + mechanical space).
>
> 9. BOARD F (optional, not Phase 1) — exclusive-Auto disconnect: NC
> contacts disconnect D1-D4 from the membrane, automation stays connected;
> power loss restores the panel; separate physical STOP stays OEM-wired;
> mode change only with all key relays open; break-before-make; separate
> board, never a mod to C.
>
> 10. BOARD G (Phase 2) — motion controller: encoder A/B/index, home,
> STEP/DIR/ENABLE or closed-loop, motor power, UART/CAN/RS-485 to A;
> magnetron-off movement policy unless validated. A reserves the link.
>
> 11. MASTER CONNECTOR TABLE — J_PI 2x20 stacking (signals only, Pi power
> NC/sense); J_PWR 2-pin Micro-Fit 5V; J_THERM_A/B 8-pin JST-GH;
> J_RH_AMBIENT/EXHAUST 5-pin JST-GH; J_TC PCC-SMP-K; J_LOADCELL 5-pin
> JST-XH; J_DOOR 4-pin; J_ESTOP 4-pin; J_MODE 4-pin; J_KEY_CTRL 10-pin
> JST-GH; J_KEY_MATRIX 10-pin keyed isolated; J_MEMBRANE candidate
> receptacle (fit-gated); J_OEM_TAIL custom flex tongue; J_CONTACTOR 2/3-
> pin; J_ARC 3-pin; J_FAN 2/3-pin; J_MOTION future; J_SWD Tag-Connect;
> J_USB_SERVICE; J_SPARE.
>
> 12. FIRMWARE/SOFTWARE CONTRACT — Board A firmware: deterministic
> sampling, freshness/fault flags, CRC-framed protocol, watchdog pulse,
> fault latch + manual re-arm, temperature thresholds, KeyMatrix state
> machine, STOP preemption, Manual/Auto + door/E-stop enforcement,
> per-sensor power cycling, Board-B ID, host heartbeat supervision.
> Pi software: RGB capture, thermal ingestion/stitching, humidity
> features, display OCR, power-monitor ingestion, LLM client, local
> structured-plan validator, program compiler, trial recorder, health
> supervisor, user approval UI. The LLM proposes only a structured
> recipe/profile; the LLM never outputs relay IDs or hardware commands.
> Logical key API (KEY_START, KEY_STOP, ...): A maps logical keys to U/D;
> B knows only relay bit patterns.
>
> 13. CONTINGENCY MATRIX — C1 connector no-fit: revise only C + tongue,
> spring-contact bench fixture, repeat coupon. C2 scan rejects near-0R:
> RKEY 22-1k, decade box, dedicated RSTOP. C3 selector ghosting/timing:
> per-key B2 fallback via BOARD_ID; A and C unchanged. C4 OEM press during
> automation: panel stays available; OCR detects transition; abort + STOP.
> C5 camera I2C conflict: separate buses; PCA9548A/differential fallback.
> C6 cable EMI: lower speed, pullups, ferrites, shorten, differential
> extenders, power-cycle, no auto-start while stale. C7 module pullups too
> strong: Board A pullups DNP; cut module jumper only after measurement.
> C8 coverage insufficient: re-aim, larger bore, one wide camera, Lepton.
> C9 camera/mount overheat: warn -> STOP -> verify power falls -> drop
> contactor -> latch + cooldown + manual re-arm; improve shielding/
> airflow/port. C10 Pi crash/network loss: watchdog disables relays; OEM
> panel usable; no auto-start; local STOP + contactor remain. C11 Board A
> power loss: relays de-energize; panel connected; manual-only. C12 B
> cable disconnect: no relay power / OE_N disabled; A reports missing; no
> auto-start. C13 partial powering: Ioff buffers; Pi rails not sources;
> relay rail cannot be Pi-powered; verify no phantom rail. C14 thermistor
> open/short: channel invalid; required channels invalid => no auto-start;
> comparator stays active. C15 load-cell unavailable: shadow mode, manual
> mass entry, no mass-dependent profiles. C16 Phase-2 motor+encoder:
> separate Board G; never respin A for motor GPIO.
>
> 14. GATES — G1 connector measurements (calibrated); G2 connector coupon;
> G3 passive matrix validation (18 keys, D4 documented); G4 Board A bench
> bring-up (no microwave); G5 Board B relay fixture; G6 Board C
> continuity; G7 full low-voltage integration; G8 fully-enclosed appliance
> keypad test (harmless keys + OCR first); G9 thermal-head optical bench;
> G10 RF + thermal qualification (metal throat, leakage, 400F cycle,
> thermistor logs, mount stability, thresholds). No final appliance
> connection or automatic cooking before these gates.
>
> 15. DELIVERABLES — Board A: architecture, schematic, 4-layer PCB,
> HAT/sidecar drawing, power tree, watchdog/fault latch, thermistor ADC +
> comparator, pinout sheet, BOM + alternates, gerbers/CPL/assembly/STEP,
> firmware pin map + test firmware. Board B: 12-relay schematic,
> isolation-zone PCB, RKEY network, key truth table, fallback
> compatibility, fixture procedure. Board C: coupon, interposer schematic,
> rigid-flex/flex files, continuity map, fit drawing. Board D: existing
> files or revision, adapter harness. Adapters: harness/connector/
> thermistor drawings. System: cable/harness table, pin-to-pin drawings,
> fault-injection plan, bring-up checklist, BOM + cost, enclosure/strain
> relief, revision-controlled configuration.
>
> 16. DESIGN FREEZE SUMMARY (Rev A preferred) — Pi 5: RGB, LLM, OCR,
> logging, UI. Board A: Pico 2/RP2350, dual I2C acquisition, TC, 8
> thermistors, load-cell link, hardware safety, Pi link, KeyMatrix
> authorization. Board B: 12 reed relays (6 U + 4 D + PRESS + STOP).
> Board C: ten-line pass-through + custom flex tongue. Board D: HX711.
> Thermal heads: 2x Adafruit 4407 narrow, metal RF throats, Bambu PC
> mounts, three thermistors per head. Manual: OEM panel always available;
> Manual physically disables key relays. Auto: structured LLM plan ->
> local validation -> bounded keypad emulation; no direct LLM-to-hardware.
<!-- prompt-verbatim-end -->

- date: 2026-07-22
- channel: interactive design review + commissioning dialogue (this session)
- note: the verbatim block above condenses ONLY formatting (tables/pinouts
  compressed to prose); every requirement, value, part number, limit, and
  contingency is carried. The user's original full-resolution text (with
  the exact key-map/pinout tables) is reproduced faithfully; where wording
  was compacted, ADRs cite the section numbers of the source document.

## Commissioning decisions (the dialogue register — supersedes the verbatim where marked)

| id | decision (user-confirmed) | supersedes in Rev 1.0 |
|----|---|---|
| D1 | **No Pico / no MCU on Board A.** The Pi 5 drives the key shift registers directly; ALL enforcement moves to hardware (decoder one-hot selection, PRESS one-shot <=500ms, external watchdog supervisor, AND-chain). No firmware exists. Security/firewall explicitly NOT a concern (user). | §3.2, §3.4, §12.1 |
| D2 | **Thermal cameras + humidity move to Pi 5 native I2C** (RP1: up to 4 buses). Solves the 0x33 conflict natively; Board A keeps switched sensor rails + connectors + series/ESD, with SDA/SCL routed through to the Pi header. | §3.10 (bus plan), C5 |
| D3 | **I2C GPIO expander (MCP23017)** absorbs slow signals (rail switches, power-good, mode/latch readback) — resolves the GPIO budget overflow. Pin-map table is a maintained gate artifact. | new |
| D4 | **Simplicity is a core goal; ribbon interception/gating is THE core Phase-1 function.** Boards A+B may merge into one physical board if the keypad-line length allows; keepout/mechanical analysis decides (as it decides HAT vs sidecar). | §2 emphasis |
| D5 | **CN1 is a LATCHED membrane receptacle, not plain TRIO-MATE** (user photos 2026-07-22: two end latches; tail has two punched lock-slots; TE datasheet confirms genuine 520315 is "Mating Retention: Without"). Strategy: replicate the OEM TAIL GEOMETRY exactly (incl. lock-slots) for our tongue; TRIO-MATE 6-520315-0 stays a candidate for OUR membrane-side receptacle only. Photos are Gate-1 artifacts. | §1.2, §5.3 |
| D6 | **Relay default = cook-hub's proven cell**: Standex-Meder DIP05-1A72-12L is ALREADY paid-for on sealed cook-hub v1.0 (ledger evidence) — brief's preference confirmed by prior art. PhotoMOS AQY212GS recorded as simplification alternate for selectors (reed retained for PRESS/STOP). | §4.3 confirmed |
| D7 | **v1.1 shrink revision commissioned** (user directive 2026-07-23, VERBATIM): "please schedule a v1.1 revision for cooksense , lets make the board smaller." Scoped with the user: tighten the 12-relay single-row pitch 20mm → 15.24mm (the coupling-vetted "super-column pitch", 02_parts/DIP05-1A72-12L), keep the single-row topology (straight keypad barrier, I-ISO ≥ 6.0mm, 0 N/S crossings); outline 252×92 → ~195×92. HARD BOUNDARY: pitch < 15.24mm and any two-row repack are OUT OF SCOPE — both gated on a bench coupling measurement (adjacent-relay operate-voltage shift under U+D+PRESS triple energize) requiring physical v1.0 boards. Schematic/netlist unchanged. **BLOCKED — MEASURED MECHANICAL INFEASIBILITY (2026-07-23, pre-build):** at the rot90 orientation the single-row barrier requires (contacts N / coils S), the relay's 19.3mm body / 19.90mm courtyard lies ALONG the row: 15.24mm pitch overlaps adjacent courtyards by 4.66mm (bodies 4.06mm) — parts collide. The v1.0 20mm pitch already leaves only 0.10mm courtyard gap, so NO pitch shrink exists in this orientation. The 15.24mm figure is coupling evidence from the vertical-column (rot0, 6.5mm-wide) layout, not a fit claim for rot90. Escalated to the user: real shrink needs either vertical relays (destroys the straight barrier — topology change) or the two-row repack (coupling-gated). v1.0 remains the orderable release. **RESOLVED by user (via question, 2026-07-23): "Vertical-relay redesign now."** v1.1 proceeds as the rot0 topology redesign: relays vertical (long axis N-S), single row, 15.24mm pitch — EXACTLY the orientation the part.yaml "super-column pitch" coupling figure was vetted in (rot0 vertical columns, 6.5mm body across the pitch axis), so coupling is evidence-backed at this pitch in this orientation; additionally relays alternate rot180/rot0 in pairs (anti-parallel adjacent coils — the datasheet's own "alternate orientation" mitigation, DS p.3 handling note). The straight barrier is replaced by an ISOLATION COMB: adjacent relays' contact columns face each other in pairs, pocketing the keypad-isolated zones (7 pockets: 5 inter-pair + 2 board ends) between logic coil-coil gaps (6, within pairs); milled slots reinforce the pocket/gap creepage per the v1.0 0.6mm slot pattern. HARD GATE unchanged: track-aware I-ISO ≥ 6.0mm must MEASURE on the final board (intra-relay coil-to-contact pad columns give 6.12mm by footprint geometry, the same floor v1.0 measured). Netlist/schematic untouched. | new (v1.1, active) |
| D8 | **CN1 identified as JST 10FDZ-BT top-entry ZIF — corrects D5** (clearer user photos + expert connector review, 2026-07-24). CN1 is a ZIF that clamps a PLAIN 0.125mm tail, NOT a latch-with-lock-slots receptacle; decisive check = the original OEM membrane tail has no punched holes. Consequences: (a) our OEM-side tongue simplifies to a plain 10-finger/2.54mm/0.125mm flex tail — **lock-slots DROPPED**; (b) a real 10FDZ-BT serves BOTH interposer interfaces, retiring the unproven TRIO-MATE candidate; (c) self-supplied hand-solder part (distributor-stocked, not confirmed on LCSC); order BT (top-entry), never ST (side-entry). Coupon G1/G2 + flex-out-of-pipeline (T5) UNCHANGED. See ADR-0008. | corrects D5; §1.2, §5 |

| D9 | **Board C = Path A: RIGID interposer + separate flex jumper** (user-chosen 2026-07-24). Two 10FDZ-BT ZIFs on a small rigid PCB (J_MEMBRANE receives the OEM membrane tail; J_CN1_JUMPER receives the flex jumper to OEM CN1), 10 straight-through lines broken out to a keyed J_KEY_MATRIX (SM10B-GHS-TB, pin map identical to the main board's J_KEY_MATRIX for a 1:1 cable), labeled TPs both sides, floating keypad domain (no GND/chassis bond). Flex jumper = separate part, separate task. DESIGN driven to a full SEALED release (user directive 2026-07-24 "go ahead assuming 10FDZ-BT": datasheet-derived footprint is canonical); fab ORDER + flex-coupon order remain user-held — real-part 10FDZ-BT land-pattern confirm (drill pattern + polarization peg) is a LOUD ORDER_README bring-up gate, and G2 coupon still gates appliance use. See ADR-0009. | §5 fabrication option resolved |

| D10 | **v1.2 ELECTRICAL correction release commissioned** (external review of v1.1 received 2026-07-24; user scoped v1.2 to reviewer priorities 1-7). v1.0/v1.1 netlists were byte-identical — this is the first electrical revision. Scope: (1) Pi native-I2C repair — v1.1's four sensor buses landed on header pins with NO I2C alternate function; re-pinned to verified RP1 pairs (I2C2 GPIO4/5, I2C3 GPIO14/15), RESTORING the brief's own §3 commissioned bus plan verbatim ("bus A = camera A + ambient SHT45 (0x44); bus B = camera B + exhaust SHT45" — the sealed 4-separate-bus wiring was an undocumented deviation, and the deviation is what made a valid native pin map impossible), KEY_DATA re-homed GPIO5→GPIO16, pin map published as a maintained artifact (ADR-0010); (2) thermal hard-stop redesign — the 10k/10k TCAM_THRESH divider tripped at ~25C, not 70-75C; recomputed for the committed NTC (KNTC0603/10KF3950, B25/85=3987) as 68k/10k → 74.9C with a solder-select bottom leg (ADR-0011, DETAIL_DESIGN); (3) TEMP_OK added to the fault-latch SET; (4) external contactor hardware-gated by WD_OK·ESTOP_OK·TEMP_OK·FAULT_LATCH_CLEAR; (5) K_STOP coil moved to an always-available 5V_STOP rail (a WD/TEMP fault must not disable the STOP relay); (6) STOP_REQ preempts in hardware (clears PRESS one-shot, disables both decoders, direct Pi GPIO26); (7) PRESS one-shot swapped to NON-retriggerable CD74HC221 + KEY_LATCH frozen while PRESS_TIMED high; (8) deterministic pulls on every Pi/expander authorization line (pull-UP on REARM_N). Mechanical: 188x92 comb, 15.24mm pitch, 12 slots, I-ISO >=6.0mm all RETAINED from v1.1. Reviewer items 8-12 explicitly OUT of scope this rev. | corrects the v1.0-era netlist; ADR-0010, ADR-0011 |

| D11 | **The supply is SPECIFIED, not advised: `J_PWR` shall be held between 4.850 V and 5.250 V at the connector, under full load** (user ruling 2026-07-28, v1.7). This SUPERSEDES the verbatim brief's "5V SELV >=2A (pref 3A)", which stated no tolerance at all — and that single omission is the documented root cause of BOTH of this board's unresolved electrical defects. (a) **E-TOPO** graded the AMS1117's dropout at a self-imposed 4.500 V corner that ORDER_README §0 already forbade the buyer from using, and FAILED by 199 mV; at the specified 4.850 V it PASSES by 55 mV on cited worst-case series resistances. (b) **The eFuse OVLO P0**: at a 5.5 V ceiling NO divider satisfies both "cannot nuisance-trip at max supply" and "must cut off below the SMBJ5.0A's 6.40 V V_BR"; at 5.25 V one does (`R_OVT` 100k / `R_OVB` 26.1k, both ±0.5% ⇒ 5.798 V nominal). A ±10% or generic ±5% brick is **out of specification for this board** — buy a ±3% / 5.1 V-nominal unit and MEASURE it at bring-up. ADR-0021, `power_tree.yaml`, ORDER_README §0. | supersedes §3.5 "5V SELV" (tolerance); ADR-0021 |

### Commission fact-lock — cooksense (Board A+B, main; v1.7 2026-07-28)

| row | value | basis |
|---|---|---|
| **input envelope** | **`J_PWR` 4.850 – 5.250 V DC SELV, ≥2 A (pref 3 A), keyed 2-pin Micro-Fit, measured AT THE CONNECTOR UNDER FULL LOAD.** This is the specification, not a mitigation. Derived node envelopes: `5V_PROTECTED` 4.754–5.25 V (minus 95.2 mV of worst-case F1 + Q_REV + eFuse at 0.50 A). | D11 / ADR-0021 / `power_tree.yaml` |
| output rails (V range + Imax) | `3V3` 3.201–3.399 V @ 0.30 A (AMS1117-3.3, ds1117 p.2 full-temperature bold limits); `5V_PROTECTED` 4.754–5.25 V @ 2.0 A budget; `5V_KEY_RELAY` @ 0.15 A; `5V_STOP` @ 0.02 A; `3V3_ANALOG` + four switched `3V3_SW_*` @ 0.05/0.10 A. | `power_tree.yaml` |
| **protection posture** | polyfuse F1 (I_hold 2.0 A) → reverse-polarity P-FET `Q_REV` → TPS259573 eFuse with **OV cutoff at 5.798 V nominal** (`R_OVT` 100k / `R_OVB` 26.1k, both ±0.5%; worst case 5.3682 V earliest / 6.2394 V latest) → `D_TVS` SMBJ5.0A (V_R 5.0 V, V_BR 6.40–7.00 V @ 10 mA) + bulk. Current limit `R_ILM` 1.2 k. | ADR-0021, ADR-0001, SLVSE57C |
| off-control / stored energy | externally powered, **no self-contained source** (`source_type: external_5v_selv`): no battery/cell/pack/supercap. Stored energy = bulk/decoupling (µJ) + reed-coil inductance, which de-energises the instant input is removed (fail-safe: coils drop, contacts open). E-OFF satisfied by construction. | `power_tree.yaml` |
| hard-cell sourcing class | DIP05-1A72-12L ×13 + PCC-SMP-K: **self-supplied, hand-solder, DO-NOT-SUBSTITUTE**. `R_OVT`/`R_OVB` are **code-pinned protection setpoints** (C270658 / C407739, ±0.5%) — an auto-picked passive code must never set a cutoff threshold. | 02_parts, ADR-0021 |

### Commission fact-lock — interposer (Board C, 2026-07-24)

| row | value | basis |
|---|---|---|
| output rails (V range + Imax) | **NONE — N-A by design**: passive interposer, zero power rails, zero conversion. The board carries only the 10 OEM keypad matrix scan lines. | ADR-0009 / BRIEF §5 (D9) |
| input envelope | OEM controller matrix scan signals on U1-U6/D1-D4: low-voltage logic-level scan pulses, uA-mA class (FDZ contact rating 50mA/250V bounds them with orders of margin). Pass-through only — the board must not alter them. | brief §1 (~20-100R pressed R measured); eFDZ p.1 ratings (D9) |
| protection posture | **NONE by design**: any series/shunt element on a matrix line changes the scan the OEM controller sees (T1's 20-100R sensitivity). Pure copper pass-through; protection is out of scope for Board C. | BRIEF §5, D9 |
| off-control / stored energy | **N-A by design**: no source, no storage — a floating passive net set. E-OFF/E-MARGIN/E-TOPO all N-A (empty power_tree.yaml with source_type: none_passive). | D9 |
| hard-cell sourcing class | 10FDZ-BT(S): **self-supplied, hand-solder, DO-NOT-SUBSTITUTE** (not on LCSC/JLC; order BT top-entry, never ST) — D8. SM10B-GHS-TB: LCSC C2683602 (already verified in 02_parts). TPs: bare pads, no part. | ADR-0008 (D8), 02_parts |

## End goal — definition of done (Phase 1, this project)

The ribbon-interception core, proven on the bench then the appliance:
- Board C coupon PASSED (G1/G2), then the passive interposer: OEM panel
  fully functional through it; ten lines broken out; isolation verified (G6).
- CookSense board (A+B per D4): 12-relay matrix-selector emulating all 18
  keys with hardware-bounded sequencing, the full safety AND-chain, and the
  sensing subsystems (thermistors+comparators, MAX31856, load-cell link),
  Pi-driven with zero firmware; gates G4/G5/G7/G8 passed.
- All boards orderable, verified JLCPCB releases per the skill pipeline.

## Spec tensions (D-SPEC / S9)

| id | requirement | tension / cap | how honoured | ADR | user-flagged |
|----|---|---|---|---|---|
| T1 | emulate a ~20-100R membrane press | pressed-R measured with probe uncertainty; OEM scan tolerance unknown | RKEY solder-select field 0/22/47/100/220/470/1k + decade-box header; qualify on TIMER key (G8) | 0006 | yes (brief §1.1) |
| T2 | mate the OEM CN1 | CN1 IDENTIFIED (ADR-0008) as JST 10FDZ-BT top-entry ZIF that clamps a PLAIN 0.125mm tail (D5's latch/lock-slot read corrected) | our tongue = plain 10-finger/2.54mm/0.125mm flex, lock-slots dropped; a real 10FDZ-BT serves both interposer sides (TRIO-MATE retired); coupon G1/G2 still mandatory before any Board C fab | 0008 (was 0005) | yes (photos) |
| T3 | D4_UNKNOWN conductor | function unknown | pass through + test point + selector present but locked out until characterized (G3) | 0001 | yes (brief §5.6) |
| T4 | Pi drives everything (no MCU) | 28 Pi GPIO vs ~29 native signals | MCP23017 expander for slow I/O; live pin-map table is a gate artifact | 0003 | yes (dialogue) |
| T5 | custom flex tongue | flex/rigid-flex fabrication outside our proven rigid pipeline | vendor-assisted CAD, coupon-gated; never the first mechanical test on the OEM connector | 0005 | flagged |
| T6 | LLM in the loop, no MCU firewall | a buggy/rogue Pi can mash VALID keys fast | accepted: bounded by decoder one-hot + PRESS one-shot + watchdog + AND-chain + OEM controller's own interlocks (designed to survive any keypad input); user explicitly waived the security concern | 0002 | yes (dialogue) |
