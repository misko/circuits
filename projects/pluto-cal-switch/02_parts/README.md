# 02_parts — status and DEVIATIONS REGISTER

State as of **2026-07-28**, during pipeline stage 4 (schematic authoring).

> **STAGE-4 UPDATE 2026-07-28 — TWO DEVIATIONS CLOSED, ONE PART ADDED.**
> Authoring the schematic is the moment the parts stage's IOUs come due, and
> two of the three did. `W25Q16JVSSIQ` and `USBLC6-2SC6` carried `pins: {}` /
> `verified: OWED`; both are now **figure-verified with their PDFs vendored**
> (see the table below). The third — the micro-USB's INFERRED signal names —
> is **still open by design**: its resolution is a fresh-context pin review
> against JLC's own footprint, which is a stage-7 gate, not something the
> schematic can settle. And `ABM8-272-T3` is **added**, closing ADR-0012's
> deferred 12 MHz crystal by resolution **(a)**, not (b).

State as of **2026-07-27**, end of pipeline stages 1-3 (design docs, parts,
rules), for everything not touched above.

> **RE-SPEC 2026-07-27 (A8 + A9, ADR-0015 / ADR-0016).** Two part changes:
> `SMP-MSLD-PCE-5T` is **DELETED** — the board connects with SMA cables, so
> there is no board-side SMP and no $101 adapter order; and the YAT count rises
> from 5 to 9 per board to carry a ≥40 dB minimum. `KH-SMA-KE-Z` goes 2 → 5.
> **The binding stock ceiling moved with it: YAT-2A+, not YAT-10A+.**

## Complete — pin map read from the datasheet FIGURE, PDF vendored

| MPN | LCSC | qty | figure cited |
|---|---|---|---|
| `BGS12WN6` | C534203 | 2 | Figure 2 (pin configuration, top view), PDF p11 — rendered and read visually, cross-checked against Table 11 |
| `YAT-10A+` | C5839318 | **4** | PAD DESCRIPTION table + TOP/BOTTOM VIEW pad-numbering figure, REV B p.2 |
| `YAT-2A+` | C5205333 | **5** | same, REV B p.2 |
| `0402WGF499JTCE` | C25120 | 3 | 2-terminal passive — exempt from the figure rule |
| `KH-SMA-KE-Z` | C504007 | **5** | drawing sheet 2/2 `PCB layout`, 5-Ø1.4 @ 5.08 mm. Gender re-verified 2026-07-27 from the p.1 产品名称 (product-name) field + the sheet-2 external-thread outline, and the RP-SMA residual closed on LCSC C504007 — see ADR-0015 |
| `RP2040` | C2040 | 1 | Tables 615-621, §5.5.2.2 Pin List, PDF pp.612-614 — all 56 pins + pad accounted for, no gaps, no duplicates |
| `ME6211C33M5G-N` | C82942 | 1 | Pin Assignment table, ME6211CXXG SOT-23-5 column, V14 p.4 |
| `W25Q16JVSSIQ` | C82317 | 1 | **NEW 2026-07-28** — Figure 1a `Pin Assignments, 8-pin SOIC150-mil/208-mil (Package Code SN, SS)`, Rev H printed p.5, cross-checked against the sec.3.3 Pin Description table on the same page |
| `USBLC6-2SC6` | C7519 | 1 | **NEW 2026-07-28** — Figure 1 `Functional diagram (top view)`, Doc ID 11265 Rev 5 p.1, cross-checked against Figure 7 p.5 |
| `ABM8-272-T3` | C20625731 | 1 | **NEW 2026-07-28** — TOP VIEW pad figure, Abracon drawing 456603 Rev B printed p.(4), rendered at 130 dpi and read visually |

## Deviations — every departure from `contracts.md`, with what must happen

The contract requires a vendored PDF and a figure-verified pin map per used
part. Three entries depart from that. **Each is declared here rather than
papered over, and each carries an empty or partial `pins:` block so it FAILS
S-VER by construction if anyone tries to build from it.**

**One deviation CLOSED by deletion, 2026-07-27:** `SMP-MSLD-PCE-5T` carried an
un-vendored PDF with sheet 1 of 3 missing (`amphenolrf.com` returns HTTP 403 to
automated fetch), and the missing number was the mating-face position relative
to the board edge — the number that set the board-to-Pluto separation. **A8
deleted the part, so the deviation closed without ever being resolved.** Worth
noting which way that went: the open item was retired by a design change, not
by obtaining the drawing, and if SMP ever returns the deviation returns with it.

