# Fresh-context red-team review — topology / protection / ratings

```yaml
review_type: topology-protection-ratings
review_date: 2026-07-31
source_commit: 962c3cdaeba5070d5b668bf01a70a4ccc6498c51
source_state: immutable-git-archive
reviewer_context: fresh-adversarial
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
```

## Provenance and scope

I reviewed an isolated `git archive` of commit
`962c3cdaeba5070d5b668bf01a70a4ccc6498c51`. No file contents under
`08_reviews/` and no prior review or disposition contents were opened. The
review inputs were the binding brief, architecture/detail design and ADRs;
part dossiers and committed vendor documents; `03_src` rules/config;
tscircuit source and circuit JSON; the KiCad schematic/PCB; a newly exported
netlist; firmware source; and the current unsealed fab/BOM/CPL/stock/twin
evidence.

The current build evidence is content-linked to the reviewed commit:

- `03_tscircuit/build/circuit.json` is SHA-256
  `b14a3b0e6df2064c043fa4a56384dcf868e5ddc1a5ebb4ddd897a5dec7bd3ca3`
  in both the current work area and the immutable archive, matching
  `06_build/build_provenance.json`.
- `04_kicad/pluto_rx2_8way_v4.kicad_pcb` is SHA-256
  `4f991628c624b0af42a33294c544d1f48354f224c9be31a9bd0c0f9269d33521`
  in both locations; the schematic likewise matches at
  `26c92d3372d4b3f11f038bdccdc952e5d71f94834fa4d162932791103a6f95db`.
- A fresh netlist export differs from `06_build/netlists/...net` only in
  export date, source path and sheet-name metadata; its electrical content is
  the reviewed schematic's content.

All numerical claims below marked **MEASURED** were recomputed in this review
from those inputs. Vendor limits are **CITED** from the committed vendor
documents/dossiers and cross-checked against the PDFs where material.

## Verdict

`design_verdict: SOUND`

The implemented carrier topology matches the binding intent and has no open
P0: seven direct antenna paths plus the two-resistor RX1 reference tap feed the
PE42482A-X; RFC feeds RX2; the RX1 main line remains continuous; V1..V4 have
source resistors and switch-side pull-downs; LS, NC and EP are grounded; the
module's 5 V pad is unconnected; and the switch rail is a real
`3V3_MOD -> FB_3V3 -> 3V3` series chain with downstream bypass. Ratings close
within the stated passive-receive, standards-compliant USB, ESD-controlled
bench envelope.

`order_verdict: BLOCKED-SOURCING`

This commit is an unsealed fabrication candidate, not an order package. The
order remains blocked until the required two-authorized-pool sourcing record
exists and JLC accepts the ten plug-in SMA parts for this order. BOM echo and
human rotation/polarity preview are also outstanding. Physical module-fit,
module-current/temperature, impedance/TDR and VNA work are acceptance gates;
they are not evidence of a carrier design defect.

## Findings

