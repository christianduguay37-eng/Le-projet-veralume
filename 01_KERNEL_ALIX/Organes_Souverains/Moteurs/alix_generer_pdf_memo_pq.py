# -*- coding: utf-8 -*-
import os
import subprocess
import shutil

html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Mémo d'Orientation Stratégique — Christian Duguay</title>
<style>
  @page {
    size: letter;
    margin: 11mm 14mm 11mm 14mm;
  }
  body {
    font-family: "Segoe UI", "Calibri", "Helvetica Neue", Arial, sans-serif;
    color: #1a202c;
    line-height: 1.32;
    font-size: 9pt;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .header-banner {
    border-bottom: 3px solid #003366;
    padding-bottom: 8px;
    margin-bottom: 10px;
  }
  .doc-type {
    font-size: 8.5pt;
    font-weight: 700;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    color: #004B87;
    margin-bottom: 3px;
  }
  h1 {
    font-size: 15.5pt;
    font-weight: 800;
    color: #002244;
    margin: 2px 0 4px 0;
    line-height: 1.18;
  }
  .subtitle {
    font-size: 10pt;
    font-weight: 600;
    color: #2d3748;
    margin-bottom: 4px;
  }
  .meta-box {
    background-color: #f4f7fb;
    border-left: 4px solid #004B87;
    padding: 8px 12px;
    font-size: 9.2pt;
    margin-bottom: 12px;
  }
  .meta-box p {
    margin: 2px 0;
    text-align: left;
  }
  h2 {
    font-size: 10.8pt;
    font-weight: 700;
    color: #003366;
    border-bottom: 1.5px solid #cbd5e0;
    padding-bottom: 2px;
    margin-top: 9px;
    margin-bottom: 5px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    page-break-after: avoid;
  }
  h3 {
    font-size: 9.2pt;
    font-weight: 700;
    color: #003366;
    margin-top: 5px;
    margin-bottom: 2.5px;
    background-color: #edf2f7;
    border-left: 3.5px solid #004B87;
    padding: 2px 8px;
    page-break-after: avoid;
  }
  .portfolio-block {
    page-break-inside: avoid;
    margin-bottom: 3.5px;
  }
  p {
    margin: 4px 0;
    text-align: justify;
  }
  ul, ol {
    margin: 2px 0 4px 0;
    padding-left: 16px;
  }
  li {
    margin-bottom: 2px;
    text-align: justify;
  }
  .highlight-box {
    background-color: #f8fafc;
    border: 1px solid #cbd5e0;
    border-left: 4px solid #003366;
    padding: 8px 12px;
    margin: 8px 0;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 6px 0;
    font-size: 8.8pt;
    page-break-inside: avoid;
  }
  th {
    background-color: #003366;
    color: #ffffff;
    font-weight: 700;
    text-align: left;
    padding: 6px 8px;
    border: 1px solid #003366;
  }
  td {
    padding: 6px 8px;
    border: 1px solid #cbd5e0;
    vertical-align: top;
  }
  tr:nth-child(even) td {
    background-color: #f8fafc;
  }
  .badge-p1 {
    display: inline-block;
    background-color: #004B87;
    color: #ffffff;
    font-weight: 700;
    font-size: 7.3pt;
    padding: 0.5px 5px;
    border-radius: 2px;
    margin-right: 3px;
  }
  .badge-p2 {
    display: inline-block;
    background-color: #2b6cb0;
    color: #ffffff;
    font-weight: 700;
    font-size: 7.3pt;
    padding: 0.5px 5px;
    border-radius: 2px;
    margin-right: 3px;
  }
  .badge-p3 {
    display: inline-block;
    background-color: #4a5568;
    color: #ffffff;
    font-weight: 700;
    font-size: 7.3pt;
    padding: 0.5px 5px;
    border-radius: 2px;
    margin-right: 3px;
  }
  .page-break {
    page-break-before: always;
  }
  .page1-content {
    font-size: 9.6pt;
    line-height: 1.42;
  }
  .footer-sig {
    margin-top: 7px;
    border-top: 2px solid #003366;
    padding-top: 5px;
    font-size: 8.8pt;
    display: flex;
    justify-content: space-between;
  }
</style>
</head>
<body>

<div class="page1-content">
  <div class="header-banner">
    <div class="doc-type">Mémo d'Orientation Stratégique &amp; Gouvernance Opérationnelle — Québec</div>
    <h1>LA MATRICE DE TEMPORALITÉ DE L'ACTION PUBLIQUE</h1>
    <div class="subtitle">Désengorger immédiatement les services de l'État et agir sur les enjeux sociaux en séparant l'intervention administrative immédiate du chantier législatif lourd</div>
  </div>

  <div class="meta-box">
    <p><strong>Auteur :</strong> Christian Duguay — B.A. en développement social, cursus de 2<sup>e</sup> cycle en développement des sociétés et territoires (UQAR)</p>
    <p><strong>Destinataires :</strong> Direction du Parti Québécois / Cabinet &amp; Équipe de stratégie et des politiques publiques</p>
    <p><strong>Objet :</strong> Proposition stratégique de priorisation des interventions en début de mandat (Jours 1 à 45) pour débloquer la première ligne et faciliter en parallèle les grands chantiers législatifs</p>
  </div>

  <h2>1. Le Diagnostic Stratégique : Pourquoi les Gouvernements s'enlisent dans leurs Réformes</h2>
  <p>Depuis trois décennies au Québec, les gouvernements successifs commettent la même erreur d'ingénierie publique lorsqu'ils prennent le pouvoir : <strong>ils confondent l'action de l'État avec le processus législatif lourd.</strong></p>
  <p>Face à un problème dans les services sociaux, la santé, l'habitation, l'éducation ou le soutien communautaire, le réflexe systématique de l'appareil consiste à lancer un « projet de loi mammouth » ou une refonte d'organigramme qui exige <strong>12 à 24 mois</strong> de travaux parlementaires et <strong>24 à 48 mois</strong> d'implantation bureaucratique.</p>
  <p><strong>Conséquence politique et sociale :</strong> Pendant que le gouvernement épuise son capital politique sur un chantier de trois ans, des centaines de blocages quotidiens — qui ne relèvent d'aucune loi mais de simples directives administratives internes — continuent d'étouffer les services de première ligne. Le citoyen ne perçoit aucun résultat rapide, les intervenants s'épuisent, et lorsque la grande réforme législative finit par arriver, le réseau est déjà saturé.</p>

  <h2>2. La Méthode : La Matrice de Temporalité et l'Effet d'Entraînement</h2>
  <p>La clé pour reprendre le contrôle réel des services de l'État consiste à instaurer, dès la préparation gouvernementale, un <strong>tri systématique selon la temporalité d'action et la nature du levier</strong> :</p>

  <div class="highlight-box">
    <p><strong>Principe directeur : Régler les « petits bouchons » administratifs immédiatement pour débloquer les grands chantiers.</strong></p>
    <p>Il n'est pas nécessaire qu'un problème soit un grand débat législatif national pour agir dessus. En réglant dès les <strong>45 premiers jours</strong> (par simple directive ministérielle, sans projet de loi) une série de petits et moyens blocages administratifs qui paralysent le terrain, on fait baisser la pression dans tout l'appareil de l'État. Cette oxygénation immédiate libère des milliers d'heures d'intervention et <strong>facilite en parallèle la résolution des plus gros enjeux</strong> qui demandent des chantiers législatifs sur plusieurs mois ou années.</p>
  </div>

  <table>
    <thead>
      <tr>
        <th style="width: 19%;">Horizon Temporel</th>
        <th style="width: 26%;">Nature du Levier</th>
        <th style="width: 27%;">Cible d'Intervention</th>
        <th style="width: 28%;">Effet Stratégique &amp; Social</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>PALIER 1 : IMMÉDIAT</strong><br>(0 à 45 jours)<br><em>0 projet de loi</em></td>
        <td><strong>Administratif Pur</strong><br>Directives ministérielles, circulaires, formulaires, règles internes de gestion</td>
        <td>Blocages opérationnels quotidiens (CLSC, DPJ, HLM/SHQ, écoles, aide sociale, organismes communautaires)</td>
        <td><strong>Désengorgement immédiat :</strong> baisse de pression, milliers d'heures terrain libérées dès le 1<sup>er</sup> mois à coût quasi nul.</td>
      </tr>
      <tr>
        <td><strong>PALIER 2 : COURT TERME</strong><br>(45 à 120 jours)<br><em>0 projet de loi</em></td>
        <td><strong>Réglementaire &amp; Décrets</strong><br>Modification de règlements existants par le Conseil des ministres (<em>Gazette officielle</em>)</td>
        <td>Barèmes, seuils d'accès, actes professionnels délégués, marges de manœuvre régionales</td>
        <td><strong>Fluidification rapide :</strong> élimination des goulots d'étranglement interministériels et régionaux.</td>
      </tr>
      <tr>
        <td><strong>PALIER 3 : MOYEN / LONG TERME</strong><br>(6 à 36 mois)<br><em>Voie parlementaire</em></td>
        <td><strong>Politique Publique &amp; Projet de Loi</strong><br>Nouvelles lois, réformes structurelles, conventions et budgets</td>
        <td>Grands enjeux nationaux nécessitant formellement l'Assemblée nationale</td>
        <td><strong>Réussite des grands chantiers :</strong> la réforme s'implante dans un réseau déjà débloqué et réceptif grâce aux Paliers 1 et 2.</td>
      </tr>
    </tbody>
  </table>
</div>

<div class="page-break"></div>

<h2>3. Carnet d'Application Concrète sur 5 Portefeuilles Sociaux Névralgiques</h2>

<div class="portfolio-block">
<h3>I. Santé, Services Sociaux, CLSC &amp; Santé Mentale (MSSS)</h3>
<ul>
  <li><span class="badge-p1">PALIER 1 — Jours 1–30 (Administratif)</span> <strong>Abolition de la « Double Évaluation » CLSC / Communautaire :</strong> Circulaire ministérielle interdisant aux guichets CLSC de refaire une évaluation de 2 h lorsqu'un citoyen arrive avec une évaluation déjà réalisée par un travailleur social, psychologue ou organisme partenaire accrédité <em>(+15 à 20 % de temps clinique libéré dès le 1<sup>er</sup> mois).</em></li>
  <li><span class="badge-p1">PALIER 1 — Jours 1–30 (Administratif)</span> <strong>Coupure de 50 % des formulaires statistiques internes :</strong> Instruction sous-ministérielle suspendant les grilles de saisie redondantes qui absorbent près de 40 % du temps des intervenants de première ligne.</li>
  <li><span class="badge-p2">PALIER 2 — Jours 45–120 (Réglementaire)</span> <strong>Élargissement par décret des actes autonomes de première ligne</strong> (IPS, pharmaciens, travailleurs sociaux, psychothérapeutes) pour désengorger les médecins et les urgences.</li>
  <li><span class="badge-p3">PALIER 3 — Mois 6–36 (Législatif)</span> <strong>Décentralisation législative de la gouvernance locale et réforme de la rémunération médicale</strong> — chantier facilité par l'oxygène redonné aux équipes dès le Jour 30.</li>
</ul>
</div>

<div class="portfolio-block">
<h3>II. Protection de la Jeunesse (DPJ) &amp; Services à la Famille (MSSS / MFA)</h3>
<ul>
  <li><span class="badge-p1">PALIER 1 — Jours 1–30 (Administratif)</span> <strong>Fin de la « Preuve Annuelle de Guérison Miracle » pour enfants lourdement handicapés :</strong> Directive à Retraite Québec / RAMQ / MESS interdisant d'obliger chaque année les parents d'un enfant atteint d'un diagnostic permanent irréversible (autisme lourd, trisomie, paralysie cérébrale) à refaire remplir des certificats médicaux pour prouver que la condition permanente existe toujours.</li>
  <li><span class="badge-p1">PALIER 1 — Jours 1–30 (Administratif)</span> <strong>Coupe-circuit administratif DPJ &rarr; CLSC :</strong> Directive interdisant de fermer un signalement non retenu à la DPJ sans transfert actif garanti sous 15 jours vers l'aide préventive du CLSC ou d'une Maison de la famille.</li>
  <li><span class="badge-p3">PALIER 3 — Mois 6–36 (Législatif)</span> <strong>Réforme de la Loi sur la protection de la jeunesse (LPJ) et parachèvement du réseau des CPE.</strong></li>
</ul>
</div>

<div class="portfolio-block">
<h3>III. Habitation, Logement Social &amp; Itinérance (SHQ / MAMH)</h3>
<ul>
  <li><span class="badge-p1">PALIER 1 — Jours 1–45 (Administratif)</span> <strong>Déblocage en 30 jours des HLM vacants pour travaux mineurs :</strong> Directive interne de la SHQ autorisant les Offices d'habitation à remettre en état par bons de travail locaux accélérés tout logement social vacant nécessitant moins de 25 000 $ de travaux (peinture, plancher, plomberie), sans appel d'offres lourd.</li>
  <li><span class="badge-p1">PALIER 1 — Jours 1–45 (Administratif)</span> <strong>Analyse simultanée (en parallèle) à la SHQ :</strong> Instruction obligeant les directions financière, architecturale et légale de la SHQ à analyser les projets de logement communautaire simultanément sous un plafond de 30 jours, plutôt qu'à la file indienne sur 12 mois.</li>
  <li><span class="badge-p1">PALIER 1 — Jours 1–45 (Administratif)</span> <strong>Protocole interministériel « Zéro Sortie Sèche vers la Rue »</strong> à la sortie d'un centre jeunesse (18 ans), d'une unité psychiatrique ou d'un centre de détention.</li>
  <li><span class="badge-p3">PALIER 3 — Mois 6–36 (Législatif)</span> <strong>Loi-cadre sur le logement hors marché, réserve foncière publique et réforme du TAL.</strong></li>
</ul>
</div>

<div class="portfolio-block">
<h3>IV. Solidarité Sociale &amp; Action Communautaire Autonome (MESS)</h3>
<ul>
  <li><span class="badge-p1">PALIER 1 — Jours 1–30 (Administratif)</span> <strong>Unification en un seul rapport annuel court (3 pages)</strong> de la reddition de comptes des organismes communautaires (banques alimentaires, refuges, centres de crise), au lieu de multiplier les rapports par sous-projet.</li>
  <li><span class="badge-p1">PALIER 1 — Jours 1–30 (Administratif)</span> <strong>Suspension des contrôles administratifs tatillons sur les petits dons d'entraide familiale</strong> pour les prestataires à contraintes sévères, en réaffectant les agents à l'accompagnement rapide des personnes en crise.</li>
  <li><span class="badge-p2">PALIER 2 — Jours 45–120 (Réglementaire)</span> <strong>Hausse par décret réglementaire des revenus de travail permis</strong> sans pénalité sur les prestations d'aide sociale.</li>
</ul>
</div>

<div class="portfolio-block">
<h3>V. Éducation &amp; Services aux Élèves en Difficulté (MEQ)</h3>
<ul>
  <li><span class="badge-p1">PALIER 1 — Jours 1–30 (Administratif)</span> <strong>Fin de l'obligation du « Diagnostic Médical Préalable » pour aider un élève :</strong> Instruction ministérielle dans les Règles budgétaires des CSS stipulant que l'évaluation pédagogique de l'enseignant et de l'équipe-école suffit dès la semaine 1 pour activer l'aide (orthopédagogie / TES), sans attendre 2 ans de délais médicaux ou un diagnostic privé.</li>
  <li><span class="badge-p1">PALIER 1 — Jours 1–30 (Administratif)</span> <strong>Convention-type d'ouverture gratuite des gymnases et locaux scolaires après 16 h</strong> pour les organismes jeunesse et communautaires locaux.</li>
  <li><span class="badge-p3">PALIER 3 — Mois 6–36 (Législatif)</span> <strong>Réforme de la Loi sur l'instruction publique (LIP) et décentralisation vers l'école.</strong></li>
</ul>
</div>

<h2>4. Proposition d'Intervention à Titre de Consultant Stratégique</h2>
<ol>
  <li><strong>Auditer les engagements et les enjeux sociaux prioritaires</strong> pour séparer rigoureusement ce qui relève de la loi (Palier 3) de ce qui est exécutable immédiatement par voie administrative (Palier 1) ou réglementaire (Palier 2) ;</li>
  <li><strong>Établir le « Carnet des Déblocages Administratifs des 45 Premiers Jours »</strong> ministère par ministère, prêt à être signé dès la prise de fonction ;</li>
  <li><strong>Coordonner la séquence temporelle (Court terme &rarr; Moyen terme &rarr; Long terme)</strong> pour que la résolution rapide des irritants quotidiens serve de levier de réussite aux grandes politiques publiques du mandat.</li>
</ol>

<div class="footer-sig">
  <div><strong>Christian Duguay</strong> — Développement social (B.A.) &amp; Développement des sociétés et territoires (2<sup>e</sup> cycle, UQAR)</div>
  <div>Stratégie &amp; Politiques publiques</div>
</div>

</body>
</html>
"""

html_path = r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Memo_Strategique_Matrice_Temporalite_Action_Publique_Duguay.html"
pdf_vault_path = r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Memo_Strategique_Matrice_Temporalite_Action_Publique_Christian_Duguay.pdf"
pdf_desktop_path = str(Path.home() / "Desktop\Memo_Strategique_Matrice_Temporalite_Action_Publique_Christian_Duguay.pdf"

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

edge_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)
if edge_exe:
    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_vault_path}",
        html_path,
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(pdf_vault_path):
        shutil.copy2(pdf_vault_path, pdf_desktop_path)
        print("PDF_SUCCESS:", os.path.getsize(pdf_vault_path), "bytes")


