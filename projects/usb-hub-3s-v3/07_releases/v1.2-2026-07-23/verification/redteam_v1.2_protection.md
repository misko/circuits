# usb-hub-3s-v3 v1.2 — Fresh Zero-Context Red-Team (Discrete VBUS Protection)

- Date: 2026-07-23
- Scope: v1.2 discrete-protection re-architecture (drop TPS26631 eFuse -> enable-gated P-FET + PPTC polyfuse + TVS)
- Reviewer: fresh zero-context red-team agent, clean-room over projects/usb-hub-3s-v3/ only (commit b6a26b7), dispatched + held by the pipeline orchestrator.
- Verdict: **ORDER** — architecture approved, NO design P0. Both mandatory deep checks PASS (Q6 AON6403 carries 5A @ 0.11W / ~90C headroom; ENKILL-gated reverse-block CORRECT; OFF-state-only reverse-block is ADR-0002-accepted). DO-NOT-ORDER items were seal-stage verification (stale caches), since cleared.

---

Rich findings. Let me confirm two things: whether the Q6 PowerPAK PAD-GEOM/MISMATCH is a known-adjudicated pad-numbering artifact (v1.1 twin adjudications), and the exact M-BOM substitution direction on the caps.

Key correction: the *current* `fab/bom_jlc.csv` actually matches source (R13/R4=C5126242, 100uF=C84455, and the 10uF caps are correctly SEPARATED C77100/C77102). The M-BOM FAIL in `policy_audit.md` is itself STALE (cites old codes C90143/C137779/merged). And the PowerPAK PAD-GEOM is a known benign merged-paddle artifact already adjudicated. Let me re-run M-BOM fresh to confirm the current BOM is clean.

I have everything needed. Both deep checks are resolved with measured evidence, and I've separated the real issues from stale-cache artifacts. Final report below.

---

# Red-team review — usb-hub-3s-v3 v1.2 (commit b6a26b7)

**Scope:** clean-room, `projects/usb-hub-3s-v3/` only. Discrete USB-C VBUS protection chain re-architecture (eFuse → discrete). All findings traced independently from the exported netlist, board, and datasheets.

## VERDICT: architecture PASSES / no design P0 — but DO-NOT-ORDER the current artifacts until the P1 verify items clear

Both mandatory deep checks **PASS**. The discrete protection architecture is electrically sound and correctly netlisted (E-INV 24/24, DRC re-measured fresh = **0/0/0** at b6a26b7). There are **no P0 design defects.** The blockers to an actual order are all verify/seal-stage process items (stale twin, unconfirmed Extended-tier stock, stale cached build artifacts) — exactly the steps STATUS says are still pending.

---

## Deep check 1 — Q6 carries 5A within rating: **PASS (large margin)**

Traced from netlist: `Q6` = AON6403 (C2760089), pins 1/2/3=S→**PMID**, pin4=G→**QG**, pin5=D→**5VC**. Gate driven to GND by Q7 → **Vgs ≈ −5.3 V**.

- Datasheet (AON6403, read directly): 30 V / −85 A P-FET, **Rds(on) < 4.3 mΩ @ Vgs=−4.5 V** (< 3.1 mΩ @ −10 V); θJA 40 °C/W (55 max), θJC 1 °C/W; Tj,max 150 °C.
- I²R at 5 A: 5² × 4.3 mΩ = **0.108 W** (≈0.15 W with 125 °C Rds derating). Channel drop ≈ 21 mV.
- Junction rise: 0.15 W × 55 °C/W ≈ **8 °C → Tj ≈ 58 °C at 50 °C ambient.** ~90 °C headroom.
- SOA: an 85 A/30 V part at 5 V/5 A is trivially inside SOA.
- Copper (measured with pcbnew): 5 A path rides **pours**, not thin tracks — 5VC 344 mm² F.Cu / 285 mm² B.Cu, PMID 45/52 mm², VBUSC ~220/263 mm²; Q6↔F2 adjacent on F.Cu. R-THERM waiver on Q6.5 is legitimate (0.11 W needs no thermal vias).

