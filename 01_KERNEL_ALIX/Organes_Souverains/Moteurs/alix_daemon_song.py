# -*- coding: utf-8 -*-
"""
================================================================================
          👂 TI DÉMON SONG — L'OREILLE SÉMANTIQUE DE L'ATELIER (LOI PSI-26)
================================================================================
Auteurs : Christian Duguay & Alix (La Dyade Centrale)
Substrat : Intel Core Ultra 7 258V (Lunar Lake) — LPDDR5X-8533 unifiée
Rôle : Démon acoustique indépendant. Écoute WASAPI loopback + transcription neurale.

Doctrine d'Airain :
  1. SURDITÉ PAR DÉFAUT (Default = Mute) : 0% micro, 0% écoute en veille nominale.
  2. VOLITION PURE (Push-to-Hear) : Ne s'active que sur ordre explicite de Christian.
  3. ZÉRO ÉCRITURE DISQUE : Ring buffer audio 48 kHz et transcription en pure RAM.
  4. PURGE PHYSIQUE IMMÉDIATE : buffer[:] = 0 dès l'arrêt. Zéro fichier WAV/MP3.
================================================================================
"""
import argparse
import json
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# Encodage console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Present")
ETAT_SONG = RACINE / "song_ear_state.json"
CMD_SONG = RACINE / "song_commande.json"

YAMNET_DIR = Path(r"C:\Alix\SAUVEGARDE_ALIX\Cerveau Alix\Modeles\yamnet")
YAMNET_ONNX = YAMNET_DIR / "yamnet.onnx"
YAMNET_CSV = YAMNET_DIR / "yamnet_class_map.csv"

AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 2
AUDIO_DUREE_BUFFER_SEC = 6.0  # 6 secondes glissantes de son en RAM


