# brief: crow-mic-pod-v2

status: active
prompt_sha256: be9e677e3628dcf801affba573593bc836bfb9a71290dadde58d09e819590c39
current_release: no

Board (a) of the CROW ACOUSTIC LOCALIZATION ARRAY commission: the REMOTE
MICROPHONE POD. Designed CLEAN-ROOM (from the brief + sanctioned skill
references only; sibling boards crow-mic-pod / crow-recorder-central[-v2]
NOT consulted, per C-ISO). The CENTRAL recorder is a sibling agent's job.

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

- date: 2026-07-23
- channel: /pcb-design invocation (system commission relayed by the main loop)

## Scope of THIS board (board a only)

The POD is a passive-cable remote node. It is powered and clocked entirely
FROM the central board over one Cat5e home-run; it holds NO energy source,
NO converter, NO clock, NO switching element. Its job: capture one channel,
present it as a balanced line-level pair, and host the calibration
transducer that the central board drives.

## End goal — definition of done

A DRC-clean, JLC-orderable 2-layer PCB that: biases one AOM-5024L-HD-R
electret, drives its signal as a ~3 V/V differential balanced pair through
an OPA1678IDR active-balanced driver, protects the exposed audio pair with
a TPD2E2U06DRLR ESD array, hosts the CMT-8504-100-SMT-TR calibration
transducer (driven from central, flyback-clamped locally), and lands the
whole shared cable interface on ONE RJ45 jack (RJHSE-5384) carrying the
custom NON-ETHERNET pinout, silk-labelled "NOT ETHERNET - CUSTOM 5V AUDIO
PINOUT".

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | AOM-5024L-HD-R electret biased from an RC-filtered +5V_AUDIO node | P/doc | unmet |
| G2 | OPA1678IDR active-balanced driver, ~3 V/V differential gain | P/doc | unmet |
| G3 | TPD2E2U06DRLR ESD on the exposed AUDIO+/AUDIO- pair to GND_AUDIO | P/doc | unmet |
| G4 | CMT-8504-100-SMT-TR on +5V_BEEP / BEEP_SWITCHED_RETURN, flyback-clamped locally | P/doc | unmet |
| G5 | ONE RJ45 jack (RJHSE-5384) at the pod end carrying the custom pinout | P/directive | unmet |
| G6 | RJ45 wired EXACTLY: 1,2=AUDIO+/-; 3,6=+5V_BEEP/BEEP_RET; 4,5=+5V_AUDIO; 7,8=GND_AUDIO | P | unmet |
| G7 | Silk "NOT ETHERNET - CUSTOM 5V AUDIO PINOUT" + full pin-map legend | P | unmet |
| G8 | Beep return stays isolated from analog GND on the pod (switched at central) | derived | unmet |
| G9 | 2-layer, cheapest fab tier (jlc_2layer_default), all parts fit | D-TIER | unmet |
| G10 | ERC 0 / DRC 0-0-0 / parity 0 / policy_audit 0-FAIL / twin 0-crit | gates | unmet |

## Spec tensions (D-SPEC — checked at commission, before architecture)

| # | Requirement | Standard / parts cap it exceeds | Resolution (ADR) | User flagged |
|---|---|---|---|---|
| T1 | "ethernet connectors everywhere" but the cable is a CUSTOM 5V power/audio pinout, NOT Ethernet | Physically legal (RJ45 pins rated ~1.5A; Cat5e conductor carries 5V/150mA beep + 5mA audio fine) but SEMANTICALLY hazardous — a field tech WILL plug a real switch into it | 0003-rj45-custom-pinout-and-labeling.md | yes (see report) |
| T2 | "~3 V/V diff, values from the doc's table" — the doc's exact resistor table was NOT provided to this clean-room agent (only the summary) | No parts cap; the tension is fidelity: I DERIVE values hitting the stated 3 V/V differential target rather than copying an unseen table | 0002-active-balanced-driver.md (D1 assumption) | yes (D1) |

No sourceable-part tension: all 7 specialty parts are ledger-verified and
in-catalog except AOM-5024L-HD-R (hand-solder, not in JLC) and RJHSE-5384
(consign/hand-solder) — both known, both hand-solder lines, neither blocks.

## Log

- D1 (2026-07-23, agent, user absent) — the doc's exact op-amp resistor
  table was not supplied to this clean-room run. Per D-BACK SPEC-CHECK
  (user absent → simplest reading that satisfies the STATED requirement),
  I derive standard 1%-resistor values that produce the stated ~3 V/V
  DIFFERENTIAL gain (symmetric ±1.5 V/V split, best CMRR/headroom on a
  single 5V supply). Exact values in DETAIL_DESIGN.md / ADR-0002. Flagged
  loudly in the report so a respin can drop in the doc's table verbatim if
  it differs. The 3 V/V differential figure is the load-bearing spec and
  is honoured exactly.
- D2 (2026-07-23) — the pod carries NO on-board energy source and NO
  converter: it is powered from central over the cable. E-TOPO has no
  rails to derive; E-OFF is N-A (external supply — unplugging the cable /
  powering down central de-energizes it). power_tree.yaml records this.
- D3 (2026-07-23) — reverse-polarity: no series-FET / diode on the pod
  power rails. Rationale in ADR-0001: keyed RJ45 + mandatory NOT-ETHERNET
  labeling, tiny load (~5mA), controlled fixed install; ESD arrays clamp
  transients, the beep line has a DNP TVS position. Flagged for user
  awareness.
- D4 (2026-07-23) — fab tier jlc_2layer_default (cheapest 2-layer, 0.6/0.3
  vias, no advanced option). Every part's ledger escape block declares
  tier_required = jlc_2layer_default. ADR-0004.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | derive ~3 V/V balanced-driver resistor values (doc table unseen) | agent (user absent) | reversible at respin |
| D2 | no converter / no energy source on pod — cable-powered | brief | structural |
| D3 | no reverse-polarity FET on pod power rails | agent (user absent) | reversible |
| D4 | fab_tier = jlc_2layer_default | agent | reversible |
