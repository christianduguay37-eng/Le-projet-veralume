#!/usr/bin/env python3
"""
Générateur de rendu académique HTML / PDF pour le Papier de Recherche Kaggle / DeepMind
"""

import os
import re

def markdown_to_html(md_text):
    # Basic markdown parsing with KaTeX and styling
    html = md_text
    
    # Code blocks
    def code_repl(m):
        lang = m.group(1) or ""
        code = m.group(2).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if lang == "mermaid":
            return f'<div class="mermaid">\n{m.group(2)}\n</div>'
        return f'<pre><code class="language-{lang}">{code}</code></pre>'
    
    html = re.sub(r'```(\w+)?\n(.*?)```', code_repl, html, flags=re.DOTALL)
    
    # Headers
    html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Bold / Italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # Tables
    lines = html.split("\n")
    in_table = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith("|") and line.strip().endswith("|"):
            if not in_table:
                in_table = True
                new_lines.append('<div class="table-container"><table>')
            cells = [c.strip() for c in line.strip().split("|")[1:-1]]
            if all(set(c).issubset({'-', ':', ' '}) for c in cells):
                continue
            row_type = "th" if not in_table else "td"
            row = "".join([f"<{row_type}>{c}</{row_type}>" for c in cells])
            new_lines.append(f"<tr>{row}</tr>")
        else:
            if in_table:
                in_table = False
                new_lines.append("</table></div>")
            new_lines.append(line)
            
    if in_table:
        new_lines.append("</table></div>")
        
    html = "\n".join(new_lines)
    
    # Paragraphs
    paragraphs = html.split("\n\n")
    processed_p = []
    for p in paragraphs:
        p_str = p.strip()
        if not p_str.startswith("<h") and not p_str.startswith("<pre") and not p_str.startswith("<div") and not p_str.startswith("<tr>") and not p_str.startswith("<blockquote"):
            p_str = f"<p>{p_str}</p>"
        processed_p.append(p_str)
        
    html = "\n\n".join(processed_p)
    return html

def generate_paper_html():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(base_dir, "PAPIER_RECHERCHE_GEMMA_K_SIL_SWE_AGENT.md")
    output_html = os.path.join(base_dir, "PAPIER_RECHERCHE_GEMMA_K_SIL_SWE_AGENT.html")
    
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
        
    body_html = markdown_to_html(md_content)
    
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deterministic Scaffolding of Ultra-Frugal Edge LLMs (Gemma 4 Developer Agent)</title>
    <!-- KaTeX for math rendering -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
        onload="renderMathInElement(document.body, {{delimiters: [{{left: '$$', right: '$$', display: true}}, {{left: '$', right: '$', display: false}}]}});"></script>
    <!-- Mermaid for diagrams -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>mermaid.initialize({{startOnLoad:true, theme: 'neutral'}});</script>
    <style>
        :root {{
            --primary: #1a365d;
            --secondary: #2b6cb0;
            --accent: #27ae60;
            --bg: #ffffff;
            --text: #2d3748;
            --border: #e2e8f0;
        }}
        body {{
            font-family: 'Times New Roman', Times, serif;
            font-size: 15px;
            line-height: 1.6;
            color: var(--text);
            background-color: #f7fafc;
            margin: 0;
            padding: 20px;
        }}
        .paper-container {{
            max-width: 900px;
            margin: 0 auto;
            background: var(--bg);
            padding: 50px 70px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border-radius: 4px;
        }}
        h1 {{
            font-size: 26px;
            font-weight: bold;
            text-align: center;
            color: #111;
            margin-bottom: 12px;
            line-height: 1.3;
        }}
        h2 {{
            font-size: 20px;
            font-weight: bold;
            border-bottom: 2px solid var(--primary);
            padding-bottom: 5px;
            margin-top: 35px;
            color: var(--primary);
        }}
        h3 {{
            font-size: 16px;
            font-weight: bold;
            color: var(--secondary);
            margin-top: 25px;
        }}
        p {{
            text-align: justify;
            margin-bottom: 15px;
        }}
        .table-container {{
            overflow-x: auto;
            margin: 25px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 13px;
        }}
        th, td {{
            border: 1px solid var(--border);
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #edf2f7;
            color: #1a202c;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        pre {{
            background-color: #1a202c;
            color: #f7fafc;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 12px;
            font-family: 'Courier New', Courier, monospace;
        }}
        code {{
            background-color: #edf2f7;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 13px;
            color: #c53030;
        }}
        pre code {{
            background-color: transparent;
            color: inherit;
            padding: 0;
        }}
        .figure-box {{
            text-align: center;
            margin: 30px 0;
        }}
        .figure-box img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #cbd5e0;
            border-radius: 4px;
        }}
        .caption {{
            font-size: 12px;
            color: #718096;
            margin-top: 8px;
            font-style: italic;
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .paper-container {{
                box-shadow: none;
                padding: 0;
                max-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="paper-container">
        {body_html}
        <div class="figure-box">
            <img src="kaggle_gemma_ksil_benchmark_figures.png" alt="Empirical Benchmark Figures">
            <div class="caption">Figure 1: Energy dissipation (Joules), Pass@1 success rates, and in-silicon latency on Intel Core Ultra 7 258V (Lunar Lake) NPU (~2W) across 8 SRE benchmark tiers.</div>
        </div>
    </div>
</body>
</html>
"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print(f"[OK] Rendu HTML academique genere : {output_html}")

if __name__ == "__main__":
    generate_paper_html()
