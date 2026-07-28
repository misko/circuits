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
 * microphone MK1 (pcbnew, sealed crow-mic-pod-v2 v1.3 board). At the
 * datasheet's >=100 dB SPL @ 10 cm the burst lands on the capsule at
 *
 *     100 dB + 20*log10(100.000 mm / 45.61798 mm)  =  106.8173 dB SPL
 *
 * The pod preamp (OPA1678, G = 1.5, VMID = 2.500 V from R4/R5 = 22k/22k)
 * runs out of LINEAR INPUT COMMON-MODE RANGE first — SBOS855E S6.7 gives
 * VCM = (V-)+0.5 .. (V+)-2 — at a worst case of mic sensitivity +3 dB and
 * V+ = 4.75 V (-5 %, which is the same instant the burst peaks):
 *
 *     worst-case ceiling  =  101.3144 dB SPL
 *     SHORTFALL           =    5.5028 dB     <- must be given back HERE
 *
 * The pod cannot fix this: its divider was measured unable to clear the
 * guaranteed spec by ANY value (best +0.86 dB, and the optimum runs the
 * OPPOSITE way from the audit's proposed 33k/18k). So the user's chosen
 * fix is a ~6 dB DRIVE REDUCTION AT CENTRAL. crow-mic-pod-v2 v1.3 stays
 * live and is NOT superseded. No copper, no BOM, no release changes.
 *
 * =====================================================================
 * WHY A DUTY CYCLE IS THE ONLY LEVER, AND WHY sin(pi*D)
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
 * resonance and rejects DC and the harmonics. A 1/6-duty square has an RMS
 * of only -4.8 dB but a FUNDAMENTAL of exactly -6.02 dB; the resonance
 * follows the latter.
 *
 * For a square drive of duty D into the coil, the fundamental is
 * proportional to sin(pi*D) — and this holds at BOTH ends of the unknown
 * inductance range, so the fix does not depend on a number the datasheet
 * never gives:
 *   L -> 0   : current = voltage/R, a duty-D square, fundamental
 *              (2V/pi/R)*sin(pi*D).
 *   L -> inf : continuous conduction, small triangular ripple of pk-pk
 *              D(1-D)(V+Vf)T/L; an asymmetric triangle's fundamental is
 *              (pk-pk/pi^2)*sin(pi*D)/(D(1-D)) = (V+Vf)T*sin(pi*D)/(pi^2 L).
 *              The D(1-D) cancels. Same law.
 * A numerical integration of i' = (v - iR)/L with the SS14 freewheel, over
 * L = 20 uH .. 3 mH, gives D=1/6 attenuations of -6.02 to -6.68 dB — always
 * AT LEAST the sin(pi*D) law's -6.02 dB. The law is a conservative bound.
 *
 * MODEL SANITY (canon M1 — checker and checked share no method). The
 * datasheet's 150 mA "at rated voltage, 4000 Hz, 1/2 duty" is a MEASURED
 * number; volt-second balance on the same circuit is an ANALYTIC one:
 *     <i> = (5*D - Vf*(1-D)) / R = (2.5 - 0.225)/15 = 151.7 mA
 * They agree to 1.1 %. The circuit model is therefore not self-certified.
 *
 * ELECTRICAL -> ACOUSTIC. A magnetic buzzer is a permanent-magnet-biased
 * coil driving a ferrous diaphragm, so force is LINEAR in current and
 * SPL(dB) = 20*log10(I1/I1_ref). The datasheet has NO SPL-vs-drive curve
 * (single trace, one drive level), so this mapping is ESTIMATED, not
 * specified. It is however the CONSERVATIVE estimate: every plausible
 * deviation delivers MORE reduction, not less — a diaphragm near its
 * excursion limit at rated drive compresses, so backing off gains more
 * than linearly; an unbiased reluctance device would be square-law
 * (-12 dB). Nothing physical makes it deliver LESS than -6.02 dB.
 * To MEASURE it: a calibrated 1/4" mic at 10 cm on axis, or the pod's own
 * MK1 with the recorder as the meter, D = 1/2 vs D = 1/6, 4 kHz band.
 *
 * =====================================================================
 * THE NUMBER, AND WHAT IT DOES NOT COVER
 * =====================================================================
 *   D = 1/6  ->  20*log10(sin(pi/6)) = 20*log10(0.5) = -6.0206 dB
 *   capsule  ->  106.8173 - 6.0206   =  100.7967 dB SPL
 *   ceiling                            101.3144 dB SPL
 *   CLEARS BY                            0.5178 dB
 *
 * Side effects, all benign: coil average current ~150 mA -> ~30-50 mA, so
 * the shared FET sees ~0.9 A -> ~0.2-0.3 A; pod 5V_BEEP cable IR drop
 * 0.19 V -> ~0.04 V; AOM-5024 capsule headroom to its own 110 dB THD<3 %
 * limit improves from 3.18 dB to 9.20 dB. Gate slew is unaffected: R_bg1*
 * C_bg = 4.7 us against a 41.667 us on-time (8.9 tau) and a 208.33 us
 * off-time (44.8 tau) — the FET still switches fully, both ways.
 *
 * *** WHAT 6 dB DOES NOT COVER — OPEN, FOR THE USER ***
 * CAL-1's 5.50 dB shortfall is computed from LS1's datasheet MINIMUM
 * (100 dB @ 10 cm). The datasheet's own TYPICAL response curve reads
 * ~104 dB at 3.9 kHz. A typical-output unit therefore puts 110.8173 dB on
 * the capsule and, even after -6.02 dB, still sits 3.48 dB OVER the
 * worst-case ceiling. -6 dB is the authorized fix for the recorded defect;
 * it is NOT proven sufficient for a loud unit. The level must be TRIMMED
 * AGAINST A MEASUREMENT at bring-up — use the ladder below and raise the
 * denominator until the measured capsule level is <= 101.3 dB SPL.
 * Do not exceed CAL_BURST_DUTY_DEN_MIN.
 */

/* --- the drive level. NAMED, DERIVED ABOVE. Not a magic number. --------- */

/* Burst carrier. The CMT-8504's rated/resonant frequency (ds rev 1.04 p.1). */
#define CAL_BURST_FREQ_HZ 4000

/* Duty as an EXACT rational, so the timer math is integer and the
 * attenuation is exact: sin(pi * 1/6) = 1/2 exactly = -6.0206 dB.
 * 1/2 (the datasheet's characterisation condition) is the PRE-FIX value and
 * is FORBIDDEN in the field — it clips the pod preamp by 5.50 dB (CAL-1). */
#define CAL_BURST_DUTY_NUM 1
#define CAL_BURST_DUTY_DEN 6

/* Trim floor. Below 1/16 the 41.667 us on-time has shrunk past ~3 gate time
 * constants (R_bg1 1k * C_bg 4.7nF = 4.7 us) and the AO3400A no longer fully
 * enhances — the FET starts spending the pulse in its linear region. */
#define CAL_BURST_DUTY_DEN_MIN 16

/* The ceiling this level exists to stay under, and the level it produces.
 * Units: dB SPL at the pod capsule MK1. Documentation for the bring-up
 * measurement; the self-test re-derives all three from first principles. */
#define CAL_BURST_CAPSULE_CEILING_DB 101.3144
#define CAL_BURST_CAPSULE_LEVEL_DB 100.7967
#define CAL_BURST_UNATTENUATED_DB 106.8173

/* Trim ladder — attenuation of the 4 kHz fundamental, 20*log10(sin(pi/den)),
 * and the resulting capsule level for a MINIMUM-output LS1. Pick by
 * MEASUREMENT, not by taste.
 *   den   duty      atten dB    capsule dB SPL
 *    2    50.000 %    0.000        106.817   <- PRE-FIX, clips. FORBIDDEN.
 *    3    33.333 %   -1.249        105.568
 *    4    25.000 %   -3.010        103.807
 *    5    20.000 %   -4.616        102.202
 *    6    16.667 %   -6.021        100.797   <- SHIPPED DEFAULT (CAL-1)
 *    8    12.500 %   -8.343         98.474
 *   10    10.000 %  -10.200         96.617
 *   12     8.333 %  -11.740         95.077   <- clears a TYPICAL-output unit
 *   16     6.250 %  -14.195         92.622   <- CAL_BURST_DUTY_DEN_MIN
 */

/* Ticks the gate must be HIGH per 4 kHz period, given the timer's period in
 * its own ticks. Integer, exact for any period divisible by the denominator;
 * rounds to nearest otherwise (a tick of error is < 0.01 dB at any realistic
 * timer rate — the XU316 100 MHz reference gives 25000 ticks per period). */
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

int main(void)
{
    /* Re-derive, from the physics, everything the #defines above assert.
     * Nothing below reads a constant to compute the value it then checks. */
    const double d_mm = hypot(33.0 - 74.0, 46.0 - 26.0);  /* LS1, MK1 (pcbnew) */
    const double burst = 100.0 + 20.0 * log10(100.0 / d_mm);

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
    const double atten = 20.0 * log10(sin(M_PI * duty));

    printf("cal_burst self-test (CAL-1, crow-mic-pod-v2 <-> crow-recorder-central-v2)\n");
    near("|LS1-MK1| mm", d_mm, 45.61798, 5e-5);
    near("burst at capsule, dB SPL", burst, CAL_BURST_UNATTENUATED_DB, 5e-4);
    near("pod mic S at 3k9 load, mV/Pa", S * 1e3, 80.680, 5e-3);
    near("worst-case input ceiling, dB SPL", ceiling, CAL_BURST_CAPSULE_CEILING_DB, 5e-4);
    near("shortfall to give back, dB", burst - ceiling, 5.5028, 5e-4);
    near("attenuation at the shipped duty, dB", atten, -6.0206, 5e-4);
    near("capsule level after, dB SPL", burst + atten, CAL_BURST_CAPSULE_LEVEL_DB, 5e-4);

    /* THE POINT OF THE WHOLE FILE: the shipped duty must clear the ceiling. */
    const double margin = ceiling - (burst + atten);
    printf("  %-46s %12.4f  (must be > 0)%s\n", "MARGIN vs the pod input ceiling, dB",
           margin, margin > 0.0 ? "" : "   <== FAIL");
    if (!(margin > 0.0))
        fails++;

    /* and it must be reachable by the gate, and inside the trim floor */
    near("on-time at 4 kHz, us", 1e6 / CAL_BURST_FREQ_HZ * duty, 41.667, 1e-3);
    near("on-time in gate RC (1k * 4.7nF) taus",
         (1e6 / CAL_BURST_FREQ_HZ * duty) / 4.7, 8.865, 1e-2);
    if (CAL_BURST_DUTY_DEN > CAL_BURST_DUTY_DEN_MIN) {
        printf("  duty denominator %d exceeds the trim floor %d   <== FAIL\n",
               CAL_BURST_DUTY_DEN, CAL_BURST_DUTY_DEN_MIN);
        fails++;
    }

    /* The integer timer helper must land within ONE TICK of the exact duty,
     * and that quantization must be acoustically invisible. 25000 ticks is
     * the XU316's 100 MHz reference at 4 kHz; 1/6 of it is not an integer,
     * so this is the real rounding case, not a convenient one. */
    const int p = 25000;
    const int on = cal_burst_on_ticks(p);
    near("cal_burst_on_ticks(25000), ticks", on, p * duty, 1.0);
    near("...and its duty error, dB", 20.0 * log10(sin(M_PI * on / p) / sin(M_PI * duty)),
         0.0, 1e-3);

    /* KNOWN-BAD: 1/2 duty is the PRE-FIX value and must NOT clear the
     * ceiling. A gate that cannot fail is worthless (repo canon). */
    const double atten_half = 20.0 * log10(sin(M_PI * 0.5));
    const double margin_half = ceiling - (burst + atten_half);
    printf("  %-46s %12.4f  (must be < 0)%s\n",
           "KNOWN-BAD 1/2 duty margin, dB", margin_half,
           margin_half < 0.0 ? "" : "   <== FAIL");
    if (!(margin_half < 0.0))
        fails++;

    printf(fails ? "\nFAIL: %d\n" : "\nPASS (0 failures)\n", fails);
    return fails ? 1 : 0;
}
#endif /* CAL_BURST_SELFTEST */
