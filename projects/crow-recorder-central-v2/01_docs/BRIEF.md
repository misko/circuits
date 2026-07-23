# brief: crow-recorder-central-v2

status: schematic-gate-green
prompt_sha256: be9e677e3628dcf801affba573593bc836bfb9a71290dadde58d09e819590c39
current_release: no

Board (b) of a two-board commission — the CENTRAL 8-channel USB audio
recorder. The remote microphone POD is a SIBLING agent's board and is NOT
designed here; this board honours only the shared cable/pinout interface.

CLEAN-ROOM: designed purely from the brief + the pcb-design/kicad-pcb skill
references (proven-parts.yaml, floorplan-archetypes.md, layout-precedents.md).
No sibling project (crow-recorder-central, crow-mic-pod, crow-mic-pod-v2) was
read. Ledger entries harvested from crow-recorder-central v1.0 ARE consumed —
`proven-parts.yaml` is a sanctioned skill reference (the compounding mechanism),
not a sibling project.

## Original prompt

<!-- prompt-verbatim-begin -->
> Verbatim user commission (invoked via /pcb-design, 2026-07-21). The user
> supplied the full "CROW ACOUSTIC LOCALIZATION ARRAY — REV-A WORKING DESIGN,
> TEXT EDITION" document (July 18, 2026) as the brief, followed by this
> directive appended to the same invocation:
>
> ", lets use ethernet cable and ethernet connectors everywhere to interface them"
>
> KEY REV-A FACTS FROM THE DOCUMENT (the full text is the commission; the
> agent must treat the document's tables as requirement sources):
>
> - Purpose: outdoor crow-call localization; 6 active-balanced microphone
>   pods, 25 ft radius, feeding ONE shared-clock 8-channel-capable USB
>   recorder (6 populated). 24-bit / 48 kHz, USB Audio Class 2 ASYNC (the
>   recorder clock is the timing authority). One physical sample clock for
>   every channel — no GPS/network sync.
> - TWO custom PCBs: (a) remote microphone POD (2-layer): AOM-5024L-HD-R
>   electret + OPA1678IDR dual op-amp active-balanced driver (~3 V/V diff,
>   values table in doc), CMT-8504-100-SMT-TR calibration transducer
>   (driven FROM the central board, 5V ~150mA coded 4kHz bursts),
>   TPD2E2U06DRLR ESD; (b) CENTRAL recorder (4-layer min, 6 preferred):
>   XU316-1024-TQ128-I24 + 2x PCM1865DBTR (TDM, shared MCLK/BCLK/LRCK,
>   NC7NZ34K8X clock buffer, FA-238 24MHz, W25Q16JVSSIQ QSPI), USB4105
>   USB-C + TPD4EUSB30DQAR, SHT40-AD1B-R2, per-cable port: RJHSE5384 RJ45
>   (8 footprints, 6 populated), TPD2E2U06 analog ESD, MINISMDC050F-2 PTC,
>   AO3400A low-side beeper MOSFET (slow edges), rails: 2x AP61102Z6-7
>   bucks (3.3V + 0.9V core), TCR2LF18 1.8V LDO, XC6227C331PR-G quiet 3.3V
>   analog LDO, Mean Well GST25A05-P1J external 5V supply.
> - Cabling: one outdoor solid-copper Cat5e home-run per pod, CUSTOM
>   pinout (NOT Ethernet): orange 1,2=AUDIO+/-; green 3,6=+5V_BEEP/
>   BEEP_SWITCHED_RETURN; blue 4,5 & brown 7,8 = +5V_AUDIO/GND_AUDIO.
>   Label everything "NOT ETHERNET - CUSTOM 5V AUDIO PINOUT".
> - USER DIRECTIVE (amends the doc): use ethernet cable AND ethernet
>   connectors EVERYWHERE to interface pods and central — i.e. the pod end
>   also gets an RJ45 jack (not gland+solder pads); keep the custom-pinout
>   safety labeling discipline.
> - XMOS multichannel audio platform (XU316 + 2x PCM1865) is the named
>   reference design: copy its power sequencing, clocking and USB
>   implementation closely (layout-precedent search mandatory).
> - Layout guidance in doc: ADCs + input RC in quiet analog region away
>   from switching regulators and beeper traces; controlled short USB;
>   test points for every rail + clocks + TDM + beeper returns;
>   same-signal injection header for inter-ADC skew; 8 port footprints
>   with 6 populated.
> - Doc's own risk register + build sequence apply (pod prototype first).
> - Budgets are advisory; stock must be rechecked (doc says so).
<!-- prompt-verbatim-end -->

- date: 2026-07-21 (commission); this build 2026-07-23
- channel: /pcb-design invocation, system commission file crow_v2_system_brief.md

## End goal — definition of done

An orderable, DRC-clean 6-layer JLCPCB release for the CENTRAL recorder: an
XU316-1024 xcore.ai USB-Audio-Class-2 async device that samples 8 balanced
microphone channels (6 populated) via 2x PCM1865 TDM ADCs on one shared
sample clock, drives per-pod calibration beepers, distributes 5V audio/beep
power to 6 pods over custom-pinout Cat5e (RJ45 both ends), and reports
enclosure temp/humidity — all powered from one external 5V/5A brick.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | XU316-1024-TQ128 xcore.ai SoC, USB Audio Class 2 async, QSPI boot | P | unmet |
| G2 | 2x PCM1865 TDM, shared MCLK/BCLK/LRCK, 24-bit/48kHz, 8ch (6 used) | P | unmet |
| G3 | NC7NZ34 clock buffer + FA-238 24MHz xtal clock tree | P | unmet |
| G4 | USB4105 USB-C + TPD4EUSB30 ESD, controlled short USB HS pair | P | unmet |
| G5 | 8x RJHSE5384 RJ45 (6 populated), custom NOT-ETHERNET 5V audio pinout | P | unmet |
| G6 | Per-port TPD2E2U06 analog ESD + MINISMDC050F-2 PTC | P | unmet |
| G7 | AO3400A low-side beeper switch, slow gate edges | P | unmet |
| G8 | Rails: 2x AP61102 buck (3V3+0V9), TCR2LF18 1V8 LDO, XC6227 3V3A LDO | P | unmet |
| G9 | Power sequencing per XMOS ref: 3V3 -> 0V9(core, PG-gated) -> 1V8 | P | unmet |
| G10 | Quiet-analog discipline: ADCs+input RC away from switchers+beeper | P | unmet |
| G11 | SHT40-AD1B-R2 temp/humidity on I2C | P | unmet |
| G12 | Test points: every rail + MCLK/BCLK/LRCK + TDM data + beeper returns | P | unmet |
| G13 | Same-signal injection header for inter-ADC skew measurement | P | unmet |
| G14 | Silk "NOT ETHERNET - CUSTOM 5V AUDIO PINOUT" on every port | P | unmet |
| G15 | 5V DC input from external GST25A05 brick + input protection ADR | P/D-SPEC | unmet |
| G16 | DRC 0/0/0, ERC 0, parity 0, all release gates green | pipeline | unmet |

## Spec tensions (D-SPEC — checked at commission, before architecture)

| # | Requirement | Standard / parts cap it exceeds | Resolution (ADR) | User flagged |
|---|---|---|---|---|
| T1 | XU316 0.4mm TQFP-128 escape at "4-layer min" | 4L (even advanced) cannot close full XU316 routing; needs 6L small-via via-in-pad (ledger + fab_tiers provenance) | ADR-0002 (D-TIER: fab_tier=jlc_6layer_smallvia; brief says "6 preferred") | yes (D-TIER) |
| T2 | 5V input, buck VIN abs-max 6.5V (AP61102/XC6227 all 6.5V, OVP 6.3V) | a standard 5.0V TVS (SMAJ5.0A) breaks down 6.4-7.1V, clamps ~9V > 6.5V abs-max under surge | ADR-0001 (input protection: RPP P-FET + TVS + fuse-on-fault; relies on regulated 5V brick, TVS+PTC crowbar a wrong-adapter fault) | yes |
| T3 | "8-channel capable, 6 populated" ports vs 2x PCM1865 (4 diff ch each) | none — 2x4=8 diff channels exactly meets 8ch; 6 RJ45 populated | — (no tension) | n/a |

## Sourcing spike (D-SPEC, at commission — scarcity discovered NOW)

SPEC-CRITICAL functions and their status (ledger-first, then part-universe):

| Function | Part | Ledger? | Status |
|---|---|---|---|
| XMOS SoC | XU316-1024-TQ128-I24 | yes (usb-audio-soc-xcore) | (b) costlier: CONSIGNMENT/global-sourcing, JLC assy stock chronically 0 — plan the consign at commission (ADR-0003) |
| 8ch TDM ADC | PCM1865DBTR | yes (audio-adc-8ch-tdm) | (a) sourceable, C181312 |
| Clock buffer | NC7NZ34K8X | yes (clock-buffer-2ch-lvcmos) | (a) C232798 |
| 3V3/0V9 buck | AP61102Z6-7 | yes (buck-1a5-sot563) | (a) C5224055 |
| Quiet analog LDO | XC6227C331PR-G | yes (analog-ldo-quiet-3v3) | (a) C6035451 |
| 1V8 LDO | TCR2LF18 (TLV70018 fallback) | yes (ldo-1v8-200ma) | (a) TCR2LF18 exact; TLV70018 C79924 in-stock alt |
| Analog ESD | TPD2E2U06DRLR | yes (esd-2ch-bidirectional-sot553) | (a) C1972959 |
| RJ45 jack | RJHSE-5384 | yes (rj45-jack-shielded-tht) | (b/c) C99* consign placeholder, NO EasyEDA CAD, hand-solder line |
| 24MHz xtal | FA-238_24.0000MD50Y-AC | researched | (a) C7190380 — BUT was OUT OF STOCK at fetch (order-day risk); CL=9pF -> 12pF load caps; confirm exact Q22 code |
| QSPI flash | W25Q16JVSSIQ | researched | (a) C82317 |
| USB-C | USB4105-GF-A | researched | (a) C3020560; alphanumeric pads -> parity_padmap.txt |
| USB ESD | TPD4EUSB30DQAR | researched | (a) C90627 (USON-10, needs 4L-adv escape; board 6L OK) |
| Temp/humidity | SHT40-AD1B-R2 | researched | (a) C2909890 |
| Audio PTC | MINISMDC050F-2 (LITTELFUSE, not Bourns) | researched | (a) C2649901 |
| Beeper FET | AO3400A (N-ch) | researched | (a) C20917; + AO3401A (P-ch RPP) C15127 |
| 5V DC input jack | DC-005-5A-2.0 (D5) | researched | (a) C381116 (5A, 5.5x2.1mm, for GST25A05-P1J) |
| Input fuse | JFC1206-1200FS (D-SUB) | researched | (a) C136345 — brief's JB12F2001R not LCSC-findable, this is the substitute alt |

## Log

- D1 (2026-07-23, agent absent-user): **Single shared beeper switch.** The
  brief lists ONE AO3400A. All six ports' +5V_BEEP tie to the 5V_BEEP bus and
  all six BEEP_SWITCHED_RETURN (green 6) tie to a common node switched by one
  AO3400A low-side FET. Fires all pods' calibration transducers together — this
  is CORRECT for inter-channel/inter-ADC SKEW calibration (a common reference
  tone at all mics is exactly what a skew measurement wants; per-pod ranging is
  not a stated requirement). Simplest reading that satisfies the single-FET
  brief. FLAGGED: if the system later needs per-pod beeper addressing (individual
  acoustic ranging), this needs 6 low-side FETs — a respin. 6x150mA=900mA peak
  through one AO3400A (rated 5.7A) is comfortable.
- D2 (2026-07-23): **fab_tier = jlc_6layer_smallvia** (D-TIER, ADR-0002). Brief
  says "4-layer min, 6 preferred"; the XU316 0.4mm TQFP-128 provably needs 6L
  small-via. Costlier tier accepted at the cheapest moment (commission).
- D3 (2026-07-23): **1V8 LDO = TCR2LF18** as the brief specifies (exact MPN);
  TLV70018DDCR (C79924, in JLC stock) is the pin-compatible fallback if TCR2LF18
  stock is thin at order day (ADR-0006). Fed from 3V3 (not 5V) so it is never
  the last rail up.
- D4 (2026-07-23): **Shared clock topology per XMOS ref + ledger:** MCLK into
  PCM1865 SCKI (pin 15), XI (pin 10) TIED TO GND (XI abs-max 2.1V — feeding MCLK
  into XI overstresses it). BCLK/LRCK/MCLK shared via SOURCE-SERIES 33R at the
  driver. I2C address strapped per-ADC via AD pin (0x4A/0x4B).
- D5 (2026-07-23, agent absent-user): **5V DC input = barrel jack (DC-005 /
  5.5x2.1mm) + 2-pin screw terminal footprint alt is NOT used** — the GST25A05-P1J
  ships a barrel plug (P1J = 2.1mm centre-positive DC plug). A 5.5x2.1mm barrel
  jack matches. FLAGGED as a D# assumption: if the actual GST25A05-P1J plug is
  2.5mm, the jack must change. Simplest reading of "external 5V supply."
- D6 (2026-07-23): USER DIRECTIVE — RJ45 (RJHSE-5384) at the CENTRAL port bank,
  8 footprints, 6 populated. The pod end also gets RJ45 (sibling board). Custom
  pinout, safety-labelled. Honoured.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | single shared beeper FET (all pods fire together) | agent (absent user) | assumption |
| D2 | fab_tier jlc_6layer_smallvia (ADR-0002) | agent (ledger-forced) | ADR |
| D3 | 1V8 LDO TCR2LF18, TLV70018 fallback (ADR-0006) | agent (brief) | ADR |
| D4 | shared-clock topology, XI-to-GND (ADR-0004) | agent (ledger) | ADR |
| D5 | 5V input via 5.5x2.1mm barrel jack | agent (absent user) | assumption |
| D6 | RJ45 both ends, custom pinout labelled | user directive | directive |
