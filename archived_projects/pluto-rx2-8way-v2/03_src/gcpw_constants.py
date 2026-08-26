#!/usr/bin/env python3
"""DERIVE the constant set for a CONDUCTOR-BACKED COPLANAR WAVEGUIDE, and the
ground-stitch bound that follows from it.

Tuple this set is identified by (rf-design.md 4A "THE RULE"):
    stackup       JLC04161H-7628, h = 0.2104 mm top prepreg, er = 4.4, t = 0.035
    w             0.360 mm
    cross-section CONDUCTOR-BACKED COPLANAR WAVEGUIDE, s = 0.2005 mm both sides,
                  BARE (no solder-mask term -- see rf-design.md 4A(iii))
    method        quasi-static conformal mapping, Ghione/Naghed-Wolff CBCPW form

Everything printed is [DERIVED]. The only [MEASURED] inputs are w and s, from
`line_type.py` on the saved board; h, er and t are DECLARED stackup fields.

Usage: gcpw_constants.py [--w 0.36] [--s 0.2005] [--h 0.2104] [--er 4.4]
                         [--t 0.035] [--f 6.0]

DECLARED BACKEND GAP (canon M8; 03_src/contracts.md makes any *.py beyond
audit_board/bom_seed a STOPGAP that must name its gap and the schema that
would replace it).
THE GAP: this repo carries 32 gates and NONE grades an RF cross-section or a
ground-stitch spacing. `rf-design.md` sec 6 ranked a via-fence gate and
REJECTED it on the premise that "all three fleet values are already
conservative"; measured, that premise was half wrong -- this board sits outside
its own bound by 2.56x -- and the rejection has since been amended but not
reversed. So the check lives here.
THE CONFIG SCHEMA THAT WOULD REPLACE IT: `rules/nets.yaml` already carries
`length_match.<G>.phase.{t_pd_ps_per_mm, f_ghz, stackup, cross_section}`; a
shared gate needs only that `cross_section` key (declared 2026-07-30) plus a
`fence: {bound_mm, band_mm, arms: []}` block, and it would then grade every
board in this family from source alone.
THIS IS THE SECOND BOARD TO NEED IT -- pluto-rx2-8way v1 carried the same
measurement -- which by the contract's own rule TRIGGERS MANDATORY PROMOTION
into the shared backend. Promotion is REPORTED to the caller and NOT done
here: this agent's partition is `projects/pluto-rx2-8way-v2/` only.
"""
import math
import sys


