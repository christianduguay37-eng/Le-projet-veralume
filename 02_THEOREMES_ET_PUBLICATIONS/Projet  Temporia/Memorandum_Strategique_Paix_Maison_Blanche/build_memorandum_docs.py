import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
base_dir = Path(__file__).parent.resolve()

docs = [
    {
        "md": base_dir / "EXECUTIVE_MEMORANDUM_PRESIDENT_UNITED_STATES_EN.md",
        "html": base_dir / "Executive_Memorandum_POTUS_EN.html",
        "pdf": base_dir / "Executive_Memorandum_POTUS_EN.pdf",
        "title": "EXECUTIVE STRATEGIC MEMORANDUM - THE DUAL-THEATER SOVEREIGN SETTLEMENT"
    },
    {
        "md": base_dir / "MEMORANDUM_STRATEGIQUE_PAIX_SOUVERAINE_FR.md",
        "html": base_dir / "Memorandum_Strategique_Paix_FR.html",
        "pdf": base_dir / "Memorandum_Strategique_Paix_FR.pdf",
        "title": "MÉMORANDUM STRATÉGIQUE - ARCHITECTURE OPÉRATIONNELLE DE PAIX SOUVERAINE"
    }
]

html_template = """<!DOCTYPE html>
<html lang="en">
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
    margin: 20mm 18mm 20mm 18mm;
  }}
  body {{
    font-family: "Georgia", "Times New Roman", Times, serif;
    font-size: 10.5pt;
    line-height: 1.5;
    color: #1a1a1a;
    max-width: 820px;
    margin: 0 auto;
    padding: 25px;
    background: #fff;
  }}
  h1 {{
    font-size: 16pt;
    text-align: center;
    margin-bottom: 0.8em;
    font-weight: bold;
    color: #0d233a;
    border-bottom: 2px solid #0d233a;
    padding-bottom: 8px;
    letter-spacing: 0.5px;
  }}
  h2 {{
    font-size: 12pt;
    color: #1a365d;
    margin-top: 1.6em;
    margin-bottom: 0.5em;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  h3 {{
    font-size: 11pt;
    color: #2b6cb0;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.2em 0;
    font-size: 9pt;
  }}
  th, td {{
    border: 1px solid #cbd5e0;
    padding: 7px 10px;
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background-color: #f1f5f9;
    font-weight: bold;
    color: #0f172a;
  }}
  blockquote {{
    border-left: 4px solid #0d233a;
    margin: 1.2em 0;
    padding: 8px 16px;
    background-color: #f8fafc;
    font-style: italic;
    color: #334155;
  }}
  code {{
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9pt;
    background-color: #f1f5f9;
    padding: 2px 4px;
    border-radius: 3px;
  }}
  pre {{
    background-color: #0f172a;
    color: #f8fafc;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 8.5pt;
    line-height: 1.35;
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
    margin: 1.8em 0;
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

import json

for doc in docs:
    md_text = doc["md"].read_text(encoding="utf-8")
    rendered_html = html_template.format(
        title=doc["title"],
        raw_json_md=json.dumps(md_text, ensure_ascii=False)
    )
    doc["html"].write_text(rendered_html, encoding="utf-8")
    print(f"[OK] HTML genere : {doc['html'].name}")

print(f"Lancement de Microsoft Edge ({edge_path}) pour la compilation PDF...")
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=edge_path)
    for doc in docs:
        page = browser.new_page()
        page.goto(f"file:///{doc['html'].as_posix()}", wait_until="networkidle")
        page.wait_for_timeout(3000)
        page.pdf(
            path=str(doc["pdf"]),
            format="Letter",
            print_background=True,
            margin={"top": "18mm", "bottom": "18mm", "left": "15mm", "right": "15mm"}
        )
        page.close()
        print(f"[OK] PDF genere avec succes : {doc['pdf'].name} ({doc['pdf'].stat().st_size} octets)")
    browser.close()

print("Traitement termine avec succes.")
