#!/usr/bin/env python3
"""Periodic 3-D quasi-static field solve for the RX2 v4 masked CPWG.

The longitudinal unit cell contains both grounded via-fence rows.  Solving
``div(epsilon * grad(V)) = 0`` twice (with the declared dielectrics and with
air everywhere) gives C and C0 per unit length.  The quasi-TEM identities are

    epsilon_eff = C / C0
    Z0 = 1 / (c * sqrt(C * C0))

This is deliberately a project-owned evidence producer: it models the actual
fabrication tuple that the generic copper-length gate consumes.  Run with the
KiCadRoutingTools venv, which supplies numpy/scipy:

    /home/mouse9911/gits/KiCadRoutingTools/.venv/bin/python \
        03_src/cpwg_field_solver.py --output 06_build/verify/cpwg_field.json

The model is conservative at the fence: both rows use the measured minimum
trace-edge offset and the measured maximum interior pitch.  Metal thickness
is represented by one voxel; the reported convergence spread is the release
uncertainty, not hidden numerical precision.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import cg


EPS0 = 8.8541878128e-12
C0 = 299_792_458.0

MODEL = {
    "stackup": "JLC04121H-7628",
    "frequency_ghz": 6.0,
    "trace_width_mm": 0.360,
    "coplanar_gap_mm": 0.2005,
    "top_to_reference_mm": 0.2104,
    "substrate_dk": 4.4,
    "mask_dk": 3.8,
    "mask_over_trace_mm": 0.01524,
    "mask_over_substrate_mm": 0.03048,
    "via_outer_diameter_mm": 0.250,
    "via_drill_mm": 0.150,
    "via_pitch_mm": 1.1769,
    # Reviewer-measured minimum trace-edge to via-center distance is 0.330 mm.
    "via_center_offset_mm": 0.510,
    "lateral_half_span_mm": 1.80,
    "air_height_mm": 0.42,
    "boundary": "periodic longitudinal; grounded lateral/reference; open top",
    "geometry_source": "saved PCB direct measurement; shared fence_pitch gate",
    "mask_source": "JLCPCB calculator defaults: 0.6 mil trace, 1.2 mil substrate",
}


def solve(step_mm: float, dielectric: bool) -> tuple[float, int, float]:
    m = MODEL
    # Cell-centred grid.  y is periodic; x sidewalls and z=bottom are ground;
    # z=top is zero-flux.  Rounding is recorded through the emitted dimensions.
    nx = int(math.ceil(2 * m["lateral_half_span_mm"] / step_mm)) + 1
    ny = int(math.ceil(m["via_pitch_mm"] / step_mm))
    nz_sub = int(math.ceil(m["top_to_reference_mm"] / step_mm))
    nz_air = int(math.ceil(m["air_height_mm"] / step_mm))
    nz = nz_sub + nz_air + 1
    dx = 2 * m["lateral_half_span_mm"] / (nx - 1)
    dy = m["via_pitch_mm"] / ny
    dz_sub = m["top_to_reference_mm"] / nz_sub
    dz_air = m["air_height_mm"] / nz_air
    # Use a uniform z grid whose size is the smaller of the two fitted steps;
    # this keeps the finite-volume face arithmetic symmetric.
    dz = min(dz_sub, dz_air)
    nz_sub = int(round(m["top_to_reference_mm"] / dz))
    nz_air = int(round(m["air_height_mm"] / dz))
    dz = m["top_to_reference_mm"] / nz_sub
    nz = nz_sub + nz_air + 1

    x = np.linspace(-m["lateral_half_span_mm"], m["lateral_half_span_mm"], nx)
    y = (np.arange(ny) + 0.5) * dy
    z = (np.arange(nz) - nz_sub) * dz
    eps = np.ones((nx, ny, nz), dtype=np.float64)
    if dielectric:
        eps[:, :, z < 0] = m["substrate_dk"]
        # Conformal mask: JLC's declared trace-top thickness and the larger
        # substrate-side thickness in the CPWG gaps/over the ground pour.
        for k, zz in enumerate(z):
            if zz <= 0:
                continue
            over_trace = np.abs(x) <= m["trace_width_mm"] / 2
            mask_t = np.where(over_trace,
                              m["mask_over_trace_mm"],
                              m["mask_over_substrate_mm"])
            eps[:, :, k] = np.where(zz <= mask_t[:, None], m["mask_dk"], 1.0)

    fixed = np.zeros((nx, ny, nz), dtype=bool)
    value = np.zeros((nx, ny, nz), dtype=np.float64)
    fixed[0, :, :] = True
    fixed[-1, :, :] = True
    fixed[:, :, 0] = True
    top_k = nz_sub
    trace = np.abs(x) <= m["trace_width_mm"] / 2
    ground = np.abs(x) >= (m["trace_width_mm"] / 2 + m["coplanar_gap_mm"])
    fixed[trace, :, top_k] = True
    value[trace, :, top_k] = 1.0
    fixed[ground, :, top_k] = True

    # Two periodic via cylinders, centred midway through the cell.  The plated
    # outer diameter is the electrostatic boundary; drill is retained in the
    # evidence tuple for fabrication cross-checking.
    yy = y - m["via_pitch_mm"] / 2
    for xc in (-m["via_center_offset_mm"], m["via_center_offset_mm"]):
        cyl = ((x[:, None] - xc) ** 2 + yy[None, :] ** 2
               <= (m["via_outer_diameter_mm"] / 2) ** 2)
        fixed[:, :, :top_k + 1] |= cyl[:, :, None]

    free = ~fixed
    ids = np.full(free.shape, -1, dtype=np.int64)
    ids[free] = np.arange(int(free.sum()))
    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    rhs = np.zeros(int(free.sum()), dtype=np.float64)

    # Finite-volume face conductance uses harmonic epsilon.  Top omission is
    # the Neumann/open boundary; y wraps periodically.
    directions = ((-1, 0, 0, dx), (1, 0, 0, dx),
                  (0, -1, 0, dy), (0, 1, 0, dy),
                  (0, 0, -1, dz), (0, 0, 1, dz))
    for i, j, k in zip(*np.nonzero(free)):
        r = int(ids[i, j, k])
        diag = 0.0
        for di, dj, dk, spacing in directions:
            ni, nj, nk = i + di, (j + dj) % ny, k + dk
            if ni < 0 or ni >= nx or nk < 0:
                continue
            if nk >= nz:  # open top
                continue
            e1, e2 = eps[i, j, k], eps[ni, nj, nk]
            # A metal voxel has no dielectric constant.  At a free/metal
            # face the field lives wholly in the free cell's material; using
            # a harmonic mean with the placeholder epsilon=1 of the fixed
            # voxel would under-count substrate capacitance severely.
            ef = e1 if fixed[ni, nj, nk] else 2 * e1 * e2 / (e1 + e2)
            g = ef / (spacing * spacing)
            diag += g
            if fixed[ni, nj, nk]:
                rhs[r] += g * value[ni, nj, nk]
            else:
                rows.append(r); cols.append(int(ids[ni, nj, nk])); data.append(-g)
        rows.append(r); cols.append(r); data.append(diag)
    a = coo_matrix((data, (rows, cols)), shape=(len(rhs), len(rhs))).tocsr()
    potential, info = cg(a, rhs, rtol=2e-9, atol=0.0, maxiter=5000)
    if info != 0:
        raise RuntimeError(f"CG did not converge (info={info}, step={step_mm})")
    v = value.copy()
    v[free] = potential

    # Electric-field energy, each face once.  Periodic y includes its wrap;
    # top Neumann contributes zero.  Coordinates are converted mm -> m.
    energy = 0.0
    spacings = ((1, 0, 0, dx), (0, 1, 0, dy), (0, 0, 1, dz))
    cell_volume_m3 = dx * dy * dz * 1e-9
    def face_epsilon(ea, eb, fa, fb):
        ef = 2 * ea * eb / (ea + eb)
        ef = np.where(fa & ~fb, eb, ef)
        ef = np.where(fb & ~fa, ea, ef)
        return ef

    for di, dj, dk, spacing in spacings:
        if di:
            dv = v[1:, :, :] - v[:-1, :, :]
            eface = face_epsilon(eps[:-1, :, :], eps[1:, :, :],
                                 fixed[:-1, :, :], fixed[1:, :, :])
        elif dj:
            dv = np.roll(v, -1, axis=1) - v
            eface = face_epsilon(eps, np.roll(eps, -1, axis=1),
                                 fixed, np.roll(fixed, -1, axis=1))
        else:
            dv = v[:, :, 1:] - v[:, :, :-1]
            eface = face_epsilon(eps[:, :, :-1], eps[:, :, 1:],
                                 fixed[:, :, :-1], fixed[:, :, 1:])
        energy += 0.5 * EPS0 * float(np.sum(eface * (dv / (spacing * 1e-3)) ** 2)) * cell_volume_m3
    capacitance_per_m = 2 * energy / (m["via_pitch_mm"] * 1e-3)
    residual = float(np.linalg.norm(a @ potential - rhs) / max(np.linalg.norm(rhs), 1e-30))
    return capacitance_per_m, len(rhs), residual


def run(steps: list[float]) -> dict:
    levels = []
    for step in steps:
        c, nodes, residual = solve(step, True)
        c_air, _, residual_air = solve(step, False)
        eps_eff = c / c_air
        z0 = 1.0 / (C0 * math.sqrt(c * c_air))
        tpd = math.sqrt(eps_eff) / 299.792458 * 1000.0
        f = MODEL["frequency_ghz"]
        levels.append({
            "step_mm": step, "free_nodes": nodes,
            "C_pF_per_m": c * 1e12, "C0_pF_per_m": c_air * 1e12,
            "epsilon_eff": eps_eff, "z0_ohm": z0,
            "t_pd_ps_per_mm": tpd,
            "lambda_g_mm": 299.792458 / (f * math.sqrt(eps_eff)),
            "deg_per_mm": 0.360 * f * tpd,
            "relative_residual": max(residual, residual_air),
        })
    final = dict(levels[-1])
    spread = max(x["z0_ohm"] for x in levels) - min(x["z0_ohm"] for x in levels)
    return {
        "method": "periodic_3d_finite_volume_quasistatic_dual_capacitance",
        "equations": ["div(epsilon grad V)=0", "epsilon_eff=C/C0",
                      "Z0=1/(c*sqrt(C*C0))"],
        "model": MODEL,
        "convergence": levels,
        "result": final,
        "z0_convergence_spread_ohm": spread,
        "acceptance": {"target_ohm": 50.0, "tolerance_percent": 10.0},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    ap.add_argument("--steps", nargs="+", type=float, default=[0.040, 0.030, 0.025])
    args = ap.parse_args()
    result = run(args.steps)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    z = result["result"]["z0_ohm"]
    uncertainty = result["z0_convergence_spread_ohm"]
    # The complete numerical interval must fit the declared +/-10% order
    # tolerance.  A point estimate alone is not a convergence gate.
    return 0 if 45.0 <= z - uncertainty and z + uncertainty <= 55.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
