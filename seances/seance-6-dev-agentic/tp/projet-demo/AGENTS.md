# GearShare

Prêt de matériel entre particuliers. Projet du module full stack (séances 1 à 6).

## Stack et arborescence

- `backend/` : FastAPI, SQLAlchemy 2, PostgreSQL 16, Alembic, pytest. Port 8000.
  - `app/models/` tables SQLAlchemy, `app/schemas/` Pydantic (entrée/sortie de l'API)
  - `app/repositories/` accès base uniquement, `app/services/` règles métier
  - `app/routers/` routes HTTP, minces : elles appellent un service
  - `app/api/deps.py` session (une transaction par requête), `get_current_user`, services
  - `app/core/exceptions.py` erreurs métier, traduites en codes HTTP dans `app/main.py`
  - `alembic/versions/` migrations, `tests/` tests pytest
- `frontend/` : FastAPI + Jinja2, rendu serveur. Port 8080. N'accède jamais à la base,
  seulement à l'API via `app/api_client.py`. Jeton dans un cookie HttpOnly.
- `docs/` : choix techniques, `docs/features/<nom>/` fiche et plan de chaque feature,
  `docs/templates/` modèles de fiche et de plan.

## Commandes

```bash
cp .env.example .env                       # une fois
docker compose up --build                  # db + migrate + backend + frontend
docker compose exec db createdb -U gearshare gearshare_test   # une fois, base de test
docker compose run --rm backend pytest     # tous les tests
docker compose run --rm backend pytest -k avis
docker compose run --rm backend alembic revision --autogenerate -m "message"
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend alembic downgrade -1
```

## Conventions

- Validation des entrées dans les schémas Pydantic (`extra="forbid"`), pas dans les routers.
- Logique métier et contrôles de propriété dans les services, qui lèvent des `DomainError`.
- Codes : 401 non connecté, 403 pas le droit, 404 introuvable, 409 conflit métier
  (doublon, mauvais statut), 422 donnée invalide.
- Les règles qui peuvent l'être sont aussi garanties en base (`CHECK`, `UNIQUE`, FK),
  contraintes nommées `<table>_<règle>`.
- Tests sur la base `gearshare_test`, une transaction annulée par test (`tests/conftest.py`).
  Fixtures : `alice` possède `item_velo`, `bob` l'emprunte (`reservation_bob`), `carol` est tierce.
- Un test par critère d'acceptation, nommé `test_ac_<story>_<critère>_<description>`
  (ex. `test_ac_02_6_un_second_avis_est_refuse`).
- Commits courts en français, un commit par étape du plan.

## Interdits

- Aucun secret dans le code ni dans un fichier versionné (`.env` est ignoré).
- Ne jamais modifier une migration déjà appliquée : en créer une nouvelle.
- Ne jamais lire l'identité (owner_id, borrower_id, auteur) dans le corps d'une requête :
  elle vient du jeton (`CurrentUser`).
- Pas de SQL concaténé avec des valeurs.
- Ne pas toucher aux fichiers hors du périmètre de l'étape en cours.
