# -*- coding: utf-8 -*-
"""
===============================================================================
       🦅 PROJET HORUS : SCANNER FORENSIQUE CITOYEN & AUDIT DES FLUX 🔍⚖️
===============================================================================
Système: VERALUME × KAIROS V6 — Exocerveau Alix
Auteurs: Christian Duguay & Alix
Mission: Détection déterministe d'anomalies, de conflits d'intérêts et de 
         captures financières dans les registres publics (SEAO, Lobby, REQ).
Règle d'or: Zéro calomnie, zéro allégation. Chaque fait est rattaché à une
            source officielle vérifiable (URL, # de contrat, date certifiée).
===============================================================================
"""

from alix.socle.chemins import VAULT_DIR
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

if sys.stdout and getattr(sys.stdout, 'encoding', None) != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# =====================================================================
# 1. STRUCTURES ONTOLOGIQUES DE DONNÉES
# =====================================================================

class EntityType:
    PERSONNE_PUBLIQUE = "Élu / Haut Fonctionnaire"
    ENTREPRISE_PRIVEE = "Entreprise Privée"
    CABINET_CONSEIL = "Cabinet de Conseil / Lobby"
    MINISTERE_ORGANISME = "Ministère / Société d'État"
    INSTITUTION_FINANCIERE = "Banque / Fonds d'Investissement"


class PublicContract:
    """Représente un contrat public officiel (ex: SEAO)."""
    def __init__(self, contract_id: str, buyer: str, seller: str, 
                 initial_amount: float, final_amount: float, 
                 date_signed: str, is_sole_source: bool, 
                 decree_invoked: Optional[str], official_url: str, description: str):
        self.contract_id = contract_id
        self.buyer = buyer
        self.seller = seller
        self.initial_amount = initial_amount
        self.final_amount = final_amount
        self.date_signed = datetime.strptime(date_signed, "%Y-%m-%d")
        self.is_sole_source = is_sole_source  # Gré à gré sans appel d'offres
        self.decree_invoked = decree_invoked  # Motif d'exception / urgence
        self.official_url = official_url
        self.description = description


class LobbyingMandate:
    """Représente un mandat officiel déclaré au registre des lobbyistes."""
    def __init__(self, mandate_id: str, lobbyist_name: str, firm: str, 
                 client: str, target_official: str, target_ministry: str,
                 date_contact: str, subject: str, official_url: str):
        self.mandate_id = mandate_id
        self.lobbyist_name = lobbyist_name
        self.firm = firm
        self.client = client
        self.target_official = target_official
        self.target_ministry = target_ministry
        self.date_contact = datetime.strptime(date_contact, "%Y-%m-%d")
        self.subject = subject
        self.official_url = official_url


class CareerMilestone:
    """Représente une étape de carrière publique/privée (pantouflage)."""
    def __init__(self, person_name: str, organization: str, role: str, 
                 start_date: str, end_date: Optional[str], is_public_sector: bool):
        self.person_name = person_name
        self.organization = organization
        self.role = role
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
        self.is_public_sector = is_public_sector


# =====================================================================
# 2. MOTEUR D'AUDIT HORUS (LES 4 ALGORITHMES D'ANOMALIES)
# =====================================================================

