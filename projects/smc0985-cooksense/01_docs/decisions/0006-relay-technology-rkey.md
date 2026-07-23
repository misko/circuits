# ADR-0006 — Relay cell: cook-hub's proven DIP05 reed default; RKEY field

status: accepted
date: 2026-07-22
tags: protection

## Decision (user D6)
Default relay = Standex-Meder DIP05-1A72-12L: ALREADY SHIPPED on
sealed cook-hub v1.0 (02_parts/DIP05-1A72-12L — paid-for prior art;
drivers + flyback pattern reusable with it). Meets brief §4.3 (SPST-NO
dry contact, >=1kV, high off-R, low off-C, 5V coil). Order-day stock
check mandatory; PhotoMOS AQY212GS recorded as the simplification
alternate for the 10 SELECTOR positions only (no coil/driver/flyback;
few-ohm Ron absorbed by RKEY) — PRESS and STOP stay REED regardless
(true mechanical open = no phantom-press leakage on the two contacts
that matter). Decide selector tech at parts stage from stock + price.

## RKEY (spec-tension T1)
Shared solder-select field 0R(default)/22/47/100/220/470/1k, 1206
pads, test points both sides, decade-box header; RSTOP separate, 0R
default. Qualification: max reliable emulation R found on the TIMER
key, fully assembled appliance, isolated interface (Gate 8).
