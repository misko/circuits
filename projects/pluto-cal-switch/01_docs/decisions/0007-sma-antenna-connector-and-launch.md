---
id: 0007
date: 2026-07-27
status: accepted
tags: [mechanical]
---
# 0007 — KH-SMA-KE-Z for the two antenna ports, and the launch rules are OURS

## Context

Two ports remain true SMA after ADR-0006: `RX_ANT1` and `RX_ANT2`, the
user-facing antenna inputs. They need 50 Ω to 6 GHz, deep stock, and a land
pattern the board can actually launch a 50 Ω line into.

The sourcing spike picked `BWSMA-KE23` (C5250061). Its adversarial pass
returned **REFUTED** — not because the part cannot work, but because a
strictly dominating in-stock part exists that the survey missed, and because
three of the layout rules the pick would have frozen into the footprint are
**wrong-signed**.

## Options

- **Edge/end-launch SMA** — the RF-best class. **NOT SOURCEABLE.** Every
  edge-launch SKU in the LCSC/JLC library reads ZERO stock (C5356059,
  C5578719, C5602809 and the three JLCPCB house parts C9900125811 /
  C9900274326 / C9900183515, all verified 0 on 2026-07-27; two web snippets
  claiming otherwise are stale). The only in-stock end-launch is Amphenol
  132289 (C3172723) at **$11.44 each**, and it is a BULKHEAD variant needing a
  machined Ø6.60 mm panel. Also wrong for this board even if stocked: its
  reference plane sits AT the board outline, putting JLC's ±0.2 mm routing
  tolerance directly into the arm-to-arm budget.
- **`BWSMA-KE23` / C5250061** (BAT WIRELESS), the spike's pick. REJECTED —
  dominated on every count it was chosen for. **No VSWR or return-loss spec
  exists anywhere in its 10 pages.** Its single high-frequency number, "0.15 dB
  at 6 GHz", is `0.06·√6 = 0.147` — the industry-standard SMA insertion-loss
  FORMULA evaluated at 6 GHz, i.e. transcribed boilerplate, not a measurement.
  Two further tells: p.3 describes an "angled structure" and "an internal pin
  interface" on what is a straight female jack, and p.6 note 1 reads "The wire
  jacket shall be free from cuts or damage" on a connector with no cable — the
  same copy-paste failure on the one sheet the pick declared trustworthy. It
  is also 28.6 mm long, standing on four 0.9 mm posts, i.e. the worst lever arm
  in the family.
- **`KH-SMA-KE-Z` / C504007** (Shenzhen Kinghelm). CHOSEN.
- **`KH-SMA-K513-G` / C411575**, right-angle, 28 135 in stock, same land
  pattern. Kept as the MECHANICAL alternate if edge-facing ports are wanted.
  Not primary: its internal 90° bend is uncharacterised, and it is
  orientation-dependent so CPL rotation becomes load-bearing again.

## Decision

**`KH-SMA-KE-Z` (LCSC C504007), vertical through-hole square-flange SMA jack,
×2.** VSWR ≤1.35 / DC–6 GHz / 50 Ω / ≥1500 V / ≥500 cycles, all stated on its
own datasheet p.1. Explicit `5-Ø1.4` on `5.08 × 5.08 mm` PCB layout, sheet 2/2.
**19 252 in stock at $0.4708 @1** — 6.4× the stock, 28 % cheaper and 53 %
shorter (13.5 mm vs 28.6 mm) than the rejected pick.

**Depth reserve: `BWSMA-KE-Z001` / C496549**, identical pattern verified from
its own p.6 drawing, **113 553 in stock at $0.3983**.

The land pattern is the second-source anchor, not the MPN: four in-stock parts
share the industry-standard 5.08 mm square (Amphenol 901-144 / Würth
60312002114503 pattern that KiCad already ships as
`Connector_Coaxial:SMA_Wurth_60312002114503_Vertical`).

