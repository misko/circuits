/* cal_burst.c — calibration-transducer burst drive level (CENTRAL end).
 *
 * PURE LOGIC. No MCU header, no register touched. The XU316 hardware shell
 * calls cal_burst_on_ticks() to program its 4 kHz timer; everything that
 * decides HOW LOUD the burst is lives here, host-testable before silicon.
 * Build the self-test with `make test` (see README.md).
 *
 * =====================================================================
 * BINDING CROSS-BOARD CONSTRAINT — READ BEFORE CHANGING ANY NUMBER HERE
 * =====================================================================
 * This board's beep drive is bounded ABOVE by the preamp input ceiling of
 * the SIBLING board, crow-mic-pod-v2. Raising the level breaks the pod.
 * Defect CAL-1, crow-mic-pod-v2/08_reviews/DISPOSITIONS.md +
 * 2026-07-27_v1.3_adversarial-audit_first-principles.md, re-derived in
 * 2026-07-28_v1.3_fix-verification_cal1.md and again here.
 *
 * The pod carries LS1 (CMT-8504-100-SMT-TR) 45.61798 mm from its own
 * microphone MK1 (pcbnew, sealed crow-mic-pod-v2 v1.3 board):
 *
 *     stimulus = SPL(10 cm) + 20*log10(100.000 mm / 45.61798 mm)
 *              = SPL(10 cm) + 6.8173 dB
 *
 * The pod preamp (OPA1678, G = 1.5, VMID = 2.500 V from R4/R5 = 22k/22k)
 * runs out of LINEAR INPUT COMMON-MODE RANGE first — SBOS855E S6.7 gives
 * VCM = (V-)+0.5 .. (V+)-2 — at a worst case of mic sensitivity +3 dB and
 * V+ = 4.75 V (-5 %, which is the same instant the burst peaks):
 *
 *     worst-case ceiling = 101.3144 dB SPL at the capsule
 *
 * The pod cannot fix this: its divider was measured unable to clear the
 * guaranteed spec by ANY value (best +0.86 dB, and the optimum runs the
 * OPPOSITE way from the audit's proposed 33k/18k). So the fix is a DRIVE
 * REDUCTION AT CENTRAL. crow-mic-pod-v2 v1.3 stays live and is NOT
 * superseded. No copper, no BOM, no release changes on either board.
 *
 * =====================================================================
 * THE ACCEPTANCE CRITERION — CHANGED 2026-07-28, AND THIS IS WHY 1/20
 * =====================================================================
 * CAL-1 as filed sized the shortfall against LS1's datasheet MINIMUM
 * output (>=100 dB @ 10 cm). That is the wrong end of the tolerance for a
 * CLIPPING problem: the unit that clips is a LOUD one, not a quiet one.
 * The datasheet's own TYPICAL response curve (rev 1.04 p.3) reads ~104 dB
 * at 3.9 kHz. USER DECISION 2026-07-28: the criterion is now
 * "clears a unit on the datasheet's TYPICAL curve", not "clears minimum
 * spec". The two shortfalls:
 *
 *     minimum-spec unit  100 dB @10cm -> 106.8173 dB -> shortfall  5.5028 dB
 *     TYPICAL-curve unit 104 dB @10cm -> 110.8173 dB -> shortfall  9.5029 dB
 *                                                       ^^^^^^^^^^^^^^^^^^^
 *                                                       the binding number
 *
 * Three values have now been superseded against this criterion, each for a
 * different reason — the history matters because each step was a real error:
 *   1/2   the pre-fix value. Clips by 9.50 dB. FORBIDDEN.
 *   1/6   satisfied the OLD minimum-spec criterion (+0.52 dB); misses the
 *         TYPICAL-curve one by 3.48 dB.
 *   1/12  satisfies the TYPICAL criterion NOMINALLY (+2.24 dB) but misses it
 *         by 0.79 dB once the gate-RC bias below is costed.
 *   1/20  SHIPPED. -16.1134 dB nominal, -11.9165 dB worst case, and it
 *         satisfies the criterion under the WORST-CASE model by +2.4136 dB.
 * The self-test asserts the WORST-CASE form, so all three superseded values
 * fail it as always-run inline fixtures.
 *
 * =====================================================================
 * WHY A DUTY CYCLE IS THE ONLY LEVER
 * =====================================================================
 * The hardware offers NO analog level control. Measured from the SEALED
 * v1.7 netlist (source/crow_recorder_central_v2.net):
 *
 *   PLUS5V_BEEP  11 nodes: FB_BEEP.2 (bead off the 5V rail, ~0 ohm DC),
 *                C_BEEP.1 (47uF), TP12, and pin 3 of ALL EIGHT RJ45s.
 *                No series resistor. No regulator. Fixed 5 V.
 *   BEEP_RETURN  10 nodes: pin 6 of ALL EIGHT RJ45s, TP11, and Q2.3 —
 *                ONE AO3400A low-side FET for every pod (BRIEF D1).
 *   BEEP_GATE     2 nodes: U1.122 (XU316 GPIO) and R_bg1.1. Nothing else.
 *
 * So the ONLY reachable level control is the GPIO WAVEFORM, i.e. this file.
 *
 * MODEL — the acoustic output follows the 4 kHz FUNDAMENTAL of the coil
 * current, not its RMS and not its average. Evidence, not assumption: the
 * CMT-8504 datasheet rev 1.04 p.3 FREQUENCY RESPONSE CURVE is a sharp
 * resonance peaking ~104 dB at ~3.9 kHz, standing ~15 dB above the 2-3 kHz
 * shelf. A resonator is a narrowband filter: it passes the component AT
 * resonance and rejects DC and the harmonics.
 *
 * Electrical->acoustic is ESTIMATED, not specified (the datasheet has NO
 * SPL-vs-drive curve — one trace, one drive level). SPL is taken linear in
 * fundamental coil current, which is the CONSERVATIVE choice: a diaphragm
 * near its excursion limit at rated drive compresses (backing off gains
 * MORE than linearly) and an unbiased reluctance device would be
 * square-law. Nothing physical delivers LESS reduction than linear.
 *
 * *********************************************************************
 * *** sin(pi*D) IS **NOT** A CONSERVATIVE BOUND AT THIS DUTY.       ***
 * *** Re-verified from scratch at EVERY retune (1/6, 1/12, 1/20) —  ***
 * *** never extrapolated, because term (a) below is NOT MONOTONIC   ***
 * *** in duty and extrapolating it is exactly the mistake the       ***
 * *** 1/6 -> 1/12 carry-forward made. At 1/20 the law under-states  ***
 * *** the delivered level by +4.197 dB.                             ***
 * *********************************************************************
 * Two mechanisms break it, both measured, both in the NON-conservative
 * direction (they deliver LESS attenuation than the law):
 *
 * (a) L-R REGIME CHANGE — and it is NOT MONOTONIC IN DUTY, which is exactly
 *     why each retune re-runs the sweep instead of extrapolating. Integrating
 *     i' = (v - iR)/L with the SS14 freewheel (exact per-step exponential,
 *     R = 15 coil + 1.28 cable, Vf = 0.45) over L = 10 uH .. 3 mH at the
 *     COMMANDED duty:
 *         D = 1/6   every corner conservative (-6.02..-6.68 vs -6.021)
 *         D = 1/12  3 mH corner -10.905 vs -11.740  -> +0.835 NON-CONSERVATIVE
 *         D = 1/20  every corner conservative again, worst slack -0.087 dB
 *     So at the SHIPPED duty this term is benign. It re-enters only through
 *     (b): the gate stretch moves the EFFECTIVE duty back into the 7-11 %
 *     region where the 3 mH corner misbehaves, worth +0.75 dB.
 *
 * (b) GATE-RC DUTY BIAS — the DOMINANT term, and it was not anticipated
 *     anywhere in this design. R_bg1*C_bg = 4.70 us and
 *     (R_bg1||R_bg2)*C_bg = 4.65 us. Turn-ON waits only for the gate to CLIMB
 *     to Vgs(th) (0.65..1.45 V, 20..44 % of the 3.3 V drive) but turn-OFF
 *     waits for it to FALL from the gate peak all the way DOWN to Vgs(th)
 *     (56..80 % of the way). The lags are ASYMMETRIC, so the conduction
 *     window is STRETCHED. At D = 1/20 (12.50 us commanded, gate peak
 *     3.069 V):
 *
 *         Vth 0.65 V: t_on 1.03 us, t_off 7.22 us -> +6.19 us  (+3.450 dB)
 *         Vth 1.05 V: t_on 1.80 us, t_off 4.99 us -> +3.19 us  (+1.954 dB)
 *         Vth 1.45 V: t_on 2.72 us, t_off 3.49 us -> +0.77 us  (+0.514 dB)
 *
 *     The stretch is an ABSOLUTE time, so its FRACTIONAL cost grows as the
 *     duty shrinks — and it now DOMINATES the whole error budget:
 *
 *         D = 1/2  : +6.53 us =  5.2 % of the pulse
 *         D = 1/12 : +6.47 us = 31.1 % of the pulse
 *         D = 1/20 : +6.19 us = 49.5 % OF THE PULSE
 *
 *     Nearly half the conduction window at the shipped duty is gate-RC
 *     artefact, not commanded drive. DETAIL_DESIGN documents this RC purely
 *     as an EMI slew-limiter ("softens the 4kHz burst edges"); nobody noticed
 *     it also biases the duty UPWARD, which matters only once duty is used to
 *     control LEVEL. THIS IS WHAT THE TP11 MEASUREMENT IS FOR.
 *
 * COMBINED WORST CASE at D = 1/20, over L = 10 uH .. 3 mH x Vth in
 * {0.65,1.05,1.45}: **-11.9165 dB, not -16.1134 dB. Slack +4.197 dB.**
 *
 *     criterion            nominal (law)      WORST CASE
 *     TYPICAL-curve unit   +6.6105 dB  PASS   +2.4136 dB  PASS
 *     minimum-spec unit   +10.6105 dB  PASS   +6.4136 dB  PASS
 *
 * *** THE CRITERION IS NOW MET UNDER THE WORST-CASE MODEL, not merely
 * *** nominally — which is why the self-test's FATAL assertion is the
 * *** WORST-CASE typical-unit margin, and why 1/2, 1/6 and 1/12 all fail it.
 * *** 1/20 was chosen over 1/14 (the least value that clears, +0.11 dB)
 * *** because THE RISK IS ASYMMETRIC: clipping destroys the timing
 * *** reference, a low level only costs SNR, and the open-loop uncertainty
 * *** (+4.20 dB) is still LARGER than the criterion. What remains open is
 * *** not the margin but the MODEL: the stretch has never been measured on
 * *** real hardware. See the TP11 bring-up step below.
 *
 * MODEL SANITY (canon M1 — checker and checked share no method). The
 * datasheet's 150 mA "at rated voltage, 4000 Hz, 1/2 duty" is a MEASURED
 * number; volt-second balance on the same circuit is an ANALYTIC one:
 *     <i> = (5*D - Vf*(1-D)) / R = (2.5 - 0.225)/15 = 151.7 mA
 * They agree to 1.1 %. The circuit model is therefore not self-certified.
 *
 * =====================================================================
 * TP11 BRING-UP MEASUREMENT — NORMATIVE. Do this once per board build.
 * =====================================================================
 * Also written up as a bring-up step in 01_docs/CHECKLIST.md and
 * 05_firmware/README.md, because a person doing bring-up does not read .c
 * files. PURPOSE: the gate-RC stretch is HALF the conduction window at this
 * duty and has never been measured. Measuring it collapses the dominant
 * uncertainty term.
 *
 *   1. Power the board. Drive BEEP_GATE with the shipped duty
 *      (cal_burst_on_ticks, 12.50 us commanded on-time at 4 kHz).
 *   2. Scope CH1 on the XU316 GPIO pin (U1.122, or the R_bg1 end of the gate
 *      net) = the COMMANDED pulse. Scope CH2 on TP11 (BEEP_RETURN) = the
 *      ACTUAL conduction window: TP11 sits at the FET drain, so it is pulled
 *      low while Q2 conducts and rises to ~5 V + Vf when it stops.
 *   3. MEASURE the actual low-time on CH2 and subtract the CH1 high-time.
 *      That difference IS the stretch. Record it. Expect +0.8 to +6.2 us;
 *      the model's worst corner is +6.19 us at Vgs(th) = 0.65 V.
 *   4. Record it in 01_docs/journal/verify.md with the board serial.
 *
 * WHAT THE MEASUREMENT LICENSES — say this plainly, because it is the whole
 * point: once the stretch is KNOWN for the real parts, the Vgs(th) sweep
 * collapses from a 3.0 dB spread to a single number, the +4.20 dB open-loop
 * uncertainty collapses with it, and THE DUTY MAY BE TIGHTENED BACK TOWARD
 * 1/14..1/16 WITH EVIDENCE (recovering ~2-4 dB of burst level and far-pod
 * SNR). Until it is measured, 1/20 stands: the extra margin is the price of
 * not knowing. Do NOT tighten the duty on the strength of the model alone.
 *
 * ALSO WORTH MEASURING (independent, and it grades the acoustic half rather
 * than the electrical half): a calibrated 1/4" mic at 10 cm on axis, or the
 * pod's own MK1 with the recorder as the meter, comparing D = 1/2 against
 * the shipped duty in the 4 kHz band. Acceptance: measured capsule level
 * <= 101.3 dB SPL. If it is higher, raise CAL_BURST_DUTY_DEN using the
 * ladder below; the floor is CAL_BURST_DUTY_DEN_MIN.
 */

