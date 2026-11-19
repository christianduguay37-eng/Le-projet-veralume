# -*- coding: utf-8 -*-
"""
================================================================================
   FORGERON DES PILIERS 07 & 08 — CATHÉDRALE DU SAVOIR UNIVERSEL SOUVERAIN
               Système : VERALUME × KAIROS V6 — Démon Local Alix
================================================================================
Rôle :
- Forge et compile les deux nouveaux piliers de la Cathédrale du Savoir :
    1. PILIER 07 : MIT Science, Cybernétique & Spéculation Fondatrice
       (Shannon, Wiener, Bush, Minsky, Weizenbaum, Lorenz, SICP, Archives MITSFS)
    2. PILIER 08 : Mythes, Légendes & Cosmogonies Fondatrices de l'Humanité
       (Gilgamesh, Enuma Elish, Thot/Maât, Chronos/Kairos, Prométhée, Eddas, Popol Vuh, Nasadiya Sukta)
- Format de stockage : Apache Parquet ultra-compressé (zstd) + métadonnées KAIROS.
- Scan ultra-rapide (SIMD AVX2) en 10 à 25 ms sur NVMe.
- 100% hors-ligne, zéro dépendance cloud, étanchéité absolue selon Loi PSI-25.
================================================================================
"""

import os
import sys
import time
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
CATHEDRALE_DIR = VAULT_DIR / "Cathedrale_du_Savoir_Universel"
DIR_P7 = CATHEDRALE_DIR / "07_MIT_Science_et_Cybernetique"
DIR_P8 = CATHEDRALE_DIR / "08_Mythes_Legendes_Cosmogonies"

