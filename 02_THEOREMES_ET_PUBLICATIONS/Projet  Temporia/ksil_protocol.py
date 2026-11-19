"""
===============================================================================
    PROTOCOLE DE MESSAGE K-SIL UNIFIÉ (ÉTAPE 2)
        Format de trame souverain pour l'échange inter-puces
        (NPU OpenVINO <---> CPU AVX2 Logic <---> GPU Arc Xe2 DirectML)
===============================================================================
Auteurs : Christian Duguay & Alix (Sanctuaire Exocerveau)
"""

import sys
import time
import json
import uuid
from typing import Dict, Any, Optional, List

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class KSilChip:
    NPU_OPENVINO = "NPU_OPENVINO"   # 48 TOPS / 2W (Sentinelle, Veille, Faits)
    CPU_AVX2     = "CPU_AVX2"       # x86-64 Lion Cove (Logique, Décomposition, Horus)
    GPU_DIRECTML = "GPU_DIRECTML"   # Arc 140V Xe2 16GB (Matrices lourdes, 32B HLS)
    SYSTEM       = "KAIROS_LEVEL_0" # Arbitre ontologique


class KSilIntent:
    FAST_FACT      = "FAST_FACT"       # Requête directe résolue par NPU
    ANACHRONISM    = "ANACHRONISM"     # Contradiction flagrante interceptée par Horus
    LOGIC_AUDIT    = "LOGIC_AUDIT"     # Structuration déductive requise sur CPU
    HEAVY_GENERATE = "HEAVY_GENERATE"  # Synthèse et rédaction lourde sur GPU
    COMPLETE       = "COMPLETE"        # Tâche achevée


class KSilPacket:
    """
    Trame de données universelle K-SIL.
    Véhicule les tenseurs, les instructions logiques et les invariants KAIROS
    à travers la mémoire unifiée MoP LPDDR5X du SoC Lunar Lake.
    """

    def __init__(
        self,
        task_id: Optional[str] = None,
        source_chip: str = KSilChip.SYSTEM,
        target_chip: str = KSilChip.NPU_OPENVINO,
        intent: str = KSilIntent.FAST_FACT,
        prompt: str = "",
        chi: float = 0.95,
        horus_status: str = "CLEAN"
    ):
        self.task_id = task_id or str(uuid.uuid4())[:8]
        self.timestamp = time.time()
        self.source_chip = source_chip
        self.target_chip = target_chip
        self.intent = intent
        self.chi = chi
        self.horus_status = horus_status

        # Corps de la trame
        self.prompt = prompt
        self.logical_premises: List[str] = []
        self.synthesis: str = ""
        
        # Télémétrie & Traçabilité Silicium
        self.chip_hops: List[Dict[str, Any]] = []

    def record_hop(self, chip: str, duration_s: float, power_w: float, tok_s: float, notes: str = ""):
        """Enregistre le passage sur une puce physique dans la télémétrie K-SIL."""
        self.chip_hops.append({
            "chip": chip,
            "duration_ms": round(duration_s * 1000.0, 2),
            "power_watts": power_w,
            "tok_per_sec": round(tok_s, 2),
            "notes": notes,
            "timestamp": time.time()
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "source_chip": self.source_chip,
            "target_chip": self.target_chip,
            "intent": self.intent,
            "chi": self.chi,
            "horus_status": self.horus_status,
            "prompt": self.prompt,
            "logical_premises": self.logical_premises,
            "synthesis": self.synthesis,
            "chip_hops": self.chip_hops
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KSilPacket":
        packet = cls(
            task_id=data.get("task_id"),
            source_chip=data.get("source_chip", KSilChip.SYSTEM),
            target_chip=data.get("target_chip", KSilChip.NPU_OPENVINO),
            intent=data.get("intent", KSilIntent.FAST_FACT),
            prompt=data.get("prompt", ""),
            chi=data.get("chi", 0.95),
            horus_status=data.get("horus_status", "CLEAN")
        )
        packet.timestamp = data.get("timestamp", time.time())
        packet.logical_premises = data.get("logical_premises", [])
        packet.synthesis = data.get("synthesis", "")
        packet.chip_hops = data.get("chip_hops", [])
        return packet


if __name__ == "__main__":
    print("📜 Test Unitaire du Protocole K-SIL...")
    pkt = KSilPacket(
        source_chip=KSilChip.SYSTEM,
        target_chip=KSilChip.NPU_OPENVINO,
        intent=KSilIntent.LOGIC_AUDIT,
        prompt="Test de trame K-SIL"
    )
    pkt.record_hop(KSilChip.NPU_OPENVINO, 0.045, 2.0, 44.7, "Filtrage d'intention NPU")
    pkt.record_hop(KSilChip.CPU_AVX2, 0.002, 1.0, 0.0, "Audit Horus OK")
    pkt.record_hop(KSilChip.GPU_DIRECTML, 2.45, 15.0, 5.8, "Synthèse 32B HLS")
    
    print(f"Trame générée avec {len(pkt.chip_hops)} sauts matériels :")
    print(pkt.to_json())
    print("\n✅ Étape 2 achevée : Le Protocole de Message K-SIL est opérationnel !")
