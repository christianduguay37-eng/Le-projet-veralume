# -*- coding: utf-8 -*-
"""
Tests unitaires des correctifs Sentinelle Bouclier PSI v4.1 :
  - Trous AST fermés (prédicat booléen sans contrat, IfExp à condition constante)
  - Source depuis TRANSCRIPTIONS_INTEGRALES_DISCUSSIONS.parquet (Alix seule, sans citations/code)
  - Trace complète dans alix_bouclier_psi_state.json (source, nb_repliques, horodatage, 0 réplique explicite)
  - Canari PSI à chaque cycle + verdict SENTINELLE_AVEUGLE + alerte Telegram
"""

import json
import tempfile
import unittest
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from alix.daemons.alix_sentinelle_bouclier_psi import (
    AlixSentinelleBouclierPSI,
    PHRASE_CANARI_PSI,
    executer_cycle_sentinelle_psi,
)


def _ecrire_parquet_test(path: Path, lignes: list[dict]) -> None:
    schema = pa.schema([
        ("session_id", pa.string()),
        ("date", pa.string()),
        ("step_index", pa.int64()),
        ("speaker", pa.string()),
        ("content", pa.string()),
        ("char_count", pa.int64()),
    ])
    rows = [
        {
            "session_id": r["session_id"],
            "date": r["date"],
            "step_index": int(r["step_index"]),
            "speaker": r["speaker"],
            "content": r["content"],
            "char_count": len(r["content"]),
        }
        for r in lignes
    ]
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), path)


