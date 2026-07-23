# ADR-0002 — Discrete USB-C VBUS protection (drop the eFuse)

status: accepted
date: 2026-07-23
supersedes: the v1.1 TPS26631 eFuse cell (added in the v1.1 revision without its
  own ADR; recorded in journal/03_schematic_v1.1 + routing_v1.1)
relates: ADR-0001 (plain 5V/5A USB-C rail, Pi override — this ADR protects that rail)
decision-log: BRIEF.md A2/D2 (user decision)

## Context

The USB-C port delivers a plain 5V/5A rail to a Pi (ADR-0001). It must be
PROTECTED: over-current (short/overload), over-voltage (a buck-fail-high must not
reach the Pi), and reverse-current (a powered device on the port must not
back-feed the 3S pack — red-team RT-T4).

v1.1 met this with a **TPS26631 eFuse** (U13) + a reverse-current-blocking FET
pair + OVP/SHDN/dVdT/ILIM set passives. Two rounds of problems proved it was
**over-built for a 5V/5A Pi rail**:

1. **Routing wall.** The eFuse is a 20-pin HTSSOP whose IN_SYS pin sits mid-row in
   a fine-pitch west escape field; two pour-fed 5VC taps (IN_SYS + the FB sense)
   could not escape. Multiple KRT rolls + keepout/placement D-BACKs stalled the
   board at DRC 11/2/0 with unroutable taps (journal 04_board "STUCK").
2. **Two electrical ORDER-BLOCKERS (v1.1 DO-NOT-ORDER red-team).**
   - Post-eFuse FB runaway: sensing VBUSC (post-eFuse) let the buck integrator
     wind 5VC toward VIN when the eFuse limited/opened.
   - SHDN 5.5V abs-max: the 0.6-ratio 5VC divider put 7.56V on SHDN at a 12.6V
     buck-HS-short, destroying the pin.
   The v1.2 schematic fixed these (local-sense FB + SHDN clamp), but at the cost
   of yet more eFuse-support parts.

The eFuse's fancy features (adjustable current limit, input-OV cutoff with
auto-retry, soft-start, active reverse-current auto-block) exceed what a
Pi-DEDICATED 5V port needs — the Pi is the sole sink and has no independent 5V
source.

## Decision

**Drop the eFuse cell** (U13 + R31/R32 OVP + R33/R36 SHDN + C51 dVdT + C52 + the
D6/D7 control clamps) and protect VBUS with a **simple discrete chain**, reusing
the on-BOM Q6/Q7 FETs (a **USER decision** — not an ideal-diode controller):

```
5VC ─ Q6 (AON6403 P-FET, reverse-block, ENABLE-GATED) ─ PMID ─ F2 (PPTC polyfuse) ─ VBUSC ─ J5
                                                                          └─ D5 (TVS) ─ GND
```

- **Reverse-current / reverse-polarity — Q6 (AON6403 P-FET) + Q7 (BSS138):**
  Q6 orientation D=5VC / S=PMID puts its **body diode** blocking PMID→5VC. Q6 is
  **enable-gated**: Q7 inverts the master-enable ENKILL onto Q6's gate (QG), with
  R30 pulling QG to the source (PMID). Hub ON (ENKILL high) → Q7 on → QG low →
  Q6 on (low-drop forward). Master-OFF (ENKILL low) → Q7 off → QG floats to PMID
  → Q6 off → **body diode blocks a powered sink back-feeding the pack** (RT-T4, in
  the OFF state — the realistic case: a device plugged into a switched-off port).
  Vgs ≤ 5.4V ≪ 20V max → no gate Zener (unlike the 12.6V input Q1).
  **Accepted limitation:** this does NOT block reverse current while the port is
  actively ON (Q6 is on); a powered sink at higher-than-5VC while the hub runs is
  bounded by the polyfuse, not instantaneously blocked. An always-on ideal-diode
  controller was explicitly declined as unnecessary for a Pi-dedicated sink.
