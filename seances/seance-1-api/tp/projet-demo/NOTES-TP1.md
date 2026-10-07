# Notes du TP 1 — observations

Auteur : Antoine LI

## Étape 0 — prise en main

- `docker compose up --build` puis `curl http://localhost:8000/health` → `{"status":"ok"}`.
- Modifier le message de `/health` sans reconstruire l'image fonctionne grâce à deux lignes du
  `docker-compose.yml` : le volume `./app:/code/app` (le code du conteneur **est** mon code local)
  et `--reload` d'uvicorn (redémarrage à chaque sauvegarde). Outils de développement uniquement :
  en production, l'image contient le code figé.

## Étape 1 — path parameters

Avant `Path(ge=1)` :

| Requête | Code | Corps |
|---|---|---|
| `GET /items/42` | 200 | `{"item_id": 42}` |
| `GET /items/abc` | 422 | `type: int_parsing`, `loc: ["path", "item_id"]` |
| `GET /items/-1` | 200 | `{"item_id": -1}` — accepté alors qu'un id négatif n'a pas de sens |

Après `Path(ge=1)` : `GET /items/-1` → 422 `greater_than_equal`, et `/docs` affiche `minimum: 1`.

## Étape 2 — query parameters

| Requête | Résultat |
|---|---|
| `/items` | 200, valeurs par défaut `skip=0`, `limit=20` |
| `/items?limit=5&q=velo` | 200 |
| `/items?limit=500` | 422 `less_than_equal` (max 100) |
| `/items?disponible=oui` | 422 `bool_parsing` : `oui` n'est pas une valeur reconnue (`true/false/1/0/yes/no/on/off`) |
| `/items?disponible=peut-etre` | 422 `bool_parsing` |

## Étape 3 — Pydantic

| Essai | Résultat |
|---|---|
| Item valide | 201, corps avec `id` et `disponible: true` par défaut |
| `"titre": "ab"` | 422 `string_too_short`, `loc: ["body", "titre"]` |
| `"tarif_jour": 0` | 422 `greater_than` (`gt=0`) |
| `"couleur": "rouge"` sans `extra="forbid"` | 201, champ **ignoré silencieusement** |
| `"couleur": "rouge"` avec `extra="forbid"` | 422 `extra_forbidden` — conservé |

## Étape 4 — CRUD, cas d'erreur vérifiés

| Requête | Code |
|---|---|
| `GET`, `PUT`, `PATCH`, `DELETE` sur `/items/999` | 404 |
| `PATCH /items/2 {"description": "..."}` | 200, les autres champs inchangés (`exclude_unset=True`) |
| `PATCH /items/2 {"titre": null}` | 422 (500 avant correction, voir [REVIEW.md](REVIEW.md)) |
| `DELETE /items/1` | 204 sans corps, puis `GET /items/1` → 404, puis `DELETE /items/1` → 404 |

## Étape 5 — routers

`main.py` ne contient plus que `/health` et les `include_router`. `/docs` regroupe les routes sous
les tags `items`, `reservations` et `monitoring`.
