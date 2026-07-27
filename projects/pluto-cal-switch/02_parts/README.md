# 02_parts — status and DEVIATIONS REGISTER

State as of **2026-07-27**, end of pipeline stages 1-3 (design docs, parts,
rules). **No schematic exists yet**, so nothing downstream has consumed any of
these entries.

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
| `W25Q16JVSSIQ` | **`pins:` EMPTY, `verified: OWED`**, no PDF | datasheet not fetched this session | fetch, extract the pin map from the figure, fill `pins:` / `limits:` / `layout:`. Re-check stock: 4 of 6 16-Mbit SKUs read out of stock 2026-07-27 |
| `USBLC6-2SC6` | **`pins:` EMPTY, `verified: OWED`**, no PDF | the cached file is an HTML error page saved with a `.pdf` extension — not a valid PDF | re-fetch from st.com; its §2.3 layout demand is already transcribed in `gotchas:` and is the strongest USB-side rule on the board |
| `U254-051T-4BH83-S1S` | **`pins:` populated but the SIGNAL NAMES ARE NOT ON THE VENDOR DRAWING** — they come from the USB Micro-B standard. Mechanical geometry IS fully read | XKB labels only "PIN 1" and "PIN 5" and gives current ratings by pin group; that is consistent with, not proof of, the standard map | **fresh-context pin review against JLC's own fetched footprint.** If the footprint numbers pin 1 at the opposite end, VBUS and GND swap and the board dies on first plug-in. This is the `jlc_twin` PAD-MISMATCH class and this fleet has already shipped one reversed connector |

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

- **12 MHz crystal — DELIBERATELY NOT SELECTED YET.** The JLC **Basic** part
  X322512MSB4SI (C9002) is **CL = 20 pF, ESR = 80 Ω** against Raspberry Pi's
  reference of **CL = 10 pF, ESR ≤ 50 Ω** — 2× the load and 1.6× the ESR
  ceiling, with the 1 kΩ damping resistor sized against the 50 Ω part. **A
  crystal that does not start means USB never enumerates.** Two fully specified
  resolutions in ADR-0012; if C9002 is taken, the load caps become **33 pF, NOT
  the reference's 15 pF**, and a start-up test at both temperature extremes
  goes into the release gate.
- ~~**SMA→SMP adapters (`134-1019-451`, Cinch)**, 3 × $33.83 = **$101**, 21 in
  stock~~ — **CANCELLED 2026-07-27 by A8/ADR-0015.** The board connects with
  SMA cables. Nothing on the critical path replaces them: **three SMA
  male–male cables, user-supplied, commodity**, of which **two must be
  IDENTICAL** (the RX pair — P6's "same path length on each run" now lands on
  the cables, not on a PCB trace match).
- **A stock query on the mid-value YAT parts is OWED before the schematic.**
  `PAD_A1` is a five-chip cascade only because YAT-10A+ and YAT-2A+ are the two
  values with verified stock. A single **YAT-15A+ / YAT-12A+** (or YAT-5A+ /
  YAT-3A+) would collapse it to two chips, save ~$7/board and ~12 mm of
  interconnect, and lift the 20-board stock ceiling. **The min column of any
  substitute must be read from its own datasheet** — ADR-0016's guarantee is
  built on min columns, and an unverified one cannot carry it.

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
