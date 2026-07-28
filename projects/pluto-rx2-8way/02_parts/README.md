# 02_parts — folder status + deviations register

**Status: D-SPEC SOURCING SPIKE output (2026-07-27/28), amended at the stage-3
design gate (2026-07-28).** Four dossiers, written before any schematic exists.
Nothing here is in a BOM yet, because there is no BOM yet. That is itself a
deviation from the contract's flow and it is registered below.

| MPN | role | LCSC | PDF present |
|---|---|---|---|
| `PE42482A-X` | the SP8T antenna selector (`U_SW`) | C5121458 | **yes** |
| `KH-SMA-KE-Z` | 10x SMA jack (8 antenna + RX1 out + RX2 out) | C504007 | **yes — fetched 2026-07-28** |
| `0402WGF2200TCE` | **220R — one of the two series arms of the RX1 pickoff** (`R_T1`, `R_T2`) | C25091 | **yes — fetched 2026-07-28** |
| `0402WGF4700TCE` | 470R single-arm pickoff — **REJECTED ALTERNATE**, not on the board | C25117 | no, by contract |

**THE PRIMARY CHANGED ON 2026-07-28.** The user confirmed BRIEF D3 with the
SPLIT-ARM variant, so the pickoff is **2 x 220 ohm in series** and the single
470 ohm part is the alternate that lost (ADR-0002). The 470 dossier is KEPT and
RE-LABELLED rather than deleted — see deviation 3.

## The standalone gap is CLOSED for two of the three parts that had one

Both missing datasheets were fetched and committed on 2026-07-28, and the
mechanism that had blocked them is worth recording: **the LCSC
`datasheet.lcsc.com/lcsc/<id>_<part>_<code>.pdf` URLs now serve an HTML landing
page**, to a browser User-Agent as well as to a plain fetch. The real document
is reachable from a CDN link embedded in that page's own markup
(`datasheet.lcsc.com/datasheet/pdf/<hash>.pdf`), which is what was used.

- **`KH-SMA-KE-Z`** — fetched independently and hashes to
  `05257621aa124d9a077a47230c4ffc0030b23477c0e5c5e694abffa5f8daee08`, **byte
  for byte the value this README recorded as the expected hash on 2026-07-27**
  from the sibling project's read-only copy. That is an independent
  confirmation, not a copy: the file committed here came off the vendor CDN
  today and agrees with a hash recorded before it was fetched.
- **`0402WGF2200TCE` / `0402WGF4700TCE`** — one document serves both: the
  UniOhm *Thick Film Chip Resistors — 1-CHIP SERIES* sheet, V.3 Feb.12,2019,
  9 pages, sha256 `11cd644d…`. It is committed once, with the part that is
  actually on the board. Every electrical fact in both dossiers is now CITED
  from that document (ordering-code decode section 3 p2, tempco section 4.8 p5,
  rated power / voltage / temperature section 5 p5) instead of from an LCSC
  parametric record.

## Deviations from `contracts.md`

1. **Four `part.yaml` exist for parts not yet on a board.** The contract
   forbids "a `part.yaml` for a part not on the board (stale after a swap)".
   These are pre-BOM by design: the D-SPEC gate requires the sourcing spike to
   VERIFY the spec-critical part before architecture, precisely so stage 2
   never DISCOVERS feasibility. **Before bring-up:** each must appear in the
   BOM or its directory must be deleted, and the swap noted in
   `01_docs/CHANGELOG.md`.

2. **`part.yaml` files were EDITED without a datasheet revision change.** The
   contract says "edit a `part.yaml` only when the datasheet REVISION
   changes". Two were edited on 2026-07-28: `0402WGF4700TCE` (re-labelled
   `status: rejected_alternate`, datasheet provenance resolved from OWED to a
   real hash, `asserts:` emptied) and this README. The reason is a DESIGN
   decision, not a document change, and it is registered here rather than
   done quietly.

