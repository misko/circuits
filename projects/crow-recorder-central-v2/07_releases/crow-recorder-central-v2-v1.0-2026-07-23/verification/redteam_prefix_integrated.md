subject: crow-recorder-central-v2 pre-v1.0 (routing-gate state 3bee9ec)
date: 2026-07-23
reviewer: redteam-agent (fresh-context, integrated topology+layout lens; session interrupted by quota stop)
context-given: zero-context
verdict: DO-NOT-ORDER

# PROVENANCE NOTE (archive honesty)

The reviewing session was killed by the 2026-07-23 session-quota stop before
its report was archived; the VERBATIM review text did not survive. This file
is a RECONSTRUCTION of its findings from the contemporaneous records written
while the review was live: `01_docs/journal/routing.md` (P0 fix-pass entry),
`RESUME.md` (WIP checkpoint 8017400), and the two ADRs the review forced
(`0005` amendment, `0007`). Findings below are faithful to those records but
are NOT the reviewer's own words — the 08_reviews verbatim rule is
acknowledged as unmet and this note is the disposition of that gap. Future
reviews: archive here FIRST, before the session can die.

# Findings (as recorded)

## P0-1 — P5VA_4 merged into AUDIO4M (port 4 loses its +5V rail)
Port-4 +5V-audio net P5VA_4 was merged into the ch4 balanced-minus audio net
AUDIO4M by board-generation net-binding: the schematic's vertical P5VA_4 wire
(280.67,136.525)->(280.67,153.035) passed exactly through (280.67,147.955),
the junction endpoint of the AUDIO4M wires, and `kicad-cli sch export
netlist` merged both nets under the name AUDIO4M. J6.4/J6.7/F4.2 landed on
the audio-minus into the ADC — port 4's pods would get NO power rail.
Invisible to ERC/DRC/count_parity (all self-consistent with the merged
netlist); caught by a per-pad port check. Verdict driver.

## P1#1 — U7 EN/mode contradiction vs ADR-0005
ADR-0005 claimed forced-PWM "for the buck feeding the analog LDO input"
while tying U7 EN high through the input — AP61102 EN>=VIN-200mV selects
auto PFM; the wiring contradicts the forced-PWM claim, and the rationale
mis-attributed the analog LDO input (U10 feeds from 5V, not 3V3).

## P1#2 — 5V trunk ampacity / fragile single-path trunk; netclasses in the
route chain; beeper legs unfused per-port
The 5V distribution to the port bank ran as a single fragile path (through
Cc2P.2's pad as a via point — confirmed during the P0 surgery when deleting
the merged tree severed a 100-item island). Netclass ampacity floors must
demonstrably ride the final board (pcbnew saves clobber netclasses). Beeper
legs (J*.3/J*.6) have no per-port PTC — a beeper-pin short is cleared only
by F_IN (2A) = whole-board outage.

## P1#3 — layout spans vs the part.yaml P-ADJ keep-short budgets
Net-span budgets declared in `layout:` blocks (P-LAYOUT) must be measured on
the final placement (P-ADJ), over-spans waived with measured numbers.

## P1#4 — per-port NOT-ETHERNET silk (brief G14)
The single banner left J3/J4/J5/J9 + the fuse row with no functional warning
within 8mm of the jack a user actually plugs. One warning per port required.

## P1#5 — PoE-injector backfeed onto P5VA/beep legs
An endspan injector (mode B: 4/5+, 7/8-) drives ~48V onto J*.4/7 = P5VA_n;
path 48V -> F_n PTC -> 5V rail exceeds AP61102 vin_abs_max 6.5V and every
5V-rail part. D1 (SMAJ5.0A) is on VIN_RAW — wrong side of Q1 for a
rail-side injection. Same class as crow-mic-pod-v2 ADR-0005 (sealed with an
accepted user waiver).

## REJECTED — Q1 reverse-polarity protection alleged wrong
A finding alleging Q1's reverse-polarity FET is wrong was REFUTED on
verification: Q1 is CORRECT AS-BUILT (E-INV asserts the D->S series chain;
schematic-gate entry 03_schematic.md records the invariant passing). GUARD:
do not "fix" it.
