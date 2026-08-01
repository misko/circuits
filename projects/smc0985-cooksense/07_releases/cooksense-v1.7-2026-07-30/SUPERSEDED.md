# SUPERSEDED — **DO NOT ORDER. 271 SOLDER JOINTS ARE OPEN VIAS UNDER PRINTED PASTE.**

## ⛔ DO NOT FABRICATE OR ASSEMBLE THIS RELEASE AS IT STANDS

**The copper is fine. The ORDER FORM is what is wrong**, and this release does
not tell you to fix it. That distinction matters: this is not a respin. The
remedy is a **single dropdown on the JLC order form**, and every gerber, drill,
BOM and CPL file in this archive stays valid when you select it.

Sealed 2026-07-30 as `design_verdict: PASS` / `SOURCING: BLOCKED-1`. That design
verdict was reached **without anyone measuring what the vias do to the solder
joints they sit in.** It was recorded as a P2 and dispositioned "recorded".
Re-measured 2026-07-31: it is a **P1**.

## What was measured, and by two methods that share no code

**From the SHIPPED GERBERS + drill file** (`08_reviews/2026-07-31_v1.7_via-in-pad_paste-window-lens.md`):

- **275** distinct vias sit inside a solderable land — **271 of them are assembly defects.**
- **254** have their 0.150 mm hole mouth **100 % under a printed `F_Paste` aperture.**
- **17** are 62–95 % covered.
- **4** are clear — and all four are 1.5 mm test points (`TP_5VKR`, `TP_3V3`,
  `TP_ESTOP`, `TP_USEL`) with nothing soldered to them.

**Independently from `pcbnew` geometry**, on a copy taken outside the repo:

- Same **275**, split **74 thermal/exposed-pad** and **201 signal-land**, all 0.150 mm drill.
- Barrel **volume** against the solder available on its own land, at a 0.120 mm
  stencil and 50 % paste metal fraction: **median 136 %, worst 314 %**, with
  **133 of 201 lands above 100 %.**

The two methods agree on the count and on the worst case. **By AREA the barrels
look benign — 1.9 % to 11.8 % of the land, median 5.1 %. By VOLUME they are not.**
Solder wicks by volume, so the area figure is the wrong measurement, and reading
it is how this shipped.

### The row that makes the order-form line mandatory rather than preferable

`U_EFUSE` (TPS259573DSGR) **pads 2 and 5**: 0.600 × 0.250 mm lands with a
0.250 mm annulus — **0.0000 mm of copper rail.** The annulus is the entire width
of the land. **No solder-mask dam of any width fits.** Barrel = **3.21 × the
whole joint.** The nets are `5V_PROTECTED` and `EF_OVLO` — the eFuse's own
protection paths.

## The vendor's own instruction

TI's package drawing for this exact part (DSG0008A, drawing 4218900/E), EXAMPLE
BOARD LAYOUT note 5, verbatim:

> *"It is recommended that vias under paste be filled, plugged or tented."*

TI's own land pattern places its two vias **inside the thermal pad** and puts
**none in the eight perimeter lands.** This board does neither thing.

## What to do instead

**Order v1.8** — which is required anyway for `C265111` (stock 0 / MOQ 21 /
canPresale −1285) — and on the order form set **Via Covering → Epoxy Filled &
Capped**. MEASURED 2026-07-31 from JLC's own order form: that option **is
selectable on a 4-layer order in the standard flow**, no quote needed. Two
caveats read from the same source: the 4-layer default is **"Plugged"**, not
filled-and-capped; and **expedited build is unavailable** with it.

**No price is published.** JLC's fee pages, the order form's client bundle and
the January-2026 extra-charge article all lack a POFV rate, setup fee or MOQ.
That is recorded as a **declared `catalog_absence`**, not estimated — the
verbatim question to put to JLC is in §7b of the lens file. Snippet-sourced
prices are refused (Q-SNIPPET).

## How this got past the v1.2 review, in one sentence

v1.2's P2-2 was withdrawn on the note *"Layout withdrew via-in-pad (SKILL.md
records 0.25/0.15 as proven orderable)"*. **Via SIZE being orderable and via
COVERING being ordered are two different questions on the same form**, and one
sentence answered both. The population then grew from 2 to 275 with nothing
re-asking.

`ORDER_README.md` in this archive has **zero** hits for `POFV`, `resin`, `epoxy`,
`via fill`, `filled via`, `plugged via` or `via covering`. `fab_tiers.yaml` sets
`via_in_pad: true` for this board's tier and **no code reads that field** — it
grants permission to place the via and creates no duty to buy the process.

## Scope

Sealed archives are never retro-edited. This file is the only sanctioned write
into a sealed release; every other artifact here is unchanged and remains a true
record of what was sealed on 2026-07-30. The board's DRC, netlist, parity and
sourcing evidence all stand — this supersede is about one order-form option and
the review that failed to ask for it.

**Fleet note:** `pluto-cal-switch` is the same shape and worse per via — 91
via-in-pad, 90 under or clipped by paste, `F_Mask` open on all 91, **75 at
0.300 mm drill / 0.600 mm OD (a 4× barrel)**, and **65 with a negative copper
rail**, ten of them on `U_MCU` carrying `XIN`, `XOUT`, `USB_DM_MCU`,
`QSPI_SCLK` and `VREG_VOUT`. It is pre-release, so there it is a routing
constraint rather than an order option.
