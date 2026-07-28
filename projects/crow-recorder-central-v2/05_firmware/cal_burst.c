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
 * THE ACCEPTANCE CRITERION — CHANGED 2026-07-28, AND THIS IS WHY 1/12
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
 * -6 dB (duty 1/6, the previous value) satisfies the OLD criterion by
 * 0.52 dB and MISSES the new one by 3.48 dB. Duty 1/12 gives -11.7401 dB
 * nominal and satisfies the new criterion by 2.2372 dB. That is the change.
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
 * *** It WAS at 1/6. It is NOT at 1/12. Re-verified 2026-07-28,     ***
 * *** and the old conclusion is NOT carried forward.                ***
 * *********************************************************************
 * Two independent mechanisms break it, both measured, both in the
 * NON-conservative direction (they deliver LESS attenuation than the law):
 *
 * (a) L-R REGIME CHANGE. Integrating i' = (v - iR)/L with the SS14
 *     freewheel (exact per-step exponential, R = 15 coil + 1.28 cable,
 *     Vf = 0.45) over L = 10 uH .. 3 mH: at D = 1/6 every corner was AT
 *     LEAST as attenuated as the law (-6.02 .. -6.68 dB vs -6.021). At
 *     D = 1/12 the 3 mH corner returns -10.905 dB against the law's
 *     -11.740 — non-conservative by +0.835 dB. The 20.8 us pulse no longer
 *     lets the current build, so the long freewheel tail dominates the
 *     waveform and its fundamental content no longer tracks sin(pi*D).
 *
 * (b) GATE-RC DUTY BIAS — larger, and it was not anticipated anywhere in
 *     this design. R_bg1*C_bg = 4.70 us and (R_bg1||R_bg2)*C_bg = 4.65 us.
 *     Turn-ON waits only for the gate to CLIMB to Vgs(th) (0.65..1.45 V,
 *     i.e. 20..44 % of the 3.3 V drive) but turn-OFF waits for it to FALL
 *     from ~3.26 V all the way DOWN to Vgs(th) (56..80 % of the way). The
 *     lags are therefore ASYMMETRIC and the conduction window is
 *     STRETCHED, by +1.11 us (Vth 1.45) to +6.47 us (Vth 0.65):
 *
 *         Vth 0.65 V: t_on 1.03 us, t_off 7.51 us -> stretch +6.47 us
 *         Vth 1.05 V: t_on 1.80 us, t_off 5.33 us -> stretch +3.53 us
 *         Vth 1.45 V: t_on 2.72 us, t_off 3.83 us -> stretch +1.11 us
 *
 *     The stretch is an ABSOLUTE time, independent of the commanded pulse,
 *     so its FRACTIONAL cost grows as the duty shrinks: 5 % of the pulse at
 *     D = 1/2, but 31 % at D = 1/12. DETAIL_DESIGN documents this RC as an
 *     EMI slew-limiter ("softens the 4kHz burst edges"); nobody noticed it
 *     also biases the duty UPWARD, which matters only once duty is used to
 *     control LEVEL. That is new, and it is the dominant error term.
 *
 * COMBINED WORST CASE at D = 1/12, over L in {20u,100u,500u,3m} x Vth in
 * {0.65,1.05,1.45}: **-8.71 dB, not -11.74 dB. Slack +3.03 dB.**
 *
 *     criterion            nominal (law)      WORST CASE
 *     TYPICAL-curve unit   +2.2372 dB  PASS   -0.79 dB  *** STILL CLIPS ***
 *     minimum-spec unit    +6.2372 dB  PASS   +3.21 dB  PASS
 *
 * *** OPEN, AND THE USER'S CALL. D = 1/12 meets the new criterion
 * *** NOMINALLY and does NOT meet it under the worst-case model. The
 * *** smallest duty that meets it under worst case is D = 1/14 (+0.11 dB);
 * *** 1/16 gives +0.93 dB and 1/20 gives +2.41 dB. See the ladder below.
 * *** The open-loop uncertainty on this hardware is ~3 dB, which is LARGER
 * *** than the 2.24 dB criterion — so the level CANNOT be set open-loop to
 * *** the required accuracy and MUST be trimmed against a MEASUREMENT at
 * *** bring-up. The ladder is the trim path; measuring is not optional.
 *
 * MODEL SANITY (canon M1 — checker and checked share no method). The
 * datasheet's 150 mA "at rated voltage, 4000 Hz, 1/2 duty" is a MEASURED
 * number; volt-second balance on the same circuit is an ANALYTIC one:
 *     <i> = (5*D - Vf*(1-D)) / R = (2.5 - 0.225)/15 = 151.7 mA
 * They agree to 1.1 %. The circuit model is therefore not self-certified.
 *
 * TO MEASURE THE REAL LEVEL: a calibrated 1/4" mic at 10 cm on axis, or the
 * pod's own MK1 with the recorder as the meter, comparing D = 1/2 against
 * the shipped duty in the 4 kHz band. Raise CAL_BURST_DUTY_DEN until the
 * measured capsule level is <= 101.3 dB SPL. Scoping BEEP_RETURN at TP11
 * also reads the gate-RC stretch directly (compare the commanded pulse
 * against the actual conduction window) — that single measurement collapses
 * most of the ~3 dB uncertainty above.
 */