def opt(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


W = opt("--w", 0.360)
S = opt("--s", 0.2005)
H = opt("--h", 0.2104)
ER = opt("--er", 4.4)
T = opt("--t", 0.035)
F = opt("--f", 6.0)
C = 299.792458  # mm*GHz


def kk(k):
    """K(k)/K'(k) -- Hilberg's closed form, exact to ~3e-6 over 0<k<1."""
    kp = math.sqrt(max(0.0, 1.0 - k * k))
    if k <= 1.0 / math.sqrt(2.0):
        return math.pi / math.log(2.0 * (1.0 + math.sqrt(kp)) / (1.0 - math.sqrt(kp)))
    return math.log(2.0 * (1.0 + math.sqrt(k)) / (1.0 - math.sqrt(k))) / math.pi


def cbcpw(w, s, h, er):
    """Ghione / Naghed-Wolff conductor-backed CPW, zero conductor thickness."""
    a, b = w / 2.0, w / 2.0 + s
    k1 = a / b
    k3 = math.tanh(math.pi * a / (2.0 * h)) / math.tanh(math.pi * b / (2.0 * h))
    r1, r3 = kk(k1), kk(k3)
    q = (1.0 / r1) * r3                      # K'(k1)K(k3) / K(k1)K'(k3)
    ee = (1.0 + er * q) / (1.0 + q)
    z0 = (60.0 * math.pi / math.sqrt(ee)) / (r1 + r3)
    return ee, z0, k1, k3, r1, r3


def cpw_thickness_delta(w, t):
    """Gupta/Garg/Bahl/Bhartia CPW finite-thickness increment."""
    return (1.25 * t / math.pi) * (1.0 + math.log(4.0 * math.pi * w / t))


ee, z0, k1, k3, r1, r3 = cbcpw(W, S, H, ER)
t_pd = math.sqrt(ee) / C * 1000.0            # ps/mm
lam_g = C / (F * math.sqrt(ee))
degmm = 360.0 * F * t_pd / 1000.0

print("=" * 74)
print("A. THE LINE  --  conductor-backed coplanar waveguide, zero-thickness CM")
print("=" * 74)
print(f"  inputs   w = {W} mm [MEASURED]   s = {S} mm [MEASURED]")
print(f"           h = {H} mm   er = {ER}   t = {T} mm   f = {F} GHz  [DECLARED]")
print(f"  a = w/2 = {W/2:.5f}   b = w/2+s = {W/2+S:.5f}")
print(f"  k1 = a/b                       = {k1:.6f}   K/K'(k1) = {r1:.6f}")
print(f"  k3 = tanh(pi a/2h)/tanh(pi b/2h) = {k3:.6f}   K/K'(k3) = {r3:.6f}")
print(f"  q  = K'(k1)K(k3)/K(k1)K'(k3)   = {(1/r1)*r3:.6f}")
print(f"  eps_eff = (1 + er q)/(1 + q)   = {ee:.4f}")
print(f"  Z0      = 60pi/sqrt(ee)/(r1+r3)= {z0:.3f} ohm")
print(f"  t_pd    = sqrt(ee)/c           = {t_pd:.4f} ps/mm")
print(f"  lambda_g @ {F} GHz              = {lam_g:.4f} mm")
print(f"  phase                          = {degmm:.4f} deg/mm")

d = cpw_thickness_delta(W, T)
we, se = W + d, S - d
if se > 0:
    ee_t, z0_t, *_ = cbcpw(we, se, H, ER)
    print(f"\n  [sensitivity] finite-thickness correction, Gupta et al.:")
    print(f"    delta = 1.25t/pi (1 + ln(4 pi w/t)) = {d:.5f} mm")
    print(f"    w_e = {we:.5f}  s_e = {se:.5f}  ->  eps_eff {ee_t:.4f}, Z0 {z0_t:.3f} ohm")
    print(f"    t/s = {T/S:.3f}, delta/s = {d/S:.3f} -- the correction is at the "
          f"EDGE of its validity (it assumes t << s), so it is reported as a "
          f"sensitivity and NOT adopted.")

print()
print("=" * 74)
print("B. THE FENCE  --  what it must DO, and the bound that follows")
print("=" * 74)
lam0 = C / F
lam_pp = lam0 / math.sqrt(ER)
print(f"  A CBCPW has TWO grounds: the coplanar pour on F.Cu and the In1.Cu")
print(f"  reference. Those two sheets are a PARALLEL-PLATE waveguide with NO")
print(f"  cutoff; any asymmetry (bend, launch, discontinuity) puts a voltage")
print(f"  between them and launches the parasitic parallel-plate / slotline")
print(f"  mode, which carries power away. Ground vias SHORT the two sheets,")
print(f"  and the via wall is only a short where it is electrically short")
print(f"  against THAT mode -- not against the CPW mode on the line.")
print()
print(f"  The parallel-plate mode fills the dielectric between two conducting")
print(f"  sheets, so its effective permittivity is the BULK er, not eps_eff:")
print(f"    lambda_0  @ {F} GHz            = {lam0:.4f} mm")
print(f"    lambda_pp = lambda_0/sqrt(er) = {lam_pp:.4f} mm")
print(f"  Divisor 20 is the fleet's inherited via-wall divisor (rf-design.md")
print(f"  sec 2, rfessentials); what changes for GCPW is the WAVELENGTH it is")
print(f"  applied to, exactly as sec 3(b) changed lambda_0 -> lambda_g for")
print(f"  microstrip.")
print()
print(f"  BOUND  ground-stitch along-arm spacing <= lambda_pp/20 = "
      f"{lam_pp/20.0:.4f} mm")
print()
print(f"  For comparison, all at {F} GHz:")
print(f"    microstrip guided  lambda_g/20 (ADR-0003, bare microstrip) = "
      f"{27.3868/20:.4f} mm")
print(f"    CBCPW      guided  lambda_g/20 (this line's OWN mode)      = "
      f"{lam_g/20:.4f} mm")
print(f"    parallel-plate     lambda_pp/20 (the mode the fence shorts)= "
      f"{lam_pp/20:.4f} mm   <-- BINDING")
print(f"    free space         lambda_0/20 (rfessentials as written)   = "
      f"{lam0/20:.4f} mm")
print()
print(f"  The parallel-plate bound is the TIGHTEST of the four, so moving to")
print(f"  the correct line type makes the requirement HARDER, not easier.")
print()
print(f"  Sensitivity of the VERDICT to the divisor, at lambda_pp:")
for div in (8, 10, 12, 20, 24):
    print(f"    lambda_pp/{div:<3d} = {lam_pp/div:7.4f} mm")
print()
print(f"  Laminate Dk window 4.2-4.6 (rf-design.md 4A(v)) moves lambda_pp/20:")
for e in (4.2, 4.4, 4.6):
    print(f"    er = {e}: lambda_pp/20 = {lam0/math.sqrt(e)/20:.4f} mm")
print()
print(f"  STANDARD VALUE the board declares: the largest 0.05 mm round value")
print(f"  under the bound = {math.floor(lam_pp/20.0/0.05)*0.05:.2f} mm")
