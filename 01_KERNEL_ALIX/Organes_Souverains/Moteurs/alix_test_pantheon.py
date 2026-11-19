import urllib.request
import re

url = "https://pantheon.org/areas/mythology/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        # Print all links on the page
        links = re.findall(r'href=[\"\']([^\"\']+)[\"\']', html)
        for l in links:
            if "/areas/" in l:
                print(" -", l)
except Exception as e:
    print("Error:", e)