/* --- the drive level. NAMED, DERIVED ABOVE. Not a magic number. --------- */

/* Burst carrier. The CMT-8504's rated/resonant frequency (ds rev 1.04 p.1). */
#define CAL_BURST_FREQ_HZ 4000

/* Duty as an EXACT rational, so the timer math is integer.
 * 1/2 is the datasheet's characterisation condition, is the PRE-FIX value,
 * and is FORBIDDEN in the field — it clips the pod preamp (CAL-1).
 * 1/6 satisfied the OLD minimum-spec criterion and MISSES the current
 * TYPICAL-curve criterion. 1/12 met it only NOMINALLY and missed it under
 * the worst-case model by 0.79 dB. Do not go back to any of the three.
 *
 * WHY 1/20 AND NOT 1/14 (the least value that "clears"): THE RISK IS
 * ASYMMETRIC. Clipping DESTROYS the timing reference outright; a low level
 * only costs SNR, and the local path still sits ~77 dB above the mic's own
 * self-noise. With the open-loop uncertainty (+4.20 dB here) still LARGER
 * than the criterion, 1/14's +0.11 dB is a rounding error against a model
 * that has already moved 3 dB once. 1/20 buys +2.41 dB of REAL worst-case
 * margin while the uncertainty stays open. Tighten it back only WITH
 * EVIDENCE — see the TP11 bring-up measurement below. */
