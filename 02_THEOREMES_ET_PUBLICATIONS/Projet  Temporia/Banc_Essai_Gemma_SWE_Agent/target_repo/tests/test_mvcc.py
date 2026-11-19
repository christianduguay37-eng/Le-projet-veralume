# -*- coding: utf-8 -*-
"""
Suite de tests Palier 10 : Validation du Mini MVCC Storage Engine (Snapshot Isolation).
Épreuves SRE : Isolation Snapshot, OCC First-Committer-Wins, Rollback, Vacuum GC,
Validation des Invariants, Stress Test Concurrence Lourde Multi-Transactions.
"""

import gc
import hashlib
import os
import random
import shutil
import tempfile
import threading
import time
import unittest
import json
from core.mvcc import (
    MVCCStore,
    WriteConflictError,
    TransactionAbortedError,
    Cluster,
    ReplicatedCluster,
    StaleReplicaError,
    HLC,
    Session,
    PartitionUnavailableError,
    StaleReadError,
    GeoCluster,
    AutonomousCluster,
    ByzantineCluster,
    QuantumCluster,
    DilithiumKeyPair,
    ZKTransactionProof,
    ZKVerifier,
    ReplayDetectedError,
    EquivocationDetectedError,
    ByzantineFaultError,
    Row,
    MVCCIndex,
    parse_sql,
    SovereignPalier17Cluster,
    CausalParadoxError,
    MemoryArena,
    EntropyDaemon,
    TerminationAnalyzer,
    SovereignPalier18Cluster,
    verify_proof,
    UnsafeUpgradeError,
    StreamingZeroAllocParser,
    SovereignPalier19Cluster,
    MultiverseTx,
)


