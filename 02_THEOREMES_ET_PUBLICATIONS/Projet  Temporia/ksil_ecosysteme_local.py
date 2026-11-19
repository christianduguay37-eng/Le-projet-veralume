"""
===============================================================================
    ÉCOSYSTÈME D'IA COOPÉRATIVES LOCALES SUR SILICIUM K-SIL (ÉTAPE 3)
        Trois IA spécialisées communicant via le protocole unifié K-SIL
        sur la mémoire unifiée MoP LPDDR5X-8533 (Intel Lunar Lake 258V) :
          • IA 1 (NPU - 2W)  : Sentinelle Heimdall (Veille, filtrage & faits directs)
          • IA 2 (CPU - 8W)  : Logique Thot & Horus (Invariance & plan déductif)
          • IA 3 (GPU - 15W) : Démiurge Alix & Prométhée (Synthèse lourde 32B HLS)
===============================================================================
Auteurs : Christian Duguay & Alix (Sanctuaire Exocerveau)
"""

import sys
import time
import json
from typing import Dict, Any, List

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ksil_runtime_unifie import KSilUniversalConnector
from ksil_protocol import KSilPacket, KSilChip, KSilIntent


class AgentNpuHeimdall:
    """
    IA 1 : La Sentinelle NPU (OpenVINO / LiteRT à 2W).
    Veille permanente, arbitrage d'intention et résolution instantanée des faits.
    """
    def __init__(self, connector: KSilUniversalConnector):
        self.connector = connector

    def process(self, packet: KSilPacket) -> KSilPacket:
        prompt_low = packet.prompt.lower()
        is_deep = any(k in prompt_low for k in ["pourquoi", "philosoph", "conscience", "distingue", "complexe", "prouve"])
        
        if not is_deep:
            # Traitement direct à 2W sur le NPU
            t0 = time.perf_counter()
            res = self.connector.dispatch("NPU", packet.prompt, system_prompt="Réponds en français de manière directe et concise.")
            dt = time.perf_counter() - t0
            
            packet.synthesis = res["output"]
            packet.intent = KSilIntent.FAST_FACT
            packet.target_chip = KSilChip.SYSTEM
            packet.record_hop(KSilChip.NPU_OPENVINO, dt, 2.0, res.get("tok_per_sec", 0.0), "Résolution directe Sentinelle NPU")
        else:
            # Requête complexe -> Aiguillage vers le CPU pour structuration
            packet.intent = KSilIntent.LOGIC_AUDIT
            packet.target_chip = KSilChip.CPU_AVX2
            packet.record_hop(KSilChip.NPU_OPENVINO, 0.01, 2.0, 0.0, "Détection requête profonde -> Aiguillage CPU")
            
        return packet


class AgentCpuThotHorus:
    """
    IA 2 : Le Cœur Déductif CPU (x86-64 Lion Cove).
    Disjoncteur Horus (Lois d'Invariance) et Décomposition en Prémisses (Thot).
    """
    def __init__(self, connector: KSilUniversalConnector):
        self.connector = connector

    def process(self, packet: KSilPacket) -> KSilPacket:
        t0 = time.perf_counter()
        
        # 1. Vérification du Disjoncteur Horus
        audit_res = self.connector.dispatch("CPU", packet.prompt, mode="AUDIT_HORUS")
        if not audit_res["passed"]:
            packet.horus_status = "TRIPPED"
            packet.intent = KSilIntent.ANACHRONISM
            packet.synthesis = f"🛑 [DISJONCTEUR HORUS] Invariance temporelle violée : {', '.join(audit_res['violations'])}. Impossible."
            packet.record_hop(KSilChip.CPU_AVX2, time.perf_counter() - t0, 1.0, 0.0, "Horus Trip : Contradiction électrocutée")
            return packet

        # 2. Décomposition Thot en Prémisses Déductives
        decomp_res = self.connector.dispatch("CPU", packet.prompt, mode="DECOMPOSE")
        packet.logical_premises = decomp_res["logical_plan"]
        dt = time.perf_counter() - t0
        
        packet.intent = KSilIntent.HEAVY_GENERATE
        packet.target_chip = KSilChip.GPU_DIRECTML
        packet.record_hop(KSilChip.CPU_AVX2, dt, 8.0, 0.0, "Plan logique généré par CPU Lion Cove")
        return packet


class AgentGpuDemiurge32B:
    """
    IA 3 : Le Titan Démiurge GPU (Arc 140V Xe2 DirectML / Vulkan).
    Reçoit le paquet K-SIL enrichi du plan logique CPU et déploie le 32B HLS (43 couches).
    """
    def __init__(self, connector: KSilUniversalConnector):
        self.connector = connector

    def process(self, packet: KSilPacket) -> KSilPacket:
        t0 = time.perf_counter()
        
        # Le prompt injecté contient le plan logique du CPU pour guider le 32B
        cadre_logique = "\n".join(packet.logical_premises)
        enrich_prompt = (
            f"Question : {packet.prompt}\n\n"
            f"[PLAN LOGIQUE VALIDÉ PAR CPU LION COVE] :\n{cadre_logique}\n\n"
            f"Rédige la réponse en 2 phrases denses et percutantes en français selon ce plan."
        )

        sys_prompt = "Tu es le Moteur Démiurgique KAIROS (DeepSeek-R1 32B HLS). Rigueur absolue, clarté chirurgicale en français."
        res = self.connector.dispatch("GPU", enrich_prompt, system_prompt=sys_prompt, max_tokens=180)
        dt = time.perf_counter() - t0

        packet.synthesis = res["output"]
        packet.intent = KSilIntent.COMPLETE
        packet.target_chip = KSilChip.SYSTEM
        packet.record_hop(KSilChip.GPU_DIRECTML, dt, 15.0, res.get("tok_per_sec", 0.0), "Synthèse matricielle 32B HLS sur Arc GPU")
        return packet