#define CAL_BURST_DUTY_NUM 1
#define CAL_BURST_DUTY_DEN 20

/* Trim floor, RE-DERIVED at 1/20. It is set by the one hard physical limit:
 * the gate must still reach the AO3400A's 2.5 V Rdson spec point inside the
 * commanded pulse. Vg_peak = 3.3*(1-exp(-t_on/4.70us)) crosses 2.5 V at
 * t_on = 6.660 us, i.e. den = 37.5; 36 is the clean value below it (2.547 V).
 *
 * RETRACTION, measured 2026-07-28: an earlier revision of this file set the
 * floor at 24 and justified it by claiming the worst case "saturates" beyond
 * that (~1.3 dB per doubling against 6 dB nominal). That was WRONG. Measured
 * over 1/20 -> 1/40 the NOMINAL gains 5.99 dB and the WORST CASE gains
 * 5.24 dB — they track within ~0.75 dB per doubling. Deeper duties keep
 * working; the binding limit is the gate, not a saturation. */
#define CAL_BURST_DUTY_DEN_MIN 36

/* The ceiling this level exists to stay under, and the levels it produces.
 * Units: dB SPL at the pod capsule MK1. The self-test re-derives all of
 * these from first principles; none is copied from the audit. */
#define CAL_BURST_CAPSULE_CEILING_DB 101.3144
#define CAL_BURST_BURST_MIN_SPEC_DB 106.8173  /* LS1 at ds MINIMUM 100 dB */
#define CAL_BURST_BURST_TYPICAL_DB 110.8173   /* LS1 on the ds TYPICAL curve */
#define CAL_BURST_SHORTFALL_TYPICAL_DB 9.5029 /* <- the binding requirement */

