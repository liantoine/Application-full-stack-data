# Ressource : reservations

Auteur : Antoine LI

Fichiers : `app/schemas/reservation.py`, `app/routers/reservations.py`
Stockage : dictionnaire en mémoire dans le router (comme `items`)

## Schémas
- `ReservationCreate` : item_id (int, >= 1), date_debut (date), date_fin (date).
  Champs inconnus refusés (`extra="forbid"`, comme `ItemCreate`).
- `ReservationRead` : id, item_id, date_debut, date_fin, statut ("active" | "annulee")

## Routes (préfixe /reservations, tag "reservations")
- POST ""              → 201, ReservationRead, statut "active". 422 si date_fin <= date_debut.
- GET  ""              → 200, list[ReservationRead]. Query : item_id optionnel (>= 1), limit (défaut 20, min 1, max 100).
- GET  "/{reservation_id}" → 200, ReservationRead. 404 si absente.
- POST "/{reservation_id}/annuler" → 200, ReservationRead avec statut "annulee".
                                     404 si absente, 409 si déjà annulée.

`reservation_id` : entier >= 1 (`Path(ge=1)`), comme `item_id` dans `items`.

## Contraintes
- Aucun accès à FAKE_DB de items.
- response_model sur toutes les routes.
- Pas de logique de validation en `if` dans le router : tout ce qui peut l'être dans Pydantic.
- La validation croisée `date_fin > date_debut` est un `model_validator` de `ReservationCreate`.
- Routes `def` synchrones (pas d'`async def` sans `await`).
- Aucune nouvelle dépendance dans `requirements.txt`.
