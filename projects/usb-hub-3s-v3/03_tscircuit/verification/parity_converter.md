=== usb_hub_3s_v2 netlist parity (converter kicad_sch vs sealed 04_kicad) ===
converter nets=64  kicad nets=59
  DIFF 'BOOT_A': only_converter=[('C8', '1'), ('D3', '2'), ('U2', '16')] only_kicad=[]
  DIFF 'ENKILL': only_converter=[('Q8', '1')] only_kicad=[]
  DIFF 'GND': only_converter=[('D10', '1'), ('D11', '1'), ('D12', '1'), ('D9', '1'), ('Q8', '2')] only_kicad=[]
  DIFF 'LEDPK': only_converter=[('D8', '2'), ('R37', '2')] only_kicad=[]
  DIFF 'LEDPKK': only_converter=[('D8', '1'), ('Q8', '3')] only_kicad=[]
  DIFF 'LEDVA1': only_converter=[('D9', '2'), ('R38', '2')] only_kicad=[]
  DIFF 'LEDVA2': only_converter=[('D10', '2'), ('R39', '2')] only_kicad=[]
  DIFF 'LEDVA3': only_converter=[('D11', '2'), ('R40', '2')] only_kicad=[]
  DIFF 'LEDVC': only_converter=[('D12', '2'), ('R41', '2')] only_kicad=[]
  DIFF 'VBUSA1': only_converter=[('R38', '1')] only_kicad=[]
  DIFF 'VBUSA2': only_converter=[('R39', '1')] only_kicad=[]
  DIFF 'VBUSA3': only_converter=[('R40', '1')] only_kicad=[]
  DIFF 'VBUSC': only_converter=[('R41', '1')] only_kicad=[]
  DIFF 'VCC_A': only_converter=[] only_kicad=[('C8', '1'), ('D3', '2'), ('U2', '16')]
  DIFF 'VIN': only_converter=[('R37', '1')] only_kicad=[]
connected nodes: converter=362 kicad=339   no-connects: converter=8 kicad=8
REAL DISCREPANCIES: 15  ->  FAIL
