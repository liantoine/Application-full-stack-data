# Plan d'implémentation — Avis sur les prêts terminés

**Fiche** : [fiche.md](fiche.md)
**Statut** : validé

## 1. Rappel du périmètre

- User stories couvertes par ce plan : US-01 (clôturer un prêt), US-02 (laisser un avis),
  US-03 (voir la réputation d'une annonce).
- Hors plan : modification d'un avis, notation de l'emprunteur, modération, moyenne dans la
  liste des annonces, clôture automatique (voir fiche, sections 5 et 8).

## 2. Décisions retenues

Reprises de la fiche :

- Le prêteur clôture explicitement une réservation `active` ; pas de condition de date.
- Avis = note entière de 1 à 5 + commentaire optionnel (1000 caractères max), un seul par
  réservation, par l'emprunteur uniquement, non modifiable.
- Moyenne et nombre d'avis calculés à la lecture, affichés sur la page de l'annonce avec la
  liste des avis.

Décisions techniques :

- Clôture : on étend le `PATCH /reservations/{id}` existant (`{"statut": "terminee"}`) plutôt
  que d'ajouter une route. `ReservationUpdate.statut` devient `Literal["annulee", "terminee"]`.
  L'aiguillage se fait dans le service (`changer_statut`), le router reste mince.
- Clôture refusée à l'emprunteur : `403` (`AccesRefuse`). Réservation pas active : `409`.
- Création : `POST /reservations/{id}/avis` -> `201`. Lecture : `GET /items/{id}/avis` -> `200`,
  publique comme `GET /items/{id}`. Les deux routes dans un nouveau `routers/avis.py`.
- Ordre des contrôles à la création : réservation introuvable `404`, pas l'emprunteur `403`,
  pas terminée `409`, doublon `409`. Note ou commentaire invalide : `422` (schéma Pydantic,
  note en `strict` pour refuser `3.5` et `true`).
- Table `avis` : `reservation_id` seul (l'auteur et l'item se retrouvent par la réservation,
  pas de colonne dupliquée qui pourrait diverger). `ON DELETE CASCADE` comme
  `reservations.item_id`.
- Doublon : contrôle dans le service (message clair) **et** `UNIQUE` en base pour le cas de
  deux requêtes simultanées ; l'`IntegrityError` du `UNIQUE` est traduite en `ConflitMetier`
  dans le repository.
- Moyenne arrondie à 2 décimales, `null` quand il n'y a aucun avis.
- Frontend : appel à `/auth/me` sur la page de l'annonce pour savoir si l'utilisateur est le
  prêteur (bouton « Clôturer ») ou l'emprunteur (formulaire d'avis).

## 3. Étapes

### Étape 1 — Clôturer une réservation (prérequis)

- **Objectif** : le propriétaire de l'item peut passer une réservation active à `terminee`.
- **Fichiers touchés** :
  - `backend/app/schemas/reservation.py`
  - `backend/app/services/reservation.py`
  - `backend/app/routers/reservations.py`
  - `backend/tests/test_cloture.py` (nouveau)
  - `backend/tests/test_autorisation.py`
- **Changements** :
  - `ReservationUpdate.statut : Literal["annulee", "terminee"]`.
  - `ReservationService.cloturer(id, current_user_id)` : `AccesRefuse` si l'utilisateur n'est
    pas le propriétaire de l'item, `ConflitMetier` si le statut n'est pas `active`.
  - `ReservationService.changer_statut(id, statut, current_user_id)` qui appelle `annuler` ou
    `cloturer` ; le router appelle `changer_statut`.
- **Tests à écrire** :
  - `test_ac_01_1_le_proprietaire_cloture_une_reservation_active`
  - `test_ac_01_2_cloture_sans_jeton_refusee`
  - `test_ac_01_3_cloture_par_l_emprunteur_ou_un_tiers_refusee` (paramétré Bob, Carol)
  - `test_ac_01_4_cloture_d_une_reservation_pas_active_refusee` (paramétré annulee, terminee)
  - `test_ac_01_5_cloture_d_une_reservation_inexistante`
  - lignes `PATCH ... terminee` dans la matrice d'autorisation
- **Critères d'acceptation couverts** : AC-01.1 à AC-01.5
- **Vérification** :

  ```bash
  docker compose run --rm backend pytest -k "ac_01 or matrice"
  ```

### Étape 2 — Table `avis` et migration

- **Objectif** : la table existe avec ses contraintes, la migration monte et descend.
- **Fichiers touchés** :
  - `backend/app/models/avis.py` (nouveau)
  - `backend/app/models/__init__.py`
  - `backend/app/models/reservation.py` (relation `avis`)
  - `backend/alembic/versions/<rev>_table_avis.py` (nouveau)
  - `backend/tests/test_avis_contraintes.py` (nouveau)
