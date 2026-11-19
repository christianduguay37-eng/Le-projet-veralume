import sys
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
base_dir = Path(r"c:\Users\Christian\Documents\Exocerveau_Souverain_Master\Projet  Temporia").resolve()

md_file = base_dir / "PAPIER_ZENODO_13_SYNTHETISEUR_ATOMIQUE_PROMETHEE.md"
html_file = base_dir / "PAPIER_ZENODO_13_SYNTHETISEUR_ATOMIQUE_PROMETHEE.html"
pdf_file = base_dir / "PAPIER_ZENODO_13_SYNTHETISEUR_ATOMIQUE_PROMETHEE.pdf"

title = "Compilation Atomique de la Matière et Recombinaison Stœchiométrique Non-Prédatrice : Publication N° 13 (CERN / Zenodo)"

html_template = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  @page {{
    size: letter;
    margin: 18mm 15mm 18mm 15mm;
    @bottom-center {{
      content: counter(page);
      font-size: 8pt;
      color: #64748b;
    }}
  }}
  body {{
    font-family: "Georgia", "Times New Roman", Times, serif;
    font-size: 9.5pt;
    line-height: 1.45;
    color: #1a1a1a;
    max-width: 820px;
    margin: 0 auto;
    padding: 20px;
    background: #fff;
  }}
  h1 {{
    font-size: 15pt;
    text-align: center;
    margin-bottom: 0.6em;
    font-weight: bold;
    color: #0d233a;
    border-bottom: 2px solid #0d233a;
    padding-bottom: 8px;
    line-height: 1.3;
  }}
  h2 {{
    font-size: 11.5pt;
    color: #1a365d;
    margin-top: 1.4em;
    margin-bottom: 0.4em;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 3px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  h3 {{
    font-size: 10.5pt;
    color: #2b6cb0;
    margin-top: 1.1em;
    margin-bottom: 0.3em;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.0em 0;
    font-size: 8pt;
  }}
  th, td {{
    border: 1px solid #cbd5e0;
    padding: 5px 8px;
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background-color: #f1f5f9;
    font-weight: bold;
    color: #0f172a;
  }}
  blockquote {{
    border-left: 3px solid #0d233a;
    margin: 1.0em 0;
    padding: 6px 12px;
    background-color: #f8fafc;
    font-style: italic;
    color: #334155;
  }}
  code {{
    font-family: "Consolas", "Courier New", monospace;
    font-size: 8.5pt;
    background-color: #f1f5f9;
    padding: 1px 3px;
    border-radius: 2px;
  }}
  pre {{
    background-color: #0f172a;
    color: #f8fafc;
    padding: 10px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 8pt;
    line-height: 1.3;
  }}
  pre code {{
    background-color: transparent;
    color: #38bdf8;
    padding: 0;
  }}
  hr {{
    border: 0;
    height: 1px;
    background: #e2e8f0;
    margin: 1.4em 0;
  }}
</style>
</head>
<body>
<div id="content"></div>
<script>
  const rawMarkdown = {raw_json_md};
  document.getElementById('content').innerHTML = marked.parse(rawMarkdown);
  document.addEventListener("DOMContentLoaded", function() {{
    renderMathInElement(document.body, {{
      delimiters: [
        {{left: '$$', right: '$$', display: true}},
        {{left: '$', right: '$', display: false}}
      ],
      throwOnError : false
    }});
  }});
</script>
</body>
</html>
"""

md_text = md_file.read_text(encoding="utf-8")
rendered_html = html_template.format(
    title=title,
    raw_json_md=json.dumps(md_text, ensure_ascii=False)
)
html_file.write_text(rendered_html, encoding="utf-8")
print(f"[OK] HTML généré : {html_file.name}")

print(f"Compilation PDF via Edge Headless...")
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=edge_path)
    page = browser.new_page()
    page.goto(f"file:///{html_file.as_posix()}", wait_until="networkidle")
    page.wait_for_timeout(3500)
    page.pdf(
        path=str(pdf_file),
        format="Letter",
        print_background=True,
        margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"}
    )
    page.close()
    browser.close()

# Copie miroir dans le Cerveau Alix
miroir_pdf = Path(r"C:\Users\Christian\Documents\Cerveau Alix\PAPIER_ZENODO_13_SYNTHETISEUR_ATOMIQUE_PROMETHEE.pdf")
miroir_pdf.write_bytes(pdf_file.read_bytes())

print(f"🎉 [SUCCÈS] PDF Académique généré : {pdf_file.name} ({pdf_file.stat().st_size} octets)")
print(f"   -> Copie miroir : {miroir_pdf}")
