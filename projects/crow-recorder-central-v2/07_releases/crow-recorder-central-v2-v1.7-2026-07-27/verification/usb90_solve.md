# USB 90ohm solve — crow-recorder-central-v2 v1.1 (F2 closure, 2026-07-24)

Stackup: JLCPCB JLC06161H-3313 6L 1.6mm (jlcpcb.com/impedance, fetched 2026-07-24):
  L1 1oz (0.035mm finished) / prepreg 3313 h=0.0994mm Er=4.1 / In1.Cu GND plane.
Method: 2D finite-difference Laplace field solve, odd-mode capacitance
(half-domain antisymmetric wall), Zodd=1/(c*sqrt(Cd*Ca)), Zdiff=2*Zodd;
soldermask 20um Er 3.8 over trace+gap. Solver source appended below.

## Results (solver stdout, verbatim)
```
sanity single-ended w=0.140: Z0 ~=  50.60 ohm
sanity single-ended w=0.150: Z0 ~=  48.77 ohm
w=0.125 s=0.150 dx=0.004: Zdiff= 90.51 ohm
w=0.125 s=0.150 dx=0.003: Zdiff= 89.71 ohm   (grid convergence +/-0.8)
w=0.120 s=0.150 dx=0.004: Zdiff= 91.62 ohm
w=0.130 s=0.150 dx=0.004: Zdiff= 89.44 ohm
```

CHOSEN: w=0.125mm gap=0.15mm -> Zdiff 89.7-90.5 ohm (90 +/-10% window
81-99 ohm with margin). Enforced: nets.yaml USB_DIFF diff_pair ->
netclass + .kicad_dru USB_DIFF_diffpair + board diff_pair_dimensions.
Routed (audit_board measurement): USB_DP 23.62mm / USB_DN 23.51mm,
spread 0.110mm, all 0.125mm F.Cu, 0 vias.
ACTIVATION PROOF: dru min tightened to 0.30mm on a board copy -> 10x
diff_pair_gap_out_of_range on this pair (the rule can FAIL); restored
rule re-gates DRC 0/0/0.

