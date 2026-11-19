from pathlib import Path
from playwright.sync_api import sync_playwright

html_file = Path("paper.html").resolve()
pdf_file = Path("Preprint_10_Non_Anthropomorphic_Robotics_Echolocation.pdf").resolve()
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print(f"Chargement de : {html_file}")
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=edge_path)
    page = browser.new_page()
    page.goto(f"file:///{html_file.as_posix()}", wait_until="networkidle")
    page.wait_for_timeout(4000) # Laisser le temps à KaTeX et Marked de rendre
    page.pdf(
        path=str(pdf_file),
        format="A4",
        print_background=True,
        margin={"top": "18mm", "bottom": "18mm", "left": "15mm", "right": "15mm"}
    )
    browser.close()

print(f"[OK] PDF genere avec succes : {pdf_file} ({pdf_file.stat().st_size} octets)")