- **Changements** :
  - `avis(id, reservation_id FK -> reservations ON DELETE CASCADE, note SMALLINT, commentaire
    TEXT NULL, created_at)`.
  - Contraintes : `avis_reservation_unique` (`UNIQUE reservation_id`), `avis_note_bornes`
    (`CHECK note BETWEEN 1 AND 5`), `avis_commentaire_longueur`
    (`CHECK char_length(commentaire) <= 1000`).
  - Migration avec `downgrade` (`drop_table`).
- **Tests à écrire** (contraintes vérifiées directement en base, sans passer par l'API) :
  - `test_contrainte_note_hors_bornes_refusee_en_base`
  - `test_contrainte_un_seul_avis_par_reservation_en_base`
- **Critères d'acceptation couverts** : socle de AC-02.6 et AC-02.7 (garantie en base)
- **Vérification** :

  ```bash
  docker compose run --rm backend alembic upgrade head
  docker compose run --rm backend alembic downgrade -1
  docker compose run --rm backend alembic upgrade head
  docker compose run --rm backend pytest -k contrainte
  ```

### Étape 3 — Laisser un avis

- **Objectif** : l'emprunteur d'une réservation terminée peut laisser un avis, une seule fois.
- **Fichiers touchés** :
  - `backend/app/schemas/avis.py` (nouveau)
  - `backend/app/repositories/avis.py` (nouveau)
  - `backend/app/services/avis.py` (nouveau)
  - `backend/app/routers/avis.py` (nouveau)
  - `backend/app/api/deps.py`
  - `backend/app/main.py`
  - `backend/tests/test_avis.py` (nouveau)
  - `backend/tests/test_autorisation.py`
- **Changements** :
  - `AvisCreate` (`note: int` strict 1..5, `commentaire: str | None` max 1000,
    `extra="forbid"`), `AvisRead` (id, reservation_id, note, commentaire, auteur, created_at).
  - `AvisService.creer(reservation_id, current_user_id, note, commentaire)` avec les contrôles
    dans l'ordre de la section 2.
  - `POST /reservations/{reservation_id}/avis`, protégé par `CurrentUser`.
- **Tests à écrire** :
  - `test_ac_02_1_l_emprunteur_laisse_un_avis_sur_un_pret_termine`
  - `test_ac_02_2_avis_sans_commentaire_accepte`
  - `test_ac_02_3_avis_sans_jeton_refuse`
  - `test_ac_02_4_avis_par_le_preteur_ou_un_tiers_refuse` (paramétré Alice, Carol)
  - `test_ac_02_5_avis_sur_un_pret_non_termine_refuse` (paramétré active, annulee)
  - `test_ac_02_6_un_second_avis_est_refuse`
  - `test_ac_02_7_note_hors_bornes_refusee` (paramétré 0, 6, 3.5)
  - `test_ac_02_8_commentaire_trop_long_refuse`
  - `test_ac_02_9_avis_sur_une_reservation_inexistante`
  - lignes `POST /reservations/{resa}/avis` dans la matrice
- **Critères d'acceptation couverts** : AC-02.1 à AC-02.9
- **Vérification** :

  ```bash
  docker compose run --rm backend pytest -k "ac_02 or matrice"
  ```

### Étape 4 — Lire la réputation d'une annonce

- **Objectif** : moyenne, nombre et liste des avis d'un item, lisibles sans connexion.
- **Fichiers touchés** :
  - `backend/app/schemas/avis.py`
  - `backend/app/repositories/avis.py`
  - `backend/app/services/avis.py`
  - `backend/app/routers/avis.py`
  - `backend/tests/test_avis.py`
  - `backend/tests/test_autorisation.py`
- **Changements** :
  - `AvisRepository.resume(item_id)` (`count`, `avg` en une requête) et
    `list_par_item(item_id)` (jointure sur `reservations`, auteur chargé avec `selectinload`).
  - `ReputationRead(item_id, nombre_avis, note_moyenne, avis: list[AvisRead])`.
  - `GET /items/{item_id}/avis`, `404` si l'item n'existe pas.
- **Tests à écrire** :
  - `test_ac_03_1_moyenne_nombre_et_avis_visibles_sans_connexion`
  - `test_ac_03_2_annonce_sans_avis`
  - `test_ac_03_3_reputation_d_une_annonce_inexistante`
  - `test_ac_03_4_seuls_les_avis_de_l_annonce_sont_comptes`
  - lignes `GET /items/{item}/avis` dans la matrice
- **Critères d'acceptation couverts** : AC-03.1 à AC-03.4
- **Vérification** :

  ```bash
  docker compose run --rm backend pytest
  ```

### Étape 5 — Frontend

- **Objectif** : clôturer, laisser un avis et voir la réputation depuis la page de l'annonce.
- **Fichiers touchés** :
  - `frontend/app/api_client.py`
  - `frontend/app/routers/items.py`
  - `frontend/app/routers/reservations.py`
  - `frontend/app/templates/items/detail.html`
  - `frontend/app/static/style.css`
- **Changements** :
  - `ApiClient.me`, `ApiClient.get_reputation`, `ApiClient.create_avis`.
  - Page de l'annonce : bloc réputation (toujours affiché), bouton « Clôturer » sur les
    réservations actives si l'utilisateur est le prêteur, formulaire d'avis sur les réservations
    terminées sans avis si l'utilisateur est l'emprunteur.
  - `POST /reservations/{id}/avis` côté frontend : PRG, erreurs `409`/`422` réaffichées sur la
    page de l'annonce avec la saisie.
  - Message de conflit sur le statut généralisé (« n'est plus active » au lieu de « déjà annulée »).
- **Tests à écrire** : pas de tests automatisés du frontend dans le projet ; recette manuelle
  (section 6).
- **Critères d'acceptation couverts** : affichage de AC-01.1, AC-02.1, AC-02.6, AC-03.1, AC-03.2
- **Vérification** : recette manuelle de la section 6.

## 4. Traçabilité critères -> tests

| Critère | Test | Étape |
|---|---|---|
| AC-01.1 | `test_ac_01_1_le_proprietaire_cloture_une_reservation_active` | 1 |
| AC-01.2 | `test_ac_01_2_cloture_sans_jeton_refusee` | 1 |
| AC-01.3 | `test_ac_01_3_cloture_par_l_emprunteur_ou_un_tiers_refusee` | 1 |
| AC-01.4 | `test_ac_01_4_cloture_d_une_reservation_pas_active_refusee` | 1 |
| AC-01.5 | `test_ac_01_5_cloture_d_une_reservation_inexistante` | 1 |
| AC-02.1 | `test_ac_02_1_l_emprunteur_laisse_un_avis_sur_un_pret_termine` | 3 |
| AC-02.2 | `test_ac_02_2_avis_sans_commentaire_accepte` | 3 |
| AC-02.3 | `test_ac_02_3_avis_sans_jeton_refuse` | 3 |
| AC-02.4 | `test_ac_02_4_avis_par_le_preteur_ou_un_tiers_refuse` | 3 |
| AC-02.5 | `test_ac_02_5_avis_sur_un_pret_non_termine_refuse` | 3 |
| AC-02.6 | `test_ac_02_6_un_second_avis_est_refuse` (+ `test_contrainte_un_seul_avis_par_reservation_en_base`) | 2, 3 |
| AC-02.7 | `test_ac_02_7_note_hors_bornes_refusee` (+ `test_contrainte_note_hors_bornes_refusee_en_base`) | 2, 3 |
| AC-02.8 | `test_ac_02_8_commentaire_trop_long_refuse` | 3 |
| AC-02.9 | `test_ac_02_9_avis_sur_une_reservation_inexistante` | 3 |
| AC-03.1 | `test_ac_03_1_moyenne_nombre_et_avis_visibles_sans_connexion` | 4 |
| AC-03.2 | `test_ac_03_2_annonce_sans_avis` | 4 |
| AC-03.3 | `test_ac_03_3_reputation_d_une_annonce_inexistante` | 4 |
| AC-03.4 | `test_ac_03_4_seuls_les_avis_de_l_annonce_sont_comptes` | 4 |

## 5. Migration et retour arrière

- La migration ne fait que créer la table `avis` ; son `downgrade` la supprime. Aucune donnée
  existante n'est modifiée (la clôture réutilise le statut `terminee`, déjà autorisé).
- Annuler la feature après livraison : `alembic downgrade -1` supprime les avis (perte des avis
  saisis, à exporter avant si besoin), puis revert des commits. Les réservations passées à
  `terminee` restent valides pour le schéma existant.

## 6. Recette manuelle

1. `docker compose up --build`, créer deux comptes : Alice (prêteuse) et Bob (emprunteur).
2. Alice publie un objet. Bob le réserve.
3. Bob, sur l'annonce : pas de bouton « Clôturer », pas de formulaire d'avis (prêt actif).
4. Alice, sur l'annonce : bouton « Clôturer » sur la réservation de Bob ; elle clôture, le
   statut passe à `terminee`.
5. Bob, sur l'annonce : formulaire d'avis. Note 6 forcée dans l'outil de dev -> message d'erreur.
   Note 4 + commentaire -> l'avis apparaît, la moyenne affiche 4 / 5 (1 avis).
6. Bob renvoie le formulaire (retour arrière du navigateur puis envoi) -> message « avis déjà
   laissé », l'avis d'origine est inchangé.
7. Déconnecté : la moyenne et les avis sont visibles, aucun bouton.
8. Commentaire `<script>alert(1)</script>` : affiché en texte, pas exécuté.