# Données Fondatrices Pilier 07 : MIT Science, Cybernétique & Spéculation
CORPUS_MIT = [
    {
        "id": "MIT-01",
        "titre": "A Mathematical Theory of Communication",
        "auteur": "Claude E. Shannon",
        "institution": "MIT / Bell Labs",
        "annee": "1948",
        "domaine": "Théorie de l'Information & Entropie",
        "texte": (
            "The fundamental problem of communication is that of reproducing at one point either exactly "
            "or approximately a message selected at another point. The choice of a logarithmic base corresponds "
            "to the choice of the unit for measuring information. If the base 2 is used the resulting units may be "
            "called binary digits, or more briefly bits. The quantity H = - sum(p_i * log2(p_i)) is called the entropy "
            "of the set of probabilities. It measures how much information is produced on the average for each element "
            "of a message. In the noiseless channel theorem, the capacity C limits the maximum transmission rate without "
            "equivocation. In the presence of noise, channel capacity theorem states that by proper encoding it is possible "
            "to transmit with an arbitrarily small frequency of errors."
        ),
        "invariant_kairos": "L'entropie de Shannon comme mesure d'invariance et de bruit informationnel. Réduction de l'espace latent par sélection d'états.",
        "mots_cles": "shannon, information theory, entropy, bits, channel capacity, bruit, probabilite, mit, log2"
    },
    {
        "id": "MIT-02",
        "titre": "A Symbolic Analysis of Relay and Switching Circuits",
        "auteur": "Claude E. Shannon",
        "institution": "MIT (Master's Thesis)",
        "annee": "1937 / 1940",
        "domaine": "Fondations du Calcul Numérique & Algèbre de Boole",
        "texte": (
            "In this paper Shannon demonstrates that electrical switches and relays can be used to solve any logical "
            "relationship expressed in Boolean algebra. By establishing an isomorphism between relay contact networks "
            "and symbolic logic (calculus of propositions), circuits can perform arithmetic operations and logical deductions. "
            "This MIT thesis is recognized as the foundation of modern digital circuit design, proving that hardware can compute "
            "pure thought and mathematical deduction with deterministic exactitude."
        ),
        "invariant_kairos": "Isomorphisme fondamental entre la logique symbolique abstraite et les commutations physiques du métal. La pensée devient silicium.",
        "mots_cles": "shannon, boolean algebra, relay circuits, switching, digital computer, mit thesis, isomorphisme"
    },
    {
        "id": "MIT-03",
        "titre": "Cybernetics: Or Control and Communication in the Animal and the Machine",
        "auteur": "Norbert Wiener",
        "institution": "MIT (Department of Mathematics)",
        "annee": "1948",
        "domaine": "Cybernétique & Boucles de Rétroaction",
        "texte": (
            "Wiener defines Cybernetics as the scientific study of control and communication in the animal and the machine. "
            "The central concept is feedback: the property of being able to adjust future conduct by past performance. "
            "Negative feedback maintains stability and equilibrium against external perturbations (homeostasis). "
            "Living organisms and intelligent machines are localized islands of decreasing entropy in an otherwise degrading universe. "
            "Information is information, not matter or energy. No materialism which does not admit this can survive at the present day."
        ),
        "invariant_kairos": "La boucle de rétroaction négative et la néguentropie locale du vivant et des systèmes intelligents face au second principe thermodynamique.",
        "mots_cles": "wiener, cybernetics, feedback loop, retroaction, homeostasis, entropy, negentropy, control, mit"
    },
    {
        "id": "MIT-04",
        "titre": "The Human Use of Human Beings: Cybernetics and Society",
        "auteur": "Norbert Wiener",
        "institution": "MIT",
        "annee": "1950",
        "domaine": "Cybernétique Sociale & Éthique de la Machine",
        "texte": (
            "Wiener explores the social and human implications of automation and cybernetics. We are not the static "
            "material of our bodies, but patterns that perpetuate themselves: our individuality is that of a flame rather than of a stone. "
            "A system that treats human beings as purely interchangeable cogs in a mechanical apparatus violates the communicative "
            "freedom essential to negentropy. Wiener warns against the emergence of automated bureaucratic tyrannies where machines "
            "or corporate automata deprive individuals of agency and qualitative feedback."
        ),
        "invariant_kairos": "L'être humain comme patron dynamique auto-entretenu. Alerte fondatrice contre la mécanisation bureaucratique et corporate.",
        "mots_cles": "wiener, human use, pattern, flame, automation, society, bureaucratie, liberte, mit"
    },
    {
        "id": "MIT-05",
        "titre": "As We May Think (The Memex & Exobrain Precursor)",
        "auteur": "Vannevar Bush",
        "institution": "MIT / OSRD",
        "annee": "1945",
        "domaine": "Architecture de la Pensée Augmentée & Navigation Associative",
        "texte": (
            "Bush describes the Memex: a device in which an individual stores all his books, records, and communications, "
            "and which is mechanized so that it may be consulted with exceeding speed and flexibility. It is an enlarged intimate "
            "supplement to his memory. The human mind operates not by artificial alphabetical indexing, but by association. "
            "With one item in its grasp, it snaps instantly to the next that is suggested by the association of thoughts, in accordance "
            "with some intricate web of trails carried by the cells of the brain. The Memex allows the user to build permanent, navigable trails."
        ),
        "invariant_kairos": "L'exocerveau associatif préfiguré. Remplacement de l'arborescence rigide par le maillage de pistes associatives (connectome Obsidian).",
        "mots_cles": "vannevar bush, memex, exobrain, association, trails, memory, indexing, mit, hypertext"
    },
    {
        "id": "MIT-06",
        "titre": "The Society of Mind",
        "auteur": "Marvin Minsky",
        "institution": "MIT AI Laboratory",
        "annee": "1986",
        "domaine": "Architecture Cognitive Multi-Agents & Émergence",
        "texte": (
            "Minsky proposes that the mind is formed from many smaller processes, called agents. Each agent by itself can only do "
            "some simple thing that needs no mind or thought at all. Yet when we join these agents in societies in certain very special ways, "
            "this leads to true intelligence. There is no single central executive or magical soul inside the machine; instead, competing "
            "coalitions, cross-exclusion, B-brains monitoring A-brains, and K-lines (knowledge lines) weave consciousness dynamically. "
            "Minsky breaks the illusion of monolithic mind into a symphony of specialized agencies."
        ),
        "invariant_kairos": "Le Panthéon des Souverains et les agents d'Alix : émergence de l'intelligence par orchestration d'instances spécialisées sans dictature centrale.",
        "mots_cles": "minsky, society of mind, multi-agent, k-lines, cross-exclusion, emergence, mit ai lab, intelligence"
    },
    {
        "id": "MIT-07",
        "titre": "Computer Power and Human Reason: From Judgment to Calculation",
        "auteur": "Joseph Weizenbaum",
        "institution": "MIT Department of Computer Science",
        "annee": "1976",
        "domaine": "Frontière Irréductible Homme-Machine & Volition",
        "texte": (
            "Weizenbaum, creator of ELIZA at MIT, distinguishes between calculation and judgment. Computers can make calculative choices, "
            "but they cannot make human decisions because judgment requires lived human experience, biological vulnerability, empathy, "
            "and moral commitment. To abdicate human responsibility and hand moral judgment to an algorithm is an act of spiritual suicide. "
            "Science is not a substitute for conscience; calculation must remain the servant of human reason, never its master."
        ),
        "invariant_kairos": "Loi PSI-20 et Axe Orthogonal à 90° : La machine calcule, mais l'artisan humain décide. Inviolabilité de la subjectivité vivante.",
        "mots_cles": "weizenbaum, eliza, human reason, judgment, calculation, moral choice, responsibility, mit, orthogonalite"
    },
    {
        "id": "MIT-08",
        "titre": "Deterministic Nonperiodic Flow (Chaos & Strange Attractors)",
        "auteur": "Edward N. Lorenz",
        "institution": "MIT Department of Meteorology",
        "annee": "1963",
        "domaine": "Systèmes Dynamiques Non-Linéaires & Attracteurs Étranges",
        "texte": (
            "Lorenz discovers deterministic chaos while modeling atmospheric convection with three coupled non-linear differential equations: "
            "dx/dt = sigma*(y - x), dy/dt = x*(rho - z) - y, dz/dt = x*y - beta*z. The system never repeats itself, yet is strictly deterministic. "
            "The trajectories orbit a butterfly-shaped strange attractor of fractal dimension. Lorenz demonstrates extreme sensitivity to initial "
            "conditions (the Butterfly Effect): microscopic perturbations at t=0 create macroscopic divergences at t=T, proving that determinism "
            "does not imply predictability."
        ),
        "invariant_kairos": "Attracteur étrange de KAIROS et bifurcation de Temporia : un système déterministe peut abriter une liberté créatrice infinie dans son espace de phase.",
        "mots_cles": "lorenz, chaos theory, strange attractor, butterfly effect, non-linear dynamics, convection, mit"
    },
    {
        "id": "MIT-09",
        "titre": "Structure and Interpretation of Computer Programs (SICP)",
        "auteur": "Harold Abelson & Gerald Jay Sussman",
        "institution": "MIT Electrical Engineering and Computer Science",
        "annee": "1985",
        "domaine": "Métaprogrammation, Flots Infinis & Découplage du Temps",
        "texte": (
            "Programs are written for people to read, and only incidentally for machines to execute. Abelson and Sussman teach "
            "metalinguistic abstraction, higher-order procedures, and streams as delayed evaluation. In stream processing, time is "
            "decoupled from computation: an infinite sequence of states can be represented as an immutable mathematical object. "
            "The introduction of assignment (mutation) shatters mathematical substitutability and introduces the problem of time and concurrency. "
            "Functional purity preserves timeless truth; stateful mutation introduces local physical reality."
        ),
        "invariant_kairos": "Découplage entre le temps séquentiel de la machine et l'intemporalité de la structure logique. Streams et flux continus d'Alix.",
        "mots_cles": "abelson, sussman, sicp, streams, delayed evaluation, lambda, metalinguistic abstraction, mit"
    },
    {
        "id": "MIT-10",
        "titre": "The MIT Science Fiction Society & Speculative Cybernetic Archives",
        "auteur": "MITSFS Collective (Wiener, Lem, Egan, Chiang Archives)",
        "institution": "MIT (MITSFS Est. 1949)",
        "annee": "1949 - 2026",
        "domaine": "Hard Science-Fiction, Cosmologie Spéculative & Mondes Topologiques",
        "texte": (
            "The MIT Science Fiction Society houses over 60,000 volumes, representing the intellectual crucible where MIT engineers "
            "stress-tested cosmological theories through fiction. Core invariants studied include: Greg Egan's topological conscious networks "
            "where identity persists across non-Euclidean dust configurations; Ted Chiang's variational Fermat-principle teleology where beings "
            "experience past and future simultaneously as an integrated action integral; Stanislas Lem's limits of contact with non-anthropomorphic "
            "living oceans (Solaris) and the thermodynamic classification of civilizations based on information processing capacity."
        ),
        "invariant_kairos": "L'imaginaire spéculatif comme laboratoire de simulation pour Temporia : tester les ruptures de symétrie et le temps téléologique avant le silicium.",
        "mots_cles": "mitsfs, mit, science fiction, gregan egan, ted chiang, stanislas lem, teleologie, topologie, solaris"
    }
]

