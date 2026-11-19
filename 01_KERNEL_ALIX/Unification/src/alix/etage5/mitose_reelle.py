"""
Test réel de l'idée de Christian (18 nov. 2026) :
  cycle 1 : un pionnier essaie, rencontre des pièges, apprend ;
  cycle t : chaque agent engendre 2 bébés qui héritent de la MÉMOIRE DE LEUR LIGNÉE
            (les pièges rayés par leurs ancêtres) et réessaient.
Problème réel : colorier 1..N en k couleurs sans a+b=c monochrome (Schur).
Un « piège » = un coup (nombre x, couleur c) qui a laissé l'agent coincé dans un
minimum local ; il est rayé, et les descendants ne le rejouent plus.

Comparaison à budget égal (même nombre total de pas) :
  A. un agent seul, sans mémoire, qui recommence au hasard quand il est coincé ;
  B. la mitose SANS mémoire (les bébés repartent de l'état du parent, mais oublient) ;
  C. la mitose AVEC mémoire de lignée (l'idée de Christian).
"""
import numpy as np, random, sys, time, json


class Etat:
    def __init__(self, N, k, rnd, col=None):
        self.N, self.k = N, k
        self.col = np.array(col if col is not None else [0] + [rnd.randrange(k) for _ in range(N)])

    def conflits_de(self, x, c):
        """Nombre de triplets monochromes que x aurait s'il était de couleur c."""
        m = (self.col == c); m[x] = True; N = self.N
        n = 0
        if x >= 2:                       # y + (x-y) = x
            ys = np.arange(1, x // 2 + 1); n += int(np.sum(m[ys] & m[x - ys]))
        hi = N - x                      # x + y = z
        if hi >= 1:
            ys = np.arange(1, hi + 1); n += int(np.sum(m[ys] & m[x + ys]))
        return n

    def energie(self):
        N, col = self.N, self.col; E = 0
        for x in range(1, N + 1):
            ys = np.arange(x, N - x + 1)
            if len(ys): E += int(np.sum((col[ys] == col[x]) & (col[x + ys] == col[x])))
        return E

    def en_conflit(self):
        return [x for x in range(1, self.N + 1) if self.conflits_de(x, self.col[x]) > 0]


def marcher(et, pas, rnd, memoire, apprendre, patience=60):
    """Recherche locale min-conflits. Quand l'énergie ne bat plus son record pendant
    `patience` pas, l'agent est dans un piège : il raye les coups (x, couleur) des
    nombres en conflit, puis se secoue. Retourne (E, pas utilisés, pièges payés)."""
    payes = 0
    E = et.energie(); record = E; depuis = 0
    for p in range(pas):
        if E == 0: return 0, p, payes
        cand = et.en_conflit()
        x = rnd.choice(cand)
        cur = et.conflits_de(x, et.col[x])
        options = [(et.conflits_de(x, c), c) for c in range(et.k)
                   if c != et.col[x] and (x, c) not in memoire]
        if options:
            best = min(o[0] for o in options)
            if best <= cur or rnd.random() < 0.1:
                c = rnd.choice([o[1] for o in options if o[0] == best])
                et.col[x] = c; E += best - cur
        if E < record: record = E; depuis = 0
        else: depuis += 1
        if depuis >= patience:                       # piège
            payes += 1
            if apprendre:
                for y in rnd.sample(cand, min(3, len(cand))):
                    memoire.add((y, int(et.col[y])))
            for y in rnd.sample(range(1, et.N + 1), max(1, et.N // 15)):   # secousse
                et.col[y] = rnd.randrange(et.k)
            E = et.energie(); record = E; depuis = 0
    return E, pas, payes


def agent_seul(N, k, budget, graine):
    rnd = random.Random(graine); payes = 0; utilises = 0
    while utilises < budget:
        et = Etat(N, k, rnd)
        E, p, py = marcher(et, min(2000, budget - utilises), rnd, set(), False)  # recommence de zéro
        utilises += p; payes += py
        if E == 0: return True, utilises, payes, et
    return False, utilises, payes, None


def mitose(N, k, budget, graine, memoire_lignee, pas_par_agent=400):
    rnd = random.Random(graine)
    generation = [(Etat(N, k, rnd), set())]   # (état, mémoire de la lignée)
    utilises = payes = 0; cycle = 0
    while utilises < budget and generation:
        cycle += 1; suivante = []
        for et, mem in generation:
            if utilises >= budget: break
            E, p, py = marcher(et, min(pas_par_agent, budget - utilises), rnd, mem, memoire_lignee)
            utilises += p; payes += py
            if E == 0: return True, utilises, payes, et, cycle
            for _ in range(2):            # deux bébés
                bebe = Etat(N, k, rnd, et.col.copy())
                for x in rnd.sample(range(1, N + 1), max(1, N // 20)):   # petite variation
                    bebe.col[x] = rnd.randrange(k)
                suivante.append((bebe, set(mem) if memoire_lignee else set()))
        # la colonie ne garde que les 2^t meilleurs pour rester à budget fixe par cycle
        suivante.sort(key=lambda t: t[0].energie())
        generation = suivante[: 2 ** min(cycle, 6)]
    return False, utilises, payes, None, cycle


if __name__ == "__main__":
    N, k, budget, essais = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    res = {"A_seul": [], "B_mitose_sans_memoire": [], "C_mitose_lignee": []}
    for g in range(essais):
        t = time.time()
        ok, u, py, et = agent_seul(N, k, budget, g); res["A_seul"].append((ok, u, py))
        ok2, u2, py2, et2, cy2 = mitose(N, k, budget, g, False); res["B_mitose_sans_memoire"].append((ok2, u2, py2))
        ok3, u3, py3, et3, cy3 = mitose(N, k, budget, g, True); res["C_mitose_lignee"].append((ok3, u3, py3))
        for e in (et, et2, et3):
            if e is not None: assert e.energie() == 0
        print(f"graine {g}: A {ok}/{u} pas/{py} pièges | B {ok2}/{u2}/{py2} | C {ok3}/{u3}/{py3} (cycle {cy3}) [{time.time()-t:.0f}s]", flush=True)
    for nom, r in res.items():
        print(nom, "réussites", sum(1 for x in r if x[0]), "/", len(r),
              "| pas moyens", int(np.mean([x[1] for x in r])), "| pièges moyens", round(np.mean([x[2] for x in r]), 1))
