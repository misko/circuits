# Revision checklist

Every revision passes this before it is tagged. A revision that will be
RELEASED must additionally pass the release gate at the bottom.

## Gates (mechanical — no judgement)
- [ ] `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity`
      → 0 violations, 0 unconnected, 0 missing footprints
- [ ] `03_src/audit_board.py` → PASS (placement/pad invariants)
- [ ] rules regenerate byte-identical from `03_src/rules/nets.yaml` (no hand-edits)
- [ ] BOM ↔ `02_parts/` parity (every used part has a datasheet + facts on file)
- [ ] netlist node-for-node parity after any schematic regeneration

## Judgement (a human or a fresh-context agent)
- [ ] every net >1A walked end-to-end for copper cross-section
- [ ] every 2-pad polarized part: pad 1's net checked against `02_parts/*/part.yaml`
      (diodes, LEDs, electrolytics, AND connectors — this is invisible to DRC)
- [ ] 3D/render review: connector bodies vs mounting holes, silk collisions
- [ ] `01_docs/CHANGELOG.md` entry written
- [ ] anything surprising captured as an ADR in `01_docs/decisions/`

## Release gate (only when ordering)
- [ ] release inputs clean (`git_dirty: false`, scope `projects/<board>/ + skills/` via `release_git_dirty.py <board>` — a dirty sibling board does not block)
- [ ] tagged
- [ ] stock re-verified TODAY (not from cache)
- [ ] `07_releases/<ver>-<date>/` written with MANIFEST + verification evidence
- [ ] fab options in ORDER_README match the board (layers, via tier)

- [ ] BRIEF.md: every acceptance criterion `met` (with evidence link) or `dropped` citing a user D#/Q# — never release with an `unmet` criterion
- [ ] BRIEF.md prompt hash verifies (`sed -n "/prompt-verbatim-begin/,/prompt-verbatim-end/p" 01_docs/BRIEF.md | sed "1d;\$d" | sha256sum`)

- [ ] JLC twin gate: `jlc_twin.py` exits 0 with the project adjudications file — zero unadjudicated MIRRORED/PAD-MISMATCH findings; twin_report.csv copied into the release verification/

- [ ] Fresh-context pin review: `pin_audit.py` dossiers generated; independent agents (no session context) reviewed every active part per `pin-review-protocol.md`; verdicts in the release verification/pin_review.md with ZERO unresolved FAILs

## Bring-up (first power, once per board build — NOT a release gate)

- [ ] **TP11 gate-RC stretch measurement (CAL-1). NORMATIVE — do this before
      the calibration burst is trusted, and before anyone tightens the duty.**

  **Why.** The calibration burst level is capped by the *pod's* preamp input
  ceiling (CAL-1, see `ARCHITECTURE.md`). The only lever is the duty cycle of
  `BEEP_GATE`, and at the shipped duty of 1/20 the gate RC (`R_bg1`·`C_bg` =
  4.70 µs) stretches the actual conduction window by an estimated **+6.19 µs —
  49 % of the 12.50 µs commanded pulse.** That stretch is the single dominant
  uncertainty in the whole chain (+4.20 dB of the level) and **it has never
  been measured on real hardware.**

  **Procedure.**
  1. Power the board; drive `BEEP_GATE` with the shipped duty (12.50 µs
     commanded on-time at 4 kHz — `cal_burst_on_ticks()`).
  2. Scope **CH1** on the XU316 GPIO pin (`U1.122`, or the `R_bg1` end of the
     gate net) — this is the **commanded** pulse.
     Scope **CH2** on **`TP11` (`BEEP_RETURN`)** — this is the **actual**
     conduction window: TP11 sits on the FET drain, held low while `Q2`
     conducts and rising to ~5 V + Vf when it stops.
  3. Measure CH2's low-time, subtract CH1's high-time. **That difference is
     the stretch.** Expect +0.8…+6.2 µs (model worst corner +6.19 µs at
     `Vgs(th)` = 0.65 V).
  4. Record the measured stretch, with the board serial, in
     `01_docs/journal/verify.md`.

  **What this measurement LICENSES.** Once the stretch is known for the real
  parts, the `Vgs(th)` 0.65–1.45 V sweep collapses to a single number and the
  **+4.20 dB open-loop uncertainty collapses with it. The duty may then be
  tightened back toward 1/14–1/16 WITH EVIDENCE**, recovering ~2–4 dB of burst
  level and far-pod SNR. Until it is measured, **1/20 stands** — the extra
  margin is the price of not knowing. **Do not tighten the duty on the
  strength of the model alone.**

- [ ] Acoustic cross-check (independent of the above — it grades the acoustic
      half, not the electrical half): calibrated ¼″ mic at 10 cm on axis, or a
      pod's own MK1 with the recorder as the meter, comparing D = 1/2 against
      the shipped duty in the 4 kHz band. **Acceptance: measured capsule level
      ≤ 101.3 dB SPL.** If higher, raise `CAL_BURST_DUTY_DEN` per the ladder in
      `05_firmware/cal_burst.c`; floor is `CAL_BURST_DUTY_DEN_MIN` = 36.