/* --- the drive level. NAMED, DERIVED ABOVE. Not a magic number. --------- */

/* Burst carrier. The CMT-8504's rated/resonant frequency (ds rev 1.04 p.1). */
#define CAL_BURST_FREQ_HZ 4000

/* Duty as an EXACT rational, so the timer math is integer.
 * 1/2 is the datasheet's characterisation condition, is the PRE-FIX value,
 * and is FORBIDDEN in the field — it clips the pod preamp (CAL-1).
 * 1/6 satisfied the OLD minimum-spec criterion and MISSES the current
 * TYPICAL-curve criterion by 3.48 dB. Do not go back to either. */
#define CAL_BURST_DUTY_NUM 1
#define CAL_BURST_DUTY_DEN 12

/* Trim floor. Raised 16 -> 24 when the gate-RC bias was characterised: the
 * OLD floor of 16 would have forbidden 1/14..1/20, which are exactly the
 * values that clear the typical unit under the worst case. At 1/24 the gate
 * still peaks at 2.94 V, clearing the AO3400A's 2.5 V Rdson spec point;
 * and beyond 1/24 each doubling of the denominator buys ~6 dB of NOMINAL
 * attenuation but only ~1.3 dB of WORST-CASE, so the model divergence
 * outgrows the benefit. Past ~1/37 the gate never reaches 2.5 V at all. */
#define CAL_BURST_DUTY_DEN_MIN 24

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
#define CAL_BURST_ATTEN_NOMINAL_DB (-11.7401)
#define CAL_BURST_ATTEN_WORST_DB (-8.71)

/* How much LESS attenuation the L-R corner (L = 3 mH, deep DCM, long
 * freewheel tail) delivers beyond what the gate-RC model alone predicts, at
 * this duty. From the exact-exponential integration described above. */
#define CAL_BURST_LR_CORNER_DB 0.75

/* AO3400A gate network and drive, for the stretch model. */
#define CAL_BURST_TAU_ON_US 4.70  /* R_bg1 1k * C_bg 4.7nF */
#define CAL_BURST_TAU_OFF_US 4.65 /* (R_bg1 || R_bg2 100k) * C_bg */
#define CAL_BURST_VDRV 3.3        /* XU316 IOT bank, 3V3 */
#define CAL_BURST_VTH_MIN 0.65    /* AO3400A Vgs(th) min — the worst corner */

