# 🛡️ GABARIT : GRILLE D'AUDIT DE CONTRAT & DEVIS

*Ce gabarit résume les points de vérification automatique appliqués par la commande `!AUDIT`.*

---

## 1. Ce qui doit être audité en priorité

| Zone à Risque | Ce qu'on cherche | Ce qui manque souvent (Le Piège) |
| :--- | :--- | :--- |
| **Portée des Travaux** | Définition exacte de ce qui est inclus et exclu. | Pas d'exclusion explicite. Tout ce qui n'est pas exclu est considéré "dû" par le client. |
| **Gestion des Extras** | Méthode d'autorisation des imprévus. | Absence d'obligation d'un avenant écrit signé AVANT de faire les travaux supplémentaires. |
| **Conditions du Site** | État du bâtiment, accès, alimentation électrique/eau. | Pas de clause prévoyant que les surprises structurelles ou cachées sont aux frais du client. |
| **Délais & Approbations** | Qui est responsable si le client tarde à choisir ses matériaux ? | Pénalités de retard contre l'entrepreneur sans clause suspensive si le client traîne. |
| **Modalités de Paiement** | Échéancier lié aux jalons physiques. | Dernier paiement trop élevé (30% ou +) retenu abusivement sous prétexte de finitions mineures. |
| **Déchets & Nettoyage** | Évacuation des gravats et rebuts. | Non spécifié, ce qui laisse au sous-traitant la charge d'un conteneur à 800 $. |

---

## 2. Exemple de Détection d'Absence par votre Copilote

**Extrait soumis par l'artisan :**
> *"Rénovation complète de la salle de bain selon les choix de madame Tremblay pour la somme forfaitaire de 12 000 $, début des travaux le 1er mai."*

**Diagnostic immédiat par `!AUDIT` :**
1. **Piège 1 (Absence de limite de coût matériel) :** *"Selon les choix de madame Tremblay"* = chèque en blanc. Si elle choisit une céramique d'importation italienne à 45 $/pi², vous êtes déficitaire.
2. **Piège 2 (Absence de clause d'accès) :** Aucune heure de chantier fixée.
3. **Piège 3 (Absence d'acompte) :** Aucun calendrier de déboursement spécifié. Risque de financement total sur vos fonds propres.
4. **Correction immédiate proposée :** Formulation verrouillée avec allocations budgétaires et échéancier 30/40/30.
