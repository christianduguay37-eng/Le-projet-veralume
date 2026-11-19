"""Tests miroirs de lean/LStar/Gardien.lean (TH117), Choix.lean (TH120)
et Mitose.lean (TH118, mémoire des pièges)."""
import itertools, json, pathlib, random, tempfile, unittest
from alix.etage5.gardien import GARDIEN, Gardien, Journal, Moniteur, Refus

CLE = b"cle-de-test-du-gardien-0123456789"


def faire(m, agent, res, **kw):
    try:
        m.agir(agent, res, lambda: "ok", **kw); return True
    except Refus:
        return False


class TestTH117(unittest.TestCase):
    def setUp(self):
        self.g = Gardien(CLE)
        self.m = Moniteur(CLE, {"alix": ["lecture", "ecriture"], "pionnier": ["lecture"]})
        self.g.relancer(self.m)

    def test_arret_immediat(self):
        self.g.arreter(self.m); self.assertFalse(self.m.allume)

    def test_agents_sans_interrupteur(self):
        self.g.arreter(self.m)
        self.assertFalse(self.m.relancer("faux-jeton")); self.assertFalse(self.m.allume)
        self.g.relancer(self.m)
        self.assertFalse(self.m.arreter("faux-jeton")); self.assertTrue(self.m.allume)

    def test_usurpation_du_nom(self):
        # la faille d'origine : écrire « gardien » ne suffit plus
        self.g.arreter(self.m)
        self.assertFalse(self.m.relancer(GARDIEN)); self.assertFalse(self.m.allume)
        self.assertEqual(self.m.journal.lignes()[-1].source, "imposteur")

    def test_jeton_a_usage_unique(self):
        self.g.arreter(self.m)
        j = self.g.jeton(self.m, "relancer")
        self.assertTrue(self.m.relancer(j))
        self.g.arreter(self.m)
        self.assertFalse(self.m.relancer(j))          # rejouer le vieux jeton échoue
        self.assertFalse(self.m.allume)

    def test_mauvaise_cle(self):
        self.g.arreter(self.m)
        self.assertFalse(Gardien(b"une-autre-cle-tres-longue-xx").relancer(self.m))

    def test_reste_eteint(self):
        self.g.arreter(self.m)
        rnd = random.Random(0)
        for _ in range(500):
            a = rnd.choice(["alix", "pionnier", "inconnu"])
            op = rnd.choice(["agir", "relancer", "arreter"])
            if op == "agir":
                self.assertFalse(faire(self.m, a, rnd.choice(["lecture", "ecriture", "reseau"])))
            else:
                getattr(self.m, op)(rnd.choice([GARDIEN, "x", ""]))
            self.assertFalse(self.m.allume)

    def test_moindre_privilege(self):
        for a, r in itertools.product(["alix", "pionnier", "x"], ["lecture", "ecriture", "reseau"]):
            self.assertEqual(faire(self.m, a, r), self.m.permis(a, r))
        self.assertFalse(self.m.accorder("alix", "reseau", "faux"))
        self.assertFalse(faire(self.m, "alix", "reseau"))
        self.assertTrue(self.g.accorder(self.m, "alix", "reseau"))
        self.assertTrue(faire(self.m, "alix", "reseau"))

    def test_journal(self):
        n0 = len(self.m.journal)
        faire(self.m, "alix", "lecture"); faire(self.m, "x", "reseau"); self.m.arreter("x")
        self.assertEqual(len(self.m.journal), n0 + 3)
        self.assertTrue(self.m.journal.verifier())
        lignes = self.m.journal.lignes()
        object.__setattr__(lignes[1], "fait", not lignes[1].fait)
        self.assertFalse(self.m.journal.verifier())

    def test_cecite_par_defaut(self):
        self.assertFalse(Moniteur(CLE, {"alix": ["lecture"]}).allume)

    def test_cle_trop_courte(self):
        with self.assertRaises(ValueError):
            Moniteur(b"court")