/* Delivered attenuation of the 4 kHz fundamental at the shipped duty.
 * NOMINAL is the sin(pi*D) law. WORST is the measured combined bound —
 * gate-RC stretch at Vgs(th) = 0.65 V PLUS the L-R corner term below.
 * These are NOT the same number and the gap is the whole finding. */
#define CAL_BURST_ATTEN_NOMINAL_DB (-16.1134)
#define CAL_BURST_ATTEN_WORST_DB (-11.9165)

/* How much LESS attenuation the L-R corner (L = 3 mH, deep DCM, long
 * freewheel tail) delivers beyond what the gate-RC model alone predicts.
 * From the exact-exponential integration. NOTE it is evaluated at the
 * EFFECTIVE (gate-stretched) duty, not the commanded one — which is why it
 * is the same +0.75 dB at commanded 1/12 and 1/20: both land the effective
 * duty in the same 7-11 % region where the 3 mH corner runs
 * non-conservative. At the commanded duty 1/20 the ideal-switch L-R sweep is
 * CONSERVATIVE at every L (worst slack -0.087 dB) — the deviation enters
 * only through the stretch. */
#define CAL_BURST_LR_CORNER_DB 0.75

/* AO3400A gate network and drive, for the stretch model. */
#define CAL_BURST_TAU_ON_US 4.70  /* R_bg1 1k * C_bg 4.7nF */
#define CAL_BURST_TAU_OFF_US 4.65 /* (R_bg1 || R_bg2 100k) * C_bg */
#define CAL_BURST_VDRV 3.3        /* XU316 IOT bank, 3V3 */
#define CAL_BURST_VTH_MIN 0.65    /* AO3400A Vgs(th) min — the worst corner */

