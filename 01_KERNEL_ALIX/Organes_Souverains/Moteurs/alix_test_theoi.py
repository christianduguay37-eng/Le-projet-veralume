import urllib.request

for u in ["https://www.theoi.com", "https://pantheon.org"]:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            print(f"{u} accessible, code: {resp.getcode()}")
    except Exception as e:
        print(f"{u} error: {e}")