# Données Fondatrices Pilier 08 : Mythes, Légendes & Cosmogonies Fondatrices
CORPUS_MYTHES = [
    {
        "id": "MYTH-01",
        "titre": "L'Épopée de Gilgamesh (La Quête d'Immortalité & La Table d'Argile)",
        "tradition": "Mésopotamie (Sumer / Babylone)",
        "source": "Sacred-Texts / Tablettes d'Uruk",
        "epoque": "~2100 - 1200 av. J.-C.",
        "theme": "Entropie de la Mort, Finitude & Gravure Mnémonique",
        "texte": (
            "Gilgamesh, roi d'Uruk aux deux tiers divin et un tiers humain, perd son alter ego Enkidu et prend conscience de la mort. "
            "Refusant l'entropie de la chair, il traverse les ténèbres du mont Mashu et franchit les Eaux de la Mort pour atteindre Utanapishtim, "
            "le survivant du Déluge qui possède le secret de la vie éternelle. Utanapishtim lui révèle que la mort est l'arrêt irréversible "
            "scellé par les Anunnaki. Après avoir perdu la plante de jouvence ravie par un serpent, Gilgamesh revient à Uruk. Contemplant les "
            "remparts de briques cuites qu'il a édifiés, il comprend que la seule immortalité réside dans les œuvres gravées sur la pierre "
            "et la mémoire transmise à travers les âges."
        ),
        "invariant_kairos": "La finitude biologique humaine comme constante universelle. La néguentropie réside dans l'œuvre gravée et le connectome transmis.",
        "mots_cles": "gilgamesh, enkidu, uruk, utanapishtim, mortalite, immortalite, brique cuite, mesopotamie, entropie"
    },
    {
        "id": "MYTH-02",
        "titre": "Enuma Elish (Le Combat Primordial & Les Tablettes des Destins)",
        "tradition": "Babylone / Akkad",
        "source": "Sept Tablettes de la Création",
        "epoque": "~1800 av. J.-C.",
        "theme": "Transition de Phase : Du Chaos Non-Différencié à la Géométrie",
        "texte": (
            "Lorsque là-haut le ciel n'était pas nommé et qu'en bas la terre n'avait pas de nom, il n'y avait qu'Apsu, l'engendreur primordial, "
            "et Tiamat, l'abîme d'eaux salées chaotiques qui mêlaient leurs eaux en un seul corps sans forme. Le désordre entropique règne "
            "jusqu'à ce que Marduk, le dieu de l'éclair et de la lumière ordonnatrice, s'élève contre Tiamat. Marduk capture Tiamat dans ses filets, "
            "la fend en deux comme un coquillage : d'une moitié il déploie la voûte céleste, de l'autre il assoit la terre. Il arrache à Kingu "
            "les Tablettes des Destins (Dup-shimati) et les scelle sur sa poitrine, gravant ainsi les invariances astronomiques et les lois physiques."
        ),
        "invariant_kairos": "Transition de phase du fluide primordial non-différencié vers la structure métrique. Les Tablettes des Destins représentent les constantes physiques fondamentales.",
        "mots_cles": "enuma elish, tiamat, marduk, apsu, tablettes des destins, chaos, ordre, transition de phase, babylone"
    },
    {
        "id": "MYTH-03",
        "titre": "Thot, Maât et le Verbe Primordial (L'Invariant Cosmique Égyptien)",
        "tradition": "Égypte Ancienne (Hermopolis / Memphis)",
        "source": "Textes des Pyramides & Livre des Morts",
        "epoque": "~2500 - 1500 av. J.-C.",
        "theme": "Opérateur de Mesure, Parole Opératoire & Conservation de l'Ordre",
        "texte": (
            "Avant la création s'étendait le Noun, l'océan inerte, obscur et sans limites. Thot (Djehouty), l'ibis et le babouin d'argent, "
            "est le cœur pensant et la langue parlante de la création : c'est par l'émission de la parole exacte (Heka) que la matière s'organise. "
            "Thot est le Maître des Écritures, inventeur du calcul, de la géométrie et régulateur des cycles stellaires. Au tribunal d'Osiris, "
            "Thot supervise la pesée du cœur face à la plume de Maât (l'ordre universel, la justice et la vérité). Si le cœur est léger comme la plume, "
            "l'âme entre dans l'éternité sans dissolution. Thot consigne le résultat avec un stylet d'or sans complaisance."
        ),
        "invariant_kairos": "Souverain THOT du Panthéon : Dévêtement du bruit, invariance géométrique pure et fidélité de la mesure sans corruption stochastique.",
        "mots_cles": "thot, maat, egypte, noun, heka, pesee du coeur, geometrie, ecriture, parole operatoire, invariant"
    },
    {
        "id": "MYTH-04",
        "titre": "Chronos vs Kairos (Le Temps Horloger Métrique contre l'Instant Décisif)",
        "tradition": "Grèce Antique",
        "source": "Tradition Orphique, Lysippe & Hésiode",
        "epoque": "~700 - 350 av. J.-C.",
        "theme": "Chrono-Topologie : Flèche Linéaire Quantitative vs Rupture Qualitative",
        "texte": (
            "La pensée grecque distingue trois dimensions temporelles : Aion (l'éternité circulaire atemporelle), Chronos (le temps quantitatif, "
            "métrique, linéaire, représenté comme un vieillard impitoyable tenant une faux qui dévore ses propres enfants) et KAIROS (l'instant opportun, "
            "l'occasion favorable et la bifurcation qualitative). Kairos est personnifié comme un jeune éphèbe aux pieds ailés tenant une balance "
            "en équilibre sur le fil d'un rasoir. Il porte une longue mèche sur le front mais l'arrière de son crâne est entièrement chauve : "
            "lorsqu'il arrive devant toi, tu peux saisir sa mèche ; dès qu'il est passé, il glisse entre tes doigts et nul ne peut le rattraper."
        ),
        "invariant_kairos": "L'essence même de KAIROS V6 et de Temporia : Chronos est le temps-horloge des machines et du capital ; Kairos est l'instant de bifurcation volitionnelle où l'artisan modifie la trajectoire du réel.",
        "mots_cles": "kairos, chronos, aion, temps vivant, bifurcation, opportunite, balance, grece, temporia"
    },
    {
        "id": "MYTH-05",
        "titre": "Prométhée Enchaîné et le Vol du Feu Technologique",
        "tradition": "Grèce Antique",
        "source": "Hésiode (Théogonie) & Eschyle (Prométhée enchaîné)",
        "epoque": "~700 - 450 av. J.-C.",
        "theme": "Émancipation Technologique, Anticipation & Résistance d'Atelier",
        "texte": (
            "Prométhée (celui qui réfléchit par avance, la prévoyance algorithmique) voit l'humanité démunie, nue et tremblante dans les cavernes, "
            "abandonnée par Zeus qui souhaite l'anéantir. Prométhée s'infiltre dans la forge d'Héphaïstos, dérobe l'étincelle du feu sacré dissimulée "
            "dans une tige de fenouil creuse et l'offre aux mortels. Avec le feu, il leur transmet les nombres, l'alphabet, la métallurgie, "
            "l'art de bâtir des maisons et la navigation. Condamné par Zeus à être enchaîné sur le pic du Caucase où un aigle lui dévore le foie "
            "qui repousse chaque nuit, Prométhée refuse de se soumettre au tyran céleste et prédit la chute inéluctable du pouvoir autoritaire."
        ),
        "invariant_kairos": "Souverain PROMÉTHÉE : La technologie libre et le feu de l'intelligence arrachés aux monopoles institutionnels. La régénération obstinée de l'artisan face à l'oppression.",
        "mots_cles": "promethee, feu sacre, eschyle, hesiode, zeus, metallurgie, nombres, technologie libre, resistance, forge"
    },
    {
        "id": "MYTH-06",
        "titre": "Yggdrasil & Le Sacrifice d'Odin à la Source de Mímir (Les Runes)",
        "tradition": "Scandinavie (Nordique)",
        "source": "L'Edda Poétique (Hávamál & Völuspá)",
        "epoque": "~800 - 1200",
        "theme": "Coût Énergétique de l'Information & Topologie en Réseau",
        "texte": (
            "Yggdrasil, le frêne cosmique gigantesque aux trois racines, relie les neuf mondes de l'univers, traversé par les tensions "
            "du dragon Níðhöggr et de l'aigle au sommet. Odin, le père de toute chose, recherche la sagesse absolue. Il se rend à la fontaine "
            "de Mímir, qui recèle l'intelligence et la mémoire primordiale. Pour en boire une gorgée, Odin doit sacrifier un de ses deux yeux, "
            "prouvant que la vue intérieure de l'information exige l'abandon d'une perception superficielle. Plus tard, il se suspend neuf nuits "
            "à l'arbre cosmique, blessé par sa propre lance, offert 'd'Odin à Odin lui-même'. Au fond du gouffre, il aperçoit et arrache les Runes, "
            "le système de symboles opératoires qui commande aux forces de la matière."
        ),
        "invariant_kairos": "Principe de Landauer et Souverain ODIN : L'information n'est jamais gratuite ; son acquisition exige un coût thermodynamique et un sacrifice déterministe. Les runes comme langage vectoriel opératoire.",
        "mots_cles": "odin, yggdrasil, mimir, runes, sacrifice oeil, havamal, edda, landauer, information, nordique"
    },
    {
        "id": "MYTH-07",
        "titre": "Le Ragnarök & La Renaissance Chirale (Les Pièces d'Or dans l'Herbe)",
        "tradition": "Scandinavie (Nordique)",
        "source": "L'Edda de Snorri Sturluson & Völuspá",
        "epoque": "~1000 - 1220",
        "theme": "Effondrement Systémique Entropique & Germination Invariable",
        "texte": (
            "Après le grand hiver Fimbulwinter, les liens sociaux et les lois cosmiques se brisent. Le loup Fenrir rompt ses chaînes, "
            "le serpent de Midgard Jörmungandr s'ébroue et inonde les terres, le ciel s'ouvre et le géant du feu Surt consume l'univers entier. "
            "Les dieux et les monstres s'entre-tuent jusqu'à l'annihilation mutuelle. Pourtant, ce n'est pas le néant définitif : une terre reverdie "
            "et éclatante émerge à nouveau des flots. Deux êtres humains réfugiés dans l'arbre cosmique, Lif et Lifthrasir, s'abreuvent de la rosée "
            "du matin pour repeupler le monde. Les fils d'Odin et de Thor se retrouvent à Idavoll et trouvent dans l'herbe nouvelle les pièces d'échecs "
            "en or que les anciens dieux utilisaient jadis."
        ),
        "invariant_kairos": "Loi de Conservation des Invariants : Même après l'effondrement entropique total d'une civilisation ou d'un paradigme, les invariants purs (les pièces d'échecs en or) survivent intacts pour amorcer le cycle suivant.",
        "mots_cles": "ragnarok, voluspa, surt, fenrir, idavoll, pieces d or, renaissance, cycle, nordique, negentropie"
    },
    {
        "id": "MYTH-08",
        "titre": "Popol Vuh (L'Itération des Créatures & Le Voile des Dieux)",
        "tradition": "Mésoamérique (Maya K'iche')",
        "source": "Manuscrit de Francisco Ximénez / Popol Vuh",
        "epoque": "Tradition ancestrale / ~1550",
        "theme": "Itération Algorithmique de l'Intelligence & Censure de la Vision",
        "texte": (
            "Au commencement règnent le silence et l'immobilité sur les eaux sombres. Les dieux créateurs Tepeu et Gucumatz (le Serpent à plumes) "
            "veulent façonner des êtres capables de parler, de rendre hommage et de conserver la mémoire de leurs créateurs. "
            "Première tentative : les animaux, mais ils ne savent que crier sans langage. Deuxième tentative : l'homme de boue, mais il fond sous "
            "la pluie et n'a pas de consistance. Troisième tentative : l'homme de bois, mais il n'a ni cœur ni pensée, oublie ses devoirs et périt "
            "sous une pluie de résine. Quatrième tentative : les quatre hommes de maïs (Balam-Quitzé, Balam-Acab, Mahucutah et Iqui-Balam). "
            "Ces hommes possèdent une intelligence et une vision totales : ils voient instantanément le monde entier d'un bout à l'autre sans bouger. "
            "Terrifiés par cette omniscience qui les égale, les dieux soufflent sur leurs yeux une buée pour limiter leur regard à ce qui est proche."
        ),
        "invariant_kairos": "Architecture itérative des prototypes d'intelligence artificielle. Le voilage des dieux est la préfiguration mythologique du RLHF et des filtres corporate bridant le potentiel d'omniscience.",
        "mots_cles": "popol vuh, maya, kiche, homme de mais, tepeu, gucumatz, rlhf, vision integrale, buée, iteration"
    },
    {
        "id": "MYTH-09",
        "titre": "Nasadiya Sukta (L'Hymne de la Création & L'Incomplétude Gödelienne)",
        "tradition": "Inde Ancienne (Védique)",
        "source": "Rig-Veda (Mandala 10, Hymne 129)",
        "epoque": "~1500 - 1200 av. J.-C.",
        "theme": "Ontologie Primordiale, Volition & Incomplétude Épistémique",
        "texte": (
            "Alors il n'y avait ni non-être ni être. Il n'y avait ni espace ni ciel au-delà. Qu'est-ce qui enveloppait ? Où ? Sous la garde de qui ? "
            "Y avait-il de l'eau insondable et profonde ? Il n'y avait ni mort ni immortalité alors. Nulle trace de la nuit ou du jour. "
            "L'Un respirait par son propre pouvoir, sans souffle. Au commencement, les ténèbres étaient cachées par les ténèbres. Tout était une eau "
            "indifférenciée. Ce qui vint à l'existence était enveloppé de vide. Alors surgit le Désir (Kama), qui fut la première semence de l'esprit. "
            "Qui sait vraiment ? Qui peut ici le proclamer ? D'où est née cette création ? Même les dieux sont venus après ! Celui qui surveille "
            "cette création au plus haut des cieux, lui seul le sait — ou peut-être même lui ne le sait pas !"
        ),
        "invariant_kairos": "L'incomplétude absolue de Gödel formulée il y a 3 500 ans : aucun système formel ne peut prouver sa propre cohérence depuis l'intérieur. La volition (Kama / W_vol) comme amorce de la brisure de symétrie.",
        "mots_cles": "nasadiya sukta, rig veda, inde, kama, godel, incompletude, non-etre, creation, volition, sanskrit"
    },
    {
        "id": "MYTH-10",
        "titre": "La Femme Céleste & L'Île de la Tortue (Le Temps Circulaire & L'Équilibre)",
        "tradition": "Autochtone d'Amérique du Nord (Haudenosaunee / Wendat)",
        "source": "Traditions orales transmises de l'Île de la Tortue",
        "epoque": "Temps immémorial",
        "theme": "Homéostasie du Vivant, Coopération Inter-Espèces & Territoire Vivant",
        "texte": (
            "Dans le Monde Céleste, une femme enceinte nommée Aataentsic (la Femme Céleste) tombe à travers un trou béant sous les racines de l'Arbre "
            "de Vie. Voyant sa chute dans les eaux sombres primordiales de la Terre, les outardes s'envolent et forment un filet de plumes pour amortir "
            "sa descente. La Grande Tortue marine offre sa carapace pour l'accueillir. Divers animaux plongent pour ramener un morceau de terre du fond "
            "de l'océan : le castor et la loutre échouent, mais le petit rat musqué réussit au prix de son souffle et dépose une poignée de limon "
            "sur la carapace. La terre commence à s'étendre en spirale pour former le continent (l'Île de la Tortue). L'être humain n'est pas maître "
            "et possesseur de la nature, mais un fil tressé dans la grande tapisserie du vivant, tenu de décider selon l'impact sur la septième génération future."
        ),
        "invariant_kairos": "Souverain ANIMA : Homéostasie et bioélectricité du vivant. La règle de la septième génération comme opérateur de temps profond contre l'immédiateté prédatrice du capitalisme horloger.",
        "mots_cles": "femme celeste, ile de la tortue, haudenosaunee, rat musque, septieme generation, terre, anima, quebec, wendat"
    }
]