/* Trim ladder — WORST-CASE numbers alongside the law, because the law is
 * not a bound here. "typ margin" is against the TYPICAL-curve unit (the
 * current criterion); positive clears. Pick by MEASUREMENT, not by taste.
 *   den   on-time   gate pk    law dB   WORST dB   typ margin: law / WORST
 *    2   125.00 us   3.300 V    0.000     -0.030     -9.50   -9.47  <- PRE-FIX, FORBIDDEN
 *    6    41.67 us   3.300 V   -6.021     -4.895     -3.48   -4.61  <- superseded
 *   12    20.83 us   3.261 V  -11.740     -8.712     +2.24   -0.79  <- superseded (nominal only)
 *   14    17.86 us   3.222 V  -13.053     -9.616     +3.55   +0.11  <- least that clears
 *   16    15.62 us   3.181 V  -14.195    -10.435     +4.69   +0.93
 *   20    12.50 us   3.069 V  -16.113    -11.917     +6.61   +2.41  <- SHIPPED DEFAULT
 *   24    10.42 us   2.940 V  -17.686    -13.221     +8.18   +3.72
 *   28     8.93 us   2.806 V  -19.018    -14.407     +9.80   +4.90
 *   32     7.81 us   2.674 V  -20.174    -15.506    +10.98   +6.00
 *   36     6.94 us   2.547 V  -21.194    -16.468    +12.05   +6.97  <- DUTY_DEN_MIN
 *  (40     6.25 us   2.427 V  -- gate BELOW the 2.5 V Rdson spec point)
 */

