---
id: 0005
date: 2026-07-23
status: accepted
supersedes: none
amends: [0001, 0003]
decided_by: USER (A1, BRIEF.md — relayed by the fix-pass coordinator)
---
# 0005 — PoE power-injection hazard: ACCEPTED WAIVER (controlled deployment)

## Context — the hazard the 4-lens red-team found (P0-A / P0-B)

The RJ45-everywhere directive (ADR-0003) put a bare, standards-compliant
8P8C jack on the pod carrying a CUSTOM non-Ethernet power/audio pinout.
Two of this board's custom power assignments alias EXACTLY onto the IEEE
802.3af/at Power-over-Ethernet "Alternative B" (spare-pair) convention,
at the same fixed polarity PoE uses:

| RJ45 contacts | This board's net | 802.3af/at Alt-B |
|---|---|---|
| 4, 5 | **5V_AUDIO** (pod supply, → U1 pin 8 V+) | **+V (PSE)** |
| 7, 8 | **GND_AUDIO** | **−V (PSE)** |

- **P0-A (injection into V+).** 5V_AUDIO is ONE net = {J1.4, J1.5, U1.8
  (V+), R1, R4, C7–C10, TP1} with ZERO series impedance between the RJ45
  contacts and the op-amp supply pin (confirmed in the exported netlist,
  net code 1). A PoE switch doing passive/legacy/forced injection on that
  port drives U1 V+ to 44–57 V DC. OPA1678IDR abs-max `vs_max = 40 V`
  (`02_parts/OPA1678IDR/part.yaml`) — exceeded by 10–42 %. Destroys U1,
  the 5 V-rated decoupling caps, and possibly the mic-bias node.
- **P0-B (sustained conduction of D1).** Mode-A PoE (+V on 1,2 / −V on 3,6,
  i.e. onto AUDIO_P/AUDIO_N) forces the TPD2E2U06 ESD array (D1) — a
  pulse-rated SOT-553 — into continuous conduction: ≈(48−9.7)×0.35 A ≈ 13 W
  into a <2 mm part → thermal failure / burn hazard in an outdoor enclosure.
- **P1-E (reverse-crimp), folded in.** The custom cable is hand-crimped, so
  4/5 could be swapped with 7/8 at a punch-down jig, putting V+ below V− on
  U1 (abs-max ordering violation). Same class of exposure, same mitigation.

The root cause is a hazard-analysis GAP, not a wiring error: ADR-0003
analysed only PHY-signal-voltage-on-AUDIO and 5 V backfeed INTO a switch
port; ADR-0001 delegated rail protection to "the central's protection …
here". NEITHER considered a switch INJECTING power into the pod — the
dominant real-world hazard, because PoE switches are common in exactly the
outdoor/security/sensor infrastructure a crow-array would share a rack with.

## Options considered

1. **PoE-defeat network** — series overvoltage clamp (<40 V TVS) + PPTC
   resettable fuse on 5V_AUDIO, or a reverse-blocking / OV crowbar.
   REJECTED for this rev: adds a protection stage + re-layout the passive
   pod was explicitly scoped to avoid; the fuse/clamp still does not make
   an RJ45 safe to plug into a switch (Mode-A into AUDIO survives the
   5V_AUDIO clamp), so it mitigates but does not eliminate.
2. **Break the PoE alias** — move 5V_AUDIO off contacts 4/5/7/8 in a respin.
   REJECTED for this rev: breaks the shared cable contract with the sibling
   CENTRAL board (ARCHITECTURE.md interface table) — a coordinated two-board
   change, out of scope for this fix pass.
3. **Keyed / non-RJ45 connector** — the only TRUE lockout. REJECTED by the
   RJ45-everywhere directive (ADR-0003), unchanged.
4. **ACCEPT the risk with a documented deployment constraint** (CHOSEN, A1).

## Decision (USER, A1)

The PoE-injection risk is **ACCEPTED WITH DOCUMENTED SIGN-OFF**. This is a
CONTROLLED DEPLOYMENT: the pod is **NEVER plugged into Ethernet/PoE
infrastructure**. It mates ONLY with the sibling CENTRAL recorder's
non-PoE, custom-pinout ports, over the custom-crimped Cat5e home-run. The
mitigation is administrative + physical, not electrical:

- the mandatory **"NOT ETHERNET — CUSTOM 5V AUDIO PINOUT"** silk banner +
  full pinout legend, now placed ADJACENT to J1 (ADR-0003 amended);
- connector/cable **keying discipline** — the whole array uses the same
  custom cable; no standard Ethernet patch cable is ever introduced;
- the deployment is **fixed and controlled** (installed once, not field-
  patched into shared racks).

**NO protection network is added. NO connector re-pin is done.** The op-amp
and ESD array are left directly on the aliased contacts, exactly as the
red-team measured.

## Residual risk (stated plainly, not hidden)

If — despite the labeling — the pod IS ever plugged into a PoE switch or a
mis-crimped cable energises V+ below V−, **U1 and D1 will be destroyed**
(and D1 may fail as a burn/smoke hazard in an outdoor enclosure). This
outcome is ACCEPTED for this controlled deployment. A future rev that must
survive uncontrolled infrastructure needs option 1 or option 2 above — this
waiver does not close that door, it scopes it out for the current build.

## Consequences

- The ORDER_README carries the exact PoE-warning line + the deployment
  constraint as a first-class order-day note (not buried).
- ADR-0001 decision 5 (reverse polarity) is amended to reference this waiver
  for the power-injection + reverse-crimp cases it had conflated with
  "wrong device plugged in".
- ADR-0003's hazard analysis is amended to add the power-INJECTION vector.
- No netlist / topology change ⇒ no new electrical invariant; the waiver is
  a deployment constraint, machine-unverifiable by construction. The
  silk-adjacency requirement it leans on IS checked (render review + the
  functional-silk gate).