- **Over-current — F2 (PPTC polyfuse), resettable.** Also bounds sustained back-feed.
- **Over-voltage — D5 (TVS to GND), SECONDARY / best-effort (HONEST LIMITATION).** On
  a buck-fail-high (12.6V) D5 clamps at ~10.3V @Ipp and, with F2 upstream, draws
  current that eventually trips the polyfuse (a **crowbar**, not a fast deterministic
  cutoff). This is **NOT guaranteed protection against a sustained buck high-side
  short**: D5's clamp (~10.3V) is above the Pi's VBUS ceiling, and the F2 trip has
  finite time — during that window the Pi sees an over-voltage. **No claim is made
  that the Pi is protected against fail-high.** The chain reliably handles the cases
  it is designed for: short-circuit / overload (F2), reverse-feed in the OFF state
  (Q6 body diode). D5 is over-voltage *mitigation*, replacing the eFuse's OVP cutoff
  with a weaker, best-effort crowbar.

### Over-voltage strategy: Option 2 — discrete secondary protection (v1.3, BRIEF A3/D3)

The user DECIDED (Option 2) to KEEP this discrete chain as SECONDARY protection and
NOT add an active OVP (SCR crowbar / OVP controller) for this revision. Rationale:
the intended context is a **supervised prototype with a replaceable Pi** — the sink
is inexpensive and an operator is present, so a best-effort crowbar plus the required
bench-qualification (ORDER_README) is proportionate.

**Escalation boundary (verbatim):** "add active OVP if the system becomes unattended,
hard-access, carries valuable storage, or powers expensive SDR". If any of those
becomes true, this ADR must be revisited and an active/deterministic OVP designed in.

**Kept from v1.1:** buck-C FB on LOCAL 5VC (R12=4.12k → 5.352V; the runaway fix).
**Reverted:** buck-C EN re-merged to ENKILL (the eFuse-era FLT→EN_C un-merge + D6
coupling diode are gone — there is no per-buck fault flag in the discrete design).

## Part selection & derating

- **F2 = 7A-hold PPTC, 2920, 16V** (SMD2920-700/16N, LCSC C6165170). WHY 7A not 6A:
  the load is **5A CONTINUOUS**; a 6A-hold PPTC derates to ~4.8A @50 °C < 5A →
  nuisance-trip (the Pi loses power). 7A → ~5.6A @50 °C > 5A. The buck-C current
  limit (~7A) is above 5A, so it cannot gate the load below the hold either → the
  7A polyfuse is required. FOOTPRINT is 2920 (a 6A/16V hold does not exist in
  1812). Vmax 16V covers a buck-fail-high (PMID up to 12.6V). **The 16V rating +
  JLC stock of C6165170 are per parts-research but UNVERIFIED in the sealed build
  env → an order-day jlc_stock recheck is MANDATORY.** Fallback: 6A 2920L600/16MR-A
  (C3762416, confirmed) — but it nuisance-trips at 5A @50 °C (degraded).
- **D5 = SMBJ6.0A UNI-directional TVS, SMB** (v1.3: **C113976**, JLC catalog-verified
  UNIDIRECTIONAL DO-214AA/SMB, stock 74758). v1.2 used **C140903**, which JLC's live
  catalog lists as **BIDIRECTIONAL** (LRC SMB-FL) — a bidirectional part has no
  cathode, so the design's uni-directional cathode=VBUSC assumption was unverifiable
  against it (external-review finding). C140903 is now on the do_not_use list.
  Vwm 6.0V clears the 5.43V no-load VBUSC max (SMBJ5.0A rejected: 5V standoff <
  5.43V). Vclamp ~10.3V is above the Pi ceiling → this is SECONDARY protection, relying
  on the F2 trip to end the exposure (see the honest limitation above). Extended-tier
  → order-day recheck.

## Consequences

- **Routing: trivial.** All discrete parts are coarse (PowerPAK SO-8, SOT-23,
  2920, SMB) — no fine-pitch escape. KRT rolled 0 unconnected / 0 violations on
  the FIRST try; the board reached **DRC 0/0/0** with only bounded source fixes.
- **Part count 118 → 110.** Removed 9 (U13 + set-pins + D6/D7), added 1 (F2);
  Q6/Q7/R30/D5 re-roled.
- **E-INV** re-derived to assert the discrete chain (this ADR is cited by those
  invariants).
- Fab tier stays STANDARD (jlc_4layer_standard). Two Extended-tier parts (F2, D5)
  carry an order-day stock recheck (ORDER_README).