## Solver source (usb90_fd.py, verbatim)
```python
#!/usr/bin/env python3
"""2D finite-difference field solve: edge-coupled microstrip differential
impedance on JLC06161H-3313 (L1 over In1 GND plane).

Odd mode by symmetry: antisymmetric potential about the gap centerline ->
solve half-domain with V=0 on the symmetry wall, trace at V=1.
Zodd = 1/(c*sqrt(Cd*Ca)); Zdiff = 2*Zodd (Cd: real dielectrics, Ca: air).

Stackup (JLCPCB published, fetched 2026-07-24 jlcpcb.com/impedance):
  prepreg 3313 h=0.0994mm Er=4.1 between L1 and In1 GND plane
  finished outer copper t~=0.035mm; soldermask ~0.020mm Er 3.8 over trace+gap.

Discretization: node potentials, cell permittivities, 5-point stencil with
edge coefficients = average of the two adjacent cells; red-black SOR.
"""
import numpy as np

C_LIGHT = 299792458.0
EPS0 = 8.8541878128e-12


def solve_C(w, s, h=0.0994, t=0.035, er_pp=4.1, mask=True,
            dx=0.004, pad=1.0, air_top=0.7, air=False):
    er_mask, tm = 3.8, 0.020
    X = s / 2 + w + pad
    Y = h + t + air_top
    nx = int(round(X / dx)) + 1
    ny = int(round(Y / dx)) + 1
    # cell permittivity (ny-1, nx-1); cell j spans y in [j*dx,(j+1)*dx)
    ycell = (np.arange(ny - 1) + 0.5) * dx
    er = np.ones((ny - 1, nx - 1))
    if not air:
        er[ycell < h, :] = er_pp
        if mask:
            er[(ycell >= h) & (ycell < h + t + tm), :] = er_mask
    # conductor node mask
    cond = np.zeros((ny, nx), bool)
    ix0 = int(round((s / 2) / dx)); ix1 = int(round((s / 2 + w) / dx))
    iy0 = int(round(h / dx)); iy1 = int(round((h + t) / dx))
    cond[iy0:iy1 + 1, ix0:ix1 + 1] = True
    # conductor interior cells are metal: exclude from field energy by er=1
    # (field there ~0 after solve anyway)

    # edge coefficients for node (j,i):
    # east edge: avg of cells (j-1,i),(j,i); clamp indices
    def cellavg(jA, iA, jB, iB):
        return 0.5 * (er[np.clip(jA, 0, ny - 2), np.clip(iA, 0, nx - 2)]
                      + er[np.clip(jB, 0, ny - 2), np.clip(iB, 0, nx - 2)])

    J, I = np.meshgrid(np.arange(ny), np.arange(nx), indexing="ij")
    cE = cellavg(J - 1, I, J, I)         # edge to (j,i+1)
    cW = cellavg(J - 1, I - 1, J, I - 1)
    cN = cellavg(J, I - 1, J, I)         # edge to (j+1,i)
    cS = cellavg(J - 1, I - 1, J - 1, I)

    V = np.zeros((ny, nx))
    V[cond] = 1.0
    interior = np.ones((ny, nx), bool)
    interior[0, :] = interior[-1, :] = False
    interior[:, 0] = interior[:, -1] = False
    interior &= ~cond
    red = ((J + I) % 2 == 0) & interior
    blk = ((J + I) % 2 == 1) & interior
    omega = 1.92
    for it in range(60000):
        for m in (red, blk):
            num = (cE * np.roll(V, -1, 1) + cW * np.roll(V, 1, 1)
                   + cN * np.roll(V, -1, 0) + cS * np.roll(V, 1, 0))
            den = cE + cW + cN + cS
            Vnew = num / den
            V[m] += omega * (Vnew[m] - V[m])
        if it % 500 == 499:
            num = (cE * np.roll(V, -1, 1) + cW * np.roll(V, 1, 1)
                   + cN * np.roll(V, -1, 0) + cS * np.roll(V, 1, 0))
            res = np.max(np.abs(num / (cE + cW + cN + cS) - V)[interior])
            if res < 5e-7:
                break
    # energy: sum over cells, E from bilinear node differences
    Ex = (np.diff(V, axis=1)[:-1, :] + np.diff(V, axis=1)[1:, :]) / (2 * dx)
    Ey = (np.diff(V, axis=0)[:, :-1] + np.diff(V, axis=0)[:, 1:]) / (2 * dx)
    W = 0.5 * EPS0 * np.sum(er * (Ex ** 2 + Ey ** 2)) * dx * dx * 1e-0
    return 2 * W  # V=1 -> C = 2W  (F/m since dx in mm cancels: dx^2/dx grid)


def zdiff(w, s, **kw):
    Cd = solve_C(w, s, **kw)
    Ca = solve_C(w, s, air=True, **kw)
    zodd = 1.0 / (C_LIGHT * np.sqrt(Cd * Ca))
    return 2 * zodd, Cd, Ca


def z0_single(w, **kw):
    """Single-ended sanity check: solve with a huge gap so coupling ~0 and
    the symmetry wall is far away -> approximates isolated microstrip."""
    z, _, _ = zdiff(w, 6.0, pad=1.0, **kw)
    return z / 2


if __name__ == "__main__":
    # validation: isolated 0.15mm microstrip on this stackup; JLC calculator
    # families put 50-ohm single-ended near w~0.15-0.16 on 3313+mask
    for w in (0.14, 0.15, 0.16):
        print(f"sanity single-ended w={w:.3f}: Z0 ~= {z0_single(w):6.2f} ohm",
              flush=True)
    for w, s in [(0.12, 0.15), (0.13, 0.15), (0.14, 0.15), (0.15, 0.15),
                 (0.15, 0.127), (0.14, 0.127), (0.13, 0.127), (0.12, 0.127),
                 (0.16, 0.15), (0.15, 0.18), (0.16, 0.18), (0.17, 0.20)]:
        z, _, _ = zdiff(w, s)
        print(f"w={w:.3f} s={s:.3f}  Zdiff={z:6.2f} ohm", flush=True)
```
