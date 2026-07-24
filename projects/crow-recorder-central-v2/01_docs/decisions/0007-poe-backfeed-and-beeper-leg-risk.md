---
id: 0007
date: 2026-07-23
status: accepted
decided_by: >
  USER waiver carried from the sibling: crow-mic-pod-v2 ADR-0005 (decided_by
  USER, A1) accepted this exact hazard class — PoE Alt-B injection on RJ45
  contacts 4/5(+)/7/8(-) of the pair's custom 5V pinout — for the SAME closed,
  owner-cabled deployment. The RESUME/fix-pass directive orders the same
  posture here. Material-difference check (2026-07-23): this board's exposure
  is NOT worse than the pod's — the pod took 48V straight into an op-amp V+
  with ZERO series impedance (rated P0); here the path runs through a per-port
  PTC into the 5V rail (rated P1 by the same red-team), and this board adds
  per-port "NOT ETH 5V!" silk at all 8 jacks + the banner, which the pod
  could not fit. Same class, same deployment, equal-or-lesser severity ->
  the pod waiver's scope covers it.
---
# 0007 — PoE-injector backfeed + unfused beeper legs (accepted risk)

## Context (red-team P1#5 + P1#2-sub, 2026-07-23)
The RJ45 port bank carries a CUSTOM 5V audio pinout (brief G2). If a user plugs
a port into PoE infrastructure, an endspan injector can drive ~48V (mode B:
pins 4/5+, 7/8-) onto J*.4/7 — our P5VA_n +5V legs. The path 48V -> F_n PTC ->
5V rail exceeds the AP61102 vin_abs_max (6.5V) and every 5V-rail part. The
input TVS (D1, SMAJ5.0A) sits on VIN_RAW — the wrong side of Q1 to clamp a
rail-side injection. Sibling precedent: crow-mic-pod-v2 ADR-0005 carries the
same class as an accepted waiver. Separately, the beeper legs (J*.3
PLUS5V_BEEP / J*.6 BEEP_RETURN) have NO per-port PTC (audio +5V legs have
F1-F8): a beeper-pin short is cleared only by F_IN (2A input fuse) = a
whole-board outage instead of a one-port trip.

## Options
- Per-port OVP (TVS per port pair + bigger PTCs) — 16+ parts, real board area
  at all 8 ports; protects against an installation error the silkscreen now
  warns about at EVERY port ("NOT ETH 5V!" per-port + the banner, brief G14).
- Accept + label (CHOSEN, matching the pod-v2 discipline): the deployment is a
  closed crow-recorder installation, cabling is owner-controlled, every port is
  individually labeled non-Ethernet, and the fleet sibling accepted the same
  class with the same mitigations.

## Decision
Accepted risk, honestly documented:
1. PoE backfeed on P5VA/beep legs can damage the 5V rail. Mitigations: per-port
   silk warnings + banner; deployment is closed/owner-cabled. NOT protected
   electrically.
2. Beeper legs unfused per-port; FB_BEEP (BLM21PG600SN1D, 2A/25mohm — see
   02_parts) is a noise bead, not protection. A short = F_IN (2A) opens.

## v-next work order
- Add F_BEEP PTC (~1.1A hold, e.g. MINISMDC110F) in series with FB_BEEP.
- Evaluate one shared SMBJ5.0A on the P5VA distribution spine as cheap
  insurance (single part, clamps any port's injection before the rail).