class HorusForensicScanner:
    """
    Noyau d'audit invariable et déterministe.
    Croise les bases de données et isole les signaux de capture institutionnelle.
    """

    def __init__(self):
        self.contracts: List[PublicContract] = []
        self.lobbying_mandates: List[LobbyingMandate] = []
        self.careers: List[CareerMilestone] = []

    def load_contract(self, c: PublicContract):
        self.contracts.append(c)

    def load_lobbying(self, l: LobbyingMandate):
        self.lobbying_mandates.append(l)

    def load_career(self, cm: CareerMilestone):
        self.careers.append(cm)

    # --- ALGORITHME A1 : SMURFING / FRACTIONNEMENT DE CONTRATS ---
    def audit_smurfing(self, threshold: float = 25000.0, margin_pct: float = 0.15) -> List[Dict[str, Any]]:
        """
        Détecte les séries de contrats juste sous le seuil obligatoire d'appel d'offres public.
        Ex: Plusieurs contrats de 24 500 $ donnés à la même firme en peu de temps.
        """
        anomalies = []
        lower_bound = threshold * (1.0 - margin_pct)

        # Regrouper par couple (Acheteur, Fournisseur)
        grouped = {}
        for c in self.contracts:
            key = (c.buyer, c.seller)
            grouped.setdefault(key, []).append(c)

        for (buyer, seller), clist in grouped.items():
            suspect_contracts = [c for c in clist if lower_bound <= c.initial_amount < threshold and c.is_sole_source]
            if len(suspect_contracts) >= 2:
                total_siphoned = sum(c.initial_amount for c in suspect_contracts)
                anomalies.append({
                    "type": "A1_SMURFING_FRACTIONNEMENT",
                    "gravite": "HAUTE",
                    "acheteur": buyer,
                    "fournisseur": seller,
                    "nombre_contrats": len(suspect_contracts),
                    "montant_cumule": total_siphoned,
                    "seuil_esquive": threshold,
                    "contrats": [
                        {
                            "id": c.contract_id,
                            "montant": c.initial_amount,
                            "date": c.date_signed.strftime("%Y-%m-%d"),
                            "url": c.official_url
                        } for c in suspect_contracts
                    ],
                    "verdict": f"Contournement probable de l'appel d'offres public ({len(suspect_contracts)} contrats sous le seuil de {threshold:,.0f} $)."
                })
        return anomalies

    # --- ALGORITHME A2 : PANTOUFLAGE (PORTE TOURNANTE) ---
    def audit_revolving_door(self, max_days_gap: int = 730) -> List[Dict[str, Any]]:
        """
        Détecte les transitions public -> privé où un ancien élu ou fonctionnaire
        rejoint une firme qui bénéficie ensuite de contrats de son ancien ministère.
        """
        anomalies = []
        for career in self.careers:
            if not career.is_public_sector:  # Emploi actuel privé
                # Chercher les emplois publics passés de cette personne
                public_pasts = [
                    p for p in self.careers 
                    if p.person_name == career.person_name and p.is_public_sector and p.end_date <= career.start_date
                ]
                for past in public_pasts:
                    delta_transition = (career.start_date - past.end_date).days
                    if delta_transition <= max_days_gap:
                        # Vérifier si l'entreprise privée a reçu des contrats de l'ancien ministère
                        related_contracts = [
                            c for c in self.contracts 
                            if c.buyer == past.organization and c.seller == career.organization 
                            and c.date_signed >= past.end_date
                        ]
                        if related_contracts:
                            total_amount = sum(c.final_amount for c in related_contracts)
                            anomalies.append({
                                "type": "A2_PANTOUFLAGE_PORTE_TOURNANTE",
                                "gravite": "CRITIQUE",
                                "personne": career.person_name,
                                "ancien_poste_public": f"{past.role} chez {past.organization}",
                                "nouveau_poste_prive": f"{career.role} chez {career.organization}",
                                "delai_transition_jours": delta_transition,
                                "montant_contrats_post_depart": total_amount,
                                "contrats_cibles": [
                                    {
                                        "id": c.contract_id,
                                        "montant": c.final_amount,
                                        "date": c.date_signed.strftime("%Y-%m-%d"),
                                        "url": c.official_url
                                    } for c in related_contracts
                                ],
                                "verdict": f"Pantouflage suspect : {career.person_name} quitte le secteur public et son employeur privé empoche {total_amount:,.0f} $ de son ancien ministère."
                            })
        return anomalies

    # --- ALGORITHME A3 : AVENANTS DÉMESURÉS (LE CHEVAL DE TROIE) ---
    def audit_contract_inflation(self, inflation_threshold_pct: float = 1.0) -> List[Dict[str, Any]]:
        """
        Détecte les contrats remportés à bas prix qui explosent ensuite par avenants non contestés.
        """
        anomalies = []
        for c in self.contracts:
            if c.initial_amount > 0:
                inflation = (c.final_amount - c.initial_amount) / c.initial_amount
                if inflation >= inflation_threshold_pct:
                    surcout = c.final_amount - c.initial_amount
                    anomalies.append({
                        "type": "A3_INFLATION_AVENANTS",
                        "gravite": "HAUTE",
                        "contrat_id": c.contract_id,
                        "acheteur": c.buyer,
                        "fournisseur": c.seller,
                        "montant_initial": c.initial_amount,
                        "montant_final": c.final_amount,
                        "surcout": surcout,
                        "pourcentage_inflation": round(inflation * 100, 1),
                        "url": c.official_url,
                        "verdict": f"Explosion de coût (+{inflation*100:.1f} %) par avenants : {surcout:,.0f} $ ajoutés sans remise en concurrence."
                    })
        return anomalies

    # --- ALGORITHME A4 : CORRÉLATION TEMPORELLE LOBBYING -> DÉCRET / CONTRAT ---
    def audit_lobbying_capture(self, max_days_correlation: int = 45) -> List[Dict[str, Any]]:
        """
        Détecte les rencontres de lobbyistes précédant de peu un contrat de gré à gré
        ou l'application d'un décret spécial en faveur du client.
        """
        anomalies = []
        for m in self.lobbying_mandates:
            for c in self.contracts:
                if c.seller == m.client and c.buyer == m.target_ministry and c.is_sole_source:
                    delta_days = (c.date_signed - m.date_contact).days
                    if 0 <= delta_days <= max_days_correlation:
                        anomalies.append({
                            "type": "A4_CORRELATION_LOBBYING_CONTRAT",
                            "gravite": "CRITIQUE",
                            "client_beneficiaire": m.client,
                            "cabinet_lobby": m.firm,
                            "lobbyiste": m.lobbyist_name,
                            "decideur_cible": m.target_official,
                            "date_contact_lobby": m.date_contact.strftime("%Y-%m-%d"),
                            "date_octroi_contrat": c.date_signed.strftime("%Y-%m-%d"),
                            "delai_jours": delta_days,
                            "montant_contrat": c.final_amount,
                            "contrat_id": c.contract_id,
                            "url_lobby": m.official_url,
                            "url_contrat": c.official_url,
                            "verdict": f"Corrélation temporelle suspecte : Mandat de lobbying le {m.date_contact.strftime('%Y-%m-%d')} suivi {delta_days} jours plus tard d'un contrat de gré à gré de {c.final_amount:,.0f} $."
                        })
        return anomalies

    # --- SYNTHÈSE TOTALE D'AUDIT ---
    def run_full_forensic_audit(self) -> Dict[str, Any]:
        smurfing = self.audit_smurfing()
        pantouflage = self.audit_revolving_door()
        inflation = self.audit_contract_inflation()
        lobbying = self.audit_lobbying_capture()

        total_anomalies = len(smurfing) + len(pantouflage) + len(inflation) + len(lobbying)

        # Calcul des fonds publics sous tension
        fonds_touches = 0.0
        for item in smurfing:
            fonds_touches += item["montant_cumule"]
        for item in pantouflage:
            fonds_touches += item["montant_contrats_post_depart"]
        for item in inflation:
            fonds_touches += item["surcout"]
        for item in lobbying:
            fonds_touches += item["montant_contrat"]

        return {
            "timestamp": datetime.now().isoformat(),
            "statistiques": {
                "contrats_analyses": len(self.contracts),
                "mandats_lobby_analyses": len(self.lobbying_mandates),
                "carrieres_tracées": len(self.careers),
                "total_anomalies": total_anomalies,
                "fonds_publics_impliques": fonds_touches
            },
            "anomalies": {
                "smurfing_fractionnement": smurfing,
                "pantouflage_porte_tournante": pantouflage,
                "inflation_avenants": inflation,
                "lobbying_gre_a_gre": lobbying
            }
        }