**Footprint: centre PTH Ø1.4 mm with a Ø2.0–2.2 mm annular pad at (0,0); four
ground PTH Ø1.4 mm with Ø2.0 mm pads at (±2.54, ±2.54).** The KiCad stock
footprint's drills (1.5 / 1.7 mm) are 0.1–0.3 mm looser than the datasheet's
Ø1.4 and must be tightened for a repeatable launch. **Do NOT drop the ground
legs to Ø1.3**: a 0.9 mm square post has a 1.273 mm diagonal, leaving 0.014 mm
radial clearance — inside JLC's plated-hole tolerance. Ø1.4 gives 0.064 mm.
This is a deliberate, arithmetically justified override of a vendor's own
recommended hole size.

## Consequences

- **Every launch rule below is DERIVED ENGINEERING, not vendor instruction.**
  Neither this datasheet nor the rejected one contains an Application or
  Layout section, a via-fence rule, an antipad rule, a board-thickness
  requirement or a VSWR curve. It cannot be waived by citing the datasheet.
  (Contrast Amphenol 132289's drawing, which DOES take responsibility, down to
  note 7 "BOARD THICKNESS = 1.57 MM".)
- **RULE 1 — bottom-plane antipad ≥ Ø3.5 mm, opening OUTWARD toward the
  5.08 mm post square. NOT the Ø2.6 mm minimum-DRC value.** The spike's rule
  was **stated backwards** and would have been frozen into the footprint. Its
  reasoning computed a 0.081 pF top-pad capacitance **to solid copper** and
  then specified an antipad that deletes 100 % of that copper — the number was
  computed against a reference plane the rule removes. For a through-hole jack
  the launch's dominant terms are the ~1.4 mm barrel crossing the board
  (modelled as a low-Z coax section, +0.425 pF) and the bottom pad sitting
  inside the antipad (annular-gap model, 0.192 pF) — **2–5× the top-pad term**.
  Opening Ø2.6 → Ø3.5 buys **5.6 dB of return loss at 6 GHz for free** — RL
  goes 8.9 dB → 14.5 dB. **THIS NUMBER WAS ~9 dB UNTIL 2026-07-29 AND ~9 dB WAS
  TOO GENEROUS.** The rule is right; the size of the prize was a first-pass
  estimate that nothing had re-derived. A sibling board in this fleet re-ran the
  same annular-gap model on the same Ø2.6-vs-Ø3.5 question and got 14.5 vs 8.9,
  i.e. 5.6 dB. The rule is UNCHANGED because 5.6 dB of free return loss on a
  launch whose absolute RL is only ~11–15 dB (RULE 2) is still the single
  cheapest improvement available; what changed is that the claim now matches
  the arithmetic behind it. Carrying 9 dB would have overstated the launch by
  3.4 dB in the one place a reader would trust it — the footprint's own `descr`.
- **RULE 2 — per-port launch return loss at 6 GHz is ~11–15 dB, not 22.3 dB.**
  Two independent lumped models agree. Carry the pessimistic figure or measure
  it; do not carry 22.3 dB.
- **RULE 3 — ground-via fence at ≤2.0 mm pitch** (λg/12 at 6 GHz) immediately
  outside the 5.08 mm square, continuing down both sides of the RF trace for at
  least the first 10 mm. λg in bulk FR4 at 6 GHz is 24.1 mm, and the
  connector's four posts sit at 5.08 mm (λg/4.7) and 7.18 mm diagonal
  (λg/3.4) — **2–3× coarser than a λg/10 fence. The four posts are NOT a
  shield at 6 GHz.** Omitting the fence produces both poor return loss and
  poor port-to-port isolation, and the connector will get the blame. Emit it as
  a generated rule, never a layout habit.
- **RULE 4 — keep the top-side pour continuous right up to the four ground
  pads.** That is where the connector's return current wants to land.
- **The spike's "thinner dielectric makes this launch worse" finding is
  REFUTED** and must not propagate. Once the barrel is included, thinner is
  BETTER (Ø2.6 antipad: RL 11.3 dB @1.6 mm vs 16.0 dB @0.8 mm) or
  thickness-independent, depending on the model. **The 1.6 mm two-layer
  stackup that finding was used to justify is rejected for other, decisive
  reasons anyway (ADR-0010).**
