=== usb_hub_3s_v2 netlist parity (converter kicad_sch vs sealed 04_kicad) ===
converter nets=64  kicad nets=65
  DIFF 'BOOT_A': only_converter=[('C8', '1'), ('D3', '2'), ('U2', '16')] only_kicad=[]
  DIFF 'VCC_A': only_converter=[] only_kicad=[('C8', '1'), ('D3', '2'), ('U2', '16')]
connected nodes: converter=364 kicad=364   no-connects: converter=8 kicad=8
REAL DISCREPANCIES: 2  ->  FAIL