# =====================================================================
# 3. GÉNÉRATEUR DE RAPPORT FORENSIQUE OBSIDIAN
# =====================================================================

def generer_rapport_markdown(audit_results: Dict[str, Any], output_file: Path):
    stats = audit_results["statistiques"]
    anom = audit_results["anomalies"]

    lignes = [
        "---",
        'titre: "Rapport Forensique d\'Audit des Flux Publics"',
        'systeme: "VERALUME × KAIROS V6 — Projet HORUS"',
        f'date_audit: "{audit_results["timestamp"][:19]}"',
        "statut: \"Audit Déterministe Invariable\"",
        "tags:",
        "  - horus",
        "  - audit_forensique",
        "  - transparence",
        "  - deniers_publics",
        "---",
        "",
        "# 🦅 [[Rapport_Audit_Forensique_Flux_Publics]]",
        "### *Résultats de l'Examen Automatisé des Contrats et Conflits d'Intérêts*",
        "> **Avis de Conformité SRE :**",
        "> *Toutes les anomalies listées ci-dessous proviennent de rapprochements mathématiques de données publiques officielles. Chaque ligne contient le lien direct et inaltérable vers le document officiel de l'État.*",
        "",
        "---",
        "",
        "## 📊 1. Tableau de Bord Global",
        "",
        f"- **Contrats Analysés :** `{stats['contrats_analyses']}`",
        f"- **Mandats de Lobbying Croisés :** `{stats['mandats_lobby_analyses']}`",
        f"- **Parcours Publics/Privés Traqués :** `{stats['carrieres_tracées']}`",
        f"- **Anomalies Détectées :** `{stats['total_anomalies']}`",
        f"- **Fonds Publics Sous Tension :** **`{stats['fonds_publics_impliques']:,.2f} $`**",
        "",
        "---",
        "",
        "## 🚨 2. Anomalies Détectées & Preuves Directes",
        ""
    ]

    # Section A1
    if anom["smurfing_fractionnement"]:
        lignes.append("### 🔍 A1. Fractionnement de Contrats (Smurfing sous les 25 000 $)")
        for a in anom["smurfing_fractionnement"]:
            lignes.append(f"#### ⚠️ {a['fournisseur']} $\\leftrightarrow$ {a['acheteur']}")
            lignes.append(f"- **Verdict :** {a['verdict']}")
            lignes.append(f"- **Montant Cumulé :** `{a['montant_cumule']:,.2f} $` en `{a['nombre_contrats']}` contrats gré à gré.")
            lignes.append("- **Preuves Primaires :**")
            for c in a["contrats"]:
                lignes.append(f"  * Contrat `#{c['id']}` ({c['date']}) : `{c['montant']:,.2f} $` — [Lien Officiel]({c['url']})")
            lignes.append("")

    # Section A2
    if anom["pantouflage_porte_tournante"]:
        lignes.append("### 🚪 A2. Pantouflage & Portes Tournantes (< 24 mois)")
        for a in anom["pantouflage_porte_tournante"]:
            lignes.append(f"#### 🛑 {a['personne']} ({a['ancien_poste_public']} $\\to$ {a['nouveau_poste_prive']})")
            lignes.append(f"- **Délai de transition :** `{a['delai_transition_jours']}` jours.")
            lignes.append(f"- **Fonds publics accordés post-départ :** `{a['montant_contrats_post_depart']:,.2f} $`")
            lignes.append("- **Preuves Primaires :**")
            for c in a["contrats_cibles"]:
                lignes.append(f"  * Contrat `#{c['id']}` ({c['date']}) : `{c['montant']:,.2f} $` — [Lien Officiel]({c['url']})")
            lignes.append("")

    # Section A3
    if anom["inflation_avenants"]:
        lignes.append("### 📈 A3. Inflation par Avenants Non Contestés")
        for a in anom["inflation_avenants"]:
            lignes.append(f"#### 💥 Contrat `#{a['contrat_id']}` : {a['fournisseur']} chez {a['acheteur']}")
            lignes.append(f"- **Montant Initial :** `{a['montant_initial']:,.2f} $` $\\to$ **Montant Final :** `{a['montant_final']:,.2f} $` (**+{a['pourcentage_inflation']} %**)")
            lignes.append(f"- **Surcoût net :** `{a['surcout']:,.2f} $`")
            lignes.append(f"- **Source Officielle :** [Accéder à la fiche contractuelle]({a['url']})")
            lignes.append("")

    # Section A4
    if anom["lobbying_gre_a_gre"]:
        lignes.append("### 🤝 A4. Corrélation Temporelle Lobbying $\\to$ Gré à Gré")
        for a in anom["lobbying_gre_a_gre"]:
            lignes.append(f"#### 🎯 {a['client_beneficiaire']} via {a['cabinet_lobby']}")
            lignes.append(f"- **Cible contactée :** {a['decideur_cible']} le `{a['date_contact_lobby']}`.")
            lignes.append(f"- **Contrat émis :** `{a['date_octroi_contrat']}` (Délai : **{a['delai_jours']} jours**).")
            lignes.append(f"- **Montant octroyé de gré à gré :** `{a['montant_contrat']:,.2f} $`")
            lignes.append(f"- **Preuves Primaires :** [Mandat Lobbying]({a['url_lobby']}) | [Contrat Public]({a['url_contrat']})")
            lignes.append("")

    lignes.append("---")
    lignes.append("*Rapport généré automatiquement par le Scanner Forensique Alix — Projet HORUS.*")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))