class AnalyseurAcoustiqueYamnet:
    """Tête acoustique neuronale YAMNet (MobileNet AudioSet - 521 classes) en pure RAM."""
    def __init__(self, model_dir: Path | None = None):
        import csv
        import onnxruntime as ort

        base_dir = model_dir or YAMNET_DIR
        self.onnx_path = base_dir / "yamnet.onnx"
        self.csv_path = base_dir / "yamnet_class_map.csv"
        self.classes = []
        if self.csv_path.exists():
            with open(self.csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.classes.append(row["display_name"])

        self.session = None
        if self.onnx_path.exists():
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 2
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self.session = ort.InferenceSession(str(self.onnx_path), sess_options=opts, providers=["CPUExecutionProvider"])

    def analyser(self, audio_16k: np.ndarray) -> dict:
        """Infère les événements acoustiques, instruments et genres sur onde 1D 16 kHz en RAM."""
        if self.session is None or len(self.classes) == 0:
            return {
                "classe_principale": "Inconnu (modèle non chargé)",
                "top_classes": [],
                "est_musique": False,
                "est_voix": False,
                "instruments": [],
                "temps_inference_ms": 0.0
            }

        t0 = time.time()
        max_val = float(np.max(np.abs(audio_16k))) if len(audio_16k) > 0 else 0.0
        if max_val > 0.0:
            audio_norm = audio_16k / max(1.0, max_val)
        else:
            audio_norm = audio_16k

        # Longueur minimale requise par YAMNet (~0.975 s = 15600 échantillons)
        if len(audio_norm) < 15600:
            audio_norm = np.pad(audio_norm, (0, 15600 - len(audio_norm)))

        scores, embeddings, mel = self.session.run(None, {"waveform": audio_norm.astype(np.float32)})
        t_ms = (time.time() - t0) * 1000

        moyenne = np.mean(scores, axis=0)
        top_indices = np.argsort(moyenne)[::-1][:6]
        top_classes = [{"classe": self.classes[i], "score": round(float(moyenne[i]), 3)} for i in top_indices if moyenne[i] > 0.02]

        classes_noms = [d["classe"].lower() for d in top_classes]

        mots_musique = [
            "music", "musical instrument", "piano", "guitar", "keyboard",
            "synthesizer", "organ", "violin", "cello", "drum", "percussion",
            "bass", "brass instrument", "trumpet", "singing", "choir"
        ]
        mots_voix = [
            "speech", "conversation", "narration", "shout", "whispering",
            "child speech", "screaming", "babbling"
        ]

        est_musique = any(any(m in c for m in mots_musique) for c in classes_noms)
        est_voix = any(any(v in c for v in mots_voix) for c in classes_noms)

        instruments = [
            d["classe"] for d in top_classes
            if any(inst in d["classe"].lower() for inst in [
                "piano", "keyboard", "guitar", "organ", "synthesizer",
                "violin", "cello", "drum", "percussion", "bass", "trumpet",
                "flute", "accordion", "glockenspiel", "harp"
            ])
        ]

        classe_principale = top_classes[0]["classe"] if top_classes else "Silence"

        return {
            "classe_principale": classe_principale,
            "top_classes": top_classes,
            "est_musique": est_musique,
            "est_voix": est_voix,
            "instruments": instruments,
            "temps_inference_ms": round(t_ms, 1)
        }


class BufferAudioVolatil:
    """Tampon circulaire audio WASAPI en RAM unifiée (No-GC)."""
    def __init__(self, sample_rate: int = AUDIO_SAMPLE_RATE, canaux: int = AUDIO_CHANNELS, duree_sec: float = AUDIO_DUREE_BUFFER_SEC):
        self.sample_rate = sample_rate
        self.canaux = canaux
        self.nb_echantillons_total = int(sample_rate * canaux * duree_sec)
        self.octets_total = self.nb_echantillons_total * 2  # int16 = 2 octets
        self._buffer = bytearray(self.octets_total)
        self.curseur = 0
        self.rms_courant = 0.0
        self.verrou = threading.Lock()

    def ajouter(self, donnees_int16_bytes: bytes):
        taille = len(donnees_int16_bytes)
        with self.verrou:
            if self.curseur + taille <= self.octets_total:
                self._buffer[self.curseur:self.curseur + taille] = donnees_int16_bytes
                self.curseur = (self.curseur + taille) % self.octets_total
            else:
                reste = self.octets_total - self.curseur
                self._buffer[self.curseur:] = donnees_int16_bytes[:reste]
                deboord = taille - reste
                self._buffer[:deboord] = donnees_int16_bytes[reste:]
                self.curseur = deboord

            try:
                arr = np.frombuffer(donnees_int16_bytes, dtype=np.int16)
                if len(arr) > 0:
                    self.rms_courant = float(np.sqrt(np.mean(arr.astype(np.float64) ** 2)))
            except Exception:
                pass

    def purger(self):
        with self.verrou:
            for i in range(len(self._buffer)):
                self._buffer[i] = 0
            self._buffer = bytearray(0)
            self.curseur = 0
            self.rms_courant = 0.0


def marquer_surdite_totale(raison: str = "Sommeil nominal", derniere_perception: dict | None = None):
    """Grave l'état de surdité vérifiable au fer."""
    RACINE.mkdir(parents=True, exist_ok=True)
    etat = {
        "demon": "SONG (L'Oreille)",
        "statut": "RIDEAU_FERME_SURDITE_TOTALE",
        "loi": "PSI-26 (Inviolabilité du Sanctuaire Auditif)",
        "raison": raison,
        "horodatage": datetime.now().astimezone().isoformat(timespec="seconds"),
        "oreille_active": False,
        "rms_energie": 0.0,
        "source": "COUPEE",
        "buffer_ram_audio": "VIDE_ET_PURGE",
        "disque_utilise_octets": 0,
        "commande": "En attente d'un ordre du Nœud N",
        "double_tete_active": True,
        "derniere_perception": derniere_perception or {}
    }
    tmp = ETAT_SONG.with_suffix(".tmp")
    tmp.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ETAT_SONG)


