# GearShare API — TP séance 2 (Antoine LI)

L'API de la séance 1 (CRUD `items`, ressource `reservations`), avec sa suite de tests pytest.

- [RAPPORT-TP2.md](RAPPORT-TP2.md) — fixtures, cas couverts, couverture, test de mutation
- [SPEC-reservations.md](SPEC-reservations.md) et [REVIEW.md](REVIEW.md) — livrables de la séance 1

## Démarrer

```bash
docker compose up --build
```

API sur <http://localhost:8000/health>, documentation sur <http://localhost:8000/docs>.

## Lancer les tests

```bash
docker compose run --rm api pytest -v
docker compose run --rm api pytest --cov=app --cov-report=term-missing --cov-fail-under=70
```

`app/`, `tests/` et `pytest.ini` sont montés en volume : pas besoin de reconstruire l'image après
une modification.

```text
tests/
├── conftest.py            # Storage, storage, client, item_velo, reservation_active
├── test_health.py
├── test_items.py
├── test_reservations.py
└── test_schemas.py        # tests unitaires Pydantic, sans HTTP
```
