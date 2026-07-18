# BRIEF — crow-array-pod

This board is part of the crow-array commission: the authoritative
verbatim brief, parse (P1-P8), Q/A (A1-A3) and decision register live in
../crow-array/01_docs/BRIEF.md (source sha 21e54984...). This file carries
board-local decisions only.

## Decision register (board-local)

- D3 (2026-07-18): mandatory input-protection ADR = decisions/0001:
  ESD (TPD2E2U06) at pod cable entry POPULATED; PTC overcurrent stays at
  the CENTRAL end per the system doc (split documented); no pod fuse; no
  series reverse diode (noise cost > risk; labeling + central limit).
- D4 (2026-07-18): board outline = the 1551WY drawing's MAXIMUM PCB,
  94.5x44.5mm with R6.25 concave corner cutouts and Ø2.7 holes on the
  75.00x35.00 boss pattern (decisions/0003). The "~50x35" notion cannot
  reach the enclosure's bosses; full length also maximizes mic-transducer
  separation (§3A).
- D5 (2026-07-18): TPD2E2U06 on the AUDIO pair is POPULATED (the doc calls
  it optional): outdoor stake-mounted pods, handled charged; the doc's own
  §4 mandates entry ESD; $0.35. See decisions/0001.
- D6 (2026-07-18): cable termination = 8-pos 3.5mm screw terminal
  (KF128L-3.5-8P class, Phoenix PT land pattern), terminal n = T568B pin n,
  hand-solder uncoded line (JLC THT = consign-only); mic = 2.54mm 2-pin
  pads for short leads (capsule 2s solder limit). decisions/0003.
- D7 (2026-07-18): CM choke (WE-SL2 footprint) + shield-bond pad (TP6 +
  R15 to GND) UNPOPULATED per A3; audio pair bridged by 0R R13/R14 so the
  choke can be fitted later by removing two jumpers.
- D8 (2026-07-18): clamp = dual SMA footprint, SS14 flyback populated,
  SMAJ6.0A TVS empty (A3; decisions/0002); R12 0R = the doc's series pads.
  Gain stays single-value 10k/20k (doc table); gain-change table lives in
  README + ORDER_README instead of dual footprints.
- D10 (2026-07-18): CMT-8504-100-SMT-TR IS in the JLC catalog
  (C22359707, exact MPN): coded for machine assembly instead of the
  expected hand-solder line. Stock is thin (182 on 2026-07-18 vs 10
  needed) - order-day re-check mandatory; Digi-Key hand-solder fallback
  stays in ORDER_README.
- D9 (2026-07-18): op-amp powered from the raw 5V rail (local 100n+10u);
  the 100R RC-filtered 5VF feeds only mic bias + midpoint divider
  (sub-mA), keeping the filter drop at ~75mV while the bias string gets
  the clean rail. PSRR of the OPA1678 covers the rest.
