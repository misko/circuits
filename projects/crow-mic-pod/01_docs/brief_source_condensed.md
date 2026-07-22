Verbatim user commission (invoked via /pcb-design, 2026-07-21). The user
supplied the full "CROW ACOUSTIC LOCALIZATION ARRAY — REV-A WORKING DESIGN,
TEXT EDITION" document (July 18, 2026) as the brief, followed by this
directive appended to the same invocation:

", lets use ethernet cable and ethernet connectors everywhere to interface them"

KEY REV-A FACTS FROM THE DOCUMENT (the full text is the commission; the
agent must treat the document's tables as requirement sources):

- Purpose: outdoor crow-call localization; 6 active-balanced microphone
  pods, 25 ft radius, feeding ONE shared-clock 8-channel-capable USB
  recorder (6 populated). 24-bit / 48 kHz, USB Audio Class 2 ASYNC (the
  recorder clock is the timing authority). One physical sample clock for
  every channel — no GPS/network sync.
- TWO custom PCBs: (a) remote microphone POD (2-layer): AOM-5024L-HD-R
  electret + OPA1678IDR dual op-amp active-balanced driver (~3 V/V diff,
  values table in doc), CMT-8504-100-SMT-TR calibration transducer
  (driven FROM the central board, 5V ~150mA coded 4kHz bursts),
  TPD2E2U06DRLR ESD; (b) CENTRAL recorder (4-layer min, 6 preferred):
  XU316-1024-TQ128-I24 + 2x PCM1865DBTR (TDM, shared MCLK/BCLK/LRCK,
  NC7NZ34K8X clock buffer, FA-238 24MHz, W25Q16JVSSIQ QSPI), USB4105
  USB-C + TPD4EUSB30DQAR, SHT40-AD1B-R2, per-cable port: RJHSE5384 RJ45
  (8 footprints, 6 populated), TPD2E2U06 analog ESD, MINISMDC050F-2 PTC,
  AO3400A low-side beeper MOSFET (slow edges), rails: 2x AP61102Z6-7
  bucks (3.3V + 0.9V core), TCR2LF18 1.8V LDO, XC6227C331PR-G quiet 3.3V
  analog LDO, Mean Well GST25A05-P1J external 5V supply.
- Cabling: one outdoor solid-copper Cat5e home-run per pod, CUSTOM
  pinout (NOT Ethernet): orange 1,2=AUDIO+/-; green 3,6=+5V_BEEP/
  BEEP_SWITCHED_RETURN; blue 4,5 & brown 7,8 = +5V_AUDIO/GND_AUDIO.
  Label everything "NOT ETHERNET - CUSTOM 5V AUDIO PINOUT".
- USER DIRECTIVE (amends the doc): use ethernet cable AND ethernet
  connectors EVERYWHERE to interface pods and central — i.e. the pod end
  also gets an RJ45 jack (not gland+solder pads); keep the custom-pinout
  safety labeling discipline.
- XMOS multichannel audio platform (XU316 + 2x PCM1865) is the named
  reference design: copy its power sequencing, clocking and USB
  implementation closely (layout-precedent search mandatory).
- Layout guidance in doc: ADCs + input RC in quiet analog region away
  from switching regulators and beeper traces; controlled short USB;
  test points for every rail + clocks + TDM + beeper returns;
  same-signal injection header for inter-ADC skew; 8 port footprints
  with 6 populated.
- Doc's own risk register + build sequence apply (pod prototype first).
- Budgets are advisory; stock must be rechecked (doc says so).
