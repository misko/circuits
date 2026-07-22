import json, time, re, sys, urllib.request
URL = ("https://jlcpcb.com/api/overseas-pcb-order/v1/"
       "shoppingCart/smtGood/selectSmtComponentList")
def query(keyword, page_size=8, retries=2):
    body = json.dumps({"currentPage":1,"pageSize":page_size,"keyword":keyword}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    for a in range(retries+1):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.load(r)
            return d["data"]["componentPageInfo"]["list"] or []
        except Exception as e:
            if a==retries:
                print(f"  ! {keyword!r}: {e}", file=sys.stderr); return []
            time.sleep(3*(a+1))
def fields(c):
    prices = c.get("prices") or c.get("componentPrices") or []
    p1 = prices[0]["productPrice"] if prices else None
    return dict(code=c.get("componentCode"), mpn=c.get("componentModelEn"),
        brand=c.get("componentBrandEn"), pkg=c.get("componentSpecificationEn"),
        stock=c.get("stockCount"), lib=c.get("componentLibraryType"), p1=p1,
        desc=(c.get("describe") or "")[:90])
KWS = ["MPR121QR2","MPR121","TMC2209","TMC2208","DRV8825","LIS2DH12TR","LIS3DHTR","ADXL345BCCZ",
"AP63205WU","MP1584EN","TPS54331DR","MT2492","TPS562201","ESP32-S3-WROOM-1",
"SMBJ18A","SMBJ16A","SS54","SS34","AO3401A","DMG3415U","AOD4185",
"1812 fuse 2A","DC-005","KF128L-3.5-2P","KF128L-3.5-3P","B4B-XH-A","XH-4AW",
"pin header 2.54mm 1x13","AMS1117-3.3","USBLC6-2SC6","TYPE-C-31-M-12","TS-1187A",
"SWPA6045S100MT","10uH 4A inductor"]
out={}
for kw in KWS:
    r = query(kw)
    time.sleep(1.2)
    out[kw]=[fields(c) for c in r]
    print("===",kw)
    for f in out[kw][:6]:
        print("  ",f)
json.dump(out, open("06_build/cache/adr_stock_2026-07-17.json","w"), indent=1)
