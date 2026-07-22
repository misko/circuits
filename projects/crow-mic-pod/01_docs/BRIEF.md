# brief: crow-mic-pod

status: in-progress
prompt_sha256: be9e677e3628dcf801affba573593bc836bfb9a71290dadde58d09e819590c39
current_release: no

## Original prompt

**UNVERIFIED (condensed).** The commissioning input this session received is a
faithful CONDENSATION of the user's full "CROW ACOUSTIC LOCALIZATION ARRAY —
REV-A WORKING DESIGN, TEXT EDITION" document (July 18, 2026); the full Rev-A
text is held by the user and was NOT transmitted verbatim. Per the 01_docs
contract's repair path, the section below quotes the condensation exactly
(file `01_docs/brief_source_condensed.md`, whole-file sha256 above). The
embedded user DIRECTIVE quote is verbatim. REPAIR: the user should attach the
full Rev-A document text so this section can be replaced with a hashable
verbatim prompt. Until then, prompt-derived requirements are tagged P but the
condensation is the proximate source.

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

- date: 2026-07-21
- channel: /pcb-design invocation (condensed relay; full Rev-A doc held by user)

## Scope of THIS project

The remote microphone POD board only — sibling project
`projects/crow-recorder-central/` carries the central recorder. Split
decision: decisions/0000-scope-two-boards.md. The prior sealed execution of
this same commission lives at `archived_projects/crow-array-pod/` (releases
v1.0/v1.1) and is used as read-only precedent (decisions/0005).

## End goal — definition of done

An orderable, verified JLCPCB release of a 2-layer outdoor microphone pod:
AOM-5024L-HD-R electret with active-balanced OPA1678 driver (~3 V/V
differential), CMT-8504 calibration transducer driven from the central board,
TPD2E2U06 cable-entry ESD, terminated in an RJ45 jack (ethernet connectors
everywhere, per the P directive) carrying the custom NOT-Ethernet 5V/audio
pinout, fitting the outdoor pod enclosure, with every SKILL gate green.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | 2-layer pod PCB: AOM-5024L-HD-R + OPA1678IDR active-balanced (~3 V/V diff) | P | unmet |
| G2 | CMT-8504-100-SMT-TR on-board, driven from central (5V ~150mA coded 4kHz bursts) | P | unmet |
| G3 | TPD2E2U06DRLR ESD at cable entry | P | unmet |
| G4 | RJ45 jack termination at the POD end (ethernet connectors everywhere) | P (directive) | unmet |
| G5 | Custom pinout preserved + "NOT ETHERNET - CUSTOM 5V AUDIO PINOUT" labeling | P | unmet |
| G6 | All pipeline gates green; orderable JLC release | SKILL | unmet |

## Spec tensions (D-SPEC — fill at commission, before architecture)

| # | Requirement | Standard / parts cap it exceeds | Resolution (ADR) | User flagged |
|---|---|---|---|---|
| T1 | POD scope: none found (RJ45 carrying 5V/audio is non-standard USE, not out-of-envelope — contacts rated 1.5A/contact, our worst leg ~150mA beep + ~20mA audio) | — | labeling discipline per P; decisions/0004 | noted in report |
| T2 | CMT-8504-100-SMT-TR JLC stock THIN (see sourcing spike log) | stock, not spec | order-day re-check + Digi-Key hand-solder fallback in ORDER_README | yes (report) |

(Recorder-side tensions — XU316 availability etc. — live in the sibling
project's BRIEF.)

## Log

### D1 — 2026-07-21 — user directive (within commission)
> ", lets use ethernet cable and ethernet connectors everywhere to interface them"
Impact: pod cable termination = RJ45 jack (not gland + solder pads/screw
terminal). Custom-pinout labeling discipline retained. Drives decisions/0004.

### A1 — 2026-07-21 — assumption (not asked)
Assumed: the condensed brief faithfully represents the full Rev-A document;
where the condensation is silent, the archived prior execution of the same
Rev-A commission (`archived_projects/crow-array/01_docs/BRIEF.md`, sha
21e54984…) supplies the detail (values tables, enclosure, §3/3A/4 numbers).
Authority: P (the condensation states it condenses the same document the
archive executed; dates and part lists match exactly).
Escalate if: the user's full Rev-A text, once attached, disagrees with the
archive-carried details.

### A2 — 2026-07-21 — assumption (not asked)
Assumed: pod enclosure = Hammond 1551WY (81x31 lid recess, boss pattern
75.00x35.00), as in the archived execution; the condensation does not name an
enclosure. Authority: A1. Escalate if: user names a different enclosure.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | RJ45 at pod end, ethernet connectors everywhere | user (P directive) | Log D1 + decisions/0004 |
| 0000 | Two projects: pod + central; pod executes first | agent (P build sequence) | decisions/0000-scope-two-boards.md |
| 0001 | Input protection: entry ESD populated, PTC at central end, no pod fuse | agent | decisions/0001-input-protection.md |
| 0002 | Beeper clamp: SS14 flyback populated + empty SMAJ6.0A TVS position | agent | decisions/0002-beeper-clamp.md |
| 0003 | Outline: 1551WY max-PCB 94.5x44.5, boss holes; mic/transducer separation | agent (A2) | decisions/0003-board-outline.md |
| 0004 | RJ45 termination RJHSE-5384, custom-pinout labeling, lid-recess fit | user D1 + agent | decisions/0004-rj45-termination.md |
| 0005 | Reuse of archived crow-array-pod sources as precedent, re-verified | agent | decisions/0005-archive-precedent.md |