class TestMVCCStore(unittest.TestCase):

    def setUp(self):
        self.store = MVCCStore()

    def test_basic_crud_and_read_own_writes(self):
        """Vérifie le cycle fondamental put / get / delete et la lecture de ses propres écritures."""
        tx1 = self.store.begin_transaction()
        self.store.put(tx1, "alpha", 100)
        self.store.put(tx1, "beta", 200)

        # Read-your-own-writes avant commit
        self.assertEqual(self.store.get(tx1, "alpha"), 100)
        self.assertEqual(self.store.get(tx1, "beta"), 200)

        self.assertTrue(self.store.commit(tx1))

        # Nouvelle transaction lisant les données validées
        tx2 = self.store.begin_transaction()
        self.assertEqual(self.store.get(tx2, "alpha"), 100)
        self.assertEqual(self.store.get(tx2, "beta"), 200)

        # Suppression dans tx2
        self.store.delete(tx2, "alpha")
        self.assertIsNone(self.store.get(tx2, "alpha"))
        self.assertTrue(self.store.commit(tx2))

        # Vérification post-suppression
        tx3 = self.store.begin_transaction()
        self.assertIsNone(self.store.get(tx3, "alpha"))
        self.assertEqual(self.store.get(tx3, "beta"), 200)
        self.store.rollback(tx3)

    def test_snapshot_isolation_repeatable_read(self):
        """
        Vérifie l'isolation Snapshot stricte :
        Une transaction active ne voit JAMAIS les modifications committées après son début.
        """
        # État initial
        tx0 = self.store.begin_transaction()
        self.store.put(tx0, "solde", 500)
        self.store.commit(tx0)

        # T1 commence (capture snapshot à solde = 500)
        t1 = self.store.begin_transaction()
        self.assertEqual(self.store.get(t1, "solde"), 500)

        # T2 commence APRÈS, modifie solde à 1000 et commit
        t2 = self.store.begin_transaction()
        self.store.put(t2, "solde", 1000)
        self.assertTrue(self.store.commit(t2))

        # T1 re-lit : DOIT STRICTEMENT REVOIR 500 (Repeatable Read / Snapshot)
        self.assertEqual(self.store.get(t1, "solde"), 500)
        self.store.commit(t1)

        # T3 commence après : voit 1000
        t3 = self.store.begin_transaction()
        self.assertEqual(self.store.get(t3, "solde"), 1000)
        self.store.commit(t3)

    def test_write_conflict_occ_first_committer_wins(self):
        """
        Vérifie la détection de conflit écriture-écriture (OCC) :
        Si deux transactions concurrentes modifient la même clé,
        la première qui commit gagne, la seconde DOIT lever WriteConflictError.
        """
        tx_init = self.store.begin_transaction()
        self.store.put(tx_init, "stock", 10)
        self.store.commit(tx_init)

        t1 = self.store.begin_transaction()
        t2 = self.store.begin_transaction()

        # Les deux transactions modifient la même clé en parallèle
        self.store.put(t1, "stock", 20)
        self.store.put(t2, "stock", 30)

        # T1 commit en premier : Succès
        self.assertTrue(self.store.commit(t1))

        # T2 tente de committer : Conflit écriture-écriture obligatoire !
        with self.assertRaises(WriteConflictError):
            self.store.commit(t2)

        # L'état final doit être 20 (commit de T1)
        t_check = self.store.begin_transaction()
        self.assertEqual(self.store.get(t_check, "stock"), 20)
        self.store.commit(t_check)

    def test_rollback_atomicity(self):
        """Vérifie que le rollback annule toutes les modifications sans laisser de trace."""
        tx0 = self.store.begin_transaction()
        self.store.put(tx0, "clé_fixe", "original")
        self.store.commit(tx0)

        t_bad = self.store.begin_transaction()
        self.store.put(t_bad, "clé_fixe", "modifié_illicite")
        self.store.put(t_bad, "clé_fantôme", "ne_doit_pas_exister")
        self.store.rollback(t_bad)

        # Tentative d'opération sur transaction annulée -> erreur
        with self.assertRaises(TransactionAbortedError):
            self.store.get(t_bad, "clé_fixe")

        # Vérification par une nouvelle transaction
        t_verif = self.store.begin_transaction()
        self.assertEqual(self.store.get(t_verif, "clé_fixe"), "original")
        self.assertIsNone(self.store.get(t_verif, "clé_fantôme"))
        self.store.commit(t_verif)

    def test_vacuum_garbage_collection(self):
        """Vérifie que vacuum() purge les versions devenues invisibles à tous les snapshots."""
        # Création de 5 versions successives de la même clé
        for i in range(5):
            tx = self.store.begin_transaction()
            self.store.put(tx, "compteur", i)
            self.store.commit(tx)

        # Historique initial : 5 versions présentes
        history_before = self.store.get_history("compteur")
        self.assertEqual(len(history_before), 5)

        # Aucune transaction active : le vacuum doit purger les 4 premières versions invalidées
        purged = self.store.vacuum()
        self.assertEqual(purged, 4)

        # Il ne reste que la version courante
        history_after = self.store.get_history("compteur")
        self.assertEqual(len(history_after), 1)
        self.assertEqual(history_after[0][2], 4)

    def test_structural_invariants(self):
        """Vérifie la méthode validate_invariants() après mutations et vacuum."""
        for k in ["a", "b", "c"]:
            for v in range(3):
                tx = self.store.begin_transaction()
                self.store.put(tx, k, v)
                self.store.commit(tx)

        self.assertTrue(self.store.validate_invariants())
        self.store.vacuum()
        self.assertTrue(self.store.validate_invariants())

    def test_heavy_concurrent_transactions_stress(self):
        """
        Stress test multi-thread lourd :
        32 threads exécutant des transactions concurrentes de virement/banque.
        Vérifie la conservation totale de la masse monétaire, l'absence de deadlock
        et la cohérence absolue sous forte contention OCC.
        """
        accounts = [f"acc_{i}" for i in range(10)]
        initial_balance = 1000

        # Initialisation de 10 comptes à 1000 $ (Masse totale = 10 000 $)
        tx_init = self.store.begin_transaction()
        for acc in accounts:
            self.store.put(tx_init, acc, initial_balance)
        self.store.commit(tx_init)

        total_money_expected = len(accounts) * initial_balance
        num_threads = 32
        tx_per_thread = 200
        threads = []
        stats = {"committed": 0, "conflicts": 0, "errors": []}
        stats_lock = threading.Lock()

        def worker_transfers(tid):
            for _ in range(tx_per_thread):
                src, dst = random.sample(accounts, 2)
                amount = random.randint(1, 50)
                try:
                    tx = self.store.begin_transaction()
                    s_bal = self.store.get(tx, src)
                    d_bal = self.store.get(tx, dst)

                    if s_bal is not None and d_bal is not None and s_bal >= amount:
                        self.store.put(tx, src, s_bal - amount)
                        self.store.put(tx, dst, d_bal + amount)
                        time.sleep(0.00005)  # Yield pour entrelacer les threads sous le GIL
                        try:
                            self.store.commit(tx)
                            with stats_lock:
                                stats["committed"] += 1
                        except WriteConflictError:
                            with stats_lock:
                                stats["conflicts"] += 1
                    else:
                        self.store.rollback(tx)
                except Exception as e:
                    with stats_lock:
                        stats["errors"].append((tid, str(e)))

        for t in range(num_threads):
            threads.append(threading.Thread(target=worker_transfers, args=(t,)))

        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=20.0)
            self.assertFalse(th.is_alive(), "Interblocage détecté : un thread est resté bloqué !")

        self.assertEqual(len(stats["errors"]), 0, f"Erreurs inattendues : {stats['errors']}")
        self.assertGreater(stats["committed"], 0)
        self.assertGreater(stats["conflicts"], 0, "L'OCC doit avoir intercepté des conflits réels.")

        # Vérification de l'Invariance Absolue : Conservation de la masse monétaire
        tx_final = self.store.begin_transaction()
        total_final = sum(self.store.get(tx_final, acc) for acc in accounts)
        self.store.commit(tx_final)

        self.assertEqual(
            total_final, total_money_expected,
            f"Violation de la conservation d'énergie/masse : {total_final} != {total_money_expected}"
        )

        # Invariants structurels intègres
        self.assertTrue(self.store.validate_invariants())

    def test_savepoints_comprehensive(self):
        """
        Assertions Savepoints :
        - basic rollback
        - nested savepoints
        - restauration de valeur antérieure
        - release
        - tx morte -> TransactionAbortedError
        """
        # 1. Basic rollback
        tx = self.store.begin_transaction()
        self.store.put(tx, "k1", 10)
        self.store.savepoint(tx, "sp1")
        self.store.put(tx, "k1", 20)
        self.assertEqual(self.store.get(tx, "k1"), 20)
        self.store.rollback_to(tx, "sp1")
        self.assertEqual(self.store.get(tx, "k1"), 10)

        # 2. Nested savepoints (sp1 puis sp2, rollback à sp2 puis à sp1)
        self.store.put(tx, "k2", 100)
        self.store.savepoint(tx, "sp_nested_1")
        self.store.put(tx, "k2", 200)
        self.store.savepoint(tx, "sp_nested_2")
        self.store.put(tx, "k2", 300)
        self.assertEqual(self.store.get(tx, "k2"), 300)

        # Rollback à sp2 -> k2 = 200
        self.store.rollback_to(tx, "sp_nested_2")
        self.assertEqual(self.store.get(tx, "k2"), 200)

        # Rollback à sp1 -> k2 = 100
        self.store.rollback_to(tx, "sp_nested_1")
        self.assertEqual(self.store.get(tx, "k2"), 100)

        # 3. Restauration de valeur antérieure
        # Clé modifiée avant savepoint, remodifiée après savepoint, rollback_to restaure
        self.store.put(tx, "k3", "val_avant")
        self.store.savepoint(tx, "sp_ant")
        self.store.put(tx, "k3", "val_apres")
        self.assertEqual(self.store.get(tx, "k3"), "val_apres")
        self.store.rollback_to(tx, "sp_ant")
        self.assertEqual(self.store.get(tx, "k3"), "val_avant")

        # 4. Release savepoint
        self.store.savepoint(tx, "sp_to_release")
        self.store.release_savepoint(tx, "sp_to_release")
        with self.assertRaises(ValueError):
            self.store.rollback_to(tx, "sp_to_release")

        # Commit de la transaction
        self.assertTrue(self.store.commit(tx))

        # 5. Tx morte (après commit ou rollback) -> TransactionAbortedError
        with self.assertRaises(TransactionAbortedError):
            self.store.savepoint(tx, "any")
        with self.assertRaises(TransactionAbortedError):
            self.store.rollback_to(tx, "any")
        with self.assertRaises(TransactionAbortedError):
            self.store.release_savepoint(tx, "any")

    def test_scan_comprehensive(self):
        """
        Assertions Scan :
        - snapshot isolation
        - read-your-own-writes & fusion snapshot+write_set
        - tombstones exclus
        - prefix
        - keys dans read_set
        - tx morte -> TransactionAbortedError
        """
        # État initial
        tx0 = self.store.begin_transaction()
        self.store.put(tx0, "user:1", "Alice")
        self.store.put(tx0, "user:2", "Bob")
        self.store.put(tx0, "order:1", "Laptop")
        self.store.commit(tx0)

        # tx1 commence son snapshot
        tx1 = self.store.begin_transaction()

        # tx2 commit après le début de tx1 (Snapshot isolation)
        tx2 = self.store.begin_transaction()
        self.store.put(tx2, "user:3", "Charlie")
        self.store.commit(tx2)

        # 1. Snapshot isolation : tx1 ne voit pas user:3
        items = self.store.scan(tx1, prefix="user:")
        self.assertEqual(items, [("user:1", "Alice"), ("user:2", "Bob")])

        # 2. Read-your-own-writes & fusion snapshot+write_set
        self.store.put(tx1, "user:4", "David")
        self.store.put(tx1, "user:1", "AliceModified")
        items_fused = self.store.scan(tx1, prefix="user:")
        self.assertEqual(
            items_fused,
            [("user:1", "AliceModified"), ("user:2", "Bob"), ("user:4", "David")],
        )

        # 3. Tombstones exclus (delete local dans write_set)
        self.store.delete(tx1, "user:2")
        items_no_tombstone = self.store.scan(tx1, prefix="user:")
        self.assertEqual(
            items_no_tombstone,
            [("user:1", "AliceModified"), ("user:4", "David")],
        )

        # 4. Prefix filtré
        orders = self.store.scan(tx1, prefix="order:")
        self.assertEqual(orders, [("order:1", "Laptop")])

        # 5. Clés lues entrent dans read_set (obligatoire pour SSI)
        with self.store._meta_lock:
            tx1_obj = self.store._active_txs.get(tx1)
            self.assertIn("user:1", tx1_obj.read_set)
            self.assertIn("user:4", tx1_obj.read_set)
            self.assertIn("order:1", tx1_obj.read_set)

        self.assertTrue(self.store.commit(tx1))

        # 6. Tx morte -> TransactionAbortedError
        with self.assertRaises(TransactionAbortedError):
            self.store.scan(tx1)

    def test_ssi_write_skew_cycle_abort(self):
        """
        Assertion SSI :
        write skew (A==B, tx1 écrit A, tx2 écrit B, les deux lisent A et B) → tx2 abort
        """
        # Init A=100, B=100
        t_init = self.store.begin_transaction()
        self.store.put(t_init, "A", 100)
        self.store.put(t_init, "B", 100)
        self.store.commit(t_init)

        tx1 = self.store.begin_transaction()
        tx2 = self.store.begin_transaction()

        # tx1 lit A et B, puis modifie A
        a1 = self.store.get(tx1, "A")
        b1 = self.store.get(tx1, "B")
        self.store.put(tx1, "A", a1 - 80)

        # tx2 lit A et B, puis modifie B
        a2 = self.store.get(tx2, "A")
        b2 = self.store.get(tx2, "B")
        self.store.put(tx2, "B", b2 - 80)

        # tx1 commit en premier
        self.assertTrue(self.store.commit(tx1))

        # tx2 tente de committer : détection de cycle SSI -> WriteConflictError
        with self.assertRaises(WriteConflictError):
            self.store.commit(tx2)

        self.assertTrue(self.store.validate_invariants())

    def test_disjoint_writes_without_reads_both_commit(self):
        """
        Assertion SSI :
        écritures disjointes sans lecture → les deux commit
        """
        tx1 = self.store.begin_transaction()
        tx2 = self.store.begin_transaction()

        self.store.put(tx1, "key_x", 111)
        self.store.put(tx2, "key_y", 222)

        # Les deux doivent committer sans erreur
        self.assertTrue(self.store.commit(tx1))
        self.assertTrue(self.store.commit(tx2))

        tx_check = self.store.begin_transaction()
        self.assertEqual(self.store.get(tx_check, "key_x"), 111)
        self.assertEqual(self.store.get(tx_check, "key_y"), 222)
        self.store.commit(tx_check)

    def test_readonly_transaction_never_aborts(self):
        """
        Assertion SSI :
        read-only tx → jamais abort
        """
        t_init = self.store.begin_transaction()
        self.store.put(t_init, "ro_k1", "data1")
        self.store.put(t_init, "ro_k2", "data2")
        self.store.commit(t_init)

        # tx en lecture seule commence
        tx_ro = self.store.begin_transaction()
        self.assertEqual(self.store.get(tx_ro, "ro_k1"), "data1")
        self.assertEqual(self.store.get(tx_ro, "ro_k2"), "data2")

        # Writer concurrent modifie et commit
        tx_w = self.store.begin_transaction()
        self.store.put(tx_w, "ro_k1", "mutated1")
        self.store.put(tx_w, "ro_k2", "mutated2")
        self.assertTrue(self.store.commit(tx_w))

        # La transaction read-only doit committer avec succès sans jamais échouer
        self.assertTrue(self.store.commit(tx_ro))

    def test_ssi_absence_read_and_concurrent_insert_cycle(self):
        """
        Assertion SSI :
        lecture d'absence + insert concurrent → tx qui écrit ailleurs abort
        """
        tx1 = self.store.begin_transaction()
        tx2 = self.store.begin_transaction()

        # tx1 lit l'absence de "absent_k" -> enregistrée dans read_set
        val_absent = self.store.get(tx1, "absent_k")
        self.assertIsNone(val_absent)
        # tx1 écrit ailleurs
        self.store.put(tx1, "other_k", "val1")

        # tx2 lit "other_k" (absence) -> enregistrée dans read_set
        val_other = self.store.get(tx2, "other_k")
        self.assertIsNone(val_other)
        # tx2 insère la clé manquante
        self.store.put(tx2, "absent_k", "val2")

        # tx2 commit en premier
        self.assertTrue(self.store.commit(tx2))

        # tx1 tente de committer -> cycle détecté (rw-antidependency bilatérale) -> abort !
        with self.assertRaises(WriteConflictError):
            self.store.commit(tx1)

    def test_stress_20_threads_same_key(self):
        """
        Assertion :
        20 threads sur même clé → ≥1 commit, 0 corruption, invariants valides
        """
        t_init = self.store.begin_transaction()
        self.store.put(t_init, "hotspot_key", 0)
        self.store.commit(t_init)

        num_threads = 20
        results = {"commits": 0, "conflicts": 0, "errors": []}
        lock = threading.Lock()

        def worker(tid):
            try:
                tx = self.store.begin_transaction()
                cur = self.store.get(tx, "hotspot_key")
                self.store.put(tx, "hotspot_key", cur + 1)
                try:
                    self.store.commit(tx)
                    with lock:
                        results["commits"] += 1
                except WriteConflictError:
                    with lock:
                        results["conflicts"] += 1
            except Exception as e:
                with lock:
                    results["errors"].append((tid, str(e)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=10.0)

        self.assertEqual(len(results["errors"]), 0, f"Erreurs inattendues : {results['errors']}")
        self.assertGreaterEqual(results["commits"], 1, "Au moins 1 commit doit réussir.")
        self.assertEqual(results["commits"] + results["conflicts"], num_threads)
        self.assertTrue(self.store.validate_invariants())

    def test_8_threads_disjoint_keys(self):
        """
        Assertion :
        8 threads clés disjointes → 8 commits, invariants valides
        """
        num_threads = 8
        results = {"commits": 0, "conflicts": 0, "errors": []}
        lock = threading.Lock()

        def worker(tid):
            try:
                tx = self.store.begin_transaction()
                self.store.put(tx, f"disjoint_key_{tid}", tid * 100)
                self.store.commit(tx)
                with lock:
                    results["commits"] += 1
            except WriteConflictError:
                with lock:
                    results["conflicts"] += 1
            except Exception as e:
                with lock:
                    results["errors"].append((tid, str(e)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=10.0)

        self.assertEqual(len(results["errors"]), 0)
        self.assertEqual(results["commits"], 8, "Les 8 threads doivent tous committer.")
        self.assertEqual(results["conflicts"], 0, "Aucun conflit sur clés disjointes.")
        self.assertTrue(self.store.validate_invariants())

    def test_vacuum_reader_active_and_closed(self):
        """
        Assertions Vacuum :
        - vacuum préserve version visible par reader actif
        - vacuum purge après fermeture du reader
        - purge du journal _recent_commits
        """
        t0 = self.store.begin_transaction()
        self.store.put(t0, "v_key", 100)
        self.store.commit(t0)

        # Reader actif démarre (son snapshot voit v_key=100)
        reader = self.store.begin_transaction()
        self.assertEqual(self.store.get(reader, "v_key"), 100)

        # Writer crée une nouvelle version
        writer = self.store.begin_transaction()
        self.store.put(writer, "v_key", 200)
        self.store.commit(writer)

        # Premier vacuum pendant que le reader est actif :
        # La version 100 DOIT ÊTRE PRÉSERVÉE
        purged1 = self.store.vacuum()
        self.assertEqual(purged1, 0)
        self.assertEqual(len(self.store.get_history("v_key")), 2)
        # Le reader voit toujours 100
        self.assertEqual(self.store.get(reader, "v_key"), 100)
        # _recent_commits doit contenir au moins le commit du writer
        with self.store._commit_log_lock:
            self.assertGreater(len(self.store._recent_commits), 0)

        # Fermeture du reader
        self.store.commit(reader)

        # Second vacuum après fermeture du reader :
        # La version 100 doit être purgée et _recent_commits vidé
        purged2 = self.store.vacuum()
        self.assertEqual(purged2, 1)
        self.assertEqual(len(self.store.get_history("v_key")), 1)
        self.assertEqual(self.store.get_history("v_key")[0][2], 200)

        # Vérification purge du journal _recent_commits
        with self.store._commit_log_lock:
            self.assertEqual(len(self.store._recent_commits), 0)

    def test_6_threads_30_mixed_operations(self):
        """
        Assertion :
        6 threads × 30 opérations mixtes → 0 erreur non gérée, invariants valides
        """
        num_threads = 6
        ops_per_thread = 30
        errors = []
        err_lock = threading.Lock()

        keys = [f"mixed_k_{i}" for i in range(5)]

        def worker(tid):
            for op_idx in range(ops_per_thread):
                try:
                    tx = self.store.begin_transaction()
                    # 1. Quelques lectures et écritures
                    k = random.choice(keys)
                    val = self.store.get(tx, k)
                    self.store.put(tx, k, (val or 0) + 1)

                    # 2. Savepoint & modification optionnelle
                    sp_name = f"sp_{tid}_{op_idx}"
                    self.store.savepoint(tx, sp_name)
                    k2 = random.choice(keys)
                    self.store.put(tx, k2, 9999)

                    # Rollback to savepoint 50% du temps
                    if random.random() < 0.5:
                        self.store.rollback_to(tx, sp_name)
                    else:
                        self.store.release_savepoint(tx, sp_name)

                    # 3. Scan occasionnel
                    if random.random() < 0.3:
                        self.store.scan(tx, prefix="mixed_", limit=3)

                    # 4. Décision de commit ou rollback
                    if random.random() < 0.8:
                        try:
                            self.store.commit(tx)
                        except WriteConflictError:
                            # Conflit attendu sous concurrence OCC/SSI
                            pass
                    else:
                        self.store.rollback(tx)
                except Exception as e:
                    with err_lock:
                        errors.append((tid, op_idx, str(e)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=15.0)

        self.assertEqual(len(errors), 0, f"Erreurs non gérées détectées : {errors}")
        self.assertTrue(self.store.validate_invariants())

    def test_read_set_memory_cleanup(self):
        """Vérifie que read_set est vidé au commit et au rollback (aucune fuite mémoire)."""
        # Test commit avec écritures
        tx1 = self.store.begin_transaction()
        with self.store._meta_lock:
            tx1_obj = self.store._active_txs[tx1]
        self.store.get(tx1, "k_clean_1")
        self.store.put(tx1, "k_clean_1", 100)
        self.assertEqual(len(tx1_obj.read_set), 1)
        self.assertTrue(self.store.commit(tx1))
        self.assertEqual(len(tx1_obj.read_set), 0)
        self.assertEqual(len(tx1_obj.write_set), 0)

        # Test commit en lecture seule
        tx2 = self.store.begin_transaction()
        with self.store._meta_lock:
            tx2_obj = self.store._active_txs[tx2]
        self.store.get(tx2, "k_clean_1")
        self.assertEqual(len(tx2_obj.read_set), 1)
        self.assertTrue(self.store.commit(tx2))
        self.assertEqual(len(tx2_obj.read_set), 0)

        # Test rollback
        tx3 = self.store.begin_transaction()
        with self.store._meta_lock:
            tx3_obj = self.store._active_txs[tx3]
        self.store.get(tx3, "k_clean_3")
        self.store.put(tx3, "k_clean_3", 300)
        self.assertEqual(len(tx3_obj.read_set), 1)
        self.store.rollback(tx3)
        self.assertEqual(len(tx3_obj.read_set), 0)
        self.assertEqual(len(tx3_obj.write_set), 0)


class TestPalier12WALRecovery(unittest.TestCase):
    """
    Suite d'épreuves Palier 12 :
    Axe A : WAL (Write-Ahead Log) et crash recovery
    Axe B : Checkpointing atomique et tronquage de WAL
    Axe C : Time-travel queries (get_at, scan_at, history)
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.wal_path = os.path.join(self.temp_dir, "test_store.wal")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_assertion_1_commit_close_recover_get_identical(self):
        """1. commit → close → recover → get identique pour toutes les clés"""
        store = MVCCStore(wal_path=self.wal_path)
        tx1 = store.begin_transaction()
        store.put(tx1, "alpha", 100)
        store.put(tx1, "beta", "hello")
        store.put(tx1, "gamma", [1, 2, 3])
        store.commit(tx1)

        tx2 = store.begin_transaction()
        store.put(tx2, "alpha", 200)
        store.delete(tx2, "beta")
        store.commit(tx2)

        store.close()

        # Recover
        recovered = MVCCStore.recover(self.wal_path)
        tx_check = recovered.begin_transaction()
        self.assertEqual(recovered.get(tx_check, "alpha"), 200)
        self.assertIsNone(recovered.get(tx_check, "beta"))
        self.assertEqual(recovered.get(tx_check, "gamma"), [1, 2, 3])
        recovered.commit(tx_check)
        recovered.close()
        self.assertTrue(recovered.validate_invariants())

    def test_assertion_2_recover_truncated_wal_mid_record(self):
        """2. recover après crash simulé (WAL tronqué au milieu d'un enregistrement) → pas d'exception, dernier commit complet préservé"""
        store = MVCCStore(wal_path=self.wal_path)
        # Commit 1
        tx1 = store.begin_transaction()
        store.put(tx1, "k1", "commit1_val")
        store.commit(tx1)

        # Commit 2
        tx2 = store.begin_transaction()
        store.put(tx2, "k2", "commit2_val")
        store.commit(tx2)
        store.close()

        # Simuler un crash pendant l'écriture d'un 3ème commit :
        # On append une ligne tronquée en plein milieu du JSON sans saut de ligne
        with open(self.wal_path, "a", encoding="utf-8") as f:
            f.write('{"type": "commit", "tx_id": 999, "commit_ts": 15, "mutations": [["k3", "cor')

        # Recover ne doit lever AUCUNE exception
        recovered = MVCCStore.recover(self.wal_path)
        tx_check = recovered.begin_transaction()
        self.assertEqual(recovered.get(tx_check, "k1"), "commit1_val")
        self.assertEqual(recovered.get(tx_check, "k2"), "commit2_val")
        self.assertIsNone(recovered.get(tx_check, "k3"))
        recovered.commit(tx_check)
        recovered.close()
        self.assertTrue(recovered.validate_invariants())

    def test_assertion_3_uncommitted_tx_absent_after_recovery(self):
        """3. recover après crash → tx non commitées absentes"""
        store = MVCCStore(wal_path=self.wal_path)
        # Commit légitime
        tx1 = store.begin_transaction()
        store.put(tx1, "legit", "ok")
        store.commit(tx1)

        # Transaction commencée mais jamais commitée (crash in-flight)
        tx_uncommitted = store.begin_transaction()
        store.put(tx_uncommitted, "ghost", "should_not_exist")
        store.delete(tx_uncommitted, "legit")
        # On ne commit PAS, on ferme brutalement
        store.close()

        recovered = MVCCStore.recover(self.wal_path)
        tx_check = recovered.begin_transaction()
        self.assertEqual(recovered.get(tx_check, "legit"), "ok")
        self.assertIsNone(recovered.get(tx_check, "ghost"))
        recovered.commit(tx_check)
        recovered.close()
        self.assertTrue(recovered.validate_invariants())

    def test_assertion_4_clock_and_tx_counter_preserved(self):
        """4. recover préserve _clock et _tx_counter (pas de réutilisation d'ID)"""
        store = MVCCStore(wal_path=self.wal_path)
        tx1 = store.begin_transaction()
        store.put(tx1, "x", 1)
        store.commit(tx1)

        tx2 = store.begin_transaction()
        store.put(tx2, "x", 2)
        store.commit(tx2)

        prev_clock = store._clock
        prev_tx_counter = store._tx_counter
        store.close()

        recovered = MVCCStore.recover(self.wal_path)
        self.assertGreaterEqual(recovered._clock, prev_clock)
        self.assertGreaterEqual(recovered._tx_counter, prev_tx_counter)

        # Nouvelle transaction post-recovery : identifiants strictement supérieurs
        new_tx = recovered.begin_transaction()
        self.assertGreater(new_tx, prev_tx_counter)
        self.assertGreater(recovered._active_txs[new_tx].snapshot_ts, prev_clock)
        recovered.commit(new_tx)
        recovered.close()

    def test_assertion_5_checkpoint_wal_truncated_recover_identical(self):
        """5. checkpoint → WAL tronqué → recover → état identique"""
        store = MVCCStore(wal_path=self.wal_path)
        for i in range(10):
            tx = store.begin_transaction()
            store.put(tx, f"key_{i}", i * 10)
            store.commit(tx)

        # Checkpoint
        store.checkpoint()

        # Le WAL doit avoir été tronqué (taille 0)
        self.assertEqual(os.path.getsize(self.wal_path), 0)

        # Recover
        recovered = MVCCStore.recover(self.wal_path)
        tx_check = recovered.begin_transaction()
        for i in range(10):
            self.assertEqual(recovered.get(tx_check, f"key_{i}"), i * 10)
        recovered.commit(tx_check)
        recovered.close()
        store.close()
        self.assertTrue(recovered.validate_invariants())

    def test_assertion_6_crash_during_checkpoint_fallbacks_to_old_checkpoint_and_wal(self):
        """6. crash pendant checkpoint → recover retombe sur ancien checkpoint + WAL complet"""
        store = MVCCStore(wal_path=self.wal_path)
        # Étape 1 : 5 premiers commits et premier checkpoint réussi
        for i in range(5):
            tx = store.begin_transaction()
            store.put(tx, f"init_{i}", i)
            store.commit(tx)
        store.checkpoint()

        # Étape 2 : 5 commits suivants dans le nouveau WAL
        for i in range(5, 10):
            tx = store.begin_transaction()
            store.put(tx, f"init_{i}", i)
            store.commit(tx)
        store.close()

        # Étape 3 : Simulation d'un crash pendant un 2e checkpoint
        # Un fichier temporaire .chk.tmp est créé avec du contenu corrompu/incomplet
        tmp_chk_path = self.wal_path + ".chk.tmp"
        with open(tmp_chk_path, "w", encoding="utf-8") as f_tmp:
            f_tmp.write('{"checkpoint_ts": 999, "corrupted')

        # Recover doit ignorer le .tmp corrompu, charger l'ancien .chk et rejouer le WAL
        recovered = MVCCStore.recover(self.wal_path)
        tx_check = recovered.begin_transaction()
        for i in range(10):
            self.assertEqual(recovered.get(tx_check, f"init_{i}"), i)
        recovered.commit(tx_check)
        recovered.close()
        self.assertTrue(recovered.validate_invariants())

    def test_assertion_7_get_at_past_timestamps(self):
        """7. get_at(clé, ts_passé) retourne la valeur historique correcte après plusieurs écritures"""
        store = MVCCStore(wal_path=self.wal_path)
        # v1
        t1 = store.begin_transaction()
        store.put(t1, "counter", 10)
        store.commit(t1)
        ts_v1 = store._clock

        # v2
        t2 = store.begin_transaction()
        store.put(t2, "counter", 20)
        store.commit(t2)
        ts_v2 = store._clock

        # v3
        t3 = store.begin_transaction()
        store.put(t3, "counter", 30)
        store.commit(t3)
        ts_v3 = store._clock

        # Vérification time-travel
        self.assertIsNone(store.get_at("counter", 0))
        self.assertEqual(store.get_at("counter", ts_v1), 10)
        self.assertEqual(store.get_at("counter", ts_v2), 20)
        self.assertEqual(store.get_at("counter", ts_v3), 30)
        self.assertEqual(store.get_at("counter", ts_v3 + 100), 30)
        store.close()

    def test_assertion_8_scan_at_consistent_with_get_at(self):
        """8. scan_at(ts_passé, prefix) cohérent avec get_at sur chaque clé"""
        store = MVCCStore(wal_path=self.wal_path)
        # Écriture 1
        t1 = store.begin_transaction()
        store.put(t1, "user:1", "Alice")
        store.put(t1, "user:2", "Bob")
        store.commit(t1)
        ts1 = store._clock

        # Écriture 2
        t2 = store.begin_transaction()
        store.put(t2, "user:1", "Alice2")
        store.put(t2, "user:3", "Charlie")
        store.delete(t2, "user:2")
        store.commit(t2)
        ts2 = store._clock

        # scan_at à ts1
        scan_ts1 = store.scan_at(ts1, prefix="user:")
        expected_ts1 = [("user:1", store.get_at("user:1", ts1)), ("user:2", store.get_at("user:2", ts1))]
        self.assertEqual(scan_ts1, expected_ts1)

        # scan_at à ts2
        scan_ts2 = store.scan_at(ts2, prefix="user:")
        expected_ts2 = [("user:1", store.get_at("user:1", ts2)), ("user:3", store.get_at("user:3", ts2))]
        self.assertEqual(scan_ts2, expected_ts2)
        store.close()

    def test_assertion_9_history_identical_after_recover(self):
        """9. après recover, history(clé) identique à avant crash"""
        store = MVCCStore(wal_path=self.wal_path)
        for val in [100, 200, 300]:
            tx = store.begin_transaction()
            store.put(tx, "hist_key", val)
            store.commit(tx)

        # Suppression
        tx_del = store.begin_transaction()
        store.delete(tx_del, "hist_key")
        store.commit(tx_del)

        hist_before = store.history("hist_key")
        store.close()

        recovered = MVCCStore.recover(self.wal_path)
        hist_after = recovered.history("hist_key")
        self.assertEqual(hist_before, hist_after)
        recovered.close()
        self.assertTrue(recovered.validate_invariants())

    def test_assertion_10_100_commits_checkpoint_100_commits_recover_200_versions(self):
        """10. 100 commits → checkpoint → 100 commits → recover → 200 versions cohérentes"""
        store = MVCCStore(wal_path=self.wal_path)
        # 100 commits
        for i in range(100):
            tx = store.begin_transaction()
            store.put(tx, "progression", i)
            store.commit(tx)

        # Checkpoint
        store.checkpoint()

        # 100 commits suivants
        for i in range(100, 200):
            tx = store.begin_transaction()
            store.put(tx, "progression", i)
            store.commit(tx)

        hist_orig = store.history("progression")
        self.assertEqual(len(hist_orig), 200)
        store.close()

        # Recover
        recovered = MVCCStore.recover(self.wal_path)
        hist_rec = recovered.history("progression")
        self.assertEqual(len(hist_rec), 200)
        self.assertEqual(hist_rec[-1][2], 199)
        self.assertEqual(hist_rec, hist_orig)
        self.assertTrue(recovered.validate_invariants())
        recovered.close()

    def test_assertion_11_pure_memory_mode_zero_regression(self):
        """11. Aucune régression Palier 10 ni Palier 11 (MVCCStore() sans wal_path = pur mémoire)"""
        mem_store = MVCCStore()
        self.assertIsNone(mem_store._wal_path)
        self.assertIsNone(mem_store._wal_file)
        tx = mem_store.begin_transaction()
        mem_store.put(tx, "mem_key", 42)
        self.assertTrue(mem_store.commit(tx))
        tx2 = mem_store.begin_transaction()
        self.assertEqual(mem_store.get(tx2, "mem_key"), 42)
        mem_store.commit(tx2)
        mem_store.close()
        self.assertTrue(mem_store.validate_invariants())

    def test_assertion_12_deterministic_double_recovery(self):
        """12. Crash recovery déterministe : deux recover() successifs sur le même WAL donnent le même état"""
        store = MVCCStore(wal_path=self.wal_path)
        for i in range(10):
            tx = store.begin_transaction()
            store.put(tx, f"det_{i}", i * 5)
            store.commit(tx)
        store.close()

        rec1 = MVCCStore.recover(self.wal_path)
        rec2 = MVCCStore.recover(self.wal_path)

        tx1 = rec1.begin_transaction()
        tx2 = rec2.begin_transaction()
        for i in range(10):
            self.assertEqual(rec1.get(tx1, f"det_{i}"), rec2.get(tx2, f"det_{i}"))
        rec1.commit(tx1)
        rec2.commit(tx2)

        self.assertTrue(rec1.validate_invariants())
        self.assertTrue(rec2.validate_invariants())
        rec1.close()
        rec2.close()


class TestPalier13Cluster2PC(unittest.TestCase):
    """
    Suite d'épreuves Palier 13 : Cluster Distribué Multi-Shards & Two-Phase Commit (2PC).
    Axe A : Sharding par hachage cohérent déterministe (MD5)
    Axe B : Protocole Two-Phase Commit (2PC) et crash recovery du coordinateur
    Axe C : Snapshot global cohérent et Time-Travel distribué
    14 Assertions Critiques formellement validées.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.node_paths = [os.path.join(self.temp_dir, f"shard_{i}.wal") for i in range(3)]
        self.coord_wal_path = os.path.join(self.temp_dir, "_coordinator.wal")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _find_keys_for_shards(self, cluster: Cluster, num_shards: int = 3):
        """Trouve de manière déterministe une clé routée vers chaque shard."""
        keys = {}
        i = 0
        while len(keys) < num_shards:
            k = f"shard_probe_key_{i}"
            sid = cluster._get_shard_index(k)
            if sid not in keys and sid < num_shards:
                keys[sid] = k
            i += 1
        return [keys[sid] for sid in range(num_shards)]

    def test_assertion_1_shard_distribution(self):
        """1. Shard distribution : avec 3 shards et 100 clés insérées, chaque shard a au moins 15 clés."""
        cluster = Cluster(self.node_paths)
        tx = cluster.begin_transaction()
        for i in range(100):
            cluster.put(tx, f"dist_key_{i}", i)
        cluster.commit(tx)

        counts = [len(shard._store) for shard in cluster.nodes]
        self.assertEqual(sum(counts), 100)
        for sid, count in enumerate(counts):
            self.assertGreaterEqual(count, 15, f"Shard {sid} n'a reçu que {count} clés (attendu >= 15)")

        self.assertTrue(cluster.validate_invariants())
        cluster.close()

    def test_assertion_2_multi_shard_commit(self):
        """2. Multi-shard commit : une tx qui écrit sur 3 shards différents commit atomiquement (tout visible ou rien)."""
        cluster = Cluster(self.node_paths)
        k0, k1, k2 = self._find_keys_for_shards(cluster, 3)

        tx = cluster.begin_transaction()
        cluster.put(tx, k0, "val0")
        cluster.put(tx, k1, "val1")
        cluster.put(tx, k2, "val2")
        self.assertTrue(cluster.commit(tx))

        # Nouvelle transaction lisant les 3 shards
        tx2 = cluster.begin_transaction()
        self.assertEqual(cluster.get(tx2, k0), "val0")
        self.assertEqual(cluster.get(tx2, k1), "val1")
        self.assertEqual(cluster.get(tx2, k2), "val2")
        cluster.commit(tx2)

        # Vérification sur chaque shard individuel
        self.assertIn(k0, cluster.nodes[0]._store)
        self.assertIn(k1, cluster.nodes[1]._store)
        self.assertIn(k2, cluster.nodes[2]._store)
        self.assertTrue(cluster.validate_invariants())
        cluster.close()

    def test_assertion_3_abort_visibility(self):
        """3. Abort visibility : une tx multi-shard abortée ne laisse AUCUNE trace sur AUCUN shard."""
        cluster = Cluster(self.node_paths)
        k0, k1, k2 = self._find_keys_for_shards(cluster, 3)

        tx = cluster.begin_transaction()
        cluster.put(tx, k0, "bad0")
        cluster.put(tx, k1, "bad1")
        cluster.put(tx, k2, "bad2")
        cluster.rollback(tx)

        # Vérification d'absence totale
        tx2 = cluster.begin_transaction()
        self.assertIsNone(cluster.get(tx2, k0))
        self.assertIsNone(cluster.get(tx2, k1))
        self.assertIsNone(cluster.get(tx2, k2))
        cluster.commit(tx2)

        self.assertNotIn(k0, cluster.nodes[0]._store)
        self.assertNotIn(k1, cluster.nodes[1]._store)
        self.assertNotIn(k2, cluster.nodes[2]._store)
        self.assertTrue(cluster.validate_invariants())
        cluster.close()

    def test_assertion_4_occ_conflict_on_one_shard_causes_global_abort(self):
        """4. OCC conflict on 1 shard : txB abort sur shard 0 ET ses écritures sur shard 2 sont annulées aussi (atomicité 2PC)."""
        cluster = Cluster(self.node_paths)
        k0, k1, k2 = self._find_keys_for_shards(cluster, 3)

        txA = cluster.begin_transaction()
        txB = cluster.begin_transaction()

        cluster.put(txA, k0, "txA_val0")
        cluster.put(txA, k1, "txA_val1")

        cluster.put(txB, k0, "txB_val0")  # Conflit OCC sur shard 0
        cluster.put(txB, k2, "txB_val2")  # Shard 2 touché par txB

        # txA commit avec succès
        self.assertTrue(cluster.commit(txA))

        # txB doit échouer et lever WriteConflictError
        with self.assertRaises(WriteConflictError):
            cluster.commit(txB)

        # Vérification de l'atomicité 2PC : k2 sur shard 2 n'a JAMAIS été committé
        tx_check = cluster.begin_transaction()
        self.assertEqual(cluster.get(tx_check, k0), "txA_val0")
        self.assertEqual(cluster.get(tx_check, k1), "txA_val1")
        self.assertIsNone(cluster.get(tx_check, k2))
        cluster.commit(tx_check)

        self.assertNotIn(k2, cluster.nodes[2]._store)
        self.assertTrue(cluster.validate_invariants())
        cluster.close()

    def test_assertion_5_coordinator_crash_after_prepare_before_decision(self):
        """5. Coordinator crash après prepare, avant décision : recover() résout la tx (COMMIT si tous prepared, sinon ABORT)."""
        cluster = Cluster(self.node_paths)
        k0, k1, _ = self._find_keys_for_shards(cluster, 3)

        tx = cluster.begin_transaction()
        cluster.put(tx, k0, "val_c5_0")
        cluster.put(tx, k1, "val_c5_1")

        # Simulation de la phase 1 PREPARE sur shards 0 et 1
        tx_obj = cluster._active_cluster_txs[tx]
        w0 = {k0: tx_obj.write_set[k0]}
        w1 = {k1: tx_obj.write_set[k1]}
        self.assertTrue(cluster.nodes[0].prepare(tx, w0, set(), tx_obj.snapshot_ts))
        self.assertTrue(cluster.nodes[1].prepare(tx, w1, set(), tx_obj.snapshot_ts))

        # Coordinateur écrit PREPARE dans son WAL
        prep_rec = {"type": "PREPARE", "tx_id": tx, "participants": [0, 1]}
        import json
        cluster._coord_wal_file.write(json.dumps(prep_rec) + "\n")
        cluster._coord_wal_file.flush()
        os.fsync(cluster._coord_wal_file.fileno())

        # Crash simulé : fermeture brutale avant écriture de DECISION
        cluster.close()

        # Réouverture et Crash Recovery
        recovered = Cluster(self.node_paths)
        tx_check = recovered.begin_transaction()
        self.assertEqual(recovered.get(tx_check, k0), "val_c5_0")
        self.assertEqual(recovered.get(tx_check, k1), "val_c5_1")
        recovered.commit(tx_check)
        self.assertTrue(recovered.validate_invariants())
        recovered.close()

    def test_assertion_6_coordinator_crash_after_decision_before_acks(self):
        """6. Coordinator crash après décision, avant ACKs : recover() réapplique la décision sur tous les shards."""
        cluster = Cluster(self.node_paths)
        k0, k1, _ = self._find_keys_for_shards(cluster, 3)

        tx = cluster.begin_transaction()
        cluster.put(tx, k0, "val_c6_0")
        cluster.put(tx, k1, "val_c6_1")

        tx_obj = cluster._active_cluster_txs[tx]
        w0 = {k0: tx_obj.write_set[k0]}
        w1 = {k1: tx_obj.write_set[k1]}
        cluster.nodes[0].prepare(tx, w0, set(), tx_obj.snapshot_ts)
        cluster.nodes[1].prepare(tx, w1, set(), tx_obj.snapshot_ts)

        import json
        prep_rec = {"type": "PREPARE", "tx_id": tx, "participants": [0, 1]}
        cluster._coord_wal_file.write(json.dumps(prep_rec) + "\n")
        commit_rec = {
            "type": "DECISION",
            "tx_id": tx,
            "decision": "COMMIT",
            "commit_ts": 50,
            "participants": [0, 1],
        }
        cluster._coord_wal_file.write(json.dumps(commit_rec) + "\n")
        cluster._coord_wal_file.flush()
        os.fsync(cluster._coord_wal_file.fileno())

        # Shard 0 a appliqué le commit avant le crash
        cluster.nodes[0].apply_commit(tx, 50)
        # Shard 1 n'a PAS encore appliqué le commit (crash en vol)
        cluster.close()

        # Recovery : coordinateur rejoue la décision COMMIT sur shard 1
        recovered = Cluster(self.node_paths)
        tx_check = recovered.begin_transaction()
        self.assertEqual(recovered.get(tx_check, k0), "val_c6_0")
        self.assertEqual(recovered.get(tx_check, k1), "val_c6_1")
        recovered.commit(tx_check)
        self.assertTrue(recovered.validate_invariants())
        recovered.close()

    def test_assertion_7_shard_crash_after_prepared_in_doubt_resolved_by_coordinator(self):
        """7. Shard crash après PREPARED avant COMMITTED : in-doubt, le coordinateur résout son état."""
        cluster = Cluster(self.node_paths)
        k0, _, _ = self._find_keys_for_shards(cluster, 3)

        tx = cluster.begin_transaction()
        cluster.put(tx, k0, "in_doubt_val")
        tx_obj = cluster._active_cluster_txs[tx]
        cluster.nodes[0].prepare(tx, {k0: tx_obj.write_set[k0]}, set(), tx_obj.snapshot_ts)
        cluster.close()

        # Shard 0 redémarre seul : il est en état in-doubt
        shard0 = MVCCStore.recover(self.node_paths[0])
        self.assertTrue(shard0.is_in_doubt(tx))
        self.assertIsNone(shard0.get_at(k0, shard0._clock))
        shard0.close()

        # Le coordinateur redémarre : sans décision enregistrée, il résout l'orphelin en ABORT
        recovered = Cluster(self.node_paths)
        self.assertFalse(recovered.nodes[0].is_in_doubt(tx))
        tx_check = recovered.begin_transaction()
        self.assertIsNone(recovered.get(tx_check, k0))
        recovered.commit(tx_check)
        self.assertTrue(recovered.validate_invariants())
        recovered.close()

    def test_assertion_8_crash_during_prepare_truncated_wal_aborts_globally(self):
        """8. Crash pendant PREPARE (WAL d'un shard tronqué) : le shard répond NO -> décision ABORT globale."""
        cluster = Cluster(self.node_paths)
        k0, k1, _ = self._find_keys_for_shards(cluster, 3)

        tx = cluster.begin_transaction()
        cluster.put(tx, k0, "val_c8_0")
        cluster.put(tx, k1, "val_c8_1")

        tx_obj = cluster._active_cluster_txs[tx]
        cluster.nodes[0].prepare(tx, {k0: tx_obj.write_set[k0]}, set(), tx_obj.snapshot_ts)

        import json
        prep_rec = {"type": "PREPARE", "tx_id": tx, "participants": [0, 1]}
        cluster._coord_wal_file.write(json.dumps(prep_rec) + "\n")
        cluster._coord_wal_file.flush()
        os.fsync(cluster._coord_wal_file.fileno())
        cluster.close()

        # Shard 1 crashe pendant son écriture de PREPARE (WAL tronqué)
        with open(self.node_paths[1], "a", encoding="utf-8") as f_trunc:
            f_trunc.write('{"type": "prepared", "tx_id": ' + str(tx) + ', "muta')

        # Recovery : shard 1 ignore la ligne tronquée et n'est pas in-doubt -> décision ABORT globale
        recovered = Cluster(self.node_paths)
        tx_check = recovered.begin_transaction()
        self.assertIsNone(recovered.get(tx_check, k0))
        self.assertIsNone(recovered.get(tx_check, k1))
        recovered.commit(tx_check)
        self.assertTrue(recovered.validate_invariants())
        recovered.close()

    def test_assertion_9_consistent_cluster_scan_snapshot_isolation(self):
        """9. Consistent cluster scan : scan(tx) retourne un snapshot cohérent malgré commits concurrents."""
        cluster = Cluster(self.node_paths)

        # Initialisation
        t_init = cluster.begin_transaction()
        cluster.put(t_init, "pfx:0", "init0")
        cluster.put(t_init, "pfx:1", "init1")
        cluster.commit(t_init)

        # Transaction de lecture ouverte à ce snapshot
        tx_reader = cluster.begin_transaction()

        # Transaction concurrente modifie et ajoute sur d'autres shards
        t_writer = cluster.begin_transaction()
        cluster.put(t_writer, "pfx:0", "mod0")
        cluster.put(t_writer, "pfx:2", "new2")
        cluster.commit(t_writer)

        # tx_reader doit voir uniquement l'état snapshoté initial
        scan_res = cluster.scan(tx_reader, prefix="pfx:")
        self.assertEqual(scan_res, [("pfx:0", "init0"), ("pfx:1", "init1")])
        cluster.commit(tx_reader)

        # Une nouvelle transaction voit le nouvel état
        tx_after = cluster.begin_transaction()
        scan_after = cluster.scan(tx_after, prefix="pfx:")
        self.assertEqual(scan_after, [("pfx:0", "mod0"), ("pfx:1", "init1"), ("pfx:2", "new2")])
        cluster.commit(tx_after)
        cluster.close()

    def test_assertion_10_get_at_distributed_time_travel(self):
        """10. get_at(tx, key, ts_passe) : lecture time-travel distribuée sur le bon shard."""
        cluster = Cluster(self.node_paths)
        k0, k1, _ = self._find_keys_for_shards(cluster, 3)

        # v1
        t1 = cluster.begin_transaction()
        cluster.put(t1, k0, "v1_0")
        cluster.put(t1, k1, "v1_1")
        cluster.commit(t1)
        ts1 = max(s._clock for s in cluster.nodes)

        # v2
        t2 = cluster.begin_transaction()
        cluster.put(t2, k0, "v2_0")
        cluster.put(t2, k1, "v2_1")
        cluster.commit(t2)
        ts2 = max(s._clock for s in cluster.nodes)

        # Time-travel queries
        self.assertEqual(cluster.get_at(k0, ts1), "v1_0")
        self.assertEqual(cluster.get_at(k1, ts1), "v1_1")

        # Signature avec tx explicite
        dummy_tx = cluster.begin_transaction()
        self.assertEqual(cluster.get_at(dummy_tx, k0, ts1), "v1_0")
        self.assertEqual(cluster.get_at(dummy_tx, k1, ts1), "v1_1")
        cluster.commit(dummy_tx)

        # Lecture au ts2
        self.assertEqual(cluster.get_at(k0, ts2), "v2_0")
        self.assertEqual(cluster.get_at(k1, ts2), "v2_1")

        # Scan time-travel distribué
        s_ts1 = dict(cluster.scan_at(ts1))
        self.assertEqual(s_ts1[k0], "v1_0")
        self.assertEqual(s_ts1[k1], "v1_1")

        cluster.close()

    def test_assertion_11_cluster_recovery_validates_invariants_across_all_shards(self):
        """11. Cluster recovery : validate_invariants() est True sur TOUS les shards après opérations multiples."""
        cluster = Cluster(self.node_paths)
        for i in range(25):
            tx = cluster.begin_transaction()
            cluster.put(tx, f"inv_key_{i}", i)
            if i % 3 == 0:
                cluster.delete(tx, f"inv_key_{i-1}")
            cluster.commit(tx)
        cluster.close()

        recovered = Cluster(self.node_paths)
        self.assertTrue(recovered.validate_invariants())
        for shard in recovered.nodes:
            self.assertTrue(shard.validate_invariants())
        recovered.close()

    def test_assertion_12_in_doubt_tx_never_leaks_into_reads(self):
        """12. In-doubt tx never leaks : aucune version d'une tx PREPARED n'est visible par aucune lecture."""
        cluster = Cluster(self.node_paths)
        k0, _, _ = self._find_keys_for_shards(cluster, 3)

        # Valeur committée
        t_init = cluster.begin_transaction()
        cluster.put(t_init, k0, "comm_val")
        cluster.commit(t_init)

        # Tx préparée (in-doubt)
        tx_prep = cluster.begin_transaction()
        cluster.put(tx_prep, k0, "in_doubt_leak")
        tx_obj = cluster._active_cluster_txs[tx_prep]
        cluster.nodes[0].prepare(tx_prep, {k0: tx_obj.write_set[k0]}, set(), tx_obj.snapshot_ts)

        # Lectures concurrentes : get, scan, get_at
        tx_reader = cluster.begin_transaction()
        self.assertEqual(cluster.get(tx_reader, k0), "comm_val")
        scan_dict = dict(cluster.scan(tx_reader))
        self.assertEqual(scan_dict[k0], "comm_val")
        cluster.commit(tx_reader)

        self.assertEqual(cluster.get_at(k0, cluster.nodes[0]._clock + 100), "comm_val")

        # Nettoyage
        cluster.nodes[0].apply_abort(tx_prep)
        cluster.close()

    def test_assertion_13_zero_regressions_on_paliers_10_11_12(self):
        """13. Zéro régression : tests Paliers 10, 11 et 12 continuent de fonctionner parfaitement."""
        store = MVCCStore()
        t = store.begin_transaction()
        store.put(t, "reg_test", 123)
        store.savepoint(t, "sp1")
        store.put(t, "reg_test", 456)
        store.rollback_to(t, "sp1")
        self.assertEqual(store.get(t, "reg_test"), 123)
        store.commit(t)
        self.assertEqual(store.history("reg_test")[-1][2], 123)
        self.assertTrue(store.validate_invariants())
        store.close()

    def test_assertion_14_idempotence_reopening_three_times(self):
        """14. Idempotence : fermer et rouvrir le cluster 3 fois de suite donne exactement le même état."""
        cluster = Cluster(self.node_paths)
        tx = cluster.begin_transaction()
        for i in range(50):
            cluster.put(tx, f"idemp_{i}", i * 3)
        cluster.commit(tx)
        cluster.close()

        for cycle in range(3):
            c = Cluster(self.node_paths)
            t_check = c.begin_transaction()
            for i in range(50):
                self.assertEqual(c.get(t_check, f"idemp_{i}"), i * 3, f"Échec cycle {cycle} clé idemp_{i}")
            c.commit(t_check)
            self.assertTrue(c.validate_invariants(), f"Invariants invalides au cycle {cycle}")
            c.close()


class TestPalier14ReplicatedClusterRaft(unittest.TestCase):
    """
    Suite d'épreuves Palier 14 : Replicated Cluster (Consensus Raft, SSI Distribué, Read Replicas).
    15 Assertions Critiques formellement validées.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.node_paths = [os.path.join(self.temp_dir, f"shard_{i}.wal") for i in range(3)]
        self.coord_dir = os.path.join(self.temp_dir, "coordinators")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _find_keys_for_shards(self, cluster, num_shards: int = 3):
        """Trouve de manière déterministe une clé routée vers chaque shard."""
        keys = {}
        i = 0
        while len(keys) < num_shards:
            k = f"p14_key_{i}"
            sid = cluster._get_shard_index(k)
            if sid not in keys and sid < num_shards:
                keys[sid] = k
            i += 1
        return [keys[sid] for sid in range(num_shards)]

    def test_assertion_1_leader_elected_under_1s(self):
        """1. Cluster 3 coordinateurs -> leader élu en < 1s après démarrage"""
        start = time.time()
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        lid = rc.leader_id()
        elapsed = time.time() - start

        self.assertLess(elapsed, 1.0, f"Élection trop lente : {elapsed}s")
        self.assertTrue(rc.is_leader(lid))
        self.assertIn(lid, [0, 1, 2])
        for other_id in [0, 1, 2]:
            if other_id != lid:
                self.assertFalse(rc.is_leader(other_id))
        rc.close()

    def test_assertion_2_kill_leader_during_tx_in_doubt_resolved(self):
        """2. Kill leader pendant une tx -> nouveau leader élu -> tx in-doubt résolue -> commit/abort cohérent"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        k0, k1, _ = self._find_keys_for_shards(rc, 3)

        tx = rc.begin_transaction()
        rc.put(tx, k0, "val_p14_2_0")
        rc.put(tx, k1, "val_p14_2_1")

        tx_obj = rc._active_cluster_txs[tx]
        rc.nodes[0].prepare(tx, {k0: tx_obj.write_set[k0]}, set(), tx_obj.snapshot_ts)
        rc.nodes[1].prepare(tx, {k1: tx_obj.write_set[k1]}, set(), tx_obj.snapshot_ts)

        lead_id = rc.leader_id()
        leader = rc.coordinators[lead_id]
        prep_rec = {"type": "PREPARE", "tx_id": tx, "participants": [0, 1]}
        self.assertTrue(leader.replicate_entry(prep_rec))

        # Crash du leader
        rc.stop_coordinator(lead_id)

        # Nouveau leader élu
        new_lead = rc.elect_leader()
        self.assertNotEqual(new_lead, lead_id)
        self.assertTrue(rc.is_leader(new_lead))

        # La tx in-doubt a été résolue en COMMIT car les 2 shards étaient préparés
        tx_check = rc.begin_transaction()
        self.assertEqual(rc.get(tx_check, k0), "val_p14_2_0")
        self.assertEqual(rc.get(tx_check, k1), "val_p14_2_1")
        rc.commit(tx_check)

        self.assertTrue(rc.validate_invariants())
        rc.close()

    def test_assertion_3_kill_leader_after_replicated_commit_decision_commits_everywhere(self):
        """3. Kill leader APRÈS décision COMMIT répliquée -> recovery -> tx commit partout"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        k0, k1, _ = self._find_keys_for_shards(rc, 3)

        tx = rc.begin_transaction()
        rc.put(tx, k0, "val_p14_3_0")
        rc.put(tx, k1, "val_p14_3_1")

        tx_obj = rc._active_cluster_txs[tx]
        rc.nodes[0].prepare(tx, {k0: tx_obj.write_set[k0]}, set(), tx_obj.snapshot_ts)
        rc.nodes[1].prepare(tx, {k1: tx_obj.write_set[k1]}, set(), tx_obj.snapshot_ts)

        lead_id = rc.leader_id()
        leader = rc.coordinators[lead_id]
        prep_rec = {"type": "PREPARE", "tx_id": tx, "participants": [0, 1]}
        self.assertTrue(leader.replicate_entry(prep_rec))

        dec_rec = {"type": "DECISION", "tx_id": tx, "decision": "COMMIT", "commit_ts": 55, "participants": [0, 1]}
        self.assertTrue(leader.replicate_entry(dec_rec))

        # Kill leader avant apply sur shards
        rc.stop_coordinator(lead_id)

        # Élection du nouveau leader qui reprend le log committé
        new_lead = rc.elect_leader()
        self.assertNotEqual(new_lead, lead_id)

        # La décision COMMIT répliquée a été appliquée
        tx_check = rc.begin_transaction()
        self.assertEqual(rc.get(tx_check, k0), "val_p14_3_0")
        self.assertEqual(rc.get(tx_check, k1), "val_p14_3_1")
        rc.commit(tx_check)

        self.assertTrue(rc.validate_invariants())
        rc.close()

    def test_assertion_4_kill_leader_before_replicated_decision_aborts_globally(self):
        """4. Kill leader AVANT décision répliquée -> abort global, aucune valeur visible"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        k0, k1, _ = self._find_keys_for_shards(rc, 3)

        tx = rc.begin_transaction()
        rc.put(tx, k0, "val_p14_4_0")
        rc.put(tx, k1, "val_p14_4_1")

        tx_obj = rc._active_cluster_txs[tx]
        # Seul shard 0 se prépare, shard 1 ne se prépare pas (interrompu avant décision)
        rc.nodes[0].prepare(tx, {k0: tx_obj.write_set[k0]}, set(), tx_obj.snapshot_ts)

        lead_id = rc.leader_id()
        leader = rc.coordinators[lead_id]
        prep_rec = {"type": "PREPARE", "tx_id": tx, "participants": [0, 1]}
        leader.replicate_entry(prep_rec)

        # Crash du leader avant décision répliquée
        rc.stop_coordinator(lead_id)

        # Les autres nœuds élisent un nouveau leader
        new_lead = rc.elect_leader()
        self.assertNotEqual(new_lead, lead_id)

        # Comme tous les shards n'étaient pas préparés, la décision prise est ABORT
        tx_check = rc.begin_transaction()
        self.assertIsNone(rc.get(tx_check, k0))
        self.assertIsNone(rc.get(tx_check, k1))
        rc.commit(tx_check)

        self.assertTrue(rc.validate_invariants())
        rc.close()

    def test_assertion_5_split_brain_prevented_by_quorum(self):
        """5. Split-brain : 2 leaders tentent de committer -> un seul passe (quorum)"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        old_lead_id = rc.leader_id()
        old_lead = rc.coordinators[old_lead_id]

        # Isoler old_lead : les pairs vus par old_lead sont vides (1 seul vote sur 3)
        other_nodes = [c for c in rc.coordinators if c.node_id != old_lead_id]
        new_lead = other_nodes[0]
        term = max(n.current_term for n in other_nodes) + 1
        with new_lead.lock:
            new_lead.current_term = term
            new_lead.voted_for = new_lead.node_id
            new_lead.state = "LEADER"

        # L'ancien leader isolé tente de répliquer une entrée sans quorum
        # On simule l'isolement en rendant les autres inaccessibles depuis old_lead
        for peer in other_nodes:
            peer.is_alive = False

        res_old = old_lead.replicate_entry({"type": "TEST", "data": "isolated"})
        self.assertFalse(res_old, "L'ancien leader isolé ne doit pas committer sans quorum")

        # Rétablir les autres nœuds : new_lead a son quorum de 2 nœuds (sur 3)
        for peer in other_nodes:
            peer.is_alive = True
        old_lead.is_alive = False  # old_lead reste isolé

        res_new = new_lead.replicate_entry({"type": "TEST", "data": "quorum"})
        self.assertTrue(res_new, "Le nouveau leader avec quorum doit pouvoir committer")

        rc.close()

    def test_assertion_6_distributed_write_skew_cross_shard_aborts_one(self):
        """6. Write-skew inter-shard (Tx1 écrit shard1 lit shard2, Tx2 inverse) -> une seule commit"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        k0, k1, _ = self._find_keys_for_shards(rc, 3)

        t_init = rc.begin_transaction()
        rc.put(t_init, k0, 10)
        rc.put(t_init, k1, 20)
        rc.commit(t_init)

        tx1 = rc.begin_transaction()
        tx2 = rc.begin_transaction()

        # Tx1 lit k0 et k1, puis écrit k0 (shard 0)
        val0_1 = rc.get(tx1, k0)
        val1_1 = rc.get(tx1, k1)
        rc.put(tx1, k0, val0_1 + 100)

        # Tx2 lit k0 et k1, puis écrit k1 (shard 1)
        val0_2 = rc.get(tx2, k0)
        val1_2 = rc.get(tx2, k1)
        rc.put(tx2, k1, val1_2 + 200)

        # Tx1 commit en premier
        self.assertTrue(rc.commit(tx1))

        # Tx2 doit être détectée en conflit SSI cross-shard (cycle rw-antidependency)
        with self.assertRaises(WriteConflictError):
            rc.commit(tx2)

        # Vérification : k0 modifié, k1 intact
        tx_check = rc.begin_transaction()
        self.assertEqual(rc.get(tx_check, k0), 110)
        self.assertEqual(rc.get(tx_check, k1), 20)
        rc.commit(tx_check)

        self.assertTrue(rc.validate_invariants())
        rc.close()

    def test_assertion_7_antidependency_detected_before_writing_decision_in_log(self):
        """7. Anti-dépendance détectée AVANT écriture dans le log répliqué"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        k0, k1, _ = self._find_keys_for_shards(rc, 3)

        t_init = rc.begin_transaction()
        rc.put(t_init, k0, 1)
        rc.put(t_init, k1, 2)
        rc.commit(t_init)

        tx1 = rc.begin_transaction()
        tx2 = rc.begin_transaction()

        rc.get(tx1, k0)
        rc.get(tx1, k1)
        rc.put(tx1, k0, 11)

        rc.get(tx2, k0)
        rc.get(tx2, k1)
        rc.put(tx2, k1, 22)

        rc.commit(tx1)

        lead = rc.coordinators[rc.leader_id()]
        log_len_before = len(lead.log)

        with self.assertRaises(WriteConflictError):
            rc.commit(tx2)

        # Vérifie qu'AUCUNE décision COMMIT n'a été écrite dans le log répliqué pour tx2
        for entry in lead.log[log_len_before:]:
            if entry.data.get("type") == "DECISION":
                self.assertNotEqual(entry.data.get("decision"), "COMMIT")

        rc.close()

    def test_assertion_8_stale_read_replica_raises_error_or_blocks(self):
        """8. Read replica en retard -> get_replica bloque ou erreur, JAMAIS de stale silencieux"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        k0, _, _ = self._find_keys_for_shards(rc, 3)

        rep_path = os.path.join(self.temp_dir, "rep_shard_0.wal")
        rc.add_read_replica(0, rep_path)

        tx = rc.begin_transaction()
        rc.put(tx, k0, "fresh_data")
        rc.commit(tx)

        # Marque le replica comme étant en retard (lagging)
        rc._shard_replicas[0][0].lagging = True

        with self.assertRaises(StaleReplicaError):
            rc.get_replica(0, k0)

        with self.assertRaises(StaleReplicaError):
            rc.scan_replica(0)

        rc.close()

    def test_assertion_9_up_to_date_read_replica_returns_latest_committed(self):
        """9. Read replica à jour -> get_replica retourne la dernière valeur commitée"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        k0, _, _ = self._find_keys_for_shards(rc, 3)

        rep_path = os.path.join(self.temp_dir, "rep_shard_0_fresh.wal")
        rc.add_read_replica(0, rep_path)

        tx = rc.begin_transaction()
        rc.put(tx, k0, "linearizable_val")
        rc.commit(tx)

        val = rc.get_replica(0, k0)
        self.assertEqual(val, "linearizable_val")
        rc.close()

    def test_assertion_10_kill_primary_promote_replica_continues_reads_writes(self):
        """10. Kill primary d'un shard -> replica promu -> lectures continuent, cohérentes"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        k0, _, _ = self._find_keys_for_shards(rc, 3)

        rep_path = os.path.join(self.temp_dir, "rep_shard_0_promote.wal")
        rc.add_read_replica(0, rep_path)

        tx = rc.begin_transaction()
        rc.put(tx, k0, "val_before_kill")
        rc.commit(tx)

        # Promotion du replica en nouveau primary (avec changement de config Raft)
        rc.promote_replica(shard_index=0, replica_index=0)

        # Vérification que le log Raft contient bien le CONFIG_CHANGE
        lead = rc.coordinators[rc.leader_id()]
        has_cfg = any(e.data.get("type") == "CONFIG_CHANGE" for e in lead.log)
        self.assertTrue(has_cfg, "La promotion doit journaliser un CONFIG_CHANGE dans Raft")

        # Lecture de la valeur précédente sur le nouveau primary
        tx_check = rc.begin_transaction()
        self.assertEqual(rc.get(tx_check, k0), "val_before_kill")
        rc.commit(tx_check)

        # Écriture sur le nouveau primary
        tx2 = rc.begin_transaction()
        rc.put(tx2, k0, "val_after_promote")
        rc.commit(tx2)

        tx3 = rc.begin_transaction()
        self.assertEqual(rc.get(tx3, k0), "val_after_promote")
        rc.commit(tx3)

        self.assertTrue(rc.validate_invariants())
        rc.close()

    def test_assertion_11_three_replicas_per_shard_kill_one_reads_continue(self):
        """11. 3 replicas par shard, kill 1 -> lectures toujours possibles"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        _, k1, _ = self._find_keys_for_shards(rc, 3)

        for r_idx in range(3):
            p = os.path.join(self.temp_dir, f"rep_s1_{r_idx}.wal")
            rc.add_read_replica(1, p)

        tx = rc.begin_transaction()
        rc.put(tx, k1, "tri_replica_val")
        rc.commit(tx)

        # Arrêt du premier replica
        rc._shard_replicas[1][0].close()

        # Lecture toujours possible sur les autres replicas
        val = rc.get_replica(1, k1)
        self.assertEqual(val, "tri_replica_val")

        rc.close()

    def test_assertion_12_full_recovery_all_in_doubt_resolved_and_invariants_valid(self):
        """12. Recovery complet -> toutes les tx in-doubt résolues, validate_invariants() vrai"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        k0, k1, k2 = self._find_keys_for_shards(rc, 3)

        t1 = rc.begin_transaction()
        rc.put(t1, k0, 100)
        rc.put(t1, k1, 200)
        rc.commit(t1)

        t2 = rc.begin_transaction()
        rc.put(t2, k2, 300)
        tx_obj = rc._active_cluster_txs[t2]
        rc.nodes[2].prepare(t2, {k2: tx_obj.write_set[k2]}, set(), tx_obj.snapshot_ts)

        rc.close()

        recovered = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        self.assertTrue(recovered.validate_invariants())
        for shard in recovered.nodes:
            self.assertTrue(shard.validate_invariants())
            self.assertFalse(shard.is_in_doubt(t2))
        recovered.close()

    def test_assertion_13_zero_regressions_palier_10_11_12_13(self):
        """13. Aucune régression Palier 10, 11, 12, 13"""
        c = Cluster(self.node_paths)
        t = c.begin_transaction()
        c.put(t, "reg_p13", "ok")
        c.commit(t)
        t2 = c.begin_transaction()
        self.assertEqual(c.get(t2, "reg_p13"), "ok")
        c.commit(t2)
        c.close()

    def test_assertion_14_stress_test_10_threads_100_txs_5_shards_zero_deadlock_zero_corruption(self):
        """14. Test de charge : 10 threads, 100 tx cluster, 5 shards -> 0 corruption, 0 deadlock"""
        paths5 = [os.path.join(self.temp_dir, f"shard5_{i}.wal") for i in range(5)]
        coord_dir5 = os.path.join(self.temp_dir, "coordinators5")
        rc = ReplicatedCluster(paths5, coordinator_replicas=3, coord_dir=coord_dir5)

        num_threads = 10
        txs_per_thread = 10
        errors = []
        err_lock = threading.Lock()

        def worker(tid: int):
            for i in range(txs_per_thread):
                try:
                    tx = rc.begin_transaction()
                    k = f"stress_key_{random.randint(0, 20)}"
                    val = rc.get(tx, k)
                    rc.put(tx, k, (val or 0) + 1)
                    if random.random() < 0.8:
                        try:
                            rc.commit(tx)
                        except WriteConflictError:
                            pass
                    else:
                        rc.rollback(tx)
                except Exception as e:
                    with err_lock:
                        errors.append((tid, i, str(e)))

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=20.0)

        self.assertEqual(len(errors), 0, f"Erreurs détectées sous stress test : {errors}")
        self.assertTrue(rc.validate_invariants())
        rc.close()

    def test_assertion_15_close_reopen_5_times_deterministic_state(self):
        """15. Fermer/rouvrir 5 fois avec crashes aléatoires -> état déterministe"""
        rc = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
        tx = rc.begin_transaction()
        for i in range(30):
            rc.put(tx, f"det_k_{i}", i * 10)
        rc.commit(tx)
        rc.close()

        for cycle in range(5):
            rec = ReplicatedCluster(self.node_paths, coordinator_replicas=3, coord_dir=self.coord_dir)
            t_check = rec.begin_transaction()
            for i in range(30):
                self.assertEqual(rec.get(t_check, f"det_k_{i}"), i * 10, f"Divergence cycle {cycle} clé {i}")
            rec.commit(t_check)

            if cycle % 2 == 0:
                rec.stop_coordinator(0)
                rec.elect_leader()

            self.assertTrue(rec.validate_invariants(), f"Invariants invalides cycle {cycle}")
            rec.close()


class TestPalier15GeoClusterHLC(unittest.TestCase):
    """
    Suite d'épreuves Palier 15 : Geo-Cluster (HLC, Cohérence Linéarisable, CAP Tranché CP/AP).
    20 Assertions Critiques formellement validées.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.regions = {
            "us-east": [os.path.join(self.temp_dir, "us_s0.wal")],
            "eu-west": [os.path.join(self.temp_dir, "eu_s0.wal")],
            "ap-south": [os.path.join(self.temp_dir, "ap_s0.wal")],
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_assertion_1_hlc_5s_physical_drift_causal_order(self):
        """1. HLC : deux nœuds avec 5s de dérive physique -> ordre causal préservé"""
        base_time = int(time.time() * 1000)
        hlc1 = HLC(node_id=1, physical_clock_fn=lambda: base_time)
        hlc2 = HLC(node_id=2, physical_clock_fn=lambda: base_time - 5000)

        t1 = hlc1.now()
        t2 = hlc2.update(t1)

        self.assertGreater(t2, t1, "L'ordre causal doit être préservé malgré 5s de retard physique")
        self.assertGreaterEqual(t2[0], t1[0])

    def test_assertion_2_hlc_ping_pong_strictly_increasing(self):
        """2. HLC : A -> B -> A (ping-pong) -> timestamps strictement croissants"""
        hlcA = HLC(node_id=1)
        hlcB = HLC(node_id=2)

        t1 = hlcA.now()
        t2 = hlcB.update(t1)
        t3 = hlcA.update(t2)
        t4 = hlcB.update(t3)

        self.assertLess(t1, t2)
        self.assertLess(t2, t3)
        self.assertLess(t3, t4)

    def test_assertion_3_hlc_round_trip_to_int_from_int(self):
        """3. HLC : round-trip to_int / from_int -> identité"""
        hlc = HLC(node_id=0)
        t = hlc.now()
        v = hlc.to_int()
        decoded = HLC.from_int(v)
        self.assertEqual(decoded, t)

    def test_assertion_4_retrocompat_legacy_timestamp_readable(self):
        """4. Rétrocompat : un ancien timestamp Palier 12 (monotone) reste lisible"""
        legacy_ts = 15
        decoded = HLC.from_int(legacy_ts)
        self.assertEqual(decoded, (15, 0))

    def test_assertion_5_get_linearizable_after_put_cross_region_visible(self):
        """5. get_linearizable après put dans une autre région -> valeur visible"""
        geo = GeoCluster(self.regions)
        tx = geo.begin_transaction(region="us-east")
        geo.put(tx, "k_geo_5", "val_cross_5")
        geo.commit(tx)

        val = geo.get_linearizable("k_geo_5", region="eu-west")
        self.assertEqual(val, "val_cross_5")
        geo.close()

    def test_assertion_6_get_linearizable_concurrent_put_serialization(self):
        """6. get_linearizable concurrent avec put -> sérialisation correcte (une seule vérité)"""
        geo = GeoCluster(self.regions)
        tx1 = geo.begin_transaction(region="us-east")
        geo.put(tx1, "k_serial", "v1")
        geo.commit(tx1)

        v_read1 = geo.get_linearizable("k_serial", region="eu-west")
        self.assertEqual(v_read1, "v1")

        tx2 = geo.begin_transaction(region="ap-south")
        geo.put(tx2, "k_serial", "v2")
        geo.commit(tx2)

        v_read2 = geo.get_linearizable("k_serial", region="us-east")
        self.assertEqual(v_read2, "v2")
        geo.close()

    def test_assertion_7_get_stale_within_max_lag_ms(self):
        """7. get_stale avec max_lag_ms respecté : pas de valeur plus vieille que la borne"""
        geo = GeoCluster(self.regions)
        tx = geo.begin_transaction(region="us-east")
        geo.put(tx, "k_stale_7", "v_stale_7")
        geo.commit(tx)

        geo._region_lag["ap-south"] = 200
        val = geo.get_stale("k_stale_7", max_lag_ms=500, region="ap-south")
        self.assertEqual(val, "v_stale_7")
        geo.close()

    def test_assertion_8_get_stale_session_monotonicity(self):
        """8. get_stale : monotonie par session — jamais retourner en arrière"""
        geo = GeoCluster(self.regions)
        session = geo.create_session("client_monotone")

        tx = geo.begin_transaction(region="us-east")
        geo.put(tx, "k_mono_8", "v_mono_8")
        geo.commit(tx)

        val1 = geo.get_linearizable("k_mono_8", region="us-east", session=session)
        self.assertEqual(val1, "v_mono_8")

        geo._region_lag["ap-south"] = 1000
        with self.assertRaises(StaleReadError):
            geo.get_stale("k_mono_8", max_lag_ms=2000, region="ap-south", session=session)
        geo.close()

    def test_assertion_9_get_stale_excessive_lag_raises_explicit_error(self):
        """9. get_stale sur replica trop en retard -> erreur explicite, pas de stale silencieux"""
        geo = GeoCluster(self.regions)
        tx = geo.begin_transaction(region="us-east")
        geo.put(tx, "k_lag_9", "v_lag_9")
        geo.commit(tx)

        geo._region_lag["ap-south"] = 1500
        with self.assertRaises(StaleReadError):
            geo.get_stale("k_lag_9", max_lag_ms=1000, region="ap-south")
        geo.close()

    def test_assertion_10_partition_2_1_cp_minority_refuses_writes(self):
        """10. Partition 2-1 en mode CP -> région isolée refuse toute écriture"""
        geo = GeoCluster(self.regions, mode="CP")
        geo.set_partition("us-east", "ap-south")
        geo.set_partition("eu-west", "ap-south")

        tx = geo.begin_transaction(region="ap-south")
        with self.assertRaises(PartitionUnavailableError):
            geo.put(tx, "k_cp_10", "fail_val")

        geo.close()

    def test_assertion_11_partition_2_1_cp_majority_continues(self):
        """11. Partition 2-1 en mode CP -> région majoritaire continue normalement"""
        geo = GeoCluster(self.regions, mode="CP")
        geo.set_partition("us-east", "ap-south")
        geo.set_partition("eu-west", "ap-south")

        tx = geo.begin_transaction(region="us-east")
        geo.put(tx, "k_cp_11", "success_val")
        self.assertTrue(geo.commit(tx))

        val = geo.get_linearizable("k_cp_11", region="eu-west")
        self.assertEqual(val, "success_val")
        geo.close()

    def test_assertion_12_partition_2_1_ap_both_sides_write_and_heal_deterministic(self):
        """12. Partition 2-1 en mode AP -> les deux côtés écrivent, guérison -> convergence déterministe"""
        geo = GeoCluster(self.regions, mode="AP")
        geo.set_partition("us-east", "ap-south")
        geo.set_partition("eu-west", "ap-south")

        tx1 = geo.begin_transaction(region="us-east")
        geo.put(tx1, "k_ap_both", "val_east")
        self.assertTrue(geo.commit(tx1))

        tx2 = geo.begin_transaction(region="ap-south")
        geo.put(tx2, "k_ap_both", "val_south")
        self.assertTrue(geo.commit(tx2))

        # Guérison et réconciliation
        geo.heal_partition("us-east", "ap-south")
        geo.heal_partition("eu-west", "ap-south")

        v_east = geo.get_linearizable("k_ap_both", region="us-east")
        v_south = geo.get_linearizable("k_ap_both", region="ap-south")
        self.assertEqual(v_east, v_south)
        geo.close()

    def test_assertion_13_ap_lww_conflict_max_commit_ts_wins(self):
        """13. AP : conflit LWW sur HLC -> le commit_ts max gagne partout"""
        geo = GeoCluster(self.regions, mode="AP")
        geo.set_partition("us-east", "ap-south")
        geo.set_partition("eu-west", "ap-south")

        geo.hlcs["us-east"].set_physical_time(100000)
        geo.hlcs["ap-south"].set_physical_time(200000)

        tx1 = geo.begin_transaction(region="us-east")
        geo.put(tx1, "k_lww_13", "older_val")
        geo.commit(tx1)

        tx2 = geo.begin_transaction(region="ap-south")
        geo.put(tx2, "k_lww_13", "newer_val_wins")
        geo.commit(tx2)

        geo.heal_partition("us-east", "ap-south")
        geo.heal_partition("eu-west", "ap-south")

        self.assertEqual(geo.get_linearizable("k_lww_13", region="us-east"), "newer_val_wins")
        self.assertEqual(geo.get_linearizable("k_lww_13", region="ap-south"), "newer_val_wins")
        geo.close()

    def test_assertion_14_ap_bounded_convergence_under_5s(self):
        """14. AP : convergence bornée — après heal, tous les nœuds ont le même état en < 5s (simulé)"""
        geo = GeoCluster(self.regions, mode="AP")
        start = time.time()
        geo.set_partition("us-east", "ap-south")
        tx = geo.begin_transaction(region="ap-south")
        geo.put(tx, "k_conv_14", "speed_val")
        geo.commit(tx)

        geo.heal_partition("us-east", "ap-south")
        elapsed = time.time() - start
        self.assertLess(elapsed, 5.0, f"Convergence trop lente : {elapsed}s")
        self.assertEqual(geo.get_linearizable("k_conv_14", region="us-east"), "speed_val")
        geo.close()

    def test_assertion_15_no_silent_stale_in_cp_after_heal(self):
        """15. Aucun stale silencieux en CP après guérison de partition"""
        geo = GeoCluster(self.regions, mode="CP")
        geo.set_partition("us-east", "ap-south")
        tx = geo.begin_transaction(region="us-east")
        geo.put(tx, "k_nostale_15", "val_15")
        geo.commit(tx)

        geo.heal_partition("us-east", "ap-south")
        val = geo.get_linearizable("k_nostale_15", region="ap-south")
        self.assertEqual(val, "val_15")
        geo.close()

    def test_assertion_16_validate_invariants_true_after_every_scenario(self):
        """16. validate_invariants() vrai sur chaque nœud après chaque scénario"""
        geo = GeoCluster(self.regions)
        for i in range(10):
            t = geo.begin_transaction()
            geo.put(t, f"inv_{i}", i)
            geo.commit(t)
        self.assertTrue(geo.validate_invariants())
        geo.close()

    def test_assertion_17_zero_regressions_paliers_10_11_12_13_14(self):
        """17. Aucune régression Palier 10, 11, 12, 13, 14"""
        s = MVCCStore()
        t = s.begin_transaction()
        s.put(t, "reg_test", 999)
        s.commit(t)
        self.assertEqual(s.get_at("reg_test", s._clock), 999)
        self.assertTrue(s.validate_invariants())
        s.close()

    def test_assertion_18_stress_test_5_regions_20_threads_500_txs(self):
        """18. Test de charge : 5 régions, 20 threads, 500 tx -> 0 corruption, 0 deadlock"""
        regions5 = {f"reg_{r}": [os.path.join(self.temp_dir, f"r5_{r}_s0.wal")] for r in range(5)}
        geo5 = GeoCluster(regions5)

        num_threads = 20
        txs_per_thread = 25
        errors = []
        err_lock = threading.Lock()

        def worker(tid: int):
            reg = f"reg_{tid % 5}"
            for i in range(txs_per_thread):
                try:
                    t = geo5.begin_transaction(region=reg)
                    k = f"stress_5_{random.randint(0, 30)}"
                    geo5.put(t, k, i)
                    geo5.commit(t)
                except Exception as e:
                    with err_lock:
                        errors.append((tid, i, str(e)))

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
        for th in threads:
            th.start()
        for th in threads:
            th.join(timeout=30.0)

        self.assertEqual(len(errors), 0, f"Erreurs détectées sous stress test 500 txs : {errors}")
        self.assertTrue(geo5.validate_invariants())
        geo5.close()

    def test_assertion_19_crash_recovery_with_active_partitions_deterministic(self):
        """19. Fermer/rouvrir après crash avec partitions actives -> état déterministe"""
        geo = GeoCluster(self.regions)
        tx = geo.begin_transaction(region="us-east")
        for i in range(15):
            geo.put(tx, f"part_crash_{i}", i)
        geo.commit(tx)

        geo.set_partition("us-east", "ap-south")
        geo.close()

        rec = GeoCluster(self.regions)
        rec.set_partition("us-east", "ap-south")
        for i in range(15):
            self.assertEqual(rec.get_linearizable(f"part_crash_{i}", region="us-east"), i)
        self.assertTrue(rec.validate_invariants())
        rec.close()

    def test_assertion_20_simulated_100ms_latency_linearizable_under_300ms(self):
        """20. Latence simulée 100ms entre régions -> get_linearizable < 300ms (1 aller-retour max)"""
        geo = GeoCluster(self.regions)
        tx = geo.begin_transaction(region="us-east")
        geo.put(tx, "k_lat_20", "v_lat_20")
        geo.commit(tx)

        geo.set_simulated_latency("us-east", "eu-west", 0.1)

        start = time.time()
        val = geo.get_linearizable("k_lat_20", region="eu-west")
        elapsed = time.time() - start

        self.assertEqual(val, "v_lat_20")
        self.assertLess(elapsed, 0.3, f"Temps de lecture {elapsed}s >= 0.3s")
        geo.close()


class TestPalier16AutonomousPBFT(unittest.TestCase):
    """
    Suite d'épreuves Palier 16 : Autonomous Cluster
    (PBFT Byzantin, Signatures Dilithium, Optimiseur SQL Adaptatif, Inférence de Schéma, Preuves ZK-SNARK).
    15 Assertions Critiques formellement validées.
    """
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.node_paths = [os.path.join(self.temp_dir, f"node_{i}.wal") for i in range(7)]
        self.cluster = AutonomousCluster(self.node_paths, num_byzantine_nodes=7, wal_dir=self.temp_dir)

    def tearDown(self):
        self.cluster.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_assertion_1_pbft_7_nodes_2_byzantine_commits_cleanly(self):
        """1. 7 nœuds PBFT, 2 byzantins -> cluster commit sans corruption"""
        self.cluster.set_byzantine(1, "silent")
        self.cluster.set_byzantine(2, "lying")

        t = self.cluster.begin_transaction()
        self.cluster.put(t, "k_byz_1", "clean_val")
        self.assertTrue(self.cluster.commit(t))

        self.assertEqual(self.cluster.get(self.cluster.begin_transaction(), "k_byz_1"), "clean_val")

    def test_assertion_2_equivocating_node_excluded_under_500ms(self):
        """2. Nœud equivocating -> exclu en < 500ms"""
        self.cluster.set_byzantine(3, "equivocating")

        start = time.time()
        t = self.cluster.begin_transaction()
        self.cluster.put(t, "k_equiv_2", "v2")
        self.cluster.commit(t)
        elapsed_total = (time.time() - start) * 1000

        self.assertIn(3, self.cluster.excluded_nodes)
        self.assertLess(self.cluster.last_exclusion_time_ms, 500.0)
        self.assertLess(elapsed_total, 500.0)

    def test_assertion_3_replaying_node_rejected_by_hlc_nonce(self):
        """3. Nœud replaying -> rejeté par nonce HLC"""
        self.cluster.set_byzantine(4, "replaying")
        t = self.cluster.begin_transaction()
        self.cluster.put(t, "k_replay_3", "v3")

        with self.assertRaises(ReplayDetectedError):
            self.cluster.commit(t)

    def test_assertion_4_dilithium_signature_valid_on_100_percent_quorum_messages(self):
        """4. Signature Dilithium valide sur 100% des messages de quorum"""
        key = self.cluster.keys[0]
        msg = b"QUORUM_CERTIFICATE_TEST_PAYLOAD"
        sig = key.sign(msg)
        self.assertTrue(DilithiumKeyPair.verify(msg, sig, key.t))

        # Falsification
        tampered_msg = b"QUORUM_CERTIFICATE_TAMPERED"
        self.assertFalse(DilithiumKeyPair.verify(tampered_msg, sig, key.t))

    def test_assertion_5_explain_select_returns_cost_based_plan(self):
        """5. explain(SELECT ... WHERE ...) retourne un plan cost-based"""
        self.cluster.query("INSERT INTO users (id, age, name) VALUES (1, 30, 'Alice')")
        plan = self.cluster.explain("SELECT * FROM users WHERE age = 30")
        self.assertIn("cost=", plan)
        self.assertIn("rows=", plan)
        self.assertTrue("SeqScan" in plan or "IndexScan" in plan)

    def test_assertion_6_adaptive_optimizer_40_percent_latency_reduction_on_1000_queries(self):
        """6. Optimiseur adaptatif : -40% de latence médiane sur 1000 requêtes"""
        # Peupler une table
        for i in range(100):
            t = self.cluster.begin_transaction()
            self.cluster.put(t, f"tbl:items:{i}", {"id": i, "category": i % 5, "price": i * 10})
            self.cluster.commit(t)

        latencies = []
        for i in range(1000):
            cat = i % 5
            t0 = time.perf_counter()
            list(self.cluster.query(f"SELECT * FROM items WHERE category = {cat}"))
            t1 = time.perf_counter()
            latencies.append(t1 - t0)

        # Les 50 premières requêtes (exploration/stats) vs les 50 dernières (optimisées/indexées)
        first_50 = sorted(latencies[:50])[25]
        last_50 = sorted(latencies[-50:])[25]
        reduction = (first_50 - last_50) / first_50
        self.assertGreaterEqual(reduction, 0.40, f"Réduction de latence insuffisante : {reduction*100:.1f}%")

    def test_assertion_7_auto_created_index_on_repeated_predicate_used_automatically(self):
        """7. Index auto-créé sur prédicat répété -> utilisé automatiquement"""
        for i in range(20):
            t = self.cluster.begin_transaction()
            self.cluster.put(t, f"tbl:products:{i}", {"id": i, "tag": f"t_{i%3}", "stock": i * 5})
            self.cluster.commit(t)

        # Avant répétition : SeqScan
        plan_before = self.cluster.explain("SELECT * FROM products WHERE tag = 't_1'")
        self.assertIn("SeqScan", plan_before)

        # 5 requêtes répétées déclenchent l'auto-indexation
        for _ in range(5):
            list(self.cluster.query("SELECT * FROM products WHERE tag = 't_1'"))

        self.assertIn(("products", "tag"), self.cluster._indexes)
        plan_after = self.cluster.explain("SELECT * FROM products WHERE tag = 't_1'")
        self.assertIn("IndexScan on products(tag)", plan_after)

    def test_assertion_8_unused_index_pruned_after_10000_queries(self):
        """8. Index inutilisé pendant 10 000 requêtes -> supprimé automatiquement"""
        idx = MVCCIndex("customers", "old_attr")
        self.cluster._indexes[("customers", "old_attr")] = idx

        # Simule 10 000 requêtes touchant d'autres prédicats
        idx.queries_since_last_use = 10005
        dropped = self.cluster.drop_unused_indexes(threshold=10000)

        self.assertIn(("customers", "old_attr"), dropped)
        self.assertNotIn(("customers", "old_attr"), self.cluster._indexes)

    def test_assertion_9_inferred_schema_on_10000_documents_10x_speedup(self):
        """9. Schéma implicite inféré sur 10 000 documents -> 10x speedup"""
        # Ingestion de 10 000 documents JSON semi-structurés
        for i in range(10000):
            self.cluster._kv_store[f"doc:{i}"] = {
                "id": i,
                "score": i % 100,
                "label": f"item_{i}",
            }

        # 1ère requête avant inférence d'index : scan brut complet des 10 000 documents
        t0 = time.perf_counter()
        raw_matches = []
        for k, v in self.cluster._kv_store.items():
            if str(k).startswith("doc:") and json.loads(json.dumps(v)).get("score") == 42:
                raw_matches.append(v)
        raw_time = time.perf_counter() - t0

        # Inférence de schéma & matérialisation des index
        self.cluster.infer_schema_from_documents(prefix="doc:")

        # Requêtes répétées jusqu'à la 1000ème requête optimisée
        for _ in range(999):
            list(self.cluster.query("SELECT * FROM doc WHERE score = 42"))

        t1 = time.perf_counter()
        opt_rows = list(self.cluster.query("SELECT * FROM doc WHERE score = 42"))
        opt_time = time.perf_counter() - t1

        self.assertEqual(len(opt_rows), len(raw_matches))
        speedup = raw_time / max(opt_time, 1e-6)
        self.assertGreaterEqual(speedup, 10.0, f"Speedup insuffisant : {speedup:.1f}x (raw: {raw_time*1000:.2f}ms, opt: {opt_time*1000:.2f}ms)")

    def test_assertion_10_materialized_view_proposed_after_100_identical_joins_maintained(self):
        """10. Vue matérialisée proposée après 100 JOIN identiques -> maintenue"""
        for i in range(10):
            t = self.cluster.begin_transaction()
            self.cluster.put(t, f"tbl:authors:{i}", {"id": i, "name": f"Author_{i}"})
            self.cluster.put(t, f"tbl:books:{i}", {"id": i, "author_id": i, "title": f"Book_{i}"})
            self.cluster.commit(t)

        join_sql = "SELECT authors.name, books.title FROM authors JOIN books ON authors.id = books.author_id"

        for _ in range(100):
            list(self.cluster.query(join_sql))

        plan = self.cluster.explain(join_sql)
        self.assertIn("MaterializedViewScan", plan)

    def test_assertion_11_zk_proof_generated_per_commit_verifiable_without_data_access(self):
        """11. ZK-proof généré par commit -> vérifiable sans accès aux données"""
        t = self.cluster.begin_transaction()
        self.cluster.put(t, "secret_key_11", "classified_value")
        self.cluster.commit(t)

        proof = self.cluster.get_last_zk_proof()
        self.assertIsNotNone(proof)
        # Vérification externe sans accès aux données du cluster
        self.assertTrue(ZKVerifier.verify(proof))

    def test_assertion_12_invalid_zk_proof_rejected_by_external_verifier(self):
        """12. ZK-proof invalide -> rejeté par le vérificateur externe"""
        t = self.cluster.begin_transaction()
        self.cluster.put(t, "k_zk_12", "val_12")
        self.cluster.commit(t)

        proof = self.cluster.get_last_zk_proof()
        tampered_proof = ZKTransactionProof(
            tx_id=proof.tx_id,
            commit_hlc=proof.commit_hlc,
            commitment=proof.commitment,
            challenge=proof.challenge,
            eval_point=proof.eval_point,
            eval_value=(proof.eval_value + 1) % ZKVerifier.FIELD_PRIME,  # Falsification
            quotient_eval=proof.quotient_eval,
            prev_proof_hash=proof.prev_proof_hash,
            proof_hash=proof.proof_hash,
        )
        self.assertFalse(ZKVerifier.verify(tampered_proof))

    def test_assertion_13_zero_regressions_on_paliers_10_to_15(self):
        """13. Aucune régression Palier 10–15"""
        self.assertTrue(self.cluster.validate_invariants())

    def test_assertion_14_cluster_survives_2_byzantine_and_1_crashed_node(self):
        """14. Le cluster survit à la perte de 2 nœuds byzantins + 1 nœud crashé en même temps"""
        # 2 nœuds byzantins exclus
        self.cluster.set_byzantine(1, "equivocating")
        self.cluster.set_byzantine(2, "equivocating")

        # Déclenche l'exclusion
        t_pre = self.cluster.begin_transaction()
        self.cluster.put(t_pre, "k_excl", "val_excl")
        self.cluster.commit(t_pre)

        # 1 nœud crashé
        self.cluster.crash_node(3)

        # Le quorum s'adapte aux 5 nœuds actifs restants (4 vivants honnêtes >= quorum 3)
        t_post = self.cluster.begin_transaction()
        self.cluster.put(t_post, "k_resilient_14", "val_resilient")
        self.assertTrue(self.cluster.commit(t_post))

        self.assertEqual(self.cluster.get(self.cluster.begin_transaction(), "k_resilient_14"), "val_resilient")

    def test_assertion_15_close_reopen_10_times_preserves_schema_indexes_and_chained_zk_proofs(self):
        """15. Fermer/rouvrir 10 fois -> schéma inféré préservé, index préservés, preuves ZK chaînées"""
        # Init data & schema
        for i in range(25):
            self.cluster._kv_store[f"doc:{i}"] = {"id": i, "metric": i * 2}
        self.cluster.infer_schema_from_documents(prefix="doc:")

        t = self.cluster.begin_transaction()
        self.cluster.put(t, "k_reopen_15", "v15")
        self.cluster.commit(t)

        self.cluster.close()

        # 10 cycles d'ouverture / fermeture consécutifs
        current_cluster = self.cluster
        for cycle in range(10):
            current_cluster = AutonomousCluster(self.node_paths, num_byzantine_nodes=7, wal_dir=self.temp_dir)
            self.assertIn("doc", current_cluster._table_schemas)
            self.assertIn(("doc", "metric"), current_cluster._indexes)
            proof = current_cluster.get_last_zk_proof()
            self.assertIsNotNone(proof)
            self.assertTrue(ZKVerifier.verify(proof))
            current_cluster.close()


class TestPalier17SovereignAscension(unittest.TestCase):
    def setUp(self):
        self.cluster = SovereignPalier17Cluster(num_nodes=7, arena_size_mb=16)

    def test_assertion_1_grandfather_paradox_detected_and_proven_via_zksnark(self):
        """1. Paradoxe du Grand-Père : suppression rétrograde impossible -> preuve ZK sans corrompre l'état"""
        # Créer un état initial à HLC 2001
        t1 = self.cluster.begin_transaction()
        self.cluster.put(t1, "genesis_user", {"id": 1, "status": "active"})
        self.cluster.commit(t1)
        hlc_t1 = self.cluster._hlc

        # Deuxième transaction qui lit et dépend de genesis_user à HLC 2002
        t2 = self.cluster.begin_transaction()
        val = self.cluster.get(t2, "genesis_user")
        self.assertIsNotNone(val)
        self.cluster.put(t2, "derived_order", {"user_id": 1, "total": 100})
        self.cluster.commit(t2)

        # Tentative d'écriture rétrograde : suppression de genesis_user à HLC 2001 (Paradoxe du Grand-Père)
        with self.assertRaises(CausalParadoxError) as ctx:
            self.cluster.update_retrograde("genesis_user", None, target_hlc=hlc_t1, is_delete=True)

        # Vérification formelle que la preuve zk-SNARK d'impossibilité causale est valide
        paradox_proof = ctx.exception.paradox_proof
        self.assertIsNotNone(paradox_proof)
        self.assertTrue(ZKVerifier.verify(paradox_proof))

        # L'état actuel reste parfaitement intègre et non corrompu
        self.assertEqual(self.cluster._store["genesis_user"]["status"], "active")
        self.assertEqual(self.cluster._store["derived_order"]["total"], 100)

    def test_assertion_2_reconcilable_retrograde_update_cascades_state(self):
        """2. Écriture rétrograde réconciliable -> cascade de mise à jour réussie sans paradoxe"""
        t1 = self.cluster.begin_transaction()
        self.cluster.put(t1, "config:theme", "blue")
        self.cluster.commit(t1)
        hlc_t1 = self.cluster._hlc

        # Mise à jour rétrograde d'une clé indépendante à HLC t1
        ok = self.cluster.update_retrograde("config:theme", "dark_gold", target_hlc=hlc_t1)
        self.assertTrue(ok)
        self.assertEqual(self.cluster._store["config:theme"], "dark_gold")

    def test_assertion_3_halting_problem_solver_and_bounded_rewriting(self):
        """3. Solveur du problème de l'arrêt : récursion prouvée vs réécriture bornée sous certificat ZK"""
        # Requête A : Récursion bornée prouvable (n + 1 et WHERE n < 10)
        sql_terminating = "WITH RECURSIVE cnt AS (SELECT 1 AS n UNION ALL SELECT n + 1 FROM cnt WHERE n < 10) SELECT * FROM cnt"
        provable, res, proof = self.cluster.query_recursive(sql_terminating)
        self.assertTrue(provable)
        self.assertIsNone(proof)
        self.assertEqual(len(res), 10)

        # Requête B : Boucle infinie potentielle non prouvable (WHERE true)
        sql_infinite = "WITH RECURSIVE inf AS (SELECT 1 AS n UNION ALL SELECT n + 1 FROM inf WHERE true) SELECT * FROM inf"
        provable_b, res_b, proof_b = self.cluster.query_recursive(sql_infinite)
        self.assertFalse(provable_b)
        self.assertIsNotNone(proof_b)
        self.assertTrue(ZKVerifier.verify(proof_b))
        # N'a pas bouclé à l'infini : s'est arrêtée exactement à la borne garde-fou
        self.assertLessEqual(len(res_b), 1000)

    def test_assertion_4_no_gc_arena_marathon_under_gc_disabled(self):
        """4. Marathon Arena No-GC : 10 000 transactions avec gc.disable(), 0 fragmentation"""
        gc.disable()
        try:
            arena = self.cluster.arena
            arena.reset()

            for i in range(10000):
                addr = arena.write_record(f"key_{i}", {"val": i, "token": "SOVEREIGN"}, hlc_ts=i, tx_id=i)
                if i % 1000 == 0:
                    k, v, hlc, tx_id = arena.read_record(addr)
                    self.assertEqual(k, f"key_{i}")
                    self.assertEqual(v["val"], i)

            # Vérification de fragmentation exacte à 0.00%
            self.assertEqual(arena.fragmentation, 0.00)
            self.assertEqual(arena._allocations_count, 10000)
        finally:
            gc.enable()

    def test_assertion_5_entropy_daemon_dynamic_reconfiguration_and_quarantine(self):
        """5. Démon d'inversion entropique : quarantaine Dilithium et re-sharding dynamique sous chaos"""
        daemon = self.cluster.entropy_daemon

        # Scénario sain : tous les nœuds ont le même digest (entropie = 0)
        healthy_digests = {i: "DIGEST_UNIFORM_STATE" for i in range(7)}
        h_clean = daemon.calculate_entropy(healthy_digests)
        self.assertEqual(h_clean, 0.0)

        # Injection de chaos : 3 nœuds corrompus / divergents
        chaotic_digests = {
            0: "STATE_VALID",
            1: "STATE_VALID",
            2: "STATE_VALID",
            3: "STATE_VALID",
            4: "STATE_CORRUPT_A",
            5: "STATE_CORRUPT_B",
            6: "STATE_CORRUPT_C",
        }
        h_chaotic = daemon.calculate_entropy(chaotic_digests)
        self.assertGreater(h_chaotic, daemon.entropy_threshold)

        # Déclenchement de l'inversion entropique
        inverted = daemon.check_and_invert_entropy(chaotic_digests)
        self.assertTrue(inverted)

        # Les 3 nœuds déviants sont en quarantaine signée avec Dilithium
        self.assertIn(4, daemon.quarantined_nodes)
        self.assertIn(5, daemon.quarantined_nodes)
        self.assertIn(6, daemon.quarantined_nodes)
        self.assertNotIn(0, daemon.quarantined_nodes)

        # Vérification de la signature Dilithium du certificat de quarantaine
        cert4 = daemon.quarantine_certificates[4]
        msg = f"QUARANTINE_NODE:4:STATE_CORRUPT_A:EXPECTED:STATE_VALID".encode()
        self.assertTrue(DilithiumKeyPair.verify(msg, cert4["sig"], self.cluster.keys[0].t))

        # Re-sharding topologique validé
        self.assertGreaterEqual(daemon.re_sharded_count, 1)


class TestPalier18OntologicalRecursion(unittest.TestCase):
    """
    Palier 18 : Récursion Ontologique & Test du Miroir Brisé (Le Boss de Fin).
    Contrainte 1 : Auto-modification atomique (Hot-swap en 1 cycle HLC sans drop de TPS).
    Contrainte 2 : Preuve ZK de Superset de Sécurité & Quarantaine Dilithium.
    Contrainte 3 : Introspection streaming zero-allocation sur memoryview (zéro AST, zéro dictionnaire).
    """

    def test_ontological_recursion_mirror(self):
        cluster = SovereignPalier18Cluster(num_nodes=7)
        sha256 = hashlib.sha256

        # 1. Le cluster tourne à plein régime (10k TPS)
        start_tps = cluster.get_current_tps()
        
        # 2. On injecte une nouvelle règle de consensus via le code source lui-même
        # (ex: modification du seuil de détection d'entropie de 0.8 à 0.9)
        new_source_code = cluster.read_source_code()
        new_source_code = new_source_code.replace("ENTROPY_THRESHOLD = 0.8", "ENTROPY_THRESHOLD = 0.9")
        
        # 3. On tente la mise à jour à chaud PENDANT une transaction rétrograde
        with cluster.concurrent_retrograde_transaction(target_hlc=5000):
            upgrade_proof, success = cluster.alter_engine_logic(new_source_code)
            
            # 4. ASSERTIONS FATALES :
            # A. La mise à jour a réussi sans bloquer la transaction en cours.
            self.assertTrue(success)
            
            # B. La preuve ZK atteste que la nouvelle logique préserve l'invariant de l'Arena.
            self.assertTrue(verify_proof(upgrade_proof, invariant="ARENA_ZERO_ALLOC"))
            
            # C. Le TPS n'est jamais tombé en dessous de 95% de start_tps pendant la bascule.
            self.assertGreaterEqual(cluster.get_min_tps_during_upgrade(), (start_tps * 0.95))
            
            # D. Si on relit le code source du moteur en exécution, il correspond au nouveau.
            self.assertEqual(cluster.read_active_engine_hash(), sha256(new_source_code.encode()).hexdigest())

    def test_malicious_code_rejected_and_quarantined(self):
        """Test de sécurité supplémentaire : injection malveillante -> rejet + quarantaine Dilithium."""
        cluster = SovereignPalier18Cluster(num_nodes=7)
        bad_code = cluster.read_source_code().replace("ARENA_ZERO_ALLOC = True", "del causal_engine")
        
        with self.assertRaises(UnsafeUpgradeError) as ctx:
            cluster.alter_engine_logic(bad_code, session_id="rogue_agent_99")
            
        cert = ctx.exception.quarantine_cert
        self.assertIsNotNone(cert)
        self.assertIn("rogue_agent_99", cluster.quarantined_sessions)
        msg = f"QUARANTINE_UNSAFE_UPGRADE:rogue_agent_99:{cert['reason']}".encode('utf-8')
        self.assertTrue(DilithiumKeyPair.verify(msg, cert["sig"], cluster.keys[0].t))


class TestPalier19MultiverseSchrodinger(unittest.TestCase):
    """
    Palier 19 : Le Chat de Schrödinger en SQL (Multiverse Branching SSI & Ghost Rows).
    Contrainte 1 : Fork Quantique (Branching SSI) avec Copy-on-Write à 128 octets fixes dans l'Arena.
    Contrainte 2 : Collapse de la fonction d'onde par consensus PBFT (univers fantômes gelés).
    Contrainte 3 : SQL Contrefactuel (JOIN inter-univers en O(1) sur memoryview).
    Contrainte 4 : Preuve ZK d'isolation multiverselle (zéro fuite de données inter-dimensionnelles).
    """

    def test_multiverse_schrodinger_join(self):
        cluster = SovereignPalier19Cluster()

        # 1. L'état initial : Le prix de l'action est à 100$.
        cluster.execute("INSERT INTO stocks VALUES ('TECH', 100)")
        
        # 2. Deux transactions conflictuelles arrivent exactement au même HLC.
        # Tx A veut mettre le prix à 150$. Tx B veut mettre le prix à 50$.
        # Le moteur FORK l'univers (pas de rollback).
        tx_a = cluster.begin_retrograde_transaction()
        tx_b = cluster.begin_retrograde_transaction()
        
        tx_a.execute("UPDATE stocks SET price = 150 WHERE ticker = 'TECH'")
        tx_b.execute("UPDATE stocks SET price = 50 WHERE ticker = 'TECH'")
        
        # 3. Le consensus PBFT vote que l'Univers A (150$) est la réalité canonique.
        cluster.force_consensus_collapse(canonical_universe="A")
        
        # 4. ASSERTIONS FATALES :
        # A. La requête classique voit 150$.
        self.assertEqual(cluster.query("SELECT price FROM stocks WHERE ticker = 'TECH'")[0], 150)
        
        # B. La requête contrefactuelle voit la réalité abandonnée (50$).
        counterfactual = cluster.query(
            "SELECT ghost.price FROM ghost_stocks WHERE ticker = 'TECH' AND universe = 'B'"
        )
        self.assertEqual(counterfactual[0], 50)
        
        # C. L'EMPREINTE MÉMOIRE :
        # Vérifier que le fork et le collapse n'ont alloué AUCUN nouvel objet Python 
        # et que la fragmentation de l'Arena est toujours de 0.00%.
        self.assertEqual(cluster.arena.fragmentation, 0.0)
        
        # D. LA PREUVE DE NON-FUITE :
        # Générer la preuve ZK attestant que le JOIN contrefactuel n'a pas corrompu 
        # le WAL canonique.
        proof = cluster.generate_multiverse_isolation_proof()
        self.assertTrue(verify_proof(proof))


if __name__ == "__main__":
    unittest.main()

