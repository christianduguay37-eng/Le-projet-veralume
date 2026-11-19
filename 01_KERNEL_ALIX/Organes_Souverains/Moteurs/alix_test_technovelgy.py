import urllib.request
import re
from html.parser import HTMLParser

class TechnovelgyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_a = False
        self.cur_href = ""
        self.cur_text = []
        self.in_row = False
        self.cur_row = []
        self.cur_cell = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "tr":
            self.in_row = True
            self.cur_row = []
        elif tag == "td":
            self.cur_cell = []
        elif tag == "a":
            href = attrs_dict.get("href", "")
            if "content.asp?Bnum=" in href:
                self.cur_href = href

    def handle_endtag(self, tag):
        if tag == "td":
            self.cur_row.append(" ".join(self.cur_cell).strip())
            self.cur_cell = []
        elif tag == "tr":
            if self.cur_row and self.cur_href:
                self.rows.append((self.cur_href, self.cur_row))
                self.cur_href = ""
            self.in_row = False

    def handle_data(self, data):
        txt = data.strip()
        if txt:
            self.cur_cell.append(txt)

url = "http://www.technovelgy.com/ct/ctnlistalpha.asp?FL=A"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        parser = TechnovelgyParser()
        parser.feed(html)
        print("HTMLParser finished! Total extracted rows:", len(parser.rows))
        for href, cells in parser.rows[:5]:
            print(f" - [{href}] {cells}")
except Exception as e:
    print("Error:", e)