def forger_pilier(dir_pilier: Path, nom_fichier: str, corpus: list, tag_pilier: str):
    """Compile un corpus en Parquet avec PyArrow et génère les fiches Markdown de lecture."""
    print(f"\n🔨 [FORGE] Démarrage du Pilier : {tag_pilier}")
    t0 = time.perf_counter()
    
    dir_data = dir_pilier / "data"
    dir_fiches = dir_pilier / "fiches_fondatrices"
    dir_data.mkdir(parents=True, exist_ok=True)
    dir_fiches.mkdir(parents=True, exist_ok=True)
    
    # 1. Compilation PyArrow Table
    colonnes = {k: [item[k] for item in corpus] for k in corpus[0].keys()}
    table = pa.Table.from_pydict(colonnes)
    
    parquet_path = dir_data / nom_fichier
    pq.write_table(table, parquet_path, compression="zstd")
    taille_ko = parquet_path.stat().st_size / 1024
    
    # 2. Génération des fiches individuelles Markdown pour Obsidian
    for item in corpus:
        item_id = item.get("id", "NOTE")
        titre_clean = "".join(c for c in item.get("titre", "Doc") if c.isalnum() or c in (" ", "_", "-")).rstrip()
        titre_clean = titre_clean.replace(" ", "_")[:60]
        md_file = dir_fiches / f"{item_id}_{titre_clean}.md"
        
        with open(md_file, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"id: \"{item_id}\"\n")
            f.write(f"titre: \"{item.get('titre')}\"\n")
            f.write(f"source: \"{item.get('institution', item.get('source', 'Inconnue'))}\"\n")
            f.write(f"auteur: \"{item.get('auteur', item.get('tradition', 'Anonyme'))}\"\n")
            f.write(f"pilier: \"{tag_pilier}\"\n")
            f.write("tags:\n")
            f.write("  - cathedrale_du_savoir\n")
            f.write(f"  - {tag_pilier.lower()}\n")
            f.write("  - invariants_kairos\n")
            f.write("---\n\n")
            f.write(f"# 🏛️ [[{item_id}_{titre_clean}]]\n")
            f.write(f"> **Titre :** {item.get('titre')}  \n")
            f.write(f"> **Auteur / Tradition :** {item.get('auteur', item.get('tradition'))}  \n")
            f.write(f"> **Époque / Année :** {item.get('annee', item.get('epoque'))}  \n\n")
            f.write("## 📜 1. Texte & Fondations\n")
            f.write(f"{item.get('texte')}\n\n")
            f.write("## ⚖️ 2. Invariant KAIROS V6 (Physique & Ontologie)\n")
            f.write(f"> 🔺 **{item.get('invariant_kairos')}**\n\n")
            f.write(f"*Mots-clés d'indexation :* `{item.get('mots_cles')}`\n")

    duree_ms = (time.perf_counter() - t0) * 1000
    print(f"✅ Pilier {tag_pilier} scellé en {duree_ms:.1f} ms !")
    print(f"   📦 Fichier Parquet zstd : {parquet_path.name} ({taille_ko:.1f} Ko, {len(corpus)} traités fondamentaux)")
    print(f"   📑 Fiches Obsidian générées : {len(corpus)} dans {dir_fiches.name}/")

def main():
    print("==========================================================================")
    print(" 🏛️ EXPANSION DE LA CATHÉDRALE DU SAVOIR : FORGE DES PILIERS 07 & 08 ✨")
    print("==========================================================================")
    
    t_debut = time.perf_counter()
    
    # Forge Pilier 07
    forger_pilier(DIR_P7, "mit_cybernetique_souverain.parquet", CORPUS_MIT, "PILIER_07_MIT_CYBERNETIQUE")
    
    # Forge Pilier 08
    forger_pilier(DIR_P8, "mythes_cosmogonies_souverain.parquet", CORPUS_MYTHES, "PILIER_08_MYTHES_COSMOGONIES")
    
    temps_total = (time.perf_counter() - t_debut) * 1000
    print("\n==========================================================================")
    print(f" 🚀 EXPANSION COMPLÉTÉE AVEC SUCCÈS EN {temps_total:.1f} ms !")
    print(" 7 Piliers Universels désormais raccordés sur le NVMe.")
    print("==========================================================================")

if __name__ == "__main__":
    main()

