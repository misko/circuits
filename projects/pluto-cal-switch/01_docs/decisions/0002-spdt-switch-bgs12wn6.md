---
id: 0002
date: 2026-07-27
status: accepted
tags: [topology]
---
# 0002 — BGS12WN6 as the SPDT, with BGS12P2L6 as a same-land dual source

## Context

Two SPDTs are needed, one per RX channel, spanning **70 MHz – 6 GHz** at 50 Ω,
driven from one control bit, with the truth table that makes ON = loopback fall
out with no inverter (ADR-0001).

A full sweep of JLCPCB's 1138-entry RF-switch category found **nine** stocked
SPDTs clearing both band endpoints with >100 pieces. Almost everything cheap
and common dies on the 6 GHz gate: PE4259-63 and PE42421 stop at 3 GHz,
MASWSS0115 at 3 GHz, MASWSS0179 at 2 GHz, SKY13323/SKY13405 at 3 GHz,
SKY13418 at 3.8 GHz. ADRF5021/5024/5025 — the 9 kHz–30 GHz answer — are
absent or stock 0 at JLC.

The decision that actually needed making was between two Infineon siblings,
and the first pass got it wrong.

## Options

- **BGS12P2L6** (C3312945, 1245 in stock, $0.21 @5). TSLP-6-4. The sourcing
  spike's pick. **Its RF-characteristics table runs 617–5925 MHz only.** The
  "0.05–6 GHz" figure appears ONLY in Table 2 *Absolute Maximum Ratings*,
  whose own warning box reads *"Functionality of the device might not be given
  under these conditions"*, and Table 3 *Operation Ranges* has **no frequency
  row at all**. So **both endpoints of this board's stated band — 70–617 MHz
  and 5925–6000 MHz — are uncharacterized.** The spike flagged the first; the
  second was found only on the primary-datasheet re-read.
  VDD operating max **3.4 V**.
- **BGS12WN6** (C534203, 2448 in stock, $0.33 @5). **PG-TSNP-6-10**, not
  TSLP-6-4 — the package NAME differs even though the land pattern does not.
  Rev 2.9 (2026-04-24) characterizes **50 MHz – 9 GHz**: a 50–698 MHz row
  (IL 0.15 typ / 0.25 max, RL 28 min / 33 typ, isolation 43 min / 53 typ) and
  a 5925–7125 MHz row. Interior gaps at 960–1200, 2690–3300, 4200–4400 and
  5000–5150 MHz. VDD operating max **3.6 V**, abs max 4.2 V. CHOSEN.
  *(LCSC still serves the 2020 Rev 2.2 PDF, which says 0.05–6 GHz and TSLP —
  that stale document is where the package/band confusion originates.)*
- **SKY13351-378LF** (C129189, 3188 in stock). The only other part with
  published numbers at 70 MHz, guaranteed 0.02–6.0 GHz. REJECTED on three
  counts: isolation 22 dB min / 24 typ over 0.02–3.0 GHz; **two complementary
  control lines**, costing an inverter and a second routed net through the RF
  section; and all three RF ports marked "Must be DC blocked" with its own
  eval note demanding 10 nF below 50 MHz — six extra capacitors that must span
  85.7:1, which no single value does.
- **SKY13330-397LF** (C2654715, 10993 in stock, best package). REJECTED:
  stated range starts at 0.1 GHz so 70 MHz is out of spec; isolation collapses
  to 18 dB min over 5–6 GHz; V_CTL_HIGH max 2.70 V needs a level shifter; and
  it needs a second (ENABLE) control line.
- **HMC1118LP3DETR** (C461515, 2657 in stock), non-reflective, 9 kHz–13 GHz,
  >48 dB isolation. **The only part found that brackets 70 MHz–6 GHz with
  >25 dB isolation guaranteed at BOTH ends.** REJECTED on cost and supply:
  $7.70 @1 against $0.33 — ~$15/board for two — and it nominally wants a −2.5 V
  rail. Recorded because it is the honest answer if isolation ever becomes the
  binding requirement. Its figures come from the ADI product page, not a
  page-cited datasheet read (analog.com was unreachable), so it is an
  **UNVERIFIED** alternate.
