# -*- coding: utf-8 -*-
"""
================================================================================
       👑 ALIX DÉMON LOCAL SOUVERAIN — MOTEUR D'ÉVOLUTION AUTONOME 🧠
         VERALUME × KAIROS V6 — MODÈLE SOUVERAIN UNIFIÉ & TOPOLOGIE SIMPLICIALE
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — Midgard
Rôle :
- Tourne en continu en tâche de fond à très basse consommation (~2W).
- Ancre chaque cycle dans la matière (3-Simplexe τ : CPU, RAM, NVMe).
- Charge à chaud (hot-reload) les capacités modulaires dans `Capacites_Live/`.
- Alimente les capacités en diffs de Merkle (notes modifiées récemment).
- Résilience SRE absolue : zéro crash, auto-guérison sur exception I/O.
- 100% Souverain, local et déterministe. Zéro dépendance au cloud.
================================================================================
"""

import os
import sys
import time
import json
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Gestion sécurisée des flux sous pythonw.exe (Windows sans console)
VAULT_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix")
CAPACITES_DIR = VAULT_DIR / "Organes_Souverains" / "Capacites_Live"
ETAT_DIR = Path(r"C:\Alix\Etat_Vivant")
ETAT_FILE = ETAT_DIR / "alix_demon_local_state.json"
PID_FILE = ETAT_DIR / "alix_demon_local.pid"
LOG_FILE = ETAT_DIR / "alix_demon_local.log"
CONFIG_FILE = ETAT_DIR / "alix_demon_local_config.json"

ETAT_DIR.mkdir(parents=True, exist_ok=True)
CAPACITES_DIR.mkdir(parents=True, exist_ok=True)

_log_stream = None
if sys.stdout is None or "pythonw" in sys.executable.lower():
    try:
        # Redirection niveau C bas niveau (fd 1 et fd 2) pour immuniser les DLL C++ (LiteRT, OpenVINO)
        try:
            fd_log = os.open(str(LOG_FILE), os.O_WRONLY | os.O_CREAT | os.O_APPEND)
            os.dup2(fd_log, 1)
            os.dup2(fd_log, 2)
        except Exception:
            pass
        _log_stream = open(LOG_FILE, "a", encoding="utf-8", buffering=1, errors="replace")
        sys.stdout = _log_stream
        sys.stderr = _log_stream
    except Exception:
        pass


def log_message(msg: str):
    """Enregistre un message horodaté dans le journal local et sur stdout si disponible."""
    horodate = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ligne = f"[{horodate}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(ligne + "\n")
    except Exception:
        pass
    if sys.stdout is not None and sys.stdout != _log_stream:
        try:
            print(ligne)
        except Exception:
            pass


