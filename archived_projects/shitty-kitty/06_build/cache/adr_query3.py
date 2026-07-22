import json, time, sys, urllib.request
URL="https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
def query(kw, n=8):
    body=json.dumps({"currentPage":1,"pageSize":n,"keyword":kw}).encode()
    req=urllib.request.Request(URL,data=body,headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0"})
    for a in range(3):
        try:
            with urllib.request.urlopen(req,timeout=20) as r: return json.load(r)["data"]["componentPageInfo"]["list"] or []
        except Exception as e:
            if a==2: print("!",kw,e,file=sys.stderr); return []
            time.sleep(3)
def f(c):
    p=c.get("prices") or []
    return (c.get("componentCode"),c.get("componentModelEn"),c.get("componentLibraryType"),c.get("stockCount"),(p[0]["productPrice"] if p else None),(c.get("describe") or "")[:60])
for kw in ["0805W8F7502T5E","22nF 0805 50V","0805W8F5101T5E","pin header 2.54mm 1x6","KH-2.54PH180-1X6P"]:
    print("===",kw)
    for c in query(kw)[:5]: print("  ",f(c))
    time.sleep(1.2)
