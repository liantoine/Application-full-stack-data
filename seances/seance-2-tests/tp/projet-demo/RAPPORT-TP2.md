# Rapport du TP 2 — tester l'API de la séance 1

Auteur : Antoine LI

## Mise en place (étape 0)

- `requirements.txt` : ajout de `pytest`, `pytest-cov`, `httpx` (versions du projet de référence).
- `pytest.ini` : `pythonpath = .` et `testpaths = tests`.
- `Dockerfile` : copie de `pytest.ini` et `tests/` dans l'image.
- `docker-compose.yml` : montage de `./tests` et `./pytest.ini` en plus de `./app`, pour lancer les
  tests sans reconstruire l'image.

```bash
docker compose run --rm api pytest -v
docker compose run --rm api pytest --cov=app --cov-report=term-missing --cov-fail-under=70
```

## Modifications de l'application

1. **Suppression des compteurs globaux `_next_id`** (items et reservations) : l'identifiant est
   déduit du dictionnaire (`max(FAKE_DB, default=0) + 1`). Il ne reste qu'un état par ressource,
   que la fixture `storage` vide. Limite connue : si on supprime l'item d'id maximal, l'id suivant
   le réutilise — une réservation qui pointait sur l'ancien item pointerait sur le nouveau. Les
   séquences PostgreSQL (séance 3/4) règlent le problème.
2. **Notification d'annulation** : `envoyer_notification_annulation(reservation_id=...)` est appelée
   par `POST /reservations/{id}/annuler`. C'est le seul effet de bord externe de l'API, donc le
   seul endroit où un `Mock` est légitime. **Décision** : l'annulation est acquise même si la
   notification échoue (l'erreur est journalisée) — protégée par un test.

## Fixtures (`tests/conftest.py`)

| Fixture | Rôle | Dépend de |
|---|---|---|
| `storage` | Poignée `Storage` sur les vrais `FAKE_DB` ; `reset_all()` avant et après chaque test | — |
| `client` | `TestClient(app)` sur une API vide | `storage` |
| `item_velo` | Un item créé par `POST /items` | `client` |
| `reservation_active` | Une réservation active sur `item_velo` | `client`, `item_velo` |

Tout en scope `function`. Seuls les tests qui préparent un volume de données (pagination,
filtres) déclarent `storage` ; ils ne l'utilisent que dans le `Given`, jamais pour constater.

## Ce qui est testé — 78 tests

| Fichier | Contenu |
|---|---|
| `test_health.py` | `/health` |
| `test_items.py` | CRUD complet : nominal, 422 (8 cas de création, query invalides, ids `0`/`-1`/`abc`), 404 sur `GET`/`PUT`/`PATCH`/`DELETE`, effet de bord du `DELETE`, pagination `skip`/`limit` et limite par défaut, filtres `q` (casse et accents) et `disponible`, `PATCH` partiel et `null` |
| `test_reservations.py` | Création, dates incohérentes (inversées et égales), payloads invalides, filtre `item_id`, `limit`, 404, annulation, 409 sur double annulation, 404 sur annulation absente, notification (appelée une fois, non appelée en cas de 409, échec toléré) |
| `test_schemas.py` | Tests unitaires Pydantic : `model_validator` des dates, `extra="forbid"`, `ItemUpdate` + `exclude_unset`, refus de `null` sur les champs obligatoires |

Règle vérifiée : **chaque `raise HTTPException` des routers a son test** (404 sur les 6 routes qui
ciblent un id, 409 de l'annulation).

Indépendance : chaque fichier passe seul (`pytest tests/test_items.py`…) et chaque test passe
isolé (`pytest -k deja_annulee`).

## Couverture

```text
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
app\main.py                       8      0   100%
app\routers\items.py             48      0   100%
app\routers\reservations.py      41      0   100%
app\schemas\item.py              26      0   100%
app\schemas\reservation.py       20      0   100%
-----------------------------------------------------------
TOTAL                           143      0   100%
```

100 % ne prouve rien à lui seul (la couverture mesure l'exécution, pas la vérification) : c'est
le test de mutation ci-dessous qui montre que les règles sont réellement protégées.

## Test de mutation (exercice imposé)

J'ai cassé volontairement le code, une règle à la fois, et relancé la suite. Un mutant est
« tué » si au moins un test devient rouge.

| Mutation introduite | Résultat | Tests devenus rouges |
|---|---|---|
| Vérification du 409 retirée de l'annulation | Tué (2 échecs) | `test_annuler_une_reservation_deja_annulee_renvoie_409`, `test_annulation_refusee_n_envoie_pas_de_notification` |
| `exclude_unset=True` retiré du `PATCH` | Tué (2) | `test_modifier_un_seul_champ_laisse_les_autres_inchanges`, `test_modifier_la_description_a_null_l_efface` |
| `extra="forbid"` retiré d'`ItemCreate` | Tué (2) | `test_creation_item_invalide_renvoie_422[couleur]`, `test_item_create_refuse_un_champ_inconnu` |
| `<=` remplacé par `<` dans `check_dates` | Tué (2) | cas « dates égales » en HTTP et en unitaire |
| `try/except` retiré autour de la notification | Tué (1) | `test_annulation_reussit_meme_si_la_notification_echoue` |
| Notification jamais envoyée | Tué (1) | `test_annulation_envoie_une_notification` |
| Filtre `disponible` ignoré | Tué (2) | `test_lister_avec_disponible_filtre_les_items` |
| `skip` décalé d'un cran | Tué (9) | tests de pagination et de filtres |
| 404 retiré du `DELETE` | Tué (1) | `test_supprimer_un_item_absent_renvoie_404` |
| Refus de `null` retiré d'`ItemUpdate` | Tué (6) | unitaires + `test_modifier_un_champ_obligatoire_a_null_renvoie_422` |
| Filtre `item_id` des réservations ignoré | Tué (1) | `test_lister_filtre_par_item_id` |

**11 mutants sur 11 tués.** Le mutant « `<=` → `<` » est le plus instructif : sans le cas
« dates égales », la suite serait restée verte avec seulement le cas « dates inversées ».

## Mocks : ce que je n'ai pas mocké

- Le stockage : c'est le vrai dictionnaire, remis à zéro par `storage`.
- `TestClient` et les routes : c'est le sujet des tests.

Seule `envoyer_notification_annulation` est remplacée (`monkeypatch` + `Mock`), parce que c'est un
appel externe dont on veut contrôler l'échec (`side_effect`).