3. **`0402WGF4700TCE` keeps its dossier despite being a rejected candidate.**
   The contract says a rejected candidate keeps its REASON and not its binary,
   and normally not its dossier either. This one was PRIMARY for a day, its
   numbers are cited in `01_docs/journal/02_parts.md`, and deleting it would
   leave those citations dangling and erase the record that the primary
   changed. It carries `status: rejected_alternate`, an empty `asserts:` (an
   assertion that can never reach a board ref should read UNREACHED, not PASS)
   and **no committed PDF** — the binary lives with the part that is on the
   board.

4. ~~**`footprint:` names do not exist yet** for `PE42482A-X` and
   `KH-SMA-KE-Z`.~~ **CLOSED 2026-07-28.** Both `.kicad_mod` are AUTHORED into
   `03_src/lib/pluto_rx2_8way.pretty/` from the vendor land drawings — pSemi
   Figure 23's RECOMMENDED LAND PATTERN inset (DOC-75785-4 p21) and the
   Kinghelm sheet-2/2 PCB inset (2021.08.10). Neither was copied; the sibling's
   `pluto_cal_switch:SMA_Vertical_5.08sq_D1.4` is declared in its `part.yaml`
   and emitted by nothing, so there was no source to copy even had it been
   allowed. Verified by an INDEPENDENT parser that re-derives every dimension
   from the emitted file text and compares it against the drawing numbers
   re-typed by hand (canon M1), plus a `pcbnew.FootprintLoad`: **48 geometry
   properties + 6 silk/courtyard clearances, all PASS.**
   Two facts the footprints now CARRY rather than leave to the board:
   the SMA's `>= D3.5` bottom/inner-plane antipad, encoded as a **0.80 mm local
   clearance on pad 1** (1.9 + 2 x 0.8 = 3.5) so it opens in every ground plane;
   and `zone_connect 2` (SOLID) on the four ground posts, because the posts ARE
   the launch return path and a thermal spoke is not one.
   **And the stock KiCad footprint would have been WRONG**, which is why this
   was authoring and not a lookup: `Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_
   EP2.65x2.65mm` is IPC-generated with 0.85 mm pads at r = 1.95 and a 2.65 mm
   EP, against the vendor's 0.60 mm pads at r = 1.90 and a 2.75 mm EP.
   `03_src/floorplan.yaml` now binds `libraries: [03_src/lib, /usr/share/kicad/
   footprints]` with the project library FIRST for exactly that reason.

5. **Two thirds of the board still has no dossier.** Stage 3 has fixed the
   architecture, so the remaining stage-2 work is now enumerable rather than
   open-ended: **`U_LDO`** (3.3 V linear, and it carries THREE derived hard
   constraints — dropout ≤ 1.35 V at 0.15 A, `V_IN` abs max ≥ 10 V so the TVS
   clamp sits inside its rating, and θ_JA ≤ 195 °C/W which DISQUALIFIES a bare
   SOT-23-5 — see `01_docs/DETAIL_DESIGN.md` §5), **`U_MCU`** (RP2040),
   **`U_FLASH`** (QSPI), **`Y_XTAL`** (12 MHz), **`J_USB`** (USB-C 2.0),
   **`D_TVS`** (5.0 V standoff), **`F_IN`** (500 mA PPTC), **`U_ESD`** (USB
   data array), **`FB_IN`** (ferrite). Until `U_LDO` lands, E-TOPO reports an
   EARNED N-A (`03_src/rules/power_tree.yaml` explains why, and the gate
   checks that claim against this folder rather than against the power tree's
   own say-so).

## OWED measurements — named, not buried

| owed | why it matters |
|---|---|
| **port-to-port isolation across ten SMA barrels on one laminate** | it bounds the AoA leakage budget from BELOW, independently of the switch. A −21.5 dB switch behind a −18 dB connector field is a −18 dB board. The vendor sheet does not touch it. ADR-0005's all-ports-terminated dark state exists to measure it |
| SMA launch **dissipative** loss | the vendor publishes VSWR only, so `DETAIL_DESIGN.md` §2's 0.10 dB per launch is a mismatch-loss LOWER BOUND |
| `C_p` for the 0402 arms | CITED for the 0402 wrap-around class (Vishay TN 60107 Table 1 p1), **ESTIMATED 0.04 ± 0.02 pF for this thick-film part**. The 6 GHz tap tilt scales linearly with it — which is the whole reason the arm is split |
| RP2040 pad output impedance | ESTIMATED 25 ± 10 Ω at 12 mA. The 47 Ω series value holds the switch's absolute-maximum bound across the whole bar, which is what makes the estimate tolerable |

