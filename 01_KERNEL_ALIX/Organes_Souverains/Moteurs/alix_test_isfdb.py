import urllib.request
import re

url = "https://www.isfdb.org/wiki/index.php/ISFDB_Downloads"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        print("ISFDB Downloads page len:", len(html))
        # Look for links
        links = re.findall(r'href=[\"\']([^\"\']+)[\"\']', html)
        for l in links:
            if "download" in l.lower() or ".zip" in l.lower() or ".tar" in l.lower() or ".sql" in l.lower() or ".gz" in l.lower() or "sf.net" in l or "sourceforge" in l:
                print(" - ISFDB link:", l)
except Exception as e:
    print("Error:", e)
