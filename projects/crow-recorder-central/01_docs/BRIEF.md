# brief: crow-recorder-central

status: agreed (commissioned; engineering not yet started — pod executes first)
prompt_sha256: be9e677e3628dcf801affba573593bc836bfb9a71290dadde58d09e819590c39
current_release: no

## Original prompt

**UNVERIFIED (condensed).** Same commission record as
`projects/crow-mic-pod/01_docs/BRIEF.md` — the prompt is a faithful
CONDENSATION of the user's full Rev-A document (July 18 2026, full text held
by the user; REPAIR: attach it to make this hashable). The condensation is
quoted verbatim there between prompt markers and stored as
`01_docs/brief_source_condensed.md` here (whole-file sha256 above, identical
bytes in both projects). The embedded directive quote is verbatim:

<!-- prompt-verbatim-begin -->
> ", lets use ethernet cable and ethernet connectors everywhere to interface them"
>
> (Full condensed commission: see 01_docs/brief_source_condensed.md — bytes
> hashed above; pod copy identical.)
<!-- prompt-verbatim-end -->

- date: 2026-07-21
- channel: /pcb-design invocation (condensed relay)

## Scope of THIS project

The CENTRAL recorder board only: XU316-1024-TQ128-I24 + 2x PCM1865DBTR
shared-clock TDM, UAC2 async USB (USB4105 + TPD4EUSB30), 8 RJ45 port
footprints (6 populated) with per-port PTC + analog ESD + beeper low-side
switch, rails per the doc (2x AP61102 bucks, TCR2LF18, XC6227 quiet analog
LDO), SHT40, W25Q16 QSPI boot flash, FA-238 24MHz + NC7NZ34 clock buffer.
Split decision: 01_docs/decisions/0000-scope-two-boards.md (mirrors pod
ADR-0000). Interop authority: RJ45 contact map = pod decisions/0004,
contact-for-contact. Precedent: `archived_projects/crow-array-central/`
(sealed v1.0-2026-07-18, 6-layer, DRC 0/0/0) — read-only reference, to be
adopted under the same provenance+re-verify rule as pod ADR-0005.

## End goal — definition of done

An orderable, verified JLCPCB release of the central recorder (4-layer min,
6 preferred — archive proved 4L does not close; expect 6L + small-via tier),
every SKILL gate green, RJ45 map matching the pod, NOT-ETHERNET labeling.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | XU316 + 2x PCM1865 shared-clock TDM, UAC2 async 24-bit/48kHz | P | unmet |
| G2 | 8 RJ45 footprints, 6 populated; per-port PTC/ESD/beeper switch | P | unmet |
| G3 | Rails: 2x AP61102 (3.3V/0.9V), TCR2LF18 1.8V, XC6227 quiet 3.3VA; GST25A05 5V input | P | unmet |
| G4 | RJ45 contact map = pod map; NOT-ETHERNET labeling | P (directive) | unmet |
| G5 | All pipeline gates green; orderable JLC release | SKILL | unmet |

## Spec tensions (D-SPEC — sourcing spike run at commission, 2026-07-21)

Live JLC stock check (scratch spike, jlc_stock_check.py, 2026-07-21):

| # | Requirement | Standard / parts cap it exceeds | Resolution (ADR) | User flagged |
|---|---|---|---|---|
| T1 | XU316-1024-TQ128-I24 (C6938291) | JLC stock = **0** (expand lib listing exists) | plan: JLC global-sourcing/consign or Digi-Key + hand/consign assembly of the TQFP-128; archive shipped it as a designated consign line. Tension ADR due at recorder parts stage; NOT a late discovery | yes (final report) |
| T2 | FA-238 24MHz (C2650433) | JLC stock = **0** (matches archive's 2026-07-17 finding) | Digi-Key fallback (28k stock @ $0.44 on 2026-07-17) or JLC global sourcing; hand-solder line | yes (final report) |
| T3 | TCR2LF18 1.8V LDO (C150173) | JLC stock = **0** (was stocked 2026-07-17) | alternate-code / equivalent-LDO search at parts stage (SOT-25 1.8V 200mA class is dense); keep exact-MPN Digi-Key fallback | yes (final report) |
| T4 | Fab tier: XU316 TQFP-128 0.4mm pitch escape | 4L standard-via could not close (archive ADR-0008/0009) | expect 6-layer + JLC small-via 0.30/0.15 (cost ceiling raised: D-TIER ADR due at parts stage); doc itself says "6 preferred" | yes (final report) |

Positively verified in the same spike (stock >= need): PCM1865DBTR (1674),
USB4105-GF-A (3958), NC7NZ34K8X (1508), AP61102Z6-7 (455), XC6227C331PR-G
(268), MINISMDC050F-2 (34k), W25Q16JVSSIQ (102k), SHT40 (13.8k),
TPD4EUSB30DQAR (6k), AO3400A/AO3401A (basic, >397k).

## Log

### D1 — 2026-07-21 — user directive (within commission)
> ", lets use ethernet cable and ethernet connectors everywhere to interface them"
Impact: RJ45 jacks both ends; central keeps RJHSE-5384 x8 (6 populated);
custom-pinout NOT-ETHERNET labeling discipline.

### A1 — 2026-07-21 — assumption (not asked)
Assumed: condensation faithful to full Rev-A; archive supplies condensed-out
detail (same wording as pod A1). Escalate if the attached full text disagrees.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | ethernet connectors everywhere | user (P directive) | Log D1 |
| 0000 | two projects, pod first | agent | decisions/0000-scope-two-boards.md |