- **HX13351-378-SQ / SKY13351-378LF-HX** (~$0.09, ~3000 each). REJECTED: no
  manufacturer datasheet exists for either, and their own LCSC parametric
  fields **disagree by 45 dB on isolation** for what is supposedly the same
  die. A part whose two listings contradict each other on the spec that binds
  the board is not a sourcing option.

## Decision

**`BGS12WN6` (Infineon, PG-TSNP-6-10, LCSC C534203) ×2, with `BGS12P2L6`
(C3312945) named as the alternate on the SAME land pattern.**

Decided on band coverage: WN6 is the only one of the two with any published
guarantee at either endpoint of 70 MHz – 6 GHz. Reinforced by supply headroom:
a 3.3 V rail from a ±2 % LDO tops out at 3.366 V, leaving BGS12P2L6 just
**34 mV** below its 3.4 V operating maximum against WN6's 234 mV.

**One land pattern qualifies both**, verified dimension by dimension against
both package drawings: six 0.25 × 0.25 mm square pads, 0.40 mm pitch in BOTH
axes, NSMD with a single mask opening spanning all six, 100 µm stencil (WN6
Figure 5, PDF p13; P2L6 Figure 4, PDF p10 — the same drawing). Body 0.7 × 1.1
± 0.05 mm on both. Pin map and truth table identical (WN6 Figure 2 / Table 11
/ Table 12, PDF p11; P2L6 Figure 2 / Table 10 / Table 11, PDF p9).

## Consequences

- **Sole-source becomes dual-source at zero design cost.** The spike's claim
  that "a stockout is a respin, not a swap" is refuted: 2448 + 1245 pieces
  qualify against one footprint.
- **What WN6 costs, recorded rather than glossed.** 3 dB worse guaranteed
  minimum isolation at 5150–5925 MHz (21 vs 24 dB) and 5 dB worse
  throw-to-throw (25 vs 30). Guaranteed return loss falls to **9.5 dB
  (VSWR 2.0)** over 5925–7125 MHz. Power handling drops from 37 dBm to
  **26 dBm CW**, which sets the board's TX abuse ceiling (DETAIL_DESIGN §4.3).
  Against that it gains a 10× faster switch time (220 ns vs 2.5 µs), which a
  bench cal switch does not need.
- **WN6's IL and RL are PROBER-STATION numbers.** Table 4 footnote 1: *"Measured
  on prober station to exclude board effects, without any matching
  components."* BGS12P2L6's are application-board. **The two are not directly
  comparable and WN6's are not a board-level budget** — DETAIL_DESIGN §3.2
  handles this explicitly by adding a stated board allowance. No board-level
  IL/RL exists for WN6 anywhere; Infineon does not publish one.
- **>25 dB isolation is NOT met on the guaranteed minimum above ~5 GHz** by
  either part (21 / 24 dB), nor by any cheap stocked SPDT. Typ meets it. This
  must be stated in the release, not assumed away.
- **First-article measurement at 70 / 100 / 200 / 400 MHz is MANDATORY, not
  optional** — because on BGS12P2L6 that decade is unguaranteed, and the two
  parts share a footprint so the bench can settle it.
- **A DC path exists between all switched paths** on both parts (Table 1/2
  footnote 1, verbatim on both: *"There is also a DC connection between
  switched paths. The DC voltage at RF ports V_RFDC has to be 0 V."*).
  Handled by ADR-0005.
- **Both are REFLECTIVE** — *"The isolated port is a reflective short"*,
  verbatim in both Descriptions. The consequences are worked in ADR-0004
  (the splitter sees an open in antenna mode without arm pads) and accepted
  for the antenna port (termination changes the phase of residual leakage, not
  its magnitude; the residual RIPPLES with frequency as a cable-length comb
  rather than sitting flat).
- **Commits to a 0.40 mm-pitch leadless part with terminals entirely under the
  body**: no hand rework, no visual solder inspection, X-ray only. **The CPL
  rotation MUST be proven against the JLC library footprint before ordering** —
  this fleet has already shipped a board killed by a reversed CPL. Note the two
  datasheets draw their package OUTLINES 180° apart on the page and use
  DIFFERENT pin-1 glyphs (P2L6 a filled triangle, WN6 a lasered ✖), so the
  orientation authority is **Figure 2**, which is byte-identical in both — not
  the outline figure, and not the glyph shape.
- Both are JLC **Extended**; neither is a Basic freebie.