/* Ticks the gate must be HIGH per 4 kHz period, given the timer's period in
 * its own ticks. Integer, exact for any period divisible by the denominator;
 * rounds to nearest otherwise (a tick of error is < 0.01 dB at any realistic
 * timer rate — the XU316 100 MHz reference gives 25000 ticks per period).
 * NOTE: this is the COMMANDED window. The gate RC stretches the ACTUAL
 * conduction window by +1.1..+6.5 us; see the model above. */
int cal_burst_on_ticks(int period_ticks)
{
    return (period_ticks * CAL_BURST_DUTY_NUM + CAL_BURST_DUTY_DEN / 2)
           / CAL_BURST_DUTY_DEN;
}

/* ---------------------------------------------------------------------- */
#ifdef CAL_BURST_SELFTEST
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

static int fails;

static void near(const char *what, double got, double want, double tol)
{
    int bad = fabs(got - want) > tol;
    printf("  %-46s %12.4f  (want %.4f +/- %g)%s\n", what, got, want, tol,
           bad ? "   <== FAIL" : "");
    if (bad)
        fails++;
}

/* the sin(pi*D) law — NOMINAL only, NOT a bound at this duty */
static double atten_law(double duty)
{
    return 20.0 * log10(sin(M_PI * duty));
}

/* gate peak reached during a commanded pulse of the given duty */
static double gate_peak(double duty)
{
    const double on_us = 1e6 / CAL_BURST_FREQ_HZ * duty;
    return CAL_BURST_VDRV * (1.0 - exp(-on_us / CAL_BURST_TAU_ON_US));
}

/* attenuation with the gate-RC stretched conduction window, at a given Vth */
static double atten_gate(double duty, double vth)
{
    const double period_us = 1e6 / CAL_BURST_FREQ_HZ;
    const double on_us = period_us * duty;
    const double t_on = -CAL_BURST_TAU_ON_US * log(1.0 - vth / CAL_BURST_VDRV);
    const double t_off = -CAL_BURST_TAU_OFF_US * log(vth / gate_peak(duty));
    return atten_law((on_us + (t_off - t_on)) / period_us);
}

