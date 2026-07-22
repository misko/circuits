# SUPERSEDED by v1.3-2026-07-17 — v1.2's J1 render is WRONG

v1.2 introduced a mistaken model_rot_z:180 on J1 (USB-C) that CANCELLED
JLC's own built-in 180deg model flip, rotating the rendered connector mouth
inboard. The board itself is fine (fab byte-identical to v1.1/v1.3, J1 pads
fit JLC CAD at 0.00mm) — only v1.2's twin render lies. Use v1.3 (or v1.1),
which render J1 correctly (contacts over the east pads, mouth at the west
board edge).
