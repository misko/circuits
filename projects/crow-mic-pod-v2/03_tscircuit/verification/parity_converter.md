=== crow_mic_pod_v2 netlist parity (converter kicad_sch vs sealed 04_kicad) ===
converter nets=17  kicad nets=17
  DIFF 'GND': only_converter=[] only_kicad=[('D1', '1'), ('D1', '2')]
  NO-CONNECT DIFF: only_converter=[('D1', '1'), ('D1', '2')] only_kicad=[('J1', '10'), ('J1', '11'), ('J1', '12'), ('J1', '9'), ('J1', 'SH'), ('LS1', '3'), ('LS1', '4')]
connected nodes: converter=76 kicad=78   no-connects: converter=2 kicad=7
REAL DISCREPANCIES: 2  ->  FAIL