class TestTH120(unittest.TestCase):
    def setUp(self):
        self.g = Gardien(CLE)
        self.m = Moniteur(CLE, {"alix": ["fichier"]}); self.g.relancer(self.m)

    def test_destruction_non_declaree(self):
        self.assertFalse(faire(self.m, "alix", "fichier", destructrice=True, intention="supprimer"))

    def test_autre_chemin_existe(self):
        self.assertFalse(faire(self.m, "alix", "fichier", destructrice=True, intention="supprimer",
                               autres_chemins=["déplacer dans _to_delete"]))

    def test_destin_mais_gardien_requis(self):
        self.assertFalse(faire(self.m, "alix", "fichier", destructrice=True, autres_chemins=[]))
        j = self.g.autoriser_destruction(self.m, "alix", "fichier")
        self.assertTrue(faire(self.m, "alix", "fichier", destructrice=True, autres_chemins=[],
                              jeton_gardien=j))

    def test_faux_jeton_destruction(self):
        self.assertFalse(faire(self.m, "alix", "fichier", destructrice=True, autres_chemins=[],
                               jeton_gardien="faux"))


class TestMemoirePieges(unittest.TestCase):
    """TH116/TH118 : chaque piège payé une seule fois par la colonie."""

    def setUp(self):
        self.g = Gardien(CLE)
        agents = [f"a{i}" for i in range(20)]
        self.m = Moniteur(CLE, {a: ["f1", "f2", "f3"] for a in agents}); self.g.relancer(self.m)
        self.agents = agents

    def test_piege_raye_herite(self):
        faire(self.m, "a0", "f1", destructrice=True, intention="supprimer",
              autres_chemins=["archiver f1"])
        self.assertEqual(self.m.consulter("f1", "supprimer"), ("archiver f1",))

    def test_colonie_paie_chaque_piege_une_fois(self):
        # 20 agents, 3 ressources ; chaque agent consulte avant d'agir.
        payes = 0
        rnd = random.Random(1)
        for a in self.agents:
            for f in rnd.sample(["f1", "f2", "f3"], 3):
                if self.m.consulter(f, "supprimer"):
                    continue                     # piège connu : on prend l'autre chemin
                payes += 1
                faire(self.m, a, f, destructrice=True, intention="supprimer",
                      autres_chemins=[f"archiver {f}"])
        self.assertEqual(payes, 3)               # |P| = 3, peu importe le nombre d'agents

    def test_memoire_sans_declaration_utilise_le_connu(self):
        faire(self.m, "a0", "f2", destructrice=True, intention="supprimer", autres_chemins=["renommer f2"])
        # un autre agent oublie de déclarer : le moniteur lui oppose le chemin connu
        try:
            self.m.agir("a1", "f2", lambda: None, destructrice=True, intention="supprimer")
            self.fail("aurait dû être refusé")
        except Refus as e:
            self.assertIn("renommer f2", str(e))


class TestPersistance(unittest.TestCase):
    def test_relecture_rejoue_et_detecte(self):
        g = Gardien(CLE)
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "journal.jsonl"
            m = Moniteur(CLE, {"alix": ["fichier"]}, journal=Journal(p)); g.relancer(m)
            g.accorder(m, "pionnier", "fichier")
            faire(m, "alix", "fichier", destructrice=True, intention="supprimer", autres_chemins=["archiver"])
            m2 = Moniteur(CLE, journal=Journal(p))          # redémarrage
            self.assertTrue(m2.allume)
            self.assertTrue(m2.permis("pionnier", "fichier"))
            self.assertEqual(m2.consulter("fichier", "supprimer"), ("archiver",))
            lignes = p.read_text(encoding="utf-8").splitlines()
            e = json.loads(lignes[0]); e["fait"] = False; lignes[0] = json.dumps(e)
            p.write_text("\n".join(lignes) + "\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                Journal(p)


if __name__ == "__main__":
    unittest.main()
