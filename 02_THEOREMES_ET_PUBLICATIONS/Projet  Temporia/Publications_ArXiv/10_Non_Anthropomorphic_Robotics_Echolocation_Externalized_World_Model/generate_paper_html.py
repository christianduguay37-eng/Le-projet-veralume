import json
from pathlib import Path

p_md = Path('PAPIER_ZENODO_10_ROBOTIQUE_ECHOLOCALISATION.md')
content = p_md.read_text(encoding='utf-8')

html_template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Preprint 10 - Decoupled Reactive World Model and Non-Anthropomorphic Echolocation for Robotics</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  @page {{
    size: A4;
    margin: 18mm 15mm 18mm 15mm;
  }}
  body {{
    font-family: "Latin Modern Roman", "Times New Roman", Times, serif;
    font-size: 10pt;
    line-height: 1.45;
    color: #111;
    max-width: 820px;
    margin: 0 auto;
    padding: 15px;
    background: #fff;
  }}
  h1 {{
    font-size: 15pt;
    text-align: center;
    margin-bottom: 0.6em;
    font-weight: bold;
    color: #0d233a;
    line-height: 1.25;
  }}
  h2 {{
    font-size: 11.5pt;
    border-bottom: 1px solid #333;
    padding-bottom: 3px;
    margin-top: 1.4em;
    color: #111;
    text-transform: uppercase;
  }}
  h3 {{
    font-size: 10.5pt;
    margin-top: 1.1em;
    color: #111;
  }}
  blockquote {{
    background: #f8f9fa;
    border-left: 3px solid #0056b3;
    margin: 1.2em 0;
    padding: 8px 12px;
    font-size: 9.5pt;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.2em 0;
    font-size: 9pt;
  }}
  th, td {{
    border: 1px solid #ccc;
    padding: 5px 8px;
    text-align: left;
  }}
  th {{
    background: #f1f3f5;
    font-weight: bold;
  }}
  pre {{
    background: #f4f4f4;
    padding: 8px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 8.5pt;
    overflow-x: auto;
  }}
</style>
</head>
<body>
<div id="content"></div>
<script>
  const rawMarkdown = {json.dumps(content, ensure_ascii=False)};
  document.getElementById('content').innerHTML = marked.parse(rawMarkdown);
  window.addEventListener('DOMContentLoaded', () => {{
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

Path('paper.html').write_text(html_template, encoding='utf-8')
print("paper.html généré avec succès !")