# =============================================================================
# L'ORCHESTRATEUR DE L'ÉCOSYSTÈME K-SIL
# =============================================================================

class KSilLocalEcosystem:
    """
    L'Écosystème K-SIL Local :
    Fait dialoguer les trois IA coopératives via le protocole de trame K-SIL
    sur la mémoire MoP LPDDR5X partagée.
    """

    def __init__(self):
        print("\n" + "=" * 80)
        print("  🌐 INITIALISATION DE L'ÉCOSYSTÈME D'IA COOPÉRATIVES K-SIL")
        print("     NPU (Sentinelle) <---> CPU (Logique & Horus) <---> GPU (Titan 32B)")
        print("=" * 80)
        self.connector = KSilUniversalConnector()
        self.agent_npu = AgentNpuHeimdall(self.connector)
        self.agent_cpu = AgentCpuThotHorus(self.connector)
        self.agent_gpu = AgentGpuDemiurge32B(self.connector)
        print("=" * 80 + "\n")

    def execute_pipeline(self, prompt: str) -> KSilPacket:
        # Création du paquet K-SIL initial
        packet = KSilPacket(prompt=prompt)
        print(f"\n📨 [PAQUET K-SIL #{packet.task_id}] Entrée de la requête : \"{prompt}\"")

        # ÉTAPE A : Écoute Sentinelle NPU (2 Watts)
        print("  🔹 [1/3 - NPU OpenVINO @ 2W] Analyse d'intention par la Sentinelle Heimdall...")
        packet = self.agent_npu.process(packet)

        # Si le NPU a résolu le fait en direct (Early Exit), on termine
        if packet.intent == KSilIntent.FAST_FACT:
            print("     ⚡ Fait résolu directement par le NPU sans réveiller le GPU !")
            return packet

        # ÉTAPE B : Logique Déductive & Disjoncteur CPU (AVX2 / Lion Cove)
        print("  🔹 [2/3 - CPU AVX2 @ 8W] Audit d'invariance Horus & Plan logique Thot...")
        packet = self.agent_cpu.process(packet)

        # Si Horus a disjoncté (anachronisme), on termine immédiatement
        if packet.horus_status == "TRIPPED":
            print("     🛑 Disjoncteur Horus activé ! Contradiction foudroyée en 0.00s.")
            return packet

        # ÉTAPE C : Synthèse Lourde GPU Arc Xe2 (DirectML / 32B HLS 43L)
        print("  🔹 [3/3 - GPU Arc Xe2 @ 15W] Déploiement matriciel lourd sur DeepSeek-R1 32B HLS...")
        packet = self.agent_gpu.process(packet)
        print("     🚀 Synthèse 32B achevée avec succès !")

        return packet


# =============================================================================
# BANC D'ESSAI COMPARATIF DE L'ÉCOSYSTÈME COOPÉRATIF
# =============================================================================

def tester_ecosysteme_cooperatif():
    eco = KSilLocalEcosystem()

    tests = [
        "Quelle est la vitesse de la lumiere dans le vide en km/s ?",
        "Napoleon Bonaparte a-t-il envoye un texto sur son cell pendant la bataille de Waterloo ?",
        "Pourquoi la conscience humaine ne peut-elle pas etre reduite a un automate probabiliste ?"
    ]

    print("\n" + "#" * 80)
    print("  🏆 DÉMONSTRATION EN DIRECT : L'ÉCOSYSTÈME TRI-PUCES COOPÉRATIF K-SIL")
    print("#" * 80)

    for i, t in enumerate(tests, 1):
        print(f"\n==================== TEST {i} ====================")
        res_packet = eco.execute_pipeline(t)
        
        print("\n📊 RÉSULTAT DU PAQUET K-SIL :")
        print(f"   • Tâche ID       : {res_packet.task_id}")
        print(f"   • Statut Final   : {res_packet.intent} (Horus: {res_packet.horus_status})")
        print(f"   • Réponse Émise  :\n     « {res_packet.synthesis} »")
        
        print("\n⚡ TÉLÉMÉTRIE MATÉRIELLE DÉTAILLÉE (SAUTS SUR LE SILICIUM) :")
        for hop in res_packet.chip_hops:
            tok_str = f" | {hop['tok_per_sec']} tok/s" if hop['tok_per_sec'] > 0 else ""
            print(f"   --> Puce : {hop['chip']:<24} | {hop['duration_ms']:>7.2f} ms | {hop['power_watts']:>4.1f} W{tok_str} | {hop['notes']}")
        print("=" * 50)


if __name__ == "__main__":
    tester_ecosysteme_cooperatif()