| ID | severity | evidence | disposition |
|---|---|---|---|
| TPR-01 | P1 | **MEASURED:** the project contains no dated `manual_quotes.yaml`/shopping-list evidence establishing the exact hard-cell parts at `stock > 10` and five-board quantity in two independent authorized supplier pools. The only current quantitative sourcing record is `06_build/fab/stock_check.json`, which grades the JLC/LCSC pool alone (11/11 PASS; PE42482 C5121458 stock 1,284; ferrite C3716677 stock 5,838; SMA C504007 stock 22,674 at capture time). | Order blocker, not a design defect. Produce a fresh Q-2SOURCE record for PE42482A-X, KH-SMA-KE-Z and the retail RP2040-Zero, then repeat it on order day. This finding drives `BLOCKED-SOURCING`. |
| TPR-02 | P1 | **MEASURED:** all ten C504007 SMA jacks remain on the CPL as 50 through-hole joints. `assembly.yaml` says JLC's catalog class is `Plugin` but explicitly says `assemblyProcess` is null and actual line acceptance is not proven. The cited raw `verification/jlc_catalog_C504007.json` is not present in the current fab candidate. `06_build/fab/assembly_coverage.json` also reports the expected pre-release MANIFEST failure. `bom_echo_gate.txt` is only a worklist, and the actual JLC-resolved BOM has not been fed back. | Obtain written JLC plug-in/THT acceptance for this order before upload approval. If declined, change BOM/CPL/population posture and cut a new candidate; do not hand-edit the upload. Complete JLC BOM echo and preview checks before ordering. |
| TPR-03 | P1 | **MEASURED:** U_MCU is correctly absent from BOM and CPL and has no paste, but no physical module has been measured. Vendor STEP establishes carrier-facing parts up to 1.000 mm, while Waveshare publishes no coplanarity/protrusion tolerance. The LDO calculation is a bound on a constituent SOT-23-5, not a measured module thermal impedance. | Physical build/acceptance caveat, not a carrier defect. Before production fitting, measure module samples and board thickness, establish positive clearance with an insulating edge-support fixture, inspect all fillets, and measure representative-firmware total current and RT9013 case temperature. Supported operation remains `I_total <= 125 mA`, `TA <= 50 C`, WS2812 dark. |
| TPR-04 | P1 | **CITED/MEASURED:** the PE42482 datasheet characterizes switching and RF performance with VDD in its 2.3–5.5 V operating range; it does not specify unpowered port match, isolation or control truth. The board text permits +18 dBm and 0 VDC in unpowered conditions. +18 dBm is below the Figure 2 RF absolute-max/input curves and at/below the recommended terminated-port curve over 70 MHz–6 GHz, but unpowered RF *performance* is not established. The same evidence supports hot switching only above 100 MHz (20 dBm maximum). | Keep the present safety envelope only as a damage-avoidance ceiling; do not claim receive path, 50-ohm termination or isolation while USB is absent. Order/bring-up instructions should require RF removed before USB power-up/down as well as before cable mating. Establish powered S-parameters and off/unpowered behavior on hardware. |
| TPR-05 | P2 | **MEASURED:** the published control proof uses 3.366 V as the settled-high driver level and omits guaranteed RP2040 VOH/VOL, PE input leakage and tolerance corners. Recomputed at `VOH(min)=2.62 V`, `VOL(max)=0.5 V`, `R_S(max)=101 ohm`, `R_PD=10k +/-1%`, and opposing 5 uA input leakage gives 2.593 V high and 0.496 V low versus PE42482 VIH(min)=1.17 V and VIL(max)=0.6 V. The conservative transient is 2.717 V versus the 3.6 V digital absolute maximum; with 99 ohm, any post-resistor line impedance up to 113.8 ohm still remains below 3.6 V. | The implemented 100-ohm value is sound; correct the derivation in DETAIL_DESIGN/TSX to use guaranteed output levels and leakage. No copper/BOM change required. |
| TPR-06 | P2 | **MEASURED:** source prose is stale in two places. `nets.yaml` still calls the implemented 100-ohm source resistors “47 ohm”. The TSX says both `C_SW1/C_SW2` are within 3 mm of U_SW.8, but PCB pad-centre measurements are U_SW.8→C_SW1.1 = 2.827 mm and U_SW.8→C_SW2.1 = 6.460 mm. All three capacitors are nevertheless correctly downstream of the ferrite; the local 100 nF part is within the 3 mm vendor-layout-derived budget, and the switch draws only 200 uA maximum. | Documentation-only correction. Do not move parts for this finding; the local high-frequency bypass and filtered-rail topology are correct. |
| TPR-07 | P2 | **MEASURED:** `electrical_invariants.py --adr-coverage` reports `E-ADR OK: 0/0`, although ADR-0002 is plainly a power-boundary/protection decision and 25 implemented invariants cite ADR-0001/0002. The physical assertions themselves pass 25/25; the coverage denominator is vacuous because the ADR metadata does not classify either decision as protection/topology. | Process-coverage defect, not an electrical defect. Add the appropriate ADR classification/metadata in a future source revision so E-ADR grades the decision rather than zero subjects. |
| TPR-08 | P1 | **CITED/MEASURED:** the RP2040-Zero USB path has no fuse, TVS, reverse/OR-ing element or VBUS series element; USB VBUS is direct to RT9013 VIN and the unused 5 V castellation. The carrier correctly leaves that castellation open, so there is no second-source contention path. Under the locked vSafe5V envelope, 5.25 V remains 0.75 V below the RT9013 6 V input absolute maximum. | Accepted module-boundary limitation, not a carrier defect. Use only a standards-compliant USB-C source; never inject power into the 5 V pad or connect a second source; retain ESD-controlled bench handling. Any wider input/transient/reverse-power requirement needs a different module or added protection. |

## Direct topology and ratings audit

### Intent versus implemented netlist/BOM

**MEASURED:** `electrical_invariants.py` passes 25/25 assertions against the
exported netlist. Independent tracing confirms:

- `J_ANT1..7.1 -> U_SW RF1..RF7`; `J_ANT8.1` and `J_RX1.1` share
  `RX1_MAIN`; `RX1_MAIN -> R_T1 220 -> RX1_TAP_MID -> R_T2 220 -> RX1_TAP
  -> U_SW RF8`; `U_SW RFC -> J_RX2.1`.
- `U_MCU GP0..GP3 -> R_S1..R_S4 100 ohm -> U_SW V1..V4`, with four 10 kohm
  pull-downs on the switch side. LS, NC and exposed pad are on GND.