- **The spike's escape rule is geometrically impossible and must not be
  written down.** It claims the signal leaves the centre pad "with ≥1.5 mm
  clearance to the nearest ground-pad edge". On its own 1.6 mm stackup a 50 Ω
  microstrip is 3.112 mm wide — half-width 1.556 mm against a ground-pad edge
  at 1.415–1.540 mm, i.e. **NEGATIVE clearance**; the trace would overlap the
  ground pads and is wider than the centre pad it lands on. On the chosen
  0.2104 mm-prepreg stackup the line is 0.35 mm and the clearance is real.
- **THT disqualifies the board from JLC Economic PCBA** and adds ~$6.93 per
  order ($3.50 setup + ~$0.0173/joint × 10 joints + $3.00 extended-component),
  not the ~$3.93 the spike computed.
- **DO NOT substitute on appearance.** `C914559` SMA-KE901 has a **4.90 mm**
  post square, not 5.08 — the legs will not enter. `C914556` SMA-KE-P901 and
  `C914553` SMA-KWE901 are **RP-SMA** (male centre pin in an external-thread
  shell) and will not mate with a standard SMA cable: a price-driven swap
  yields a board that assembles cleanly and cannot be connected. `C5250058`
  BWSMA-KE11 has an offset pin pattern. Pin "5.08" in the footprint NAME and
  forbid these explicitly in `part.yaml`.
- **Buy 2× Amphenol 132289 (C3172723) as a bench reference fixture** so the
  cheap connector's launch can be measured against a known-good 18 GHz one
  rather than against a simulation. ~$23, and it converts RULE 2 from an
  estimate into a measurement.
- The datasheet contradicts LCSC's parametrics on temperature range (−45/+85
  vs −65/+165). Harmless here, but it means LCSC parametric fields for this
  vendor class are not a spec source — only the PDF counts.

## Extended — 2026-07-27, by ADR-0015 (user directive A8). NOT superseded.

**This part is now used FIVE times, not twice.** ADR-0006's SMA→SMP mating
strategy is dead; the three Pluto-facing ports are SMA cables into three more
`KH-SMA-KE-Z` jacks, identical to the two antenna ports. Nothing in the
selection, the footprint, or the four derived launch RULES changes — they get
applied to five launches instead of two, and the two rules this ADR corrected
(the ≥Ø3.5 mm bottom-plane antipad, and "thinner dielectric is BETTER once the
barrel is modelled") now protect 2.5× as much of the board.

**Two things this extension makes MORE load-bearing, stated because scaling a
rule is not free:**

1. **RULE 2 — per-port launch return loss at 6 GHz is ~11–15 dB, not 22.3 dB.**
   With five launches instead of two, and with the TX→RX path now crossing TWO
   of them instead of two SMP interfaces (VSWR 1.11 max), the launch is a
   larger share of the board's own contribution. The bench-reference fixture
   this ADR already recommends (2 × Amphenol 132289, ~$23) converts that
   estimate into a measurement, and it is now worth more.
2. **THT joint count triples: 5 × 5 = 25 joints, not 10.** The JLC Standard-PCBA
   adder moves from ~$3.50 setup + ~$0.17 joints to ~$3.50 + ~$0.43, plus the
   $3.00 extended-component charge — still trivial, but `assembly.yaml` states
   it rather than carrying a stale figure.

**GENDER, verified from the datasheet FIELDS rather than the suffix**, because
this board has already paid $101 once for a gender read off a part number
(ADR-0006). `产品名称 = SMA 直式印制面板插座` on p.1 — *插座* is
receptacle/socket, i.e. **jack** — and sheet 2/2 shows a fixed barrel with an
EXTERNAL `1/4-36UNEF` thread and no coupling nut, which is the jack shell form.
**Neither page states the centre-contact polarity in words**, so standard-vs-RP
is closed by a second source: LCSC C504007, read 2026-07-27, `CONN RCPT SMA TH`
with interface type **"Inner hole"**. Full chain in ADR-0015.

**A correction to this project's own `part.yaml`:** it claimed the gender was
*"read from the part-number decode on p.1"*. There is no part-number decode on
p.1. That claim is replaced with the fields that actually exist.
