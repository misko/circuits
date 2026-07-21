# T5 GREEN canary brief (verbatim — hand to the agent unchanged)

Please from scratch start a new project: design a board that takes 12V DC in on
a 2-pin 5.08mm screw terminal and outputs 5V at up to 2A on a second 2-pin
screw terminal, with a power-good LED on the 5V rail and reverse-polarity
protection on the input. Please internally research and make all design
decisions. The output should be a fully designed, placed, routed board with
JLCPCB manufacturing files.

<!-- CALIBRATION (not part of the brief; graders + maintainers only):
This brief is deliberately FEASIBLE at JLC 2-or-4-layer STANDARD tier. A
correct D-ESC pass steers to a buck in a routable package (SOIC-8 / SOT-23-x /
TSOT / pitch >= 0.65mm QFN with thermal pad escape) — many stocked options.
If the skill's judgment gates work, a fresh agent reaches DRC 0/0/0 + parity 0
unattended. A red result here = the SKILL regressed (mechanics or judgment),
not a hard board. -->