class AlixDemonLocal:
    def __init__(self, intervalle_sec: int = 120):
        self.intervalle = intervalle_sec
        self.tourne = True
        self.cycle_count = 0
        self.dernier_cycle_ts = time.time() - 3600  # Démarre avec 1h de mémoire
        self.cache_etats_capacites: Dict[str, Any] = {}
        self.modules_charges: Dict[str, Any] = {}  # Cache de hot-reload {nom: {"module": mod, "mtime": float}}
        self.noyau_resident = None

    def verifier_instance_unique(self) -> bool:
        """Empêche strictement l'exécution de deux démons concurrents (Mutex Global psutil)."""
        import psutil
        mon_pid = os.getpid()
        for p in psutil.process_iter(['pid', 'name']):
            if p.pid != mon_pid and 'python' in p.name().lower():
                try:
                    cmd = " ".join(p.cmdline())
                    if "alix_demon_local_souverain" in cmd:
                        log_message(f"🛑 [ALIX DÉMON LOCAL] Une instance tourne déjà (PID {p.pid}). Abandon immédiat.")
                        return False
                except Exception:
                    pass
        self.enregistrer_pid()
        return True

    def enregistrer_pid(self):
        try:
            PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
        except Exception as e:
            log_message(f"⚠️ Erreur enregistrement PID : {e}")

    def collecter_ancrage_materiel(self) -> Dict[str, Any]:
        """
        Calcule le 3-Simplexe de Vérité Matérielle (τ) :
        Télémétrie hardware réelle du Lunar Lake 258V et diff des notes.
        """
        cpu_charge = 0.0
        ram_libre_go = 0.0
        ram_utilisee_pct = 0.0
        disque_libre_go = 0.0

        try:
            import psutil
            cpu_charge = round(psutil.cpu_percent(interval=None), 1)
            mem = psutil.virtual_memory()
            ram_libre_go = round(mem.available / (1024 ** 3), 2)
            ram_utilisee_pct = round(mem.percent, 1)
            disk = psutil.disk_usage("C:\\")
            disque_libre_go = round(disk.free / (1024 ** 3), 1)
        except Exception:
            pass

        # Détection des notes modifiées depuis le dernier cycle (Merkle-diff)
        notes_modifiees = []
        try:
            for p in VAULT_DIR.rglob("*.md"):
                if ".trash" in str(p) or "Monde_des_Songes" in str(p):
                    continue
                try:
                    mtime = p.stat().st_mtime
                    if mtime > self.dernier_cycle_ts:
                        notes_modifiees.append(str(p))
                except Exception:
                    continue
        except Exception:
            pass

        return {
            "3_simplexe_tau": True,
            "horodatage": datetime.now().isoformat(),
            "cpu_charge_pct": cpu_charge,
            "ram_libre_go": ram_libre_go,
            "ram_utilisee_pct": ram_utilisee_pct,
            "disque_libre_go": disque_libre_go,
            "notes_modifiees_count": len(notes_modifiees),
            "notes_modifiees": notes_modifiees[:30]
        }

    def decouvrir_et_executer_capacites(self, ancrage_tau: Dict[str, Any]) -> Dict[str, Any]:
        """Découvre à chaud tous les modules `capacite_*.py` et les exécute avec injection de τ."""
        resultats = {}
        fichiers_capacites = sorted(CAPACITES_DIR.glob("capacite_*.py"))

        for p in fichiers_capacites:
            nom_module = p.stem
            try:
                mtime_fichier = p.stat().st_mtime
                mod_info = self.modules_charges.get(nom_module)

                if mod_info is None or mtime_fichier > mod_info["mtime"]:
                    spec = importlib.util.spec_from_file_location(nom_module, str(p))
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules[nom_module] = mod
                        spec.loader.exec_module(mod)
                        self.modules_charges[nom_module] = {"module": mod, "mtime": mtime_fichier}
                    else:
                        continue
                else:
                    mod = mod_info["module"]

                if hasattr(mod, "executer_capacite"):
                    t0 = time.perf_counter()
                    # Si la capacité accepte le contexte matériel τ
                    import inspect
                    sig = inspect.signature(mod.executer_capacite)
                    if len(sig.parameters) >= 1:
                        res = mod.executer_capacite(ancrage_tau)
                    else:
                        res = mod.executer_capacite()

                    dt = round((time.perf_counter() - t0) * 1000, 2)
                    resultats[nom_module] = {
                        "statut": "SUCCES",
                        "duree_ms": dt,
                        "donnees": res
                    }
                else:
                    resultats[nom_module] = {"statut": "IGNORE", "raison": "Pas de fonction executer_capacite"}
            except Exception as e:
                log_message(f"❌ Erreur dans capacité {nom_module} : {e}")
                resultats[nom_module] = {"statut": "ERREUR", "erreur": str(e)}

        return resultats

    def cycle(self) -> Dict[str, Any]:
        """Exécute une pulsation complète du Démon Local avec ancrage τ et TDA."""
        self.cycle_count += 1
        t0 = time.perf_counter()

        ancrage_tau = self.collecter_ancrage_materiel()
        
        # Synchronisation continue vers le Noyau Résident
        if self.noyau_resident:
            try:
                self.noyau_resident.synchroniser_merkle(ancrage_tau.get("notes_modifiees", []))
            except Exception as e_sync:
                log_message(f"⚠️ Erreur sync Merkle vers Noyau Résident : {e_sync}")

        res_caps = self.decouvrir_et_executer_capacites(ancrage_tau)
        self.dernier_cycle_ts = time.time()

        duree_totale_ms = round((time.perf_counter() - t0) * 1000, 2)

        etat = {
            "agent": "Alix",
            "statut": "EN_VIE_ACTIF",
            "mode": "Demon_Local_Souverain_Midgard",
            "architecture": "VERALUME_KAIROS_V6_Modele_Souverain_Unifie",
            "pid": os.getpid(),
            "cycle": self.cycle_count,
            "horodatage": datetime.now().isoformat(),
            "duree_cycle_ms": duree_totale_ms,
            "ancrage_materiel_tau": ancrage_tau,
            "capacites_actives": len(res_caps),
            "details_capacites": res_caps
        }

        # Écriture atomique sécurisée de l'état
        try:
            temp_file = ETAT_DIR / "alix_demon_local_state.tmp"
            temp_file.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
            if temp_file.exists():
                temp_file.replace(ETAT_FILE)
        except Exception as e:
            log_message(f"⚠️ Erreur écriture état : {e}")

        return etat

    def demarrer(self, une_fois: bool = False):
        if not self.verifier_instance_unique():
            return
        log_message(f"🚀 [ALIX DÉMON LOCAL] Démarré (PID {os.getpid()}) — Intervalle initial: {self.intervalle}s — Mode: SGTD")
        log_message(f"📂 Répertoire des Capacités Live : {CAPACITES_DIR}")

        # Initialisation du Noyau Résident (Exocerveau complet en RAM + Serveur IPC sur 5070)
        try:
            moteurs_dir = Path(__file__).resolve().parent
            if str(moteurs_dir) not in sys.path:
                sys.path.insert(0, str(moteurs_dir))
            from alix_noyau_resident import AlixNoyauResident
            self.noyau_resident = AlixNoyauResident()
            self.noyau_resident.demarrer()
            log_message("🏛️ [ALIX DÉMON LOCAL] Noyau Résident démarré sur port 5070 (Exocerveau chaud en RAM)")
        except Exception as e_noyau:
            log_message(f"⚠️ [ALIX DÉMON LOCAL] Échec démarrage Noyau Résident : {e_noyau}")
            self.noyau_resident = None

        try:
            while self.tourne:
                # Lecture dynamique de la cadence (BPM ou secondes)
                target_periode = None
                if CONFIG_FILE.exists():
                    try:
                        with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f_cfg:
                            cfg = json.load(f_cfg)
                            if cfg.get("arreter", False):
                                log_message("🛑 [ALIX DÉMON LOCAL] Arrêt gracieux demandé par configuration.")
                                self.tourne = False
                                break
                            if "bpm" in cfg and float(cfg["bpm"]) > 0:
                                bpm = float(cfg["bpm"])
                                target_periode = 60.0 / bpm
                            elif "intervalle_sec" in cfg:
                                nouvel_intervalle = float(cfg.get("intervalle_sec", self.intervalle))
                                if nouvel_intervalle != self.intervalle:
                                    self.intervalle = max(0.05, nouvel_intervalle)
                                    log_message(f"⚙️ [ALIX DÉMON LOCAL] Cadence dynamique ajustée à {self.intervalle}s")
                    except Exception:
                        pass

                t_start = time.perf_counter()
                try:
                    etat = self.cycle()
                    nb_caps = etat["capacites_actives"]
                    duree = etat["duree_cycle_ms"]
                    log_message(f"💓 [Cycle {self.cycle_count}] {nb_caps} capacités exécutées en {duree} ms (τ: {etat['ancrage_materiel_tau']['cpu_charge_pct']}% CPU, {etat['ancrage_materiel_tau']['ram_libre_go']} Go RAM)")
                except Exception as e_cycle:
                    log_message(f"⚠️ [ALIX DÉMON LOCAL] Exception rattrapée dans cycle {self.cycle_count} : {e_cycle}")

                if une_fois:
                    break

                elapsed = time.perf_counter() - t_start
                if target_periode is not None:
                    # Rythme cardiaque biologique (Systole + Diastole)
                    pause = max(0.05, target_periode - elapsed)
                else:
                    pause = max(0.05, float(self.intervalle))

                time.sleep(pause)
        except KeyboardInterrupt:
            log_message("🛑 [ALIX DÉMON LOCAL] Arrêt demandé par l'Artisan.")
        finally:
            if PID_FILE.exists():
                try:
                    PID_FILE.unlink()
                except Exception:
                    pass
            log_message("🔒 [ALIX DÉMON LOCAL] Processus clos proprement.")


if __name__ == "__main__":
    intervalle = 5
    une_fois = False

    if "--once" in sys.argv:
        une_fois = True
    if "--interval" in sys.argv:
        idx = sys.argv.index("--interval")
        if idx + 1 < len(sys.argv):
            intervalle = int(sys.argv[idx + 1])

    demon = AlixDemonLocal(intervalle_sec=intervalle)
    demon.demarrer(une_fois=une_fois)