## Rejected candidates — no PDF committed, reason recorded

Per the contract, rejected candidates get the reason, not the binary. The full
reasoning is in the D-SPEC spike report; the one-line verdicts:

| candidate | LCSC | verdict |
|---|---|---|
| `BGS12WN6` (7x SPDT tree) | C1854968 / C27749420 | **STOCK 0 on every catalogue entry**, and the tree's worst-case isolation is one switch's, not three |
| `BGS12P2L6E6327` (7x SPDT tree) | C3312945 | in stock (1225) but no published RF row at 70 MHz or 6 GHz; 3.4 V VDD max |
| `PE42462A-X` | C22419301 | **SP6T, not SP8T** — datasheet cover, `UltraCMOS SP6T RF Switch, 10 MHz-8 GHz` |
| `HMC321ALP4E` | C1526237 | **stock 0** ($34.90/1, would be self-supplied); and GaAs IL is 1.7 typ / **1.8 max** even in the DC-2.0 GHz row vs PE42482's 1.1 max at 70 MHz. **NOT a negative-rail part** — an earlier note in this project's own spike brief said so and was WRONG: the datasheet title reads `GaAs MMIC SP8T NON-REFLECTIVE POSITIVE CONTROL SWITCH, DC*-8 GHz`, single +5 V bias, 0/+5 V TTL control, integrated 3:8 decoder. Rejected on stock and loss, never on supply. Also needs 9 DC blocking caps (RFC + 8 RF ports) whose value sets the low corner |
| `HMC322ALP4E` | C1558622 | stock 0 both codes |
| `SKY13418-485LF` | C150871 | 100 MHz-3.8 GHz — fails both band ends |
| `SKY13322-375LF` | C151465 | **SP4T**, not SP8T |
| `PE42582A-X` | C500479 | qualifies on spec; stock 7 at $14.91 — kept as an alternate, not primary |
| `ADRF5040BCPZ` | C579319 | SP4T; stock 7+20 |
| `MASW-008322` | C3304131 | SPDT; stock 3 |
| `0402WGF4700TCE` | C25117 | **470R single-arm pickoff — the primary until 2026-07-28.** Its arithmetic is correct; it loses because a single arm carries the full 0402 shunt parasitic, so its 6 GHz tap tilt is +1.69 dB with a **2.73 dB-wide uncertainty band** against +0.43 dB / 0.83 dB for the split arm. Dossier KEPT (deviation 3) |

## Stock, MEASURED 2026-07-28 — and the pool trap

Against the **JLCPCB assembly parts library** (`jlc_stock_check.py`), which is
the pool a PCBA order allocates from:

| LCSC | MPN | library | stock |
|---|---|---|---|
| C25091 | 0402WGF2200TCE | base | **995,162** |
| C25117 | 0402WGF4700TCE | base | 1,871,945 |
| C5121458 | PE42482A-X | extended | **1,498** |
| C504007 | KH-SMA-KE-Z | extended | **18,585** (19,136 on 2026-07-27 — −551 in a day) |

**The trap, worth the line it costs:** the LCSC RETAIL product page for
**C25091 reports stock 0** on the same day it shows 995,162 in the assembly
library. Two different pools. Measuring the retail page is measuring the state
of a catalog record, not the state of the part (canon M-QUOTE) — and this is
the code the whole confirmed pickoff design depends on, so a casual retail
check would have read as a blocker that is not one. It WOULD be a blocker if
the part ever had to be hand-supplied.

(These figures are OBSERVATIONS with a date, recorded here because the folder
status is what they describe. The volatile numbers a build consumes live in
`06_build/cache/`, never in a `part.yaml`.)
