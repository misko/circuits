# journal — 00_commission

## 2026-07-27 — start
- did: scaffolded `projects/pluto-cal-switch/` from the pcb-design skill's OWN
  canonical templates (15 contracts.md, 03_src config seeds). No config copied
  from a sibling project — the clean-room coupling rule.
- result: 15 contracts placed; 03_src seeded with floorplan/route/rebuild +
  rules/{nets,power_tree,electrical_invariants,assembly}.yaml.
- next: BRIEF with the verbatim prompt, then the D-SPEC sourcing spike.

## 2026-07-27 — iterate 1 (commission Q&A)
- did: asked 4 fact-lock questions, then 3 follow-ups after the answers
  surfaced a CONTRADICTION and an unanswered item.
- result: locked frequency 70 MHz-6 GHz; 30 dB = TOTAL TX->each RX; micro-USB
  5 V; USB **and** GPIO control; ON = loopback.
  THE CONTRADICTION: the verbatim brief says GPIO ON = loopback, the follow-up
  answer said "30db only when gpio off". Did NOT guess — asked, and the user
  confirmed the brief stands (A3). Recorded as spec tension T2, because a
  silent guess here inverts the entire control logic.
  THE RELAXATION THAT ISN'T ONE: the user relaxed length-matching ("as long as
  distance is precisely known, it will be software offset") then added "but
  lets try to make them the exact same if possible". Read together that is not
  a loose tolerance, it is a DOCUMENTATION requirement: build symmetric, and
  PUBLISH the measured electrical length of each run plus the delta, because a
  software offset is only as good as the number it is handed. Recorded as D4;
  it becomes a release artifact, not just a routing goal.
- next: fact-lock is complete except TX drive level (flagged open).

## 2026-07-27 — iterate 2 (D-SPEC sourcing spike)
- did: consulted `references/proven-parts.yaml` FIRST, per D-ESC.
- result: **31 ledger entries, ZERO RF parts.** No switch, splitter,
  attenuator, SMA, or USB MCU — the ledger is entirely power/USB from the
  hub and recorder families. This board is a new CLASS for the repo, so
  every spec-critical function needs live research; nothing can be copied.
- next: fanned out 6 concurrent research agents (SPDT switch, 2-way splitter,
  attenuator, USB control MCU, SMA connector, micro-USB + 3V3 rail), each
  followed by an ADVERSARIAL refutation pass. Verdict per function must be
  sourceable / costlier_tier / not_sourceable BEFORE any architecture is drawn.
