import json, time, sys, urllib.request
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
        desc=(c.get("describe") or "")[:80])
KWS = ["C2913204","1812 fuse 3A resettable","100uF 25V electrolytic SMD","10uF 25V 1206","22uF 25V 1206",
"B3B-XH-A","B2B-XH-A","C2297","C49678","C28323","C45783","C17414","C17513","C25804 10k",
"0805W8F1002T5E","0805W8F1001T5E","0805W8F1000T5E","0805W8F4701T5E","0805W8F1003T5E",
"C2071056","C91322","C2150710","C110926","C81582","2.2uF 0805 25V","4.7uF 0805 25V"]
out={}
for kw in KWS:
    r = query(kw)
    time.sleep(1.2)
    out[kw]=[fields(c) for c in r]
    print("===",kw)
    for f in out[kw][:5]:
        print("  ",f)
json.dump(out, open("06_build/cache/adr_stock2_2026-07-17.json","w"), indent=1)