| MPN | deviation | why | before bring-up |
|---|---|---|---|
| ~~`W25Q16JVSSIQ`~~ | ~~`pins:` EMPTY, `verified: OWED`, no PDF~~ | — | **CLOSED 2026-07-28.** PDF fetched (Rev H, sha256 `81af3f69…`) and vendored; `pins:`, `limits:` and `layout:` filled from Figure 1a + the sec.3.3 table on printed p.5. Stock re-check at order time still stands |
| ~~`USBLC6-2SC6`~~ | ~~`pins:` EMPTY, `verified: OWED`, no PDF~~ | — | **CLOSED 2026-07-28.** A valid ST PDF (Doc ID 11265 Rev 5, sha256 `8ba7ab4e…`) was located and vendored; `pins:` filled from Figure 1. **Provenance stated rather than implied:** st.com refused an automated re-fetch (HTTP/2 `INTERNAL_ERROR`; the CCC mirror times out), so the copy used is the byte-identical one already in this repo at `projects/usb-hub-3s-v3/02_parts/USBLC6-2SC6/`, whose sha256 matches |
| `U254-051T-4BH83-S1S` | **`pins:` populated but the SIGNAL NAMES ARE NOT ON THE VENDOR DRAWING** — they come from the USB Micro-B standard. Mechanical geometry IS fully read | XKB labels only "PIN 1" and "PIN 5" and gives current ratings by pin group; that is consistent with, not proof of, the standard map | **STILL OPEN — and the schematic cannot close it.** The resolution is a **fresh-context pin review against JLC's own fetched footprint**, i.e. a stage-7 `jlc_twin` PAD-MISMATCH check on a board that does not exist yet. The schematic authored on 2026-07-28 binds `J_USB` to this map, so a later correction is a netlist change, not a rework. If the footprint numbers pin 1 at the opposite end, VBUS and GND swap and the board dies on first plug-in; this fleet has already shipped one reversed connector |

### What the two closures actually changed

Both were closed by READING, not by deciding — but the USBLC6 read produced a
fact the schematic would otherwise have got wrong, and it is worth naming:
**pins 1/6 carry the SAME label `I/O1` and pins 3/4 the same label `I/O2`.**
Each pair is ONE internal node. Figure 7's "route the data line in one pin and
out the other" is a **copper** instruction (no stub in the clamp path), not two
electrical nets. Splitting `USB_DP` into `USB_DP_CON` → `USB_DP` across pins 1
and 6 would have drawn a part that does not exist, and would have made an ESD
shunt look like a series element to every downstream reader — including a human
reviewing the schematic PDF.

## Not yet created — parts whose refdes set the schematic decides

Generic passives are added when their reference designators exist. Values are
already DERIVED in `01_docs/DETAIL_DESIGN.md` §9 and must not be re-invented:

| function | value | derived in |
|---|---|---|
| RF DC block, `RX_ANT1/2` | **1 nF 0402 C0G/NP0 50 V** — a value choice, not a generic decoupler. RL 32.9 dB @70 MHz / 16.5 dB @6 GHz; 0201 is the documented upgrade (20.6 dB) | DETAIL_DESIGN §8, ADR-0005 |
| switch CTRL series | 1 kΩ ×2 | DETAIL_DESIGN §9 |
| switch CTRL shunt | 1 nF 0402 X7R ×2 | DETAIL_DESIGN §9 |
| switch CTRL pull-down | 10 kΩ ×2 | DETAIL_DESIGN §9, ADR-0001 |
| header divider | 2.2 kΩ / 3.3 kΩ | DETAIL_DESIGN §9.1, ADR-0008 |
| header STATE_OUT series | 1 kΩ | ADR-0008 |
| LED series | 680 Ω ×2 | DETAIL_DESIGN §9 |
| USB series termination | 27 Ω ×2 | RP2040 vendor guide §2.4.1 |
| VBUS bulk | 4.7 µF + 100 nF; **total board bulk ≤ 10 µF, a USB 2.0 §7.2.4.1 HARD LIMIT** | ADR-0009 |
| LDO in/out | 1 µF each — a datasheet SPEC CONDITION, not a suggestion | ME6211 Fig 2 p.2 |
| RP2040 decoupling | 10 × 100 nF + 2 × 1 µF | RP2040 §2.9.1 p.151 |

**The 1 nF DC block, the 2.2 k/3.3 k divider and the 10 k pull-downs are
VALUE-CRITICAL and get their own `02_parts/` entries** when the schematic
lands — they are not interchangeable decouplers.

## Open sourcing items

