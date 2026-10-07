# GearShare API — TP séance 1 (Antoine LI)

API FastAPI en mémoire : CRUD complet sur `items`, ressource `reservations`, découpage en routers.

- [SPEC-reservations.md](SPEC-reservations.md) — la spécification donnée à l'agent
- [REVIEW.md](REVIEW.md) — la review du code généré, avec les corrections
- [NOTES-TP1.md](NOTES-TP1.md) — observations des étapes 0 à 5

## Démarrer

```bash
docker compose up --build
```

- Santé : <http://localhost:8000/health>
- Documentation : <http://localhost:8000/docs> (tags `items`, `reservations`, `monitoring`)

Le montage de volume et `--reload` sont réservés au développement : le code est rechargé à chaque
sauvegarde sans reconstruction de l'image.

## Routes

| Route | Succès | Erreurs |
|---|---|---|
| `GET /items?skip&limit&q&disponible` | 200 | 422 |
| `POST /items` | 201 | 422 |
| `GET /items/{item_id}` | 200 | 404, 422 |
| `PUT /items/{item_id}` | 200 | 404, 422 |
| `PATCH /items/{item_id}` | 200 | 404, 422 |
| `DELETE /items/{item_id}` | 204 | 404, 422 |
| `POST /reservations` | 201 | 422 |
| `GET /reservations?item_id&limit` | 200 | 422 |
| `GET /reservations/{reservation_id}` | 200 | 404, 422 |
| `POST /reservations/{reservation_id}/annuler` | 200 | 404, 409, 422 |
