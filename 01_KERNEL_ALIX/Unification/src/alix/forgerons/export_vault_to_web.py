"""
Générateur de Site Web Interactif pour Cerveau Alix
Auteur: Christian Duguay & Alix
Système: VERALUME × KAIROS V6
"""

from alix.socle.chemins import VAULT_DIR
import os
import re
import sys
import json
from pathlib import Path

# Configuration de l'encodage standard pour l'environnement Windows
if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

VAULT_DIR = VAULT_DIR
OUTPUT_HTML = VAULT_DIR / "cerveau_alix_showcase.html"

def extract_metadata_and_content(file_path: Path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        with open(file_path, "r", encoding="latin-1") as f:
            raw = f.read()
            
    title = file_path.stem
    tags = []
    category = "Autre"
    content = raw
    
    # Frontmatter YAML
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            content = parts[2].strip()
            
            # Extraction titre
            m_titre = re.search(r'titre:\s*["\']?(.*?)["\']?\s*$', fm_text, re.MULTILINE)
            if m_titre:
                title = m_titre.group(1).strip()
                
            # Extraction tags
            m_tags = re.findall(r'-\s+([a-zA-Z0-9_-]+)', fm_text)
            if m_tags:
                tags = m_tags
                
    # Catégorisation intelligente
    name_lower = file_path.stem.lower()
    if "opérateur" in name_lower or "operateur" in name_lower:
        category = "Opérateurs VERALUME"
    elif "protocole" in name_lower or "sonde" in name_lower or "heuristique" in name_lower:
        category = "Protocoles d'Immunité"
    elif "moteur" in name_lower or "kernel" in name_lower or "engine" in name_lower:
        category = "Moteurs & Algorithmes"
    elif "tableau" in name_lower or "double stric" in name_lower or "temporia" in name_lower or "prise de terre" in name_lower or "cartographie" in name_lower:
        category = "Piliers & Cartographies"
    elif "noeud" in name_lower or "matrice" in name_lower or "pattern" in name_lower:
        category = "Matrices & Nœuds KAIROS"
    elif "memoire" in name_lower or "audit" in name_lower:
        category = "Système & Mémoire Active"
        
    return {
        "id": file_path.stem,
        "title": title,
        "category": category,
        "tags": tags,
        "content": content
    }

def build_showcase():
    md_files = [f for f in VAULT_DIR.glob("*.md") if not f.name.startswith(".")]
    notes_data = {}
    
    for f in md_files:
        data = extract_metadata_and_content(f)
        notes_data[data["id"]] = data
        
    # Extraction des liens
    links = []
    in_degrees = {k: 0 for k in notes_data}
    
    for src_id, note in notes_data.items():
        targets = re.findall(r'\[\[(.*?)\]\]', note["content"])
        for tgt in targets:
            tgt_clean = tgt.split("|")[0].split("#")[0].strip()
            if tgt_clean in notes_data:
                links.append({"source": src_id, "target": tgt_clean})
                in_degrees[tgt_clean] = in_degrees.get(tgt_clean, 0) + 1
                
    # Construction des nœuds pour D3
    nodes = []
    category_colors = {
        "Piliers & Cartographies": "#00f0ff",
        "Opérateurs VERALUME": "#10b981",
        "Moteurs & Algorithmes": "#a855f7",
        "Protocoles d'Immunité": "#f59e0b",
        "Matrices & Nœuds KAIROS": "#ec4899",
        "Système & Mémoire Active": "#6366f1",
        "Autre": "#94a3b8"
    }
    
    for note_id, note in notes_data.items():
        score = in_degrees.get(note_id, 0)
        radius = max(6, min(24, 6 + score * 1.4))
        nodes.append({
            "id": note_id,
            "title": note["title"],
            "category": note["category"],
            "color": category_colors.get(note["category"], "#94a3b8"),
            "radius": radius,
            "in_degree": score
        })
        
    html_template = """<!DOCTYPE html>
<html lang="fr" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 Cerveau Alix — Exploration Interactive</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        cyber: {
                            900: '#0a0d14',
                            800: '#0f172a',
                            700: '#1e293b',
                            cyan: '#00f0ff',
                            emerald: '#10b981',
                            purple: '#a855f7',
                            amber: '#f59e0b'
                        }
                    }
                }
            }
        }
    </script>
    
    <!-- D3.js pour le Graphe -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <!-- Marked.js pour le Markdown -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <!-- KaTeX pour les Formules Mathématiques -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    <!-- Highlight.js pour le Code -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    
    <style>
        body { background-color: #07090e; color: #e2e8f0; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .glass-panel { background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow-cyan { box-shadow: 0 0 25px rgba(0, 240, 255, 0.2); }
        
        /* Markdown Pro Styling */
        .markdown-body h1 { font-size: 1.8rem; font-weight: 800; color: #00f0ff; margin-bottom: 1rem; border-bottom: 1px solid rgba(0,240,255,0.2); padding-bottom: 0.5rem; }
        .markdown-body h2 { font-size: 1.4rem; font-weight: 700; color: #38bdf8; margin-top: 1.5rem; margin-bottom: 0.75rem; }
        .markdown-body h3 { font-size: 1.15rem; font-weight: 600; color: #a5f3fc; margin-top: 1.25rem; margin-bottom: 0.5rem; }
        .markdown-body p { margin-bottom: 1rem; line-height: 1.7; color: #cbd5e1; }
        .markdown-body ul, .markdown-body ol { margin-left: 1.5rem; margin-bottom: 1rem; list-style-type: disc; color: #cbd5e1; }
        .markdown-body blockquote { border-left: 4px solid #00f0ff; padding-left: 1rem; font-style: italic; background: rgba(0, 240, 255, 0.05); padding-top: 0.5rem; padding-bottom: 0.5rem; border-radius: 0 8px 8px 0; margin-bottom: 1rem; }
        .markdown-body code:not(pre code) { background: rgba(30, 41, 59, 0.8); color: #38bdf8; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.9em; }
        .markdown-body pre { background: #0b1120; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; overflow-x: auto; }
        .markdown-body table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; }
        .markdown-body th, .markdown-body td { border: 1px solid rgba(255,255,255,0.1); padding: 0.6rem 0.8rem; text-align: left; }
        .markdown-body th { background: rgba(30, 41, 59, 0.6); color: #00f0ff; }
        
        .wikilink { color: #00f0ff; text-decoration: none; border-bottom: 1px dashed #00f0ff; cursor: pointer; transition: all 0.2s; }
        .wikilink:hover { color: #ffffff; background: rgba(0, 240, 255, 0.2); border-radius: 2px; }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: rgba(15, 23, 42, 0.6); }
        ::-webkit-scrollbar-thumb { background: rgba(56, 189, 248, 0.3); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(0, 240, 255, 0.6); }
    </style>
</head>
<body class="h-screen flex flex-col overflow-hidden">

    <!-- Header Navigation -->
    <header class="h-16 glass-panel border-b border-slate-800 flex items-center justify-between px-6 z-20 shrink-0">
        <div class="flex items-center space-x-3 cursor-pointer" onclick="loadNote('TABLEAU_DE_BORD')">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 flex items-center justify-center text-xl shadow-lg shadow-cyan-500/20">
                🧠
            </div>
            <div>
                <h1 class="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                    CERVEAU ALIX
                    <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">VERALUME × KAIROS V6</span>
                </h1>
                <p class="text-xs text-slate-400">Exocerveau & Ingénierie Cognitive — Christian Duguay</p>
            </div>
        </div>

        <!-- Center Controls -->
        <div class="flex items-center space-x-2 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
            <button id="btn-reader" onclick="switchView('reader')" class="px-4 py-1.5 rounded-lg text-xs font-semibold transition bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                📖 Fiches & Notes
            </button>
            <button id="btn-graph" onclick="switchView('graph')" class="px-4 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition">
                🌌 Vue Graphique
            </button>
        </div>

        <!-- Right Stats -->
        <div class="flex items-center space-x-4 text-xs font-mono text-slate-400">
            <div class="flex items-center gap-1.5 bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-700/50">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span><strong class="text-white">__TOTAL_NOTES__</strong> Notes</span>
            </div>
            <div class="flex items-center gap-1.5 bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-700/50">
                <span class="text-cyan-400 font-bold">__TOTAL_LINKS__</span> Liens
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <div class="flex-1 flex overflow-hidden relative">
        
        <!-- Left Sidebar (Explorateur de Notes) -->
        <aside class="w-80 glass-panel border-r border-slate-800 flex flex-col shrink-0 z-10">
            <!-- Search Box -->
            <div class="p-4 border-b border-slate-800/60">
                <div class="relative">
                    <input type="text" id="searchInput" placeholder="Rechercher une idée, formule, opérateur..." 
                        class="w-full bg-slate-900/90 border border-slate-700/80 rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition">
                    <span class="absolute left-3 top-2.5 text-slate-500 text-xs">🔍</span>
                </div>
            </div>

            <!-- Notes List -->
            <div class="flex-1 overflow-y-auto p-3 space-y-4" id="notesList">
                <!-- Injected via JavaScript -->
            </div>
        </aside>

        <!-- Center Content Area -->
        <main class="flex-1 flex flex-col relative overflow-hidden bg-gradient-to-b from-[#07090e] to-[#0b1120]">
            
            <!-- VIEW 1: Reader View -->
            <div id="view-reader" class="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto w-full">
                <div class="glass-panel p-8 rounded-2xl glow-cyan border border-slate-800/80">
                    <div id="note-header" class="mb-6 pb-4 border-b border-slate-800 flex justify-between items-start">
                        <div>
                            <span id="note-category-badge" class="text-xs px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
                                Catégorie
                            </span>
                            <h2 id="note-title" class="text-2xl font-bold text-white mt-2">Titre de la note</h2>
                        </div>
                        <button onclick="switchView('graph')" class="text-xs text-slate-400 hover:text-cyan-400 flex items-center gap-1 border border-slate-700 px-3 py-1.5 rounded-lg">
                            🌌 Voir dans le Graphe
                        </button>
                    </div>
                    
                    <div id="note-body" class="markdown-body text-sm">
                        <!-- Markdown Rendered Content -->
                    </div>

                    <!-- Backlinks Footer -->
                    <div id="note-backlinks" class="mt-10 pt-6 border-t border-slate-800/80">
                        <h4 class="text-xs font-mono uppercase text-slate-400 tracking-wider mb-3">🔗 Notes connectées à ce nœud :</h4>
                        <div id="backlinks-container" class="flex flex-wrap gap-2">
                            <!-- Injected Backlinks -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- VIEW 2: Interactive Graph View -->
            <div id="view-graph" class="flex-1 w-full h-full hidden relative">
                <svg id="graph-svg" class="w-full h-full cursor-grab active:cursor-grabbing"></svg>
                
                <!-- Graph Floating Overlay Controls -->
                <div class="absolute bottom-6 right-6 glass-panel px-4 py-3 rounded-xl border border-slate-700 flex items-center gap-4 text-xs font-mono text-slate-300">
                    <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#00f0ff]"></span> Piliers</div>
                    <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#10b981]"></span> Opérateurs</div>
                    <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#a855f7]"></span> Moteurs</div>
                    <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#f59e0b]"></span> Immunité</div>
                    <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-[#ec4899]"></span> Matrices</div>
                </div>

                <div class="absolute top-6 left-6 glass-panel px-4 py-2 rounded-xl text-xs text-slate-400">
                    💡 <em>Clique sur un nœud pour ouvrir la fiche. Molette pour zoomer / glisser pour explorer.</em>
                </div>
            </div>

        </main>
    </div>

    <!-- Data Injection -->
    <script>
        const VAULT_DATA = __VAULT_JSON__;
        const GRAPH_NODES = __GRAPH_NODES_JSON__;
        const GRAPH_LINKS = __GRAPH_LINKS_JSON__;
    </script>

    <!-- Application Script -->
    <script>
        let currentNoteId = "TABLEAU_DE_BORD";
        let simulation = null;

        // Custom Renderer for Wikilinks
        function parseWikilinks(markdownText) {
            return markdownText.replace(/\\[\\[(.*?)\\]\\]/g, (match, p1) => {
                let target = p1.trim();
                let label = target;
                if (target.includes("|")) {
                    const parts = target.split("|");
                    target = parts[0].trim();
                    label = parts[1].trim();
                }
                const targetKey = target.split("#")[0].trim();
                if (VAULT_DATA[targetKey]) {
                    return `<a class="wikilink" onclick="loadNote('${targetKey}')">${label}</a>`;
                }
                return `<span class="text-slate-500 underline decoration-dotted" title="Note non créée">${label}</span>`;
            });
        }

        function loadNote(noteId) {
            if (!VAULT_DATA[noteId]) return;
            currentNoteId = noteId;
            const note = VAULT_DATA[noteId];

            document.getElementById('note-title').textContent = note.title;
            document.getElementById('note-category-badge').textContent = note.category;
            
            // Render Markdown
            const parsedText = parseWikilinks(note.content);
            document.getElementById('note-body').innerHTML = marked.parse(parsedText);
            
            // Math Render
            renderMathInElement(document.getElementById('note-body'), {
                delimiters: [
                    {left: '$$', right: '$$', display: true},
                    {left: '$', right: '$', display: false}
                ],
                throwOnError: false
            });

            // Code Syntax Highlight
            document.querySelectorAll('#note-body pre code').forEach((el) => {
                hljs.highlightElement(el);
            });

            // Render Backlinks
            const backlinksContainer = document.getElementById('backlinks-container');
            backlinksContainer.innerHTML = '';
            
            const incoming = GRAPH_LINKS.filter(l => (typeof l.target === 'object' ? l.target.id : l.target) === noteId);
            if (incoming.length > 0) {
                incoming.forEach(link => {
                    const srcId = typeof link.source === 'object' ? link.source.id : link.source;
                    const srcNote = VAULT_DATA[srcId];
                    if (srcNote) {
                        const badge = document.createElement('button');
                        badge.className = 'text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-cyan-500/20 hover:text-cyan-300 text-slate-300 border border-slate-700 transition font-mono';
                        badge.textContent = `[[${srcNote.title}]]`;
                        badge.onclick = () => loadNote(srcId);
                        backlinksContainer.appendChild(badge);
                    }
                });
            } else {
                backlinksContainer.innerHTML = '<span class="text-xs text-slate-500 italic">Aucune note liée en amont.</span>';
            }

            // Scroll to top
            document.getElementById('view-reader').scrollTop = 0;
            switchView('reader');

            // Update Active in List
            document.querySelectorAll('.note-item').forEach(el => {
                el.classList.remove('bg-cyan-500/20', 'border-cyan-500/40', 'text-cyan-300');
                if (el.dataset.id === noteId) {
                    el.classList.add('bg-cyan-500/20', 'border-cyan-500/40', 'text-cyan-300');
                }
            });
        }

        function switchView(viewName) {
            if (viewName === 'reader') {
                document.getElementById('view-reader').classList.remove('hidden');
                document.getElementById('view-graph').classList.add('hidden');
                document.getElementById('btn-reader').className = "px-4 py-1.5 rounded-lg text-xs font-semibold transition bg-cyan-500/20 text-cyan-300 border border-cyan-500/30";
                document.getElementById('btn-graph').className = "px-4 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition";
            } else {
                document.getElementById('view-reader').classList.add('hidden');
                document.getElementById('view-graph').classList.remove('hidden');
                document.getElementById('btn-graph').className = "px-4 py-1.5 rounded-lg text-xs font-semibold transition bg-cyan-500/20 text-cyan-300 border border-cyan-500/30";
                document.getElementById('btn-reader').className = "px-4 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white transition";
                initGraph();
            }
        }

        function renderSidebar() {
            const list = document.getElementById('notesList');
            list.innerHTML = '';
            
            const categories = {};
            Object.values(VAULT_DATA).forEach(note => {
                if (!categories[note.category]) categories[note.category] = [];
                categories[note.category].push(note);
            });

            for (const [catName, catNotes] of Object.entries(categories)) {
                const catGroup = document.createElement('div');
                catGroup.className = 'space-y-1';
                
                const catTitle = document.createElement('h3');
                catTitle.className = 'text-xs font-mono font-bold uppercase text-slate-400 tracking-wider px-2 py-1';
                catTitle.textContent = `${catName} (${catNotes.length})`;
                catGroup.appendChild(catTitle);

                catNotes.forEach(note => {
                    const btn = document.createElement('button');
                    btn.className = `note-item w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center justify-between border border-transparent hover:bg-slate-800 text-slate-300`;
                    btn.dataset.id = note.id;
                    btn.innerHTML = `<span class="truncate">${note.title}</span>`;
                    btn.onclick = () => loadNote(note.id);
                    catGroup.appendChild(btn);
                });

                list.appendChild(catGroup);
            }
        }

        // Search Filter
        document.getElementById('searchInput').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.note-item').forEach(el => {
                const id = el.dataset.id;
                const note = VAULT_DATA[id];
                const match = note.title.toLowerCase().includes(query) || note.content.toLowerCase().includes(query);
                el.style.display = match ? 'flex' : 'none';
            });
        });

        // Initialize D3 Graph
        function initGraph() {
            const svg = d3.select("#graph-svg");
            svg.selectAll("*").remove();

            const width = svg.node().parentElement.clientWidth;
            const height = svg.node().parentElement.clientHeight;

            const g = svg.append("g");

            // Zoom
            const zoom = d3.zoom()
                .scaleExtent([0.1, 4])
                .on("zoom", (event) => g.attr("transform", event.transform));
            svg.call(zoom);

            simulation = d3.forceSimulation(GRAPH_NODES)
                .force("link", d3.forceLink(GRAPH_LINKS).id(d => d.id).distance(60))
                .force("charge", d3.forceManyBody().strength(-120))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(d => d.radius + 6));

            // Draw Links
            const link = g.append("g")
                .selectAll("line")
                .data(GRAPH_LINKS)
                .join("line")
                .attr("stroke", "rgba(255, 255, 255, 0.12)")
                .attr("stroke-width", 1);

            // Draw Nodes
            const node = g.append("g")
                .selectAll("g")
                .data(GRAPH_NODES)
                .join("g")
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended))
                .on("click", (event, d) => loadNote(d.id));

            node.append("circle")
                .attr("r", d => d.radius)
                .attr("fill", d => d.color)
                .attr("stroke", "#ffffff")
                .attr("stroke-width", d => d.id === currentNoteId ? 2.5 : 0.8)
                .attr("class", "transition duration-200 hover:brightness-125");

            node.append("text")
                .text(d => d.title.length > 20 ? d.title.substring(0, 18) + '...' : d.title)
                .attr("x", d => d.radius + 4)
                .attr("y", 4)
                .attr("font-size", "10px")
                .attr("fill", "#cbd5e1")
                .attr("font-family", "system-ui")
                .attr("pointer-events", "none");

            simulation.on("tick", () => {
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                node.attr("transform", d => `translate(${d.x},${d.y})`);
            });

            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }

            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }

            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
        }

        // Init App
        renderSidebar();
        loadNote("TABLEAU_DE_BORD");
    </script>
</body>
</html>"""

    # Remplacement des balises templates
    total_notes_str = str(len(notes_data))
    total_links_str = str(len(links))
    
    html_output = html_template.replace("__TOTAL_NOTES__", total_notes_str)
    html_output = html_output.replace("__TOTAL_LINKS__", total_links_str)
    html_output = html_output.replace("__VAULT_JSON__", json.dumps(notes_data, ensure_ascii=False))
    html_output = html_output.replace("__GRAPH_NODES_JSON__", json.dumps(nodes, ensure_ascii=False))
    html_output = html_output.replace("__GRAPH_LINKS_JSON__", json.dumps(links, ensure_ascii=False))
    
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_output)
        
    print(f"✅ Site interactif généré avec succès dans : {OUTPUT_HTML}")
    print(f"📊 {len(notes_data)} notes et {len(links)} liens compilés en un fichier unique autonome.")

if __name__ == "__main__":
    build_showcase()