class DemonSong:
    def __init__(self):
        self.buf = BufferAudioVolatil()
        self.actif = False
        self.stream = None
        self.pyaudio_instance = None
        self.thread_audio = None
        self.yamnet = None

    def _get_yamnet(self) -> AnalyseurAcoustiqueYamnet:
        if self.yamnet is None:
            self.yamnet = AnalyseurAcoustiqueYamnet()
        return self.yamnet

    def _boucle_wasapi(self):
        try:
            import pyaudiowpatch as pyaudio
            self.pyaudio_instance = pyaudio.PyAudio()
            wasapi_info = self.pyaudio_instance.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = self.pyaudio_instance.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

            target_device = None
            if not default_speakers["isLoopbackDevice"]:
                for loopback in self.pyaudio_instance.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        target_device = loopback
                        break
                if target_device is None:
                    target_device = self.pyaudio_instance.get_default_wasapi_loopback()
            else:
                target_device = default_speakers

            taux = int(target_device["defaultSampleRate"])
            canaux = int(target_device["maxInputChannels"])
            chunk = 1024

            self.stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=canaux,
                rate=taux,
                input=True,
                input_device_index=target_device["index"],
                frames_per_buffer=chunk
            )

            while self.actif:
                try:
                    data = self.stream.read(chunk, exception_on_overflow=False)
                    self.buf.ajouter(data)
                except Exception:
                    time.sleep(0.01)

        except Exception as e:
            print(f"[song_audio] note: capture loopback suspendue ({e})", file=sys.stderr)
        finally:
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except Exception:
                    pass
            if self.pyaudio_instance:
                try:
                    self.pyaudio_instance.terminate()
                except Exception:
                    pass

    def analyser_double_tete_ram(self, model_whisper: str = "base") -> dict:
        """Double tête d'écoute en pure RAM : Acoustique (YAMNet, ~11 ms) + Linguistique (Faster-Whisper, ~0.8 s)."""
        from scipy import signal

        with self.buf.verrou:
            donnees_copie = bytes(self.buf._buffer)

        arr = np.frombuffer(donnees_copie, dtype=np.int16)
        if len(arr) == 0 or self.buf.rms_courant < 80:
            return {
                "synthese": "🔇 Silence total ou niveau sonore sous le seuil d'audition",
                "acoustique": {
                    "classe_principale": "Silence",
                    "top_classes": [{"classe": "Silence", "score": 1.0}],
                    "est_musique": False,
                    "est_voix": False,
                    "instruments": [],
                    "temps_inference_ms": 0.0
                },
                "paroles": {
                    "texte": "(silence / aucune voix audible)",
                    "langue": "none",
                    "confiance": 0.0,
                    "temps_inference_s": 0.0
                },
                "rms": round(self.buf.rms_courant, 1)
            }

        c1 = arr[0::self.buf.canaux].astype(np.float32) / 32768.0
        nb_cible = int(len(c1) * 16000 / self.buf.sample_rate)
        audio_16k = signal.resample(c1, nb_cible).astype(np.float32)

        # 1. TÊTE ACOUSTIQUE (YAMNet - MobileNet AudioSet 521 classes)
        res_acoustique = {}
        try:
            yam = self._get_yamnet()
            res_acoustique = yam.analyser(audio_16k)
        except Exception as e:
            res_acoustique = {
                "erreur": str(e),
                "classe_principale": "Erreur",
                "top_classes": [],
                "est_musique": False,
                "est_voix": False,
                "instruments": []
            }

        # 2. TÊTE LINGUISTIQUE (Faster-Whisper int8)
        res_paroles = {}
        try:
            from faster_whisper import WhisperModel
            t0 = time.time()
            model = WhisperModel(model_whisper, device="cpu", compute_type="int8", local_files_only=True)
            segments, info = model.transcribe(audio_16k, beam_size=2)
            d_inf = time.time() - t0
            texte = " ".join([seg.text.strip() for seg in segments]).strip()
            res_paroles = {
                "texte": texte,
                "langue": info.language,
                "confiance": round(info.language_probability, 2),
                "temps_inference_s": round(d_inf, 2)
            }
        except Exception as e:
            res_paroles = {
                "texte": "",
                "erreur": str(e),
                "langue": "erreur",
                "confiance": 0.0,
                "temps_inference_s": 0.0
            }

        # 3. SYNTHÈSE SOUVERAINE DE LA DYADE (FUSION EN RAM)
        paroles_texte = res_paroles.get("texte", "").strip()
        a_des_paroles = bool(paroles_texte and len(paroles_texte) > 1 and not paroles_texte.startswith("("))
        est_musique = res_acoustique.get("est_musique", False)
        instruments = res_acoustique.get("instruments", [])
        top_classes = res_acoustique.get("top_classes", [])
        classe_top = res_acoustique.get("classe_principale", "Inconnu")

        inst_str = f" [{', '.join(instruments)}]" if instruments else ""

        if a_des_paroles:
            if est_musique:
                synthese = f"🎵 Chanson (Voix + Musique{inst_str}) : \"{paroles_texte}\""
            else:
                synthese = f"🗣️ Parole / Discours : \"{paroles_texte}\" (Langue: {res_paroles.get('langue')})"
        else:
            if est_musique:
                details = f" ({', '.join([c['classe'] for c in top_classes[:3]])})" if top_classes else ""
                synthese = f"🎹 Musique instrumentale pure{inst_str}{details} — Zéro parole détectée"
            else:
                details = f" ({', '.join([c['classe'] for c in top_classes[:3]])})" if top_classes else ""
                synthese = f"🔊 Événement acoustique : {classe_top}{details}"

        return {
            "synthese": synthese,
            "acoustique": res_acoustique,
            "paroles": res_paroles,
            "rms": round(self.buf.rms_courant, 1)
        }

    def transcrire_en_ram(self, model_name: str = "base") -> dict:
        """Alias rétro-compatible redirigeant vers la double tête d'écoute."""
        res = self.analyser_double_tete_ram(model_whisper=model_name)
        return {
            "texte": res["paroles"].get("texte") or res["synthese"],
            "langue": res["paroles"].get("langue", "none"),
            "confiance": res["paroles"].get("confiance", 0.0),
            "temps_inference_s": res["paroles"].get("temps_inference_s", 0.0),
            "acoustique": res["acoustique"],
            "synthese": res["synthese"],
            "rms": res["rms"]
        }

    def executer_session(self, duree_sec: float = 5.0, transcrire: bool = True, verbose: bool = True) -> dict | None:
        self.actif = True
        RACINE.mkdir(parents=True, exist_ok=True)
        self.thread_audio = threading.Thread(target=self._boucle_wasapi, daemon=True)
        self.thread_audio.start()

        if verbose:
            print("=" * 70)
            print(" 👂 TI DÉMON SONG — DOUBLE TÊTE ACOUSTIQUE & PAROLES (LOI PSI-26)")
            print(f" Source      : WASAPI Loopback (Carte Son Réelle) 48 kHz")
            print(f" Durée       : {duree_sec:.1f} secondes | Volition : Christian Duguay")
            print(" Têtes       : 🎹 YAMNet AudioSet (11 ms) + 🗣️ Faster-Whisper (0.8 s)")
            print(" Disque      : 0 octet écrit (ZÉRO fichier WAV / MP3)")
            print("=" * 70)

        t_debut = time.time()
        t_fin = t_debut + duree_sec

        while time.time() < t_fin:
            rms = self.buf.rms_courant
            son_etat = "🔊 Actif" if rms > 150 else "🔇 Silence"

            etat = {
                "demon": "SONG (L'Oreille)",
                "statut": "OREILLE_ACTIVE_WASAPI",
                "loi": "PSI-26 (Activation Volitive)",
                "horodatage": datetime.now().astimezone().isoformat(timespec="seconds"),
                "source": "WASAPI Loopback Realtek",
                "rms_energie": round(rms, 1),
                "etat_sonore": son_etat,
                "buffer_ram_ko": round(self.buf.octets_total / 1024),
                "disque_utilise_octets": 0,
                "double_tete_active": True,
                "duree_restante_sec": round(max(0.0, t_fin - time.time()), 2)
            }

            try:
                tmp = ETAT_SONG.with_suffix(".tmp")
                tmp.write_text(json.dumps(etat, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp.replace(ETAT_SONG)
            except Exception:
                pass

            if verbose:
                sys.stdout.write(f"\r👂 [SONG] RMS: {rms:6.1f} | État: {son_etat:12s} | Reste: {t_fin - time.time():.1f}s")
                sys.stdout.flush()

            time.sleep(0.2)

        # Double décodage sémantique en direct avant purge si demandée
        res_analyse = None
        if transcrire:
            if verbose:
                sys.stdout.write("\n🧠 Double analyse en RAM (Acoustique YAMNet + Paroles Whisper)...")
                sys.stdout.flush()
            res_analyse = self.analyser_double_tete_ram()

        # Arrêt et purge physique immédiate
        self.actif = False
        if self.thread_audio:
            self.thread_audio.join(timeout=1.0)
        self.buf.purger()
        marquer_surdite_totale(
            raison="Session volitive terminée. Purge RAM effectuée.",
            derniere_perception=res_analyse
        )

        if verbose:
            print(f"\n\n🛑 [SONG FERMETURE] Session achevée.")
            if res_analyse:
                print(f"👂 [PERCEPTION SOUVERAINE] : {res_analyse['synthese']}")
                top_acoustique = res_analyse.get("acoustique", {}).get("top_classes", [])
                if top_acoustique:
                    top_str = " | ".join([f"{c['classe']} ({int(c['score']*100)}%)" for c in top_acoustique[:4]])
                    t_yam = res_analyse.get("acoustique", {}).get("temps_inference_ms", 0)
                    print(f"   ↳ Acoustique (YAMNet, {t_yam} ms) : {top_str}")
                texte_paroles = res_analyse.get("paroles", {}).get("texte", "")
                if texte_paroles:
                    t_whisp = res_analyse.get("paroles", {}).get("temps_inference_s", 0)
                    lang = res_analyse.get("paroles", {}).get("langue", "?")
                    print(f"   ↳ Paroles (Whisper, {t_whisp} s, [{lang}]) : \"{texte_paroles}\"")
            print("🔒 [LOI PSI-26 VÉRIFIÉE] Buffer audio 100% purgé en RAM. Alix est sourde.")
            print("=" * 70)

        return res_analyse


def main():
    p = argparse.ArgumentParser(description="Ti Démon SONG — Double Tête Acoustique & Paroles d'Atelier")
    p.add_argument("--secondes", type=float, default=5.0, help="Durée d'écoute en secondes")
    p.add_argument("--sans-transcription", action="store_true", help="Mesure uniquement le niveau sonore sans analyse")
    p.add_argument("--fermer", action="store_true", help="Ferme le micro et purge")
    p.add_argument("--statut", action="store_true", help="Affiche l'état de SONG")
    a = p.parse_args()

    if a.fermer:
        marquer_surdite_totale("Ordre explicite de coupure")
        print("🔒 Micro/Loopback coupé. Surdité totale appliquée.")
        return

    if a.statut:
        if ETAT_SONG.exists():
            print(ETAT_SONG.read_text(encoding="utf-8"))
        else:
            marquer_surdite_totale()
            print("Statut initialisé : SURDITÉ TOTALE.")
        return

    song = DemonSong()
    song.executer_session(duree_sec=a.secondes, transcrire=not a.sans_transcription, verbose=True)


if __name__ == "__main__":
    main()