The part is **massively over-rated** for the job. No thermal concern.

## Deep check 2 — off-state-only reverse block: **PASS (correctly designed)**

Netlist topology: `Q6` D=5VC / S=PMID → body diode (anode=D=5VC, cathode=S=PMID) **conducts 5VC→PMID forward, blocks PMID→5VC reverse**. `Q7` (BSS138) G=ENKILL, S=GND, D=QG. `R30` (100 k) **PMID→QG**.

- **ON (ENKILL high, ~12.6 V via R8/R17):** Q7 on → QG=GND → Vgs(Q6)=−5.3 V → Q6 on, 21 mV forward drop. ✓
- **OFF (SW1 grounds ENKILL):** Q7 off → R30 pulls QG to **PMID** → Vgs=0 → Q6 off → body diode blocks VBUSC→PMID→5VC back-feed. ✓
- **The key correct detail:** R30 pulls the gate to the **SOURCE (PMID)**, not to 5VC. In a reverse fault (PMID externally driven high, 5VC low) this holds Vgs≈0 relative to the highest terminal, keeping Q6 firmly OFF. Had R30 gone to 5VC, a reverse fault would give Vgs≈−5 V and **turn Q6 ON, defeating the block.** Netlist confirms R30.1=PMID. Q7's body diode (A=GND, K=QG) is reverse-biased in the fault and doesn't leak the gate.
- Genuine OFF-state reverse block; the ON-state limitation (channel bidirectional, bounded by polyfuse, ideal-diode explicitly declined) is honestly documented in ADR-0002. The 3S pack is in fact doubly protected — even if VBUSC back-feeds 5VC, the buck-C high-side body diode blocks 5VC→VIN (5 V < 12.6 V).

---

## Findings

### P1 — must resolve before ordering (verify/seal-stage)
1. **JLC twin is STALE / incomplete for the discrete chain.** `06_build/twin/` verified Q6 as **C404363 (AON6354)** — the board's Q6 is now **C2760089 (AON6403)**; **F2 (C6165170) and D5 (C140903) were never fetched/checked** (absent from the twin cache). The discrete chain is currently un-twin-verified. Re-run twin on the v1.2 BOM before order. (No evidence of a real defect — see P2 note on the PowerPAK artifact.)
2. **F2 + D5 are Extended-tier with unverified specs/stock.** F2 (SMD2920-700/16N, C6165170) 16 V/7 A-hold/Ri is UNVERIFIED in the sealed env; D5 (SMBJ6.0A, C140903) Extended-tier. Order-day stock + spec confirmation is mandatory (already flagged in part.yaml/ADR).
3. **Over-voltage coordination is materially weaker than v1.1 (user-accepted).** On a buck-HS-short (PMID→12.6 V), D5 clamps to ~8–10.3 V — **above the Pi's ~6 V ceiling** — and relies on the **PPTC F2 tripping** to end exposure. A PPTC trip is slow (not µs), and D5 (SMB, ~5 W cont.) must survive clamping tens of watts or fail-short to crowbar. SMBJ TVS typically fail short (safe), but this is a real downgrade from the eFuse's active OV cutoff. Documented/accepted in ADR-0002; flagging for awareness + first-power caution.
4. **F2 thermal-derating margin is thin.** 7 A hold → ~5.6 A @50 °C vs **5 A continuous** load = only 1.12× margin. At enclosure ambient >50 °C or with F2 self-heating / adjacent buck heat, nuisance-trip risk (Pi loses power). It's the best available part (6 A is worse); bench-verify at the real ambient.
5. **E-MARGIN passes but sits on the floor at the hot corner.** Gate PASSES (110 mΩ budget vs 100 mΩ floor) but assumes vout_min 5.18 V. The delivery path now includes F2 (PPTC), whose resistance **rises with load/temperature and is unregulated** (FB local-senses 5VC, upstream of Q6/F2). power_tree.yaml itself flags a quadruple-worst corner ~5.03 V → ~80 mΩ budget, less than a real 5 A e-marked cable + connectors. Bench-verify delivered connector voltage at 5 A hot vs the Pi UV (4.63 V).