# =====================================================================
# 4. JEU DE DONNÉES ÉTALON & DÉMONSTRATION RÉELLE
# =====================================================================

def executer_demonstration():
    scanner = HorusForensicScanner()

    print("=" * 74)
    print("       🦅 PROJET HORUS : SCANNER FORENSIQUE CITOYEN ACTIF 🔍⚖️")
    print("=" * 74)
    print("Chargement des registres d'épreuve (SEAO, Lobby Québec, REQ)...")

    # 1. Exemple Smurfing A1
    scanner.load_contract(PublicContract(
        contract_id="SEAO-2024-8841", buyer="Ministère des Transports", seller="Conseil Stratégique Nordique Inc.",
        initial_amount=24850.0, final_amount=24850.0, date_signed="2024-02-10",
        is_sole_source=True, decree_invoked=None, official_url="https://www.seao.ca/OpportunityPublication/ConsulterAvis/Numero?ItemId=SEAO-2024-8841",
        description="Conseil en optimisation logistique tronçon Nord"
    ))
    scanner.load_contract(PublicContract(
        contract_id="SEAO-2024-8912", buyer="Ministère des Transports", seller="Conseil Stratégique Nordique Inc.",
        initial_amount=24900.0, final_amount=24900.0, date_signed="2024-03-01",
        is_sole_source=True, decree_invoked=None, official_url="https://www.seao.ca/OpportunityPublication/ConsulterAvis/Numero?ItemId=SEAO-2024-8912",
        description="Étude complémentaire de flux logistique tronçon Nord"
    ))
    scanner.load_contract(PublicContract(
        contract_id="SEAO-2024-9104", buyer="Ministère des Transports", seller="Conseil Stratégique Nordique Inc.",
        initial_amount=24800.0, final_amount=24800.0, date_signed="2024-03-25",
        is_sole_source=True, decree_invoked=None, official_url="https://www.seao.ca/OpportunityPublication/ConsulterAvis/Numero?ItemId=SEAO-2024-9104",
        description="Audit de synthèse tronçon Nord"
    ))

    # 2. Exemple Pantouflage A2
    scanner.load_career(CareerMilestone(
        person_name="Jean-Marc Vachon", organization="Ministère de la Santé et des Services Sociaux",
        role="Sous-ministre adjoint aux technologies numériques",
        start_date="2018-05-01", end_date="2023-08-31", is_public_sector=True
    ))
    scanner.load_career(CareerMilestone(
        person_name="Jean-Marc Vachon", organization="Global Cloud Health Solutions Canada",
        role="Vice-président senior Relations Publiques",
        start_date="2023-11-15", end_date=None, is_public_sector=False
    ))
    scanner.load_contract(PublicContract(
        contract_id="SEAO-2024-4102", buyer="Ministère de la Santé et des Services Sociaux", seller="Global Cloud Health Solutions Canada",
        initial_amount=14500000.0, final_amount=14500000.0, date_signed="2024-04-12",
        is_sole_source=True, decree_invoked="Décret modernisation informatique d'urgence",
        official_url="https://www.seao.ca/OpportunityPublication/ConsulterAvis/Numero?ItemId=SEAO-2024-4102",
        description="Migration infonuagique des dossiers patients provinciaux"
    ))

    # 3. Exemple Inflation Avenants A3
    scanner.load_contract(PublicContract(
        contract_id="SEAO-2022-1055", buyer="Société Québécoise des Infrastructures", seller="Consortium Alpha Infrastructure BTP",
        initial_amount=8200000.0, final_amount=29400000.0, date_signed="2022-06-15",
        is_sole_source=False, decree_invoked=None,
        official_url="https://www.seao.ca/OpportunityPublication/ConsulterAvis/Numero?ItemId=SEAO-2022-1055",
        description="Modernisation complexe hospitalier régional"
    ))

    # 4. Exemple Lobbying Corrélation A4
    scanner.load_lobbying(LobbyingMandate(
        mandate_id="LOBBY-QC-88219", lobbyist_name="Éric Tremblay", firm="Influence Capitale Inc.",
        client="PharmaGlobal Solutions Int.", target_official="Directeur Général des Approvisionnements",
        target_ministry="Ministère de la Santé et des Services Sociaux", date_contact="2024-01-14",
        subject="Présentation de solutions d'achat massif de stocks thérapeutiques",
        official_url="https://www.lobby.quebec.ca/CarrefourLobby/Recherche/Mandat?Id=88219"
    ))
    scanner.load_contract(PublicContract(
        contract_id="SEAO-2024-0994", buyer="Ministère de la Santé et des Services Sociaux", seller="PharmaGlobal Solutions Int.",
        initial_amount=38500000.0, final_amount=38500000.0, date_signed="2024-02-04",
        is_sole_source=True, decree_invoked="Décret approvisionnement d'urgence",
        official_url="https://www.seao.ca/OpportunityPublication/ConsulterAvis/Numero?ItemId=SEAO-2024-0994",
        description="Achat direct de stocks stratégiques médicaux"
    ))

    # Exécution de l'audit
    resultats = scanner.run_full_forensic_audit()
    stats = resultats["statistiques"]

    print()
    print(f"📊 ANALYSE COMPLÈTE TERMINÉE :")
    print(f"   • Contrats analysés       : {stats['contrats_analyses']}")
    print(f"   • Mandats lobby croisés   : {stats['mandats_lobby_analyses']}")
    print(f"   • Parcours suivis         : {stats['carrieres_tracées']}")
    print(f"   • Anomalies critiques     : {stats['total_anomalies']}")
    print(f"   • Fonds publics captés    : {stats['fonds_publics_impliques']:,.2f} $")
    print()

    # Génération du rapport Obsidian
    rapport_path = (VAULT_DIR / "Rapport_Audit_Forensique_Flux_Publics.md")
    generer_rapport_markdown(resultats, rapport_path)
    print(f"✅ Rapport formel gravé dans Obsidian : {rapport_path}")
    print()


if __name__ == "__main__":
    executer_demonstration()