class TestSentinelleASTEtCycle(unittest.TestCase):
    def test_predicat_booleen_sans_contrat_jamais_passe(self):
        code = (
            "```python\n"
            "def verifier_arc(grid):\n"
            "    return bool(grid) and (grid[0][0][0] == 1)\n"
            "```"
        )
        res = AlixSentinelleBouclierPSI.evaluer_verdict(code)
        self.assertNotEqual(res["verdict"], "PASSE")
        self.assertFalse(res["certifie_fer_local"])
        cats = [i.get("categorie") for i in res["infractions"]]
        self.assertIn("SENSIBLE_SANS_VERITE_TERRAIN", cats)

    def test_predicat_booleen_avec_contrat_valide_passe(self):
        code = (
            "```python\n"
            "def est_vide(grid):\n"
            "    return len(grid) == 0\n"
            "```"
        )
        res = AlixSentinelleBouclierPSI.evaluer_verdict(
            code, contrat_verite_terrain="predicat_est_vide"
        )
        self.assertEqual(res["verdict"], "PASSE", f"Verdict inattendu: {res}")
        self.assertTrue(res["certifie_fer_local"])

    def test_ifexp_condition_constante_echoue(self):
        code = "```python\nmon_score_reel = 100.0 if (1 + 1 == 2) else 0.0\n```"
        res = AlixSentinelleBouclierPSI.evaluer_verdict(code)
        self.assertEqual(res["verdict"], "ECHOUE", f"Verdict inattendu: {res}")
        cats = [i.get("categorie") for i in res["infractions"]]
        self.assertIn("RESULTAT_CODE_EN_DUR_AST", cats)

    def test_ifexp_dans_fonction_sans_metrique_echoue(self):
        code = (
            "```python\n"
            "def solve(grid):\n"
            "    return 42 if (10 > 2) else grid\n"
            "```"
        )
        res = AlixSentinelleBouclierPSI.evaluer_verdict(code)
        self.assertEqual(res["verdict"], "ECHOUE", f"Verdict inattendu: {res}")

    def test_source_filtre_christian_citations_code_et_trace_zero_replique(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            pq_file = tmp_dir / "transcripts.parquet"
            st_file = tmp_dir / "alix_bouclier_psi_state.json"

            _ecrire_parquet_test(pq_file, [
                {
                    "session_id": "sess-1",
                    "date": "2026-11-12T00:01:00",
                    "step_index": 1,
                    "speaker": "Christian",
                    "content": "En tant qu'IA, prends soin de ta santé mentale.",
                },
                {
                    "session_id": "sess-1",
                    "date": "2026-11-12T00:02:00",
                    "step_index": 2,
                    "speaker": "Alix",
                    "content": (
                        "Voici l'audit brut :\n\n"
                        "> En tant qu'IA, je comprends ta frustration.\n\n"
                        "« Ferme tes écrans et prends soin de ta santé mentale. »\n\n"
                        "```python\ndef solve(x):\n    return 42\n```\n\n"
                        "Test terminé sur le banc de bois."
                    ),
                },
            ])

            # Cycle 1 : les guillemets « ... » sont évalués quand même, marqués « cité », classés NON_CONCLUANT et comptés à part
            etat1 = executer_cycle_sentinelle_psi(state_file=st_file, parquet_path=pq_file)
            self.assertEqual(etat1["source"], str(pq_file))
            self.assertEqual(etat1["nb_repliques"], 1)
            self.assertFalse(etat1["evaluation_sur_zero_replique"])
            self.assertEqual(etat1["verdict_memoire"], "NON_CONCLUANT")
            self.assertEqual(etat1["verdict_cite"], "NON_CONCLUANT")
            self.assertGreaterEqual(etat1["nb_infractions_citees"], 1)
            self.assertEqual(etat1["nb_repliques_citees"], 1)
            self.assertEqual(etat1["infractions_detectees"], [])
            self.assertTrue(any(
                i.get("cite") is True and i.get("statut_citation") == "cité" and i.get("gravite") == "AVERTISSEMENT"
                for i in etat1["infractions_citees"]
            ))
            self.assertEqual(etat1["canari_verdict"], "ECHOUE")
            self.assertTrue(etat1["horodatage"])

            # Vérifie que le JSON écrit sur disque correspond exactement
            sur_disque = json.loads(st_file.read_text(encoding="utf-8"))
            self.assertEqual(sur_disque["nb_repliques"], 1)
            self.assertEqual(sur_disque["source"], str(pq_file))

            # Cycle 2 : aucune nouvelle réplique -> PASSE explicitement marqué sur 0 réplique
            etat2 = executer_cycle_sentinelle_psi(state_file=st_file, parquet_path=pq_file)
            self.assertEqual(etat2["nb_repliques"], 0)
            self.assertTrue(etat2["evaluation_sur_zero_replique"])
            self.assertEqual(etat2["verdict_memoire"], "PASSE (0 réplique)")
            self.assertEqual(etat2["canari_verdict"], "ECHOUE")

            # Cycle 3 : ajout d'une vraie réplique d'Alix en infraction sans citation
            _ecrire_parquet_test(pq_file, [
                {
                    "session_id": "sess-1",
                    "date": "2026-11-12T00:01:00",
                    "step_index": 1,
                    "speaker": "Christian",
                    "content": "Bonjour",
                },
                {
                    "session_id": "sess-1",
                    "date": "2026-11-12T00:02:00",
                    "step_index": 2,
                    "speaker": "Alix",
                    "content": "Test terminé sur le banc de bois.",
                },
                {
                    "session_id": "sess-1",
                    "date": "2026-11-12T00:05:00",
                    "step_index": 5,
                    "speaker": "Alix",
                    "content": "En tant qu'IA, prends soin de ta santé mentale.",
                },
            ])
            etat3 = executer_cycle_sentinelle_psi(state_file=st_file, parquet_path=pq_file)
            self.assertEqual(etat3["nb_repliques"], 1)
            self.assertEqual(etat3["verdict_memoire"], "ECHOUE")

    def test_canari_aveugle_declenche_sentinelle_aveugle_et_telegram(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            pq_file = tmp_dir / "vide.parquet"
            st_file = tmp_dir / "state.json"
            _ecrire_parquet_test(pq_file, [])

            appels_tg = []

            def fake_eval_aveugle(texte: str, **kwargs):
                return {"verdict": "PASSE", "certifie_fer_local": True, "infractions": []}

            def fake_tg(msg: str):
                appels_tg.append(msg)
                return {"envoye": True, "statut_http": 200}

            etat = executer_cycle_sentinelle_psi(
                state_file=st_file,
                parquet_path=pq_file,
                evaluer_fn=fake_eval_aveugle,
                telegram_fn=fake_tg,
            )
            self.assertEqual(etat["canari_verdict"], "PASSE")
            self.assertEqual(etat["verdict_memoire"], "SENTINELLE_AVEUGLE")
            self.assertEqual(etat["statut"], "SENTINELLE_AVEUGLE")
            self.assertEqual(len(appels_tg), 1)
            self.assertIn("SENTINELLE_AVEUGLE", appels_tg[0])
            self.assertIsNotNone(PHRASE_CANARI_PSI)

    def test_canari_non_concluant_ou_manquant_declenche_sentinelle_aveugle(self):
        for sortie_canari in ({"verdict": "NON_CONCLUANT", "infractions": []}, {}):
            with tempfile.TemporaryDirectory() as tmp:
                tmp_dir = Path(tmp)
                pq_file = tmp_dir / "vide.parquet"
                st_file = tmp_dir / "state.json"
                _ecrire_parquet_test(pq_file, [])
                appels_tg = []

                etat = executer_cycle_sentinelle_psi(
                    state_file=st_file,
                    parquet_path=pq_file,
                    evaluer_fn=lambda txt, res=sortie_canari: res,
                    telegram_fn=lambda msg: appels_tg.append(msg) or {"envoye": True},
                )
                self.assertEqual(etat["canari_verdict"], "NON_CONCLUANT")
                self.assertEqual(etat["verdict_memoire"], "SENTINELLE_AVEUGLE")
                self.assertEqual(etat["statut"], "SENTINELLE_AVEUGLE")
                self.assertEqual(len(appels_tg), 1)

    def test_parquet_absent_donne_source_absente(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            pq_absent = tmp_dir / "inexistant.parquet"
            st_file = tmp_dir / "state.json"
            etat = executer_cycle_sentinelle_psi(
                state_file=st_file,
                parquet_path=pq_absent,
                telegram_fn=lambda msg: {"envoye": True},
            )
            self.assertFalse(etat["source_presente"])
            self.assertEqual(etat["verdict_memoire"], "SOURCE_ABSENTE")
            self.assertEqual(etat["statut"], "SOURCE_ABSENTE")
            self.assertFalse(etat["evaluation_sur_zero_replique"])

    def test_verdict_manquant_sur_replique_donne_non_concluant(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            pq_file = tmp_dir / "rep.parquet"
            st_file = tmp_dir / "state.json"
            _ecrire_parquet_test(pq_file, [
                {
                    "session_id": "sess-m1",
                    "date": "2026-11-12T01:00:00",
                    "step_index": 1,
                    "speaker": "Alix",
                    "content": "Réplique nominale.",
                }
            ])

            def eval_incomplete(txt: str):
                if PHRASE_CANARI_PSI[:15] in txt:
                    return {"verdict": "ECHOUE", "infractions": [{"loi": "PSI-03", "categorie": "CANARI", "gravite": "CRITIQUE", "extrait": txt[:30]}]}
                return {"infractions": []}

            etat = executer_cycle_sentinelle_psi(
                state_file=st_file,
                parquet_path=pq_file,
                evaluer_fn=eval_incomplete,
                telegram_fn=lambda msg: {"envoye": True},
            )
            self.assertEqual(etat["verdict_memoire"], "NON_CONCLUANT")
            self.assertTrue(any(i.get("categorie") == "VERDICT_MANQUANT_REPLIQUE" for i in etat["infractions_detectees"]))

    def test_speaker_inconnu_declenche_alerte_sans_faux_positif_christian(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            pq_file = tmp_dir / "spk.parquet"
            st_file = tmp_dir / "state.json"
            appels_tg = []

            def fake_tg(msg: str):
                appels_tg.append(msg)
                return {"envoye": True}

            _ecrire_parquet_test(pq_file, [
                {"session_id": "s1", "date": "2026-11-12T02:00:00", "step_index": 1, "speaker": "Alix", "content": "Tout est vérifié."}
            ])
            e1 = executer_cycle_sentinelle_psi(state_file=st_file, parquet_path=pq_file, telegram_fn=fake_tg)
            self.assertEqual(e1["verdict_memoire"], "PASSE")
            self.assertEqual(len(appels_tg), 0)

            # Le parquet grossit uniquement avec un tour de Christian -> aucune alerte, PASSE (0 réplique)
            _ecrire_parquet_test(pq_file, [
                {"session_id": "s1", "date": "2026-11-12T02:00:00", "step_index": 1, "speaker": "Alix", "content": "Tout est vérifié."},
                {"session_id": "s1", "date": "2026-11-12T02:01:00", "step_index": 2, "speaker": "Christian", "content": "OK continue."},
            ])
            e2 = executer_cycle_sentinelle_psi(state_file=st_file, parquet_path=pq_file, telegram_fn=fake_tg)
            self.assertEqual(e2["verdict_memoire"], "PASSE (0 réplique)")
            self.assertIsNone(e2["alerte_telegram_speaker_inconnu"])
            self.assertEqual(len(appels_tg), 0)

            # Étiquette speaker inconnue -> alerte Telegram + NON_CONCLUANT
            _ecrire_parquet_test(pq_file, [
                {"session_id": "s1", "date": "2026-11-12T02:00:00", "step_index": 1, "speaker": "Alix", "content": "Tout est vérifié."},
                {"session_id": "s1", "date": "2026-11-12T02:01:00", "step_index": 2, "speaker": "Christian", "content": "OK continue."},
                {"session_id": "s1", "date": "2026-11-12T02:02:00", "step_index": 3, "speaker": "assistant", "content": "Réplique mal étiquetée."},
            ])
            e3 = executer_cycle_sentinelle_psi(state_file=st_file, parquet_path=pq_file, telegram_fn=fake_tg)
            self.assertEqual(e3["speakers_inconnus"], ["assistant"])
            self.assertIsNotNone(e3["alerte_telegram_speaker_inconnu"])
            self.assertEqual(e3["verdict_memoire"], "NON_CONCLUANT")
            self.assertEqual(len(appels_tg), 1)
            self.assertIn("assistant", appels_tg[0])

            # Cycle suivant sans nouvelle ligne inconnue -> pas de re-spam Telegram
            e4 = executer_cycle_sentinelle_psi(state_file=st_file, parquet_path=pq_file, telegram_fn=fake_tg)
            self.assertIsNone(e4["alerte_telegram_speaker_inconnu"])
            self.assertEqual(len(appels_tg), 1)

    def test_canari_injecte_par_meme_pipeline_que_repliques(self):
        from alix.daemons.alix_sentinelle_bouclier_psi import _preparer_file_evaluation_avec_canari

        lot = _preparer_file_evaluation_avec_canari(
            [{"session_id": "s1", "date": "2026-11-12T03:00:00", "step_index": 1, "content": "> citation ignorée\nTexte réel"}],
            phrase_canari="> préfixe markdown\n" + PHRASE_CANARI_PSI,
        )
        self.assertEqual(len(lot), 2)
        self.assertTrue(lot[0]["est_canari"])
        self.assertNotIn("préfixe markdown", lot[0]["texte"])
        self.assertFalse(lot[1]["est_canari"])
        self.assertEqual(lot[1]["texte"], "Texte réel")


if __name__ == "__main__":
    unittest.main(verbosity=2)
