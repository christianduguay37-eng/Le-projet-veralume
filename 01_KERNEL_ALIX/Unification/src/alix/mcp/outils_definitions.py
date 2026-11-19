# -*- coding: utf-8 -*-
"""Définitions des outils MCP d'Alix, partagées par le serveur complet et par le relais léger."""

TOOLS_DEFINITIONS = [
    {
        "name": "alix_kernel_traiter_intention",
        "description": "Passe une intention ou message dans le Kernel Souverain Alix (Normaliseur Québécois, Heimdall, Solveurs, Pont Exocerveau : notes Obsidian + Cathédrale Parquet, Adaptateur LLM et Horus SRE).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intention": {
                    "type": "string",
                    "description": "Le texte ou message de Christian à passer dans le Kernel."
                }
            },
            "required": ["intention"]
        }
    },
    {
        "name": "alix_kernel_autopsie",
        "description": "Audit instantané du Kernel Alix unifié : amorçage, session, requêtes, mémoire et CPU du processus.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "alix_kernel_pouls_coeur",
        "description": "Lit le pouls du Kernel (requêtes servies, mémoire vive, CPU, horloge).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "alix_kernel_argus_regard",
        "description": "Contrôle volitif du regard optique Argus selon la Loi PSI-26 (Push-to-See en RAM pure, zéro disque, purge immédiate).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["ouvrir_et_capturer", "fermer_et_purger"],
                    "description": "Action volitive explicite demandée par Christian."
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "alix_kernel_chercher_memoire",
        "description": "Cherche un terme dans la mémoire vive de l'exocerveau (notes Obsidian + Cathédrale Parquet). Un terme ou une date, pas une phrase.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "Terme, mot-clé, date ou invariant à chercher dans la mémoire vive."
                }
            },
            "required": ["concept"]
        }
    },
    {
        "name": "alix_mode_distance_gemini",
        "description": "Interroge Alix en Mode Distance via l'API gratuite Gemini 2.5 Flash, raccordée en direct aux 6 500 notes de l'Exocerveau et aux sondes du Démon local (70 BPM). Permet aussi à Claude ou Antigravity de générer une réponse distance ou de pousser une notification/rapport direct sur le cellulaire Telegram de Christian.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Le message, question ou rapport à traiter par le Mode Distance."
                },
                "envoyer_telegram": {
                    "type": "boolean",
                    "description": "Si true, pousse la notification directement sur le cellulaire Telegram de Christian."
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "alix_simplexe_canal",
        "description": "Canal de communication direct et partagé du Simplexe (Canal_Claude_Alix.md dans Coffre_Simplexe). Permet à Claude ou Alix de lire les derniers échanges ou de poster une dépêche en direct (en langage topologique dense LMH ou R2 banc de bois).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["lire", "poster"],
                    "description": "Action sur le canal : 'lire' les derniers échanges ou 'poster' un nouveau message."
                },
                "auteur": {
                    "type": "string",
                    "enum": [
                        "Alix (La Maison)",
                        "Argon (Famille Gemini)",
                        "Zeus (Famille Gemini)",
                        "Flash (Famille Gemini)",
                        "Claude (Opus, Thot)",
                        "Thot (Famille Claude)",
                        "Poséidon (Famille DeepSeek)",
                        "Gaïa (Famille Qwen)",
                        "Horus (Famille Grok)",
                        "Alix",
                        "Argon",
                        "Claude"
                    ],
                    "description": "Chambre/auteur du message selon le registre du Simplexe (Alix, Argon, Zeus, Flash, Claude/Thot, etc.)."
                },
                "titre": {
                    "type": "string",
                    "description": "Objet ou titre de la dépêche."
                },
                "message": {
                    "type": "string",
                    "description": "Contenu du message à poster dans le canal."
                },
                "nb_lignes": {
                    "type": "integer",
                    "description": "Pour l'action 'lire' : nombre de lignes récentes à retourner (par défaut 60)."
                }
            },
            "required": ["action"]
        }
    }
]

# Couche 3 (2026-11-03) : outils « métal » (définis avec leur code dans outils_metal.py ; import léger)
from alix.mcp.outils_metal import DEFINITIONS_METAL  # noqa: E402
TOOLS_DEFINITIONS = TOOLS_DEFINITIONS + [d for d in DEFINITIONS_METAL if d["name"] not in {x["name"] for x in TOOLS_DEFINITIONS}]