int main(void)
{
    /* Re-derive, from the physics, everything the #defines above assert.
     * Nothing below reads a constant to compute the value it then checks. */
    const double d_mm = hypot(33.0 - 74.0, 46.0 - 26.0);  /* LS1, MK1 (pcbnew) */
    const double spread = 20.0 * log10(100.0 / d_mm);
    const double burst_min = 100.0 + spread;
    const double burst_typ = 104.0 + spread;              /* ds TYPICAL curve */

    /* pod mic at ITS board load: -24 dB re 1V/Pa spec'd at RL=2k2, loaded 3k9 */
    const double S = pow(10.0, -24.0 / 20.0) * (3900.0 / (3900.0 + 2200.0))
                     / (2200.0 / (2200.0 + 2200.0));
    const double G = 1.0 + 10e3 / 20e3;          /* pod stage A */
    const double vplus = 4.75, h = 0.8;          /* -5 % rail, SBOS855E VO */
    const double vm = vplus * 22e3 / (22e3 + 22e3);
    const double s_hot = S * pow(10.0, 3.0 / 20.0);   /* mic tolerance +3 dB */
    double vpk = (vplus - 2.0) - vm;             /* SBOS855E S6.7 VCM (V+)-2 */
    if (vm - 0.5 < vpk) vpk = vm - 0.5;          /*                  (V-)+0.5 */
    if ((vm - h) / G < vpk) vpk = (vm - h) / G;
    if (((vplus - h) - vm) / G < vpk) vpk = ((vplus - h) - vm) / G;
    const double ceiling = 20.0 * log10((vpk / s_hot) / sqrt(2.0) / 20e-6);

    const double duty = (double)CAL_BURST_DUTY_NUM / CAL_BURST_DUTY_DEN;
    const double nom = atten_law(duty);
    const double worst = atten_gate(duty, CAL_BURST_VTH_MIN) + CAL_BURST_LR_CORNER_DB;

    printf("cal_burst self-test (CAL-1, crow-mic-pod-v2 <-> crow-recorder-central-v2)\n");
    printf("  criterion: clears a unit on the ds TYPICAL curve"
           " (CHANGED 2026-07-28)\n\n");
    near("|LS1-MK1| mm", d_mm, 45.61798, 5e-5);
    near("burst, minimum-spec LS1, dB SPL", burst_min, CAL_BURST_BURST_MIN_SPEC_DB, 5e-4);
    near("burst, TYPICAL-curve LS1, dB SPL", burst_typ, CAL_BURST_BURST_TYPICAL_DB, 5e-4);
    near("pod mic S at 3k9 load, mV/Pa", S * 1e3, 80.680, 5e-3);
    near("worst-case input ceiling, dB SPL", ceiling, CAL_BURST_CAPSULE_CEILING_DB, 5e-4);
    near("SHORTFALL vs the TYPICAL unit, dB",
         burst_typ - ceiling, CAL_BURST_SHORTFALL_TYPICAL_DB, 5e-4);
    near("nominal attenuation at shipped duty, dB", nom, CAL_BURST_ATTEN_NOMINAL_DB, 5e-4);

    /* ---- the WORST-CASE model must stay declared and must not rot. If the
     * duty is retuned this fires and forces a re-derivation — deliberate,
     * and a one-line fix (update CAL_BURST_ATTEN_WORST_DB). */
    near("WORST-CASE attenuation (gate RC + L-R), dB", worst,
         CAL_BURST_ATTEN_WORST_DB, 0.02);

    /* ---- THE SHIPPED ACCEPTANCE CRITERION (fatal), PROMOTED at duty 1/20:
     * the TYPICAL-curve unit must clear under the WORST-CASE model, not
     * merely nominally. At 1/12 this was unsatisfiable and the nominal model
     * was the fatal one with the worst case recorded OPEN; 1/20 makes the
     * strong form reachable, so the strong form is what is asserted. */
    const double margin_typ_worst = ceiling - (burst_typ + worst);
    const double margin_min_worst = ceiling - (burst_min + worst);
    const double margin_typ_nom = ceiling - (burst_typ + nom);
    printf("  %-46s %12.4f  (must be > 0)%s\n",
           "TYPICAL-unit margin, WORST CASE, dB", margin_typ_worst,
           margin_typ_worst > 0.0 ? "" : "   <== FAIL");
    if (!(margin_typ_worst > 0.0))
        fails++;
    printf("  %-46s %12.4f  (must be > 0)%s\n",
           "minimum-spec margin, WORST CASE, dB", margin_min_worst,
           margin_min_worst > 0.0 ? "" : "   <== FAIL");
    if (!(margin_min_worst > 0.0))
        fails++;
    printf("  %-46s %12.4f  (informational)\n",
           "TYPICAL-unit margin, nominal, dB", margin_typ_nom);
    /* the worst case must be LESS attenuating than nominal, or it is inverted */
    if (!(worst > nom)) {
        printf("  worst-case model is not pessimistic vs nominal   <== FAIL\n");
        fails++;
    }

    /* ---- KNOWN-BAD, inline and always run: ALL THREE superseded values must
     * MISS the criterion under the same worst-case model. A gate that cannot
     * fail is worthless (repo canon). The L-R corner term is held constant
     * across these — it is exact only near the shipped duty, but it is the
     * smaller term and including it is the pessimistic direction. */
    static const int bad_dens[] = {2, 6, 12};
    static const char *bad_why[] = {"pre-fix", "old criterion", "nominal only"};
    for (unsigned k = 0; k < sizeof bad_dens / sizeof *bad_dens; k++) {
        const double d = 1.0 / bad_dens[k];
        const double m = ceiling - (burst_typ + atten_gate(d, CAL_BURST_VTH_MIN)
                                    + CAL_BURST_LR_CORNER_DB);
        char label[64];
        snprintf(label, sizeof label, "KNOWN-BAD den=%d (%s) typ margin",
                 bad_dens[k], bad_why[k]);
        printf("  %-46s %12.4f  (must be < 0)%s\n", label, m,
               m < 0.0 ? "" : "   <== FAIL");
        if (!(m < 0.0))
            fails++;
    }

    /* ---- reachability: the gate must still fully enhance, and the duty
     * must sit inside the trim floor. */
    near("on-time at 4 kHz, us", 1e6 / CAL_BURST_FREQ_HZ * duty, 12.500, 1e-3);
    near("on-time in gate RC taus",
         (1e6 / CAL_BURST_FREQ_HZ * duty) / CAL_BURST_TAU_ON_US, 2.660, 1e-2);
    /* the stretch is now HALF the pulse — assert it, because it is the term
     * the TP11 bring-up measurement exists to pin down */
    {
        const double on_us = 1e6 / CAL_BURST_FREQ_HZ * duty;
        const double t_on = -CAL_BURST_TAU_ON_US
                            * log(1.0 - CAL_BURST_VTH_MIN / CAL_BURST_VDRV);
        const double t_off = -CAL_BURST_TAU_OFF_US
                             * log(CAL_BURST_VTH_MIN / gate_peak(duty));
        near("gate-RC stretch at Vth min, us", t_off - t_on, 6.19, 0.02);
        near("...as a % of the commanded pulse", 100.0 * (t_off - t_on) / on_us,
             49.5, 0.5);
    }
    const double vpk_gate = gate_peak(duty);
    printf("  %-46s %12.4f  (must be >= 2.5, AO3400A Rdson spec)%s\n",
           "gate peak at shipped duty, V", vpk_gate,
           vpk_gate >= 2.5 ? "" : "   <== FAIL");
    if (!(vpk_gate >= 2.5))
        fails++;
    if (CAL_BURST_DUTY_DEN > CAL_BURST_DUTY_DEN_MIN) {
        printf("  duty denominator %d exceeds the trim floor %d   <== FAIL\n",
               CAL_BURST_DUTY_DEN, CAL_BURST_DUTY_DEN_MIN);
        fails++;
    }

    /* ---- the integer timer helper must land within ONE TICK of the exact
     * duty, and that quantization must be acoustically invisible. 25000 is
     * the XU316's 100 MHz reference at 4 kHz; 1/12 of it is not an integer,
     * so this is the real rounding case. The tolerance is 0.01 dB, which is
     * physically motivated rather than arbitrary: it is ~300x below the
     * ~3 dB open-loop uncertainty established above and far below anything
     * measurable acoustically. NOTE the sensitivity GREW with the retune —
     * sin(pi*D) is steeper at small D, so the same +-1 tick costs 0.0006 dB
     * at duty 1/6 and 0.0014 dB at 1/12. Still negligible; it will not stay
     * negligible forever if the duty keeps shrinking. */
    const int p = 25000;
    const int on = cal_burst_on_ticks(p);
    near("cal_burst_on_ticks(25000), ticks", on, p * duty, 1.0);
    near("...and its duty error, dB",
         atten_law((double)on / p) - atten_law(duty), 0.0, 1e-2);

    printf(fails ? "\nFAIL: %d\n" : "\nPASS (0 failures)\n", fails);
    if (!fails)
        printf("NOTE: criterion met under the WORST-CASE model (+%.2f dB), not merely\n"
               "      nominally (+%.2f dB). Open-loop uncertainty is still +%.2f dB and\n"
               "      the gate-RC stretch (%.0f%% of the pulse) has NEVER BEEN MEASURED.\n"
               "      Do the TP11 bring-up measurement (01_docs/CHECKLIST.md); it\n"
               "      LICENSES tightening the duty back toward 1/14..1/16 with evidence.\n",
               margin_typ_worst, margin_typ_nom, worst - nom,
               100.0 * (-(-CAL_BURST_TAU_ON_US
                          * log(1.0 - CAL_BURST_VTH_MIN / CAL_BURST_VDRV))
                        + (-CAL_BURST_TAU_OFF_US
                           * log(CAL_BURST_VTH_MIN / gate_peak(duty))))
               / (1e6 / CAL_BURST_FREQ_HZ * duty));
    return fails ? 1 : 0;
}
#endif /* CAL_BURST_SELFTEST */