- `U_MCU.21 -> 3V3_MOD -> FB_3V3 -> 3V3 -> U_SW.8`; 4.7 uF, 1 uF and
  100 nF are all from downstream `3V3` to GND. `U_MCU.23` (5 V) is a declared
  no-connect.
- Firmware reverses the three address bits into PE42482 V1-as-MSB order and
  uses `0x08` for the V4 all-ports-terminated state. PIO writes GP0..GP3 in one
  instruction. The 128-sample blank is 4.267 us at 30 Msps, comfortably above
  the PE42482 1.4 us maximum 0.05 dB settling time.
- The fab BOM has the intended 11 rows/27 placed refs. BOM-source/value grading
  passes all rows. U_MCU is absent from BOM/CPL as intended; no hidden parallel
  power entry exists.

### RF power and resistor envelope

**MEASURED:** for +18 dBm available power from a 50-ohm source into the RX1
main line with a 50-ohm RX1 load and a 440+50-ohm tap branch:

- main-line loss = 0.4322 dB;
- tap = -20.2567 dB relative to the unloaded through voltage;
- input return loss = 26.2773 dB;
- branch current = 3.449 mA RMS and each 220-ohm resistor dissipates only
  2.617 mW, versus its 62.5 mW rating.

For direct switch ports, +18 dBm is below the PE42482 Figure 2 terminated-port
limit across the declared band and 2 dB below its 20 dBm hot-switch limit above
100 MHz. The 70–<100 MHz cold-switch restriction is therefore correct. As a
deliberately conservative aggregate check, seven simultaneous +18 dBm
terminated ports would absorb 0.442 W; at the cited 63 C/W that is a 27.8 C
rise and gives about 132.8 C junction at 105 C ambient, below the 150 C
absolute maximum. This is not a substitute for a vendor multiport guarantee;
the supported use remains passive receive-only, not coherent RF generators on
multiple ports.

The control-network DC load is tiny: a high control bit dissipates about
11 uW in its 100-ohm series resistor through the 10 kohm pull-down. The status
LED worst case is approximately 2.33 mA at 3.366 V/Vf=1.8 V; LED and 680-ohm
resistor power remain far below 25 mA/40 mW and 62.5 mW ratings respectively.
The GPIO-bank 50 mA total limit has wide margin.

### Rail, clamp and off-state review

There is no TVS/clamp chain on the carrier to mismatch against downstream
ratings. That absence is deliberate and bounded:

- USB power/protection is the purchased module boundary; carrier 5 V is open.
  The allowed 4.75–5.25 V source is below the RT9013 6 V input absolute max.
- Filtered-rail maximum is 3.366 V, leaving 2.134 V to the PE42482 5.5 V VDD
  absolute max. The 100-ohm networks keep control transients below the separate
  3.6 V digital-pin maximum.
- At the deliberately over-conservative 125 mA rail current and 100 milliohm
  delivery path, `3V3` remains 3.2215 V at the low setpoint, 921.5 mV above
  the PE42482 2.3 V operating minimum. In reality only the switch's <=200 uA
  crosses the ferrite.
- Worst declared LDO dissipation is 252 mW. Using the documented 250 C/W model
  at 50 C gives an estimated 113 C junction and 148 mW of the stated 400 mW
  budget remaining. This is arithmetic margin, not a physical module thermal
  measurement (TPR-03).
- There is no battery or alternate energy source. Unplugging the sole USB-C
  de-energizes the assembly; stored quiescent drain is not applicable. The
  local downstream capacitance tends to keep U_SW powered after the MCU rail
  begins falling, and the pull-downs force RF1 when control is undriven. No
  claim is made that the RF switch remains functional or matched without VDD
  (TPR-04).

## Order-day and hardware-acceptance worklist

These are blockers/caveats, not newly discovered design defects:

1. Produce current two-authorized-pool sourcing evidence and recheck all JLC
   allocation/MOQ data.
2. Get written JLC acceptance of C504007 plug-in/THT assembly for all ten jacks.
3. Upload and compare JLC's resolved BOM; confirm U_SW pin 1, LED cathode,
   every SMA identity and all rotations in the actual preview.
4. Select `JLC04161H-7628`, four layers, ENIG, advanced 0.25/0.15 mm vias and
   impedance control; retain solver/coupon/TDR evidence.
5. Measure representative RP2040-Zero samples and execute the insulating
   support/positive-gap/fillet-inspection procedure; then measure current and
   LDO case temperature under released firmware.
6. Measure powered and unpowered RF behavior, all path S-parameters, RX1 tap,
   isolation and phase at the declared frequencies; publish Touchstone data
   and correction tables before calibrated-AoA claims.

No unresolved P0 finding remains in this lens.