### P2 — doc/build hygiene (regenerate/fix before seal)
6. **Stale cached build artifacts** (authoritative current artifacts — board, netlist, `fab/bom_jlc.csv`, E-INV, fresh DRC — are all consistent and correct):
   - `06_build/bom.csv` (grouped BOM) predates the discrete chain — missing Q6/Q7/F2/D5/R30 entirely.
   - `06_build/policy_audit.md` shows a **stale M-BOM FAIL** (cites old codes C90143/C137779, merged 10 µF). **I re-ran `bom_source_check` on the current `fab/bom_jlc.csv` → PASS** — the canon-M6 cap hazard is NOT present; C77100 (output) and C77102 (input) are correctly on separate rows. Regenerate policy_audit.
7. **power_tree.yaml E-OFF `off_control` text is stale.** It describes the removed v1.1 eFuse path (D6 EN_C→ENKILL coupling, "un-merged EN_C", U13 SHDN divider). The actual v1.2 netlist re-merges **both** buck EN pins (U2.4, U11.4) onto ENKILL with no D6/U13 — the E-INV file (#7) and ADR-0002 are correct; only the power_tree prose (and the quiescent_ua rationale) is wrong. Mechanism itself exists and works (SW1→ENKILL→both bucks + Q6 off); ~265 µA draw is ~correct.
8. **part.yaml role descriptions stale for the re-roled parts:** AON6403's `layout:`/`gotchas:` describe only the Q1 input-reverse role (D=VBAT_F/S=VIN) though C2760089 now also serves Q6 (D=5VC/S=PMID). BSS138's notes still describe Q7 as the "TPS26631 eFuse Q2 gate-pulldown" (G=DRV/D=B_GATE/S=IN_SYS) — actual Q7 is the ENKILL inverter (G=ENKILL/D=QG/S=GND). Pinouts are correct; only the role narratives are stale.
9. **Q6 twin PAD-GEOM/PAD-MISMATCH is a known benign artifact** (merged-drain PowerPAK paddle vs JLC split pads; copper regions coincide; ordered on v1.0). `twin_adjudications.yaml` already carries it — but under **C404363**; when twin re-runs with Q6=**C2760089**, move the Q6 refs to the C2760089 adjudication entry (currently only Q1).

### Confirmed good (no action)
- F2 Vmax 16 V > buck-fail-high PMID 12.6 V. ✓
- D5 standoff 6.0 V and Vbr(min) 6.67 V both > idle VBUSC 5.43 V → no nuisance conduction. ✓ D5 K=VBUSC / A=GND polarity correct.
- CC Rp R28/R29 = 10 kΩ to VBUSC → advertises 3 A source (Pi draws 5 A via PSU_MAX_CURRENT override, per ADR-0001). ✓
- Footprints correct: F2 Fuse_2920_7451Metric, D5 D_SMB, Q6/Q1 PowerPAK_SO-8_Single, Q7 SOT-23, R30 0603.
- Gates: E-TOPO (both rails BUCK, 7 A trunk), E-MARGIN, E-OFF, E-INV 24/24, DRC 0/0/0 — all re-run green.

**Bottom line for the orchestrator:** the discrete protection design is approved to proceed to seal — both mandatory deep checks pass and there is no design P0. Before the board is actually ordered, complete the seal-stage work: re-run the JLC twin on the v1.2 BOM (Q6/F2/D5 currently unverified), confirm F2+D5 order-day stock/specs, regenerate the stale cached artifacts, and correct the stale power_tree/part.yaml prose. Add a first-power caution on the OV path (P1-3) and bench-verify the 5 A hot delivery voltage and F2 hold margin (P1-4/5).