- ~~**12 MHz crystal — DELIBERATELY NOT SELECTED YET.**~~ **CLOSED 2026-07-28
  by SELECTING `ABM8-272-T3` (Abracon, JLC `C20625731`, Extended, 17 567 in
  stock) — ADR-0012 resolution (a), not (b).** The JLC **Basic** part
  X322512MSB4SI (C9002) is **CL = 20 pF, ESR = 80 Ω** against Raspberry Pi's
  reference of **CL = 10 pF, ESR ≤ 50 Ω** — 2× the load and 1.6× the ESR
  ceiling, with the 1 kΩ damping resistor sized against the 50 Ω part. **A
  crystal that does not start means USB never enumerates — and on this board
  that is not a degraded mode, it is a brick, because the ONLY programming path
  is the USB mass-storage bootloader.** ABM8-272-T3 lands exactly on both
  limits (CL = 10 pF typ, R1 = **50 Ω max**) and its own datasheet, printed
  p.(2), states *"Crystal approved for use with Raspberry Pi's RP2040 and
  RP235x range of microcontroller products"* — a vendor statement about this
  part number, not an inference. So the schematic carries the reference
  circuit **unmodified**: 2 × 15 pF load caps (derived, `2 × (10 − 3) = 14 pF →
  E24 15 pF`) and the 1 kΩ series damping resistor, with **no** start-up test
  at temperature extremes added to the release gate. Cost of the choice, stated:
  Extended-library status (a one-time feeder fee) and **zero ESR margin** —
  50 Ω max against a ≤ 50 Ω limit. What buys that back is that 50 Ω is the
  value the vendor's own 1 kΩ damping resistor was sized against; an 80 Ω part
  has no such backing. C9002 remains the documented fallback and takes
  resolution (b) **with** its 33 pF caps and its start-up test.
- ~~**SMA→SMP adapters (`134-1019-451`, Cinch)**, 3 × $33.83 = **$101**, 21 in
  stock~~ — **CANCELLED 2026-07-27 by A8/ADR-0015.** The board connects with
  SMA cables. Nothing on the critical path replaces them: **three SMA
  male–male cables, user-supplied, commodity**, of which **two must be
  IDENTICAL** (the RX pair — P6's "same path length on each run" now lands on
  the cables, not on a PCB trace match).
- ~~**A stock query on the mid-value YAT parts is OWED before the schematic.**~~
  **QUERIED 2026-07-28 — the answer is MEASURED, and the collapse is NOT taken
  at stage 4.** JLC `selectSmtComponentList`, exact model match, read
  2026-07-28: **YAT-15A+ `C7169783` 79 · YAT-12A+ `C5839322` 4 · YAT-5A+
  `C6338032` 10 · YAT-3A+ `C5205332` 152** (against the committed YAT-10A+
  `C5839318` **150** and YAT-2A+ `C5205333` **103**). So **YAT-15A+ is the only
  mid value with usable stock**, and YAT-12A+/5A+ are effectively unbuyable.
  A `YAT-15A+ + YAT-10A+` pre-split pad would be 25 dB nominal against the
  present 25.78 dB, would drop the per-board YAT-2A+ count from 5 to 2 (lifting
  the binding ceiling from 20 boards to ~51), and would delete ~12 mm of
  interconnect. **It is not taken here, and the reason is the same one that
  makes ADR-0016 claimable at all: the guarantee is built on datasheet MIN
  columns, and YAT-15A+'s min column has not been read.** Substituting it is a
  re-derivation of `DETAIL_DESIGN` §3.4 and a change to ADR-0016's arithmetic —
  a stage-1/3 backtrack, not a schematic edit. **Escalated to the user as a
  costed option, not silently taken and not silently dropped.**

## Stock, checked 2026-07-27 — informational, NEVER a committed truth

Per the three-tier model in `contracts.md`, stock belongs in `06_build/cache/`
with a TTL. Reproduced here only as the state at design time:

`C534203` 2448 · `C5839318` 150 (**⇒ 37 boards** at 4/board) ·
`C5205333` 103 (**⇒ 20 boards** at 5/board — **THE BINDING CEILING since A9**;
it was YAT-10A+ at 50 boards under the 30 dB build) ·
`C25120` 1.78 M (Basic) · `C504007` 19 252 (⇒ 3850 boards at 5/board) ·
`C2040` 57 220 · `C82317` 8 927 · `C82942` ~large ·
`C319160` 31 612 · `C7519` ~large. `C6297051` (SMP) no longer used.

**Everything except `C25120` is JLC Extended.**