/* Trim ladder — WORST-CASE numbers alongside the law, because the law is
 * not a bound here. "typ margin" is against the TYPICAL-curve unit (the
 * current criterion); positive clears. Pick by MEASUREMENT, not by taste.
 *   den   on-time    law dB    WORST dB   typ margin: law / WORST
 *    2   125.00 us    0.000     +0.006      -9.50   -9.51  <- PRE-FIX. FORBIDDEN.
 *    3    83.33 us   -1.249     -0.876      -8.25   -8.63
 *    4    62.50 us   -3.010     -2.354      -6.49   -7.15
 *    6    41.67 us   -6.021     -4.895      -3.48   -4.61  <- old value, MISSES
 *    8    31.25 us   -8.343     -6.698      -1.16   -2.80
 *   10    25.00 us  -10.200     -7.766      +0.70   -1.74
 *   12    20.83 us  -11.740     -8.712      +2.24   -0.79  <- SHIPPED DEFAULT
 *   14    17.86 us  -13.053     -9.616      +3.55   +0.11  <- first to clear WORST
 *   16    15.62 us  -14.195    -10.435      +4.69   +0.93
 *   20    12.50 us  -16.113    -11.917      +6.61   +2.41
 *   24    10.42 us  -17.686    -13.221      +8.18   +3.72  <- DUTY_DEN_MIN
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

    /* ---- THE SHIPPED ACCEPTANCE CRITERION (fatal): nominal, TYPICAL unit */
    const double margin_typ_nom = ceiling - (burst_typ + nom);
    printf("  %-46s %12.4f  (must be > 0)%s\n",
           "TYPICAL-unit margin, NOMINAL, dB", margin_typ_nom,
           margin_typ_nom > 0.0 ? "" : "   <== FAIL");
    if (!(margin_typ_nom > 0.0))
        fails++;

    /* ---- KNOWN-BAD, inline and always run: BOTH previous values must MISS
     * the new criterion. A gate that cannot fail is worthless (repo canon). */
    const double m_half = ceiling - (burst_typ + atten_law(0.5));
    const double m_sixth = ceiling - (burst_typ + atten_law(1.0 / 6.0));
    printf("  %-46s %12.4f  (must be < 0)%s\n",
           "KNOWN-BAD den=2 (pre-fix) typ margin, dB", m_half,
           m_half < 0.0 ? "" : "   <== FAIL");
    if (!(m_half < 0.0)) fails++;
    printf("  %-46s %12.4f  (must be < 0)%s\n",
           "KNOWN-BAD den=6 (old criterion) typ margin", m_sixth,
           m_sixth < 0.0 ? "" : "   <== FAIL");
    if (!(m_sixth < 0.0)) fails++;

    /* ---- the WORST-CASE model must stay declared and must not rot. If the
     * duty is retuned this fires and forces a re-derivation — deliberate,
     * and a one-line fix (update CAL_BURST_ATTEN_WORST_DB). */
    near("WORST-CASE attenuation (gate RC + L-R), dB", worst,
         CAL_BURST_ATTEN_WORST_DB, 0.02);
    const double margin_typ_worst = ceiling - (burst_typ + worst);
    const double margin_min_worst = ceiling - (burst_min + worst);
    printf("  %-46s %12.4f  %s\n", "TYPICAL-unit margin, WORST CASE, dB",
           margin_typ_worst,
           margin_typ_worst > 0.0 ? "(clears)" : "*** OPEN: DOES NOT CLEAR ***");
    printf("  %-46s %12.4f  %s\n", "minimum-spec margin, WORST CASE, dB",
           margin_min_worst, margin_min_worst > 0.0 ? "(clears)" : "   <== FAIL");
    if (!(margin_min_worst > 0.0))
        fails++;
    /* the worst case must be LESS attenuating than nominal, or it is inverted */
    if (!(worst > nom)) {
        printf("  worst-case model is not pessimistic vs nominal   <== FAIL\n");
        fails++;
    }

    /* ---- reachability: the gate must still fully enhance, and the duty
     * must sit inside the trim floor. */
    near("on-time at 4 kHz, us", 1e6 / CAL_BURST_FREQ_HZ * duty, 20.833, 1e-3);
    near("on-time in gate RC taus",
         (1e6 / CAL_BURST_FREQ_HZ * duty) / CAL_BURST_TAU_ON_US, 4.433, 1e-2);
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
    if (!fails && margin_typ_worst <= 0.0)
        printf("NOTE: the criterion is met NOMINALLY (+%.2f dB); under the"
               " WORST-CASE model\n      it is MISSED by %.2f dB. Open-loop"
               " uncertainty on this hardware is\n      ~%.1f dB, LARGER than the"
               " criterion itself. TRIM AGAINST A MEASUREMENT\n      at bring-up"
               " — den 14 is the first that clears worst case.\n",
               margin_typ_nom, -margin_typ_worst, worst - nom);
    return fails ? 1 : 0;
}
#endif /* CAL_BURST_SELFTEST */
